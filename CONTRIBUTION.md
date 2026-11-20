# Repository maintenance entry

For changes to reference sources, start with [AGENTS.md](AGENTS.md), including Part II and its task routing table. Follow the [contribution process](.github/CONTRIBUTING.md), [AI development guide](docs/development/ai-guide.md) and [validation ownership](docs/development/testing.md). This entry adds navigation, not a second set of contribution rules.

[Architecture](docs/architecture/overview.md) describes current implementation. The [V0.2 implementation ledger](docs/development/v0.2-todo.md) distinguishes completed work from the design target and records pending integration and acceptance.

Private applications belong in ignored `projects/<name>` workspaces or explicitly selected external directories. Creating an application does not make it a repository contribution. See [project workspaces](docs/development/project-workspaces.md). Promote reusable native changes only through their owning Platform/Target and the contribution gate; never register a private application as a reference dependency.
