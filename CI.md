# CI

The scaffold CI currently checks:

- installability with `uv`
- linting with `ruff`
- formatting with `ruff format --check`
- type checking with `mypy`
- tests with `pytest`
- package build integrity with `python -m build` and `twine check`

The workflows live under [`.github/workflows/`](.github/workflows/).

