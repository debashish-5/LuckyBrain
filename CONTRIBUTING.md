# Contributing to LuckyBrain

Thanks for helping build LuckyBrain. It is an early project, so thoughtful questions, use cases, documentation, tests, and small implementations are all valuable contributions.

## Before you start

- Read the [project principles](README.md#project-principles) and [architecture notes](docs/architecture.md).
- Search existing issues and pull requests before starting substantial work. For a new feature, open an issue first to discuss its use case and fit.
- For significant design changes, propose the problem, alternatives, trade-offs, and a migration path before writing a large implementation.
- Keep changes focused. Avoid adding provider dependencies to core unless the project has agreed that they belong there.

## Local development

Use Python 3.11 or newer. Install the package and development tools in an isolated environment:

```bash
python -m venv .venv
# Activate the environment for your shell, then:
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

Format changed Python files with `python -m ruff format .`. Add or update tests for behavior changes. Tests should be deterministic and should not require live model, database, or network credentials.

## Pull requests

- Explain the user problem and the behavior your change adds or corrects.
- Keep public API changes minimal and document any compatibility impact.
- Include focused tests and update docs when behavior or setup changes.
- Run the checks above before requesting review.
- Never include secrets, private data, generated indexes, or unrelated formatting changes.

## Design proposals

When proposing a module or abstraction, include its intended users, a small usage example, provider-neutrality needs, failure behavior, and how it will be evaluated. The project favors composable interfaces and measurable quality over feature count.

By participating, you agree to follow the standards in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).