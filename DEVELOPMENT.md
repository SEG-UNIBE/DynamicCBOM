# Development Guide

This guide covers development, testing, and publishing workflows for Dynamic CBOM.

## Setup Development Environment

### Using UV (Recommended)

```bash
# Install dependencies
cd src
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### Using pip + venv

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Development Tasks

### Running Linting

```bash
# Check code style
ruff check src/

# Format code
black src/
```

### Running Tests

```bash
pytest tests/

# With coverage
pytest --cov=interface tests/
```

### Building Distribution

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build
python -m build

# Or use the helper script
python build_and_publish.py
```

## Version Management

Update version in `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Change this
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH**
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

Example:
- 0.1.0 → 0.2.0 (new features)
- 0.1.0 → 0.1.1 (bug fixes)
- 0.1.0 → 1.0.0 (breaking changes)

## Commit Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Test additions
- `ci`: CI/CD changes
- `chore`: Build, dependencies, etc.

Examples:
```
feat(cbom-matcher): add fuzzy matching for algorithms

fix(parser): handle empty crypto trace logs

docs: update installation instructions

chore(deps): update matplotlib to 3.11
```

## Updating CHANGELOG

Before releasing, update `CHANGELOG.md`:

1. Add new section under `## [Unreleased]`
2. Categorize changes (Added, Changed, Fixed, etc.)
3. Move content to new version section
4. Update links at bottom

Example:
```markdown
## [0.2.0] - 2025-02-15

### Added
- New fuzzy matching algorithm for CBOM comparison

### Fixed
- Bug in TLS probe handling

### Changed
- Improved performance of log post-processor

[0.2.0]: https://github.com/SEG-UNIBE/DynamicCBOM/compare/v0.1.0...v0.2.0
```

## Publishing to PyPI

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions.

Quick summary:
```bash
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Test locally
python -m build

# 4. Create git tag
git tag v0.2.0
git push origin v0.2.0

# 5. Create GitHub Release
# GitHub Actions will automatically publish to PyPI

# Or manually:
python -m twine upload --repository testpypi dist/*  # Test first
python -m twine upload dist/*                        # Production
```

## Code Style Guidelines

### Python

- **PEP 8** compliance (via black)
- **Type hints** for functions (Python 3.12+)
- **Docstrings** for public functions (Google style)
- **Line length**: 100 characters max

Example:
```python
def extract_cbom(target_path: str, probe_type: str = "algorithms") -> dict:
    """Extract cryptography bill of materials from a target.
    
    Args:
        target_path: Path to the target executable or script
        probe_type: Type of bpftrace probe to use
    
    Returns:
        Dictionary containing the CBOM in CycloneDX format
        
    Raises:
        FileNotFoundError: If target executable is not found
        RuntimeError: If bpftrace execution fails
    """
    # Implementation
    pass
```

### YAML

- 2-space indentation
- Clear comments for complex rules
- Keep rules organized by algorithm type

### TOML

- Logical grouping of sections
- Clear comments for non-obvious settings
- Alphabetical order within sections when possible

## Testing Strategy

### Unit Tests

```python
# tests/test_cbom_matcher.py
import pytest
from interface.cbomMatcher import CBOMMatcher

def test_exact_match():
    matcher = CBOMMatcher()
    # Test implementation
    assert matcher.match("EVP_PKEY_encrypt", "EVP_PKEY_encrypt") == 1.0
```

### Integration Tests

Test entire workflows, including CLI commands.

### Property-Based Tests

Use hypothesis for fuzzy matching tests.

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def function(param1: str, param2: int) -> bool:
    """Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
        
    Raises:
        ValueError: When value is invalid
        
    Example:
        >>> function("test", 42)
        True
    """
```

### Markdown

- Clear headings hierarchy (# > ## > ###)
- Code blocks with language specification
- Links to related files/docs
- Examples where helpful

## Troubleshooting

### ImportError when developing

```bash
# Make sure package is installed in editable mode
pip install -e ".[dev]"
```

### Tests fail after changes

```bash
# Clear cache and reinstall
rm -rf .pytest_cache __pycache__
pip install -e ".[dev]" --force-reinstall
```

### Build fails

```bash
# Clean and rebuild
rm -rf build/ dist/ *.egg-info/
python -m build
```

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [Setuptools Documentation](https://setuptools.pypa.io/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
