# Contributing to LuckyBrain

Thanks for helping build LuckyBrain. This is an early-stage project: questions,
bug reports, use cases, documentation, tests, design proposals, and
implementations are all valuable contributions.

## Find or propose work

- Read the [project principles](README.md#principles), [architecture](docs/architecture.md),
  [roadmap](docs/roadmap.md), and [security policy](SECURITY.md).
- Search existing issues and pull requests before starting substantial work.
  For a large feature or public API change, open an issue or design proposal
  first to discuss the use case, alternatives, trade-offs, and migration path.
- Contributions are not limited to existing folders or listed roadmap items.
  You may propose new packages, directories, integrations, modalities, or
  project-wide improvements. Explain the responsibility and how it fits the
  architecture; folder names are not an approval boundary.
- Check the current package version and implemented behavior before writing
  examples or documentation. Be clear when describing proposals or experimental
  functionality; do not document plans as if they already work.

## Local development

Use Python 3.11 or newer. Install the package and development tools in an
isolated environment:

```bash
python -m venv .venv
# Activate the environment for your shell, then:
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

Format changed Python files with `python -m ruff format .`. Add or update tests
for behavior changes. Tests should be deterministic and should not require live
model, database, or network credentials.

## Security and privacy

Security is part of every contribution, not a separate folder or final review
step:

- Never commit API keys, tokens, private datasets, personal information, or
  production logs. Use environment variables or a secret manager for local
  credentials, and sanitized fixtures for tests.
- Treat user content, retrieved documents, media, model output, and tool
  arguments as untrusted. Validate inputs and bound file sizes, work, and
  network activity where applicable.
- Give integrations and tools only the permissions they need. Make data sent
  to external providers, retention behavior, and side effects clear.
- Avoid logging secrets or sensitive content. Add tests for security-relevant
  validation and failure behavior.
- Report suspected vulnerabilities privately as described in
  [Security Policy](SECURITY.md), not in a public issue.

## Pull requests

- Explain the user problem and the behavior your change adds or corrects.
- Keep changes focused. Include tests and update directly related docs when
  behavior, setup, security, or supported APIs change.
- Keep public API changes deliberate and document compatibility impact.
- Run the relevant checks above before requesting review; report any checks you
  could not run and why.
- Do not include secrets, private data, generated indexes, or unrelated
  formatting changes.

## Design proposals

For a new module, integration, or abstraction, describe its intended users,
responsibility, a small usage example, provider-neutrality needs, data and
security implications, failure behavior, and how it will be tested or
evaluated. Prefer a new well-scoped package when it makes the architecture
clearer; there is no requirement to force unrelated capabilities into the
current folders.

By participating, you agree to follow the standards in
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
