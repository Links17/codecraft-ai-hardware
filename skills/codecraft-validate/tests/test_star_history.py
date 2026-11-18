"""Offline checks for the README chart workflow, invoked by the public runner."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / '.github/star-history.cjs'
NS = {'svg': 'http://www.w3.org/2000/svg'}


def evaluate(body, payload=None):
    script = """
const chart = require(process.argv[1]);
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
(async () => {
""" + body + "\n})().catch(error => { console.error(error); process.exitCode = 1; });"
    run = subprocess.run(['node', '-e', script, str(MODULE)],
                         input=json.dumps(payload or {}), text=True,
                         capture_output=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr
    return json.loads(run.stdout)


def test_zero_stars_have_a_zero_line_and_month_labels_in_both_themes():
    charts = evaluate("""
const repository = {full_name: 'owner/repo', created_at: '2026-11-17T09:29:16Z', stargazers_count: 0};
const series = chart.monthlySeries(repository, [], new Date('2026-11-18T05:36:30.892Z'));
console.log(JSON.stringify(['light', 'dark'].map(theme => chart.renderChart(repository, series, theme))));
""")
    for svg in charts:
        root = ET.fromstring(svg)
        assert [node.text for node in root.findall('.//svg:text[@class="x-tick"]', NS)] == ['2026-11']
        assert [node.text for node in root.findall('.//svg:text[@class="y-tick"]', NS)] == ['0', '1']
        assert root.find('.//svg:path[@class="star-line"]', NS).get('d') == 'M64,272.00 L766,272.00'
        assert 'No stars yet' in svg and '0 stars' in svg
        assert '.892' not in svg and 'NaN' not in svg and 'Infinity' not in svg
    assert '#ffffff' in charts[0] and '#0d1117' in charts[1]


def test_zero_star_history_covers_quiet_months():
    series = evaluate("""
const repository = {created_at: '2026-08-20T00:00:00Z', stargazers_count: 0};
console.log(JSON.stringify(chart.monthlySeries(repository, [], new Date('2026-11-18T00:00:00Z'))));
""")
    assert series == [{'month': f'2026-{month:02}', 'count': 0} for month in range(8, 12)]


def test_single_month_with_stars_has_integer_counts_and_a_visible_line():
    result = evaluate("""
const repository = {full_name: 'owner/repo', created_at: '2026-11-17T00:00:00Z', stargazers_count: 1};
const weeks = [{week: Date.parse('2026-11-15T00:00:00Z') / 1000, days: [0, 0, 1, 0, 0, 0, 0]}];
const series = chart.monthlySeries(repository, weeks, new Date('2026-11-18T00:00:00Z'));
console.log(JSON.stringify({series, svg: chart.renderChart(repository, series, 'light')}));
""")
    assert result['series'] == [{'month': '2026-11', 'count': 1}]
    root = ET.fromstring(result['svg'])
    assert root.find('.//svg:path[@class="star-line"]', NS).get('d') == 'M64,96.00 L766,96.00'
    assert 'No stars yet' not in result['svg']


def test_week_boundaries_year_changes_and_removed_stars_keep_monthly_counts():
    series = evaluate("""
const repository = {created_at: '2025-11-01T00:00:00Z', stargazers_count: 8};
const weeks = [
  {week: Date.parse('2026-02-01T00:00:00Z') / 1000, days: [4, 0, 0, 0, 0, 0, 0]},
  {week: Date.parse('2026-01-25T00:00:00Z') / 1000, days: [0, 0, 0, 0, 0, 0, 3]},
  {week: Date.parse('2025-11-30T00:00:00Z') / 1000, days: [1, 2, 0, 0, 0, 0, 0]},
];
console.log(JSON.stringify(chart.monthlySeries(repository, weeks, new Date('2026-02-02T00:00:00Z'))));
""")
    assert series == [
        {'month': '2025-11', 'count': 1}, {'month': '2025-12', 'count': 3},
        {'month': '2026-01', 'count': 6}, {'month': '2026-02', 'count': 8},
    ]


def test_long_history_keeps_readable_month_labels_and_escapes_repository_text():
    svg = evaluate("""
const repository = {full_name: 'owner/<repo>&', created_at: '2018-01-01T00:00:00Z', stargazers_count: 0};
const series = chart.monthlySeries(repository, [], new Date('2026-11-18T00:00:00Z'));
console.log(JSON.stringify(chart.renderChart(repository, series, 'light')));
""")
    root = ET.fromstring(svg)
    labels = [node.text for node in root.findall('.//svg:text[@class="x-tick"]', NS)]
    assert len(labels) == 7 and len(set(labels)) == 7
    assert labels[0] == '2018-01' and labels[-1] == '2026-11'
    assert all(re.fullmatch(r'\d{4}-\d{2}', label) for label in labels)
    assert root.find('svg:title', NS).text.endswith('owner/<repo>&')


def test_invalid_or_missing_history_is_not_silently_rendered_as_zero():
    errors = evaluate("""
const repository = {created_at: '2026-11-01T00:00:00Z', stargazers_count: 1};
const week = {week: 1794700800, days: [0, 0, 1, 0, 0, 0, 0]};
const inputs = [[], null, [week, week], [{...week, days: [0]}],
  [{...week, days: [-1, 0, 0, 0, 0, 0, 0]}], [{...week, week: 'invalid'}]];
console.log(JSON.stringify(inputs.map(weeks => {
  try { chart.monthlySeries(repository, weeks, new Date('2026-11-18T00:00:00Z')); return false; }
  catch { return true; }
})));
""")
    assert errors == [True] * 6


def test_api_or_validation_failure_preserves_both_existing_images():
    with tempfile.TemporaryDirectory() as directory:
        for theme in ('light', 'dark'):
            (Path(directory) / f'star-history-{theme}.svg').write_text(theme)
        result = evaluate("""
const repository = {full_name: 'owner/repo', created_at: '2026-11-01T00:00:00Z', stargazers_count: 1};
const failures = [];
for (const paginate of [async () => { throw new Error('API unavailable'); }, async () => []]) {
  const github = {rest: {repos: {get: async () => ({data: repository})}}, paginate};
  try { await chart.updateCharts({github, repo: {owner: 'owner', repo: 'repo'}, directory: input.directory}); }
  catch { failures.push(true); }
}
console.log(JSON.stringify(failures));
""", {'directory': directory})
        assert result == [True, True]
        for theme in ('light', 'dark'):
            assert (Path(directory) / f'star-history-{theme}.svg').read_text() == theme


def test_update_uses_paginated_history_and_unchanged_counts_produce_identical_files():
    with tempfile.TemporaryDirectory() as directory:
        result = evaluate("""
const repository = {full_name: 'owner/repo', created_at: '2026-10-30T00:00:00Z', stargazers_count: 3};
const calls = [];
const github = {
  rest: {repos: {get: async repo => { calls.push(repo); return {data: repository}; }}},
  paginate: async (route, parameters) => {
    calls.push({route, parameters});
    return [
      {week: Date.parse('2026-11-01T00:00:00Z') / 1000, days: [2, 0, 0, 0, 0, 0, 0]},
      {week: Date.parse('2026-10-25T00:00:00Z') / 1000, days: [0, 0, 0, 0, 0, 1, 0]},
    ];
  },
};
const options = {github, repo: {owner: 'owner', repo: 'repo'}, directory: input.directory};
const files = await chart.updateCharts({...options, now: new Date('2026-11-18T00:00:00Z')});
const first = files.map(file => fs.readFileSync(file, 'utf8'));
await chart.updateCharts({...options, now: new Date('2026-11-19T00:00:00Z')});
console.log(JSON.stringify({calls, first, second: files.map(file => fs.readFileSync(file, 'utf8'))}));
""", {'directory': directory})
        assert result['calls'][0] == {'owner': 'owner', 'repo': 'repo'}
        assert result['calls'][1] == {
            'route': 'GET /repos/{owner}/{repo}/stargazers/history',
            'parameters': {'owner': 'owner', 'repo': 'repo', 'per_page': 30},
        }
        assert result['first'] == result['second']
        assert len(list(Path(directory).glob('*.svg'))) == 2
        for svg in result['first']:
            root = ET.fromstring(svg)
            assert [node.text for node in root.findall('.//svg:text[@class="x-tick"]', NS)] == ['2026-10', '2026-11']
            assert '3 stars' in svg
