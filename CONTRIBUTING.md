# Contributing to LuckyBrain

Thank you for considering a contribution. LuckyBrain is an early-stage project,
so clear bug reports, focused tests, documentation, design proposals, and code
are all useful. You do not need to be an expert in RAG or work within an
existing folder to contribute.

## Contribution workflow

1. **Get oriented.** Read the [README](README.md), [architecture](docs/architecture.md),
   [roadmap](docs/roadmap.md), and [security policy](SECURITY.md). Check what is
   implemented today; roadmap items are proposals, not existing features.
2. **Choose an issue or describe your idea.** Search existing issues and pull
   requests first. Small fixes can go straight to a pull request. For a new
   feature, new subsystem, dependency, or public API change, open an issue or
   discussion before investing in a large implementation. Explain the problem,
   intended users, and why the change belongs in LuckyBrain.
3. **Agree on the shape for larger work.** Outline alternatives, trade-offs,
   compatibility impact, testing, security, privacy, and data-handling needs.
   Wait for maintainer feedback before making a large change; this helps avoid
   wasted work but does not guarantee acceptance.
4. **Make a focused change.** Work on a branch or fork, keep unrelated changes
   out of the patch, and add tests and documentation alongside behavior changes.
5. **Run the relevant checks** described below. Include the results in your
   pull request, and mention any check you could not run.
6. **Open a pull request** against the official LuckyBrain repository. Describe
   the problem, solution, important trade-offs, and how reviewers can verify
   it. Respond to review feedback and update the pull request until it is ready.

Example branch names: `fix/document-validation`,
`feat/image-input-contract`, or `docs/contributor-guide`.

## What can I contribute?

Contributions are not limited to the current package layout or roadmap. You may
propose new folders, packages, capabilities, integrations, examples, or
project-wide improvements, including work on:

- Knowledge sources, parsing, chunking, embeddings, search, retrieval,
  reranking, citations, and evaluation.
- Image, audio, video, and mixed-media processing.
- Agents, tools, memory, orchestration, permissions, and human approval.
- Model providers, local inference, storage, and interoperability.
- Security, privacy, observability, testing, benchmarks, and documentation.

For new code, give each module a clear responsibility, keep dependencies
intentional, and explain how it fits the architecture. Do not add a dependency
or public abstraction without a concrete use case. Clearly label experimental
behavior and proposals; documentation and examples must not imply that
unimplemented features work.

## Set up a development environment

Use Python 3.11 or newer. From the repository root, create and activate a
virtual environment, then install the project and development tools:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

On macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

If activation is unavailable, run the environment's Python executable
directly. For example, on Windows use
`.\.venv\Scripts\python.exe -m pytest`.

## Tests and quality checks

Run these from the repository root:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

Format Python code with `python -m ruff format .`. Add or update tests for
behavior changes. Tests should be deterministic and must not require live
provider credentials, network access, or paid services. Use fakes for external
services; keep any live integration tests explicitly opt-in.

## Pull request checklist

Before requesting review, check that:

- [ ] The change addresses a clear problem and stays focused.
- [ ] Tests cover changed behavior; all relevant checks pass.
- [ ] User-facing behavior, setup, and directly related docs are updated.
- [ ] Public API or compatibility changes and limitations are explained.
- [ ] External inputs and failures are handled explicitly; resource use is
  bounded where relevant.
- [ ] No credentials, private data, generated indexes, or unrelated formatting
  changes are included.
- [ ] Security, privacy, provider data handling, and tool permissions have been
  considered.

## Security and privacy

Security is part of every contribution, not a final folder or optional review:

- Never commit API keys, tokens, passwords, personal information, private
  datasets, or production logs. Use environment variables or a secret manager
  for credentials and sanitized fixtures for tests.
- Treat documents, URLs, uploaded media, retrieved content, model responses,
  and tool arguments as untrusted. Validate inputs and consider malicious
  content, prompt injection, oversized files, and resource exhaustion.
- Give tools and integrations only the permissions they need. Make external
  data transfers, retention, and side effects clear.
- Avoid logging secrets or sensitive content. Test security-relevant
  validation and failure behavior.
- Report suspected vulnerabilities privately as described in the
  [Security Policy](SECURITY.md), not in a public issue.

## Copyright, license, and attribution

LuckyBrain is currently distributed under the MIT License; read [LICENSE](LICENSE)
before contributing or reusing code. Under that license, people may copy,
modify, redistribute, and build products using the project, including
commercial products, as long as they preserve the required copyright and
license notices. A public repository cannot use the MIT License to prevent
someone from creating a fork or a competing derivative project.

By submitting a contribution, you confirm that you have the right to submit
it and agree that the contribution may be distributed under the repository's
MIT License. You retain copyright in your contribution; this is not a copyright
assignment or a promise of exclusive ownership. Do not submit code, text, or
other material copied from a source whose license or terms are incompatible.
Identify substantial third-party material and its license so maintainers can
review it before inclusion.

The project's name and branding are separate from the copyright license for
the code. Do not imply that your fork or product is the official LuckyBrain
project or is endorsed by its maintainers. This guidance does not claim that
the name is a registered trademark.

## Maintainer safeguards

Repository access and review controls help protect the official project even
when its code is openly licensed. Maintainers should use GitHub settings to:

- Require pull requests and passing checks for the default branch; prevent
  direct pushes and force-pushes where practical.
- Require review for changes to protected branches and sensitive areas such as
  workflows, release configuration, and security policy.
- Enable multi-factor authentication, grant write access sparingly, and remove
  access that is no longer needed.
- Enable available secret scanning and dependency alerts, and protect release
  credentials and publishing workflows.

These controls protect the official repository and release process; they
cannot prevent lawful reuse or forks permitted by the MIT License.

## Community

By participating, you agree to follow the standards in
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). For questions about contributing,
use the repository's public discussion or issue channels. Never post secrets,
private data, or vulnerability details publicly.
