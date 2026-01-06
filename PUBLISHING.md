# Publishing Dynamic CBOM to PyPI

This document describes how to publish the Dynamic CBOM package to PyPI (Python Package Index).

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org)
2. **GitHub Account**: The package is hosted on GitHub
3. **Build Tools**: Install `build` and `twine`

## Setup Steps

### 1. Install Build Tools

```bash
pip install build twine
```

### 2. Create PyPI API Token

1. Log in to [pypi.org](https://pypi.org)
2. Go to Account Settings → API tokens
3. Create a new token with "Entire PyPI" scope
4. Save the token securely

### 3. Configure Credentials

Create or update `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi_YOUR_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi_YOUR_TEST_TOKEN_HERE
```

**Security Note**: Protect this file with `chmod 600 ~/.pypirc`

## Publishing Steps

### 1. Build the Package

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build wheel and source distribution
python -m build
```

This creates:
- `dist/dynamic_cbom-0.1.0.tar.gz` - Source distribution
- `dist/dynamic_cbom-0.1.0-py3-none-any.whl` - Wheel distribution

### 2. Test Upload (Recommended)

```bash
# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI to verify
pip install -i https://test.pypi.org/simple/ dynamic-cbom==0.1.0
```

### 3. Verify on TestPyPI

- Visit: https://test.pypi.org/project/dynamic-cbom/
- Check metadata, description, and files
- Test installation works correctly

### 4. Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*

# Verify at: https://pypi.org/project/dynamic-cbom/
```

## Installation Verification

After publishing, users can install with:

```bash
# Install from PyPI
pip install dynamic-cbom

# Verify installation
dynamic-cbom --help
```

## Version Management

### Incrementing Versions

Edit `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Increment version
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (0.1.0 → 1.0.0): Breaking changes
- **MINOR** (0.1.0 → 0.2.0): New features
- **PATCH** (0.1.0 → 0.1.1): Bug fixes

## GitHub Integration

### 1. Create Release

```bash
git tag v0.1.0
git push origin v0.1.0
```

Then on GitHub, create a Release with the changelog.

### 2. Automated Publishing (Optional)

Create `.github/workflows/publish.yml` for automated PyPI uploads on release:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install build twine
      - run: python -m build
      - run: python -m twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```

## Package Metadata

The following are configured in `pyproject.toml`:

- **Name**: `dynamic-cbom` (PyPI uses lowercase with hyphens)
- **Version**: `0.1.0` (Semantic versioning)
- **Description**: Short description
- **Classifiers**: Package categorization
- **Keywords**: Searchability
- **License**: MIT
- **URLs**: Links to documentation, repo, issues
- **Dependencies**: Required packages
- **Entry points**: CLI commands

## Troubleshooting

### "InvalidDistribution: File already exists"

A file with the same version already exists on PyPI. Increment the version.

### "Repository does not allow deletion"

PyPI doesn't allow deleting published packages. Use a new version instead.

### "400 Bad Request: Invalid distribution"

Check:
- Long description (README.md) is valid reStructuredText
- All required metadata is present
- No invalid classifiers

### "twine: command not found"

```bash
pip install --upgrade twine
```

## Security Best Practices

1. **Never commit PyPI tokens** to git
2. **Use environment variables** for secrets
3. **Use separate test and production tokens**
4. **Rotate tokens periodically**
5. **Sign releases** with GPG (optional but recommended)

## References

- [PyPI Help](https://pypi.org/help/)
- [Setuptools Documentation](https://setuptools.pypa.io/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
