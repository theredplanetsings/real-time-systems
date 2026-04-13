# Contributing

## Workflow

1. Create a branch from `main`.
2. Make focused, test-backed changes.
3. Run `make check` locally (or run lint/format/test commands directly).
4. Open a pull request with a clear summary.

## Commit Convention

- Keep commit messages short, specific, and unique.
- Prefer 1 to 4 words where possible.
- Use imperative style.

Examples:
- `core sched tests`
- `cache compare runs`
- `benchmark suite page`

## Pull Request Checklist

- Tests added or updated for behavior changes.
- Existing tests still pass.
- No unrelated refactors in feature commits.
- UI changes verified in Streamlit locally.
- Exports verified for changed pages.

## Local Commands

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
make check
```

## Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

This runs the same style and formatting checks used in CI before each commit.

Note: `make check` currently enforces defect-focused Ruff checks (`F`/`B`) plus formatting on actively maintained app and test paths.