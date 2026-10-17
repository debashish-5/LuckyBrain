# Contributing

Thanks for helping improve LuckyBrain. The project is early-stage, and focused
bug fixes, tests, documentation, and well-scoped design proposals are welcome.

## A practical first contribution

1. Read the [architecture](architecture.md), [roadmap](roadmap.md), and
   [production-readiness notes](guides/production-readiness.md).
2. Search existing issues and pull requests. For a substantial new dependency,
   public abstraction, or subsystem, open an issue before building it.
3. Keep the change focused, add deterministic tests, and document the behavior
   you changed.
4. Run checks locally:

   ```bash
   python -m pytest
   python -m ruff check .
   python -m ruff format --check .
   python -m mypy src
   python -m mkdocs build --strict
   ```

5. Open a pull request with the problem, implementation, limitations, and
   verification steps.

## Documentation is part of the feature

For every new public module, class, or method:

- Add useful source docstrings describing its purpose and public behavior.
- Document parameters, return values, exceptions, side effects, and limits in
  the relevant user guide.
- Add public symbols to [API reference](api-reference.md); signatures and
  docstrings are rendered from source by MkDocs and mkdocstrings.
- Add a focused runnable example when it clarifies how the feature is used.
- Update navigation and mark experimental or unimplemented capabilities
  clearly.

Install the documentation tools with `python -m pip install -e ".[docs]"`.
Run `python -m mkdocs serve` for a local preview, or
`python -m mkdocs build --strict` to validate the production site build.
See the [code of conduct](code-of-conduct.md) and private
[security reporting guide](security.md) before contributing.
