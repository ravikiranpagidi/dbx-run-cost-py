# PyPI Release

Before the first release, create the project on PyPI or configure PyPI trusted publishing for this repository.

Build locally:

```bash
python -m pip install ".[dev]"
python -m build
python -m twine check dist/*
```

Upload to TestPyPI first:

```bash
python -m twine upload --repository testpypi dist/*
```

Then upload to PyPI:

```bash
python -m twine upload dist/*
```

After publishing, update the README install command from the GitHub URL to:

```bash
pip install dbx-run-cost-py
```
