# README Star History

The root README language pair uses generated light and dark SVG charts in
`docs/assets/`. The horizontal labels are UTC calendar months (`YYYY-MM`).
A zero-star repository shows a line at zero and "No stars yet"; a single month
uses a horizontal segment, so date-axis milliseconds can never appear.

The internal workflow module [.github/star-history.cjs](../../.github/star-history.cjs)
reads repository metadata and all pages of GitHub's
[star history API](https://github.blog/changelog/2026-09-04-new-api-endpoint-provides-privacy-safe-star-history-data/).
Daily additions are accumulated into calendar months, including months without
new stars. The current month's point uses the repository's current star count,
which can decrease when stars are removed. The charts contain no stargazer
identities or credentials. Do not edit the generated SVGs by hand.

The [Update Star History workflow](../../.github/workflows/star-history.yml)
runs daily at 02:17 UTC (10:17 Asia/Shanghai), on changes to its implementation,
or manually through GitHub Actions. GitHub's built-in `GITHUB_TOKEN` supplies
repository access; no personal token or additional secret is required. Only the
two chart files are committed, and only when their contents change. An API or
data-validation failure fails the job and leaves the existing charts in place.
GitHub's image cache can delay the displayed update.

Scheduled runs require the workflow on the repository's default branch (`main`).
Until it is merged there, an implementation push can refresh that branch once,
but the daily schedule is not active. GitHub may delay scheduled jobs and disables
public-repository schedules after 60 days without repository activity; re-enable
the workflow in Actions if necessary. Repository policy must permit the workflow
to push its chart commit; branch protection is not bypassed.

The implementation is an internal module for `actions/github-script`, not an
additional command-line entry point. Its offline tests require `node` on `PATH`;
the workflow uses the Node.js 24 runtime bundled with `actions/github-script` v8.
Run its offline host checks through the public repository CLI:

```sh
python3 codecraft.py test --path skills/codecraft-validate/tests/test_star_history.py
```
