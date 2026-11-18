<p align="right"><strong>English</strong> · <a href="README.zh_CN.md">简体中文</a></p>

# CodeCraft AI Hardware

A development reference for Seeed devices: device knowledge, native BSPs and examples, cloud Skill contracts, and standalone Agent workflows. The four cloud API client Skills are maintained under [skills/](skills/README.md); the cloud service and account infrastructure remain external.

Start with [AGENTS.md](AGENTS.md). [Devices](devices/AGENTS.md) and the [native interface matrix](docs/inventory.md) are generated from their source manifests.

## Quick start

```sh
python3 codecraft.py catalog
python3 codecraft.py discover --interface display
python3 codecraft.py cloud-catalog
python3 codecraft.py check-cloud-skills
python3 codecraft.py resolve-capability --capability asr
python3 codecraft.py context --target esp-idf/reterminal-e1001
python3 codecraft.py validate --static
python3 codecraft.py validate --target esp-idf/reterminal-e1001
```

Activate the Target's declared toolchain before building. To create a portable private workspace:

```sh
python3 codecraft.py new --target esp-idf/reterminal-e1001 --example epd_hello --output projects/my-e1001-project
python3 codecraft.py build-project projects/my-e1001-project
```

The output directory must not already exist. `project.yaml` records selections; `codecraft.lock` records imported file hashes, the repository revision and toolchain. Generated projects and build logs are not committed. `projects/` is ignored; explicit external paths remain supported. Use codecraft-ideate and `new --brief <file.json>` to capture purpose, target users, scenarios and BOM in project.yaml and the generated application AGENTS region. See [project workspaces](docs/development/project-workspaces.md).

The public entry is also included in new exports; from an application directory use `python3 codecraft.py build-project .`. No global CLI installation is needed. Standalone cloud Skills remain independent; maintain package releases through the [candidate workflow](docs/development/skill-releases.md).

## Optional SenseCraft platform tool

For SenseCraft devices, telemetry, CodeCraft Hub, files, model-library management or cloud deployment, use the external [sensecraft-cli](https://github.com/Seeed-Solution/sensecraft-cli) and its official Agent Skill. The verified package version is 0.5.0 (Node.js 16+):

```sh
npx --yes @seeed-studio/sensecraft-cli@0.5.0 --version
npx --yes @seeed-studio/sensecraft-cli@0.5.0 --help
```

See [installation, Skill discovery and task routing](docs/development/sensecraft-cli.md). Native development does not require this tool; installation does not authorize cloud operations. The existing LLM/ASR/TTS/image-generation clients remain separate from these platform-management commands.

## Structure and contribution

`devices/` owns facts and sources; `platforms/` owns native implementations; `capabilities/` owns contracts consumed by cloud Skills; `skills/` owns orchestration, scripts and contract tests. Read [architecture](docs/architecture/overview.md) and [contribution rules](.github/CONTRIBUTING.md).

After source metadata changes, run `python3 codecraft.py generate`, then `python3 codecraft.py generate --check`. CI and discovery use the same Target records. The complete software gate is `python3 codecraft.py validate`; physical verification is separate and remains unperformed until real evidence is recorded.

Apache License 2.0. Retained third-party attributions: [NOTICE](NOTICE).

V0.2 implementation is tracked in the [TODO ledger](docs/development/v0.2-todo.md); [CONTRIBUTION.md](CONTRIBUTION.md) links the maintenance rules. The external SenseCraft CLI is referenced directly; simulation and physical acceptance remain open work items.
