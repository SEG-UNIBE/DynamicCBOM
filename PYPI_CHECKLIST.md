# PyPI Publishing Checklist

Use this checklist to ensure everything is set up correctly for PyPI publishing.

## Pre-Publishing Setup (One-time)

- [ ] **PyPI Account**
  - [ ] Account created on https://pypi.org
  - [ ] Email verified

- [ ] **GitHub Account**
  - [ ] Repository created
  - [ ] Admin access to repository settings

- [ ] **Package Configuration**
  - [ ] ✅ `pyproject.toml` created in root directory
  - [ ] ✅ `setup.cfg` created for backwards compatibility
  - [ ] ✅ `MANIFEST.in` created to include data files
  - [ ] ✅ `.gitignore` updated for build artifacts

- [ ] **Documentation**
  - [ ] ✅ `PUBLISHING.md` - Publishing instructions
  - [ ] ✅ `DEVELOPMENT.md` - Developer guide
  - [ ] ✅ `CHANGELOG.md` - Version history
  - [ ] ✅ `README.md` - Updated with PyPI installation

- [ ] **GitHub Actions**
  - [ ] ✅ `.github/workflows/test.yml` - Testing on push/PR
  - [ ] ✅ `.github/workflows/publish.yml` - Publishing on release

- [ ] **GitHub Secrets**
  - [ ] Create PyPI API token at https://pypi.org/account/api-tokens/
  - [ ] Add as GitHub Secret: `PYPI_API_TOKEN`
    1. Go to Repository Settings
    2. Secrets and variables → Actions
    3. New repository secret
    4. Name: `PYPI_API_TOKEN`
    5. Value: `pypi_...` (from PyPI)

## Before First Release

- [ ] **Version Management**
  - [ ] ✅ Version defined in `pyproject.toml` (currently 0.1.0)
  - [ ] ✅ Version follows Semantic Versioning (MAJOR.MINOR.PATCH)

- [ ] **Code Quality**
  - [ ] Code follows PEP 8 style
  - [ ] All imports are resolvable
  - [ ] No hardcoded paths or credentials

- [ ] **Dependencies**
  - [ ] ✅ All dependencies listed in `pyproject.toml`
  - [ ] Removed unnecessary dependencies (datetime, pathlib, uuid, ruff)
  - [ ] Optional dev dependencies in `[project.optional-dependencies]`

- [ ] **Package Contents**
  - [ ] ✅ Python modules are in `src/interface/`
  - [ ] ✅ Data files (YAML, TOML) included via `MANIFEST.in`
  - [ ] ✅ Entry point configured: `dynamic-cbom = interface.client:app`

- [ ] **Build Test**
  - [ ] ✅ Package builds successfully: `python -m build`
  - [ ] ✅ Wheel validates: `python -m twine check dist/*`
  - [ ] ✅ All modules are included in wheel
  - [ ] ✅ Entry point is functional

- [ ] **Metadata Verification**
  - [ ] Package name correct: `dynamic-cbom`
  - [ ] License correct: MIT
  - [ ] Author/maintainer info accurate
  - [ ] Repository URLs point to correct GitHub repo
  - [ ] Keywords and classifiers are accurate

## For Each Release

### Before Creating Release

- [ ] **Update Files**
  - [ ] Update version in `pyproject.toml`
  - [ ] Update `CHANGELOG.md` with changes
  - [ ] Commit: `git add pyproject.toml CHANGELOG.md`
  - [ ] Commit message: `chore: bump version to X.Y.Z`

- [ ] **Code Review**
  - [ ] All changes reviewed
  - [ ] Tests pass (if any exist)
  - [ ] No breaking changes without major version bump

- [ ] **Local Testing**
  - [ ] Clean build: `rm -rf build/ dist/ *.egg-info/`
  - [ ] Build: `python -m build`
  - [ ] Check: `python -m twine check dist/*`

### Creating Release

- [ ] **Git Tag**
  - [ ] Create tag: `git tag vX.Y.Z`
  - [ ] Push tag: `git push origin vX.Y.Z`

- [ ] **GitHub Release**
  - [ ] Go to Releases → Draft new release
  - [ ] Tag version: `vX.Y.Z`
  - [ ] Release title: `vX.Y.Z - Brief Description`
  - [ ] Description: Copy relevant entries from `CHANGELOG.md`
  - [ ] Release notes with:
    - [ ] New features
    - [ ] Bug fixes
    - [ ] Breaking changes (if any)
    - [ ] Thanks to contributors
  - [ ] Set as latest release (if applicable)
  - [ ] Click "Publish release"

### After Release

- [ ] **Verify Publishing**
  - [ ] Go to Actions tab
  - [ ] Wait for "Publish to PyPI" workflow to complete
  - [ ] Check for green checkmark (success)

- [ ] **Verify on PyPI**
  - [ ] Visit: https://pypi.org/project/dynamic-cbom/
  - [ ] Version appears in release history
  - [ ] Description renders correctly
  - [ ] Files section shows wheel and source dist

- [ ] **Verify Installation**
  - [ ] Install in test environment: `pip install dynamic-cbom==X.Y.Z`
  - [ ] Test CLI: `dynamic-cbom --help`
  - [ ] Test basic functionality

- [ ] **Announce Release**
  - [ ] Update README.md if needed
  - [ ] Add unreleased section to CHANGELOG.md
  - [ ] Commit and push

## Maintenance

- [ ] **Regular Updates**
  - [ ] Monitor dependency updates
  - [ ] Update dependencies as needed
  - [ ] Keep changelog updated

- [ ] **Issue Monitoring**
  - [ ] Review GitHub issues
  - [ ] Plan releases around issues/PRs
  - [ ] Close issues in changelog/release notes

- [ ] **Documentation**
  - [ ] Keep docs in sync with code
  - [ ] Update examples if API changes
  - [ ] Document breaking changes clearly

## Troubleshooting Checklist

If publishing fails, verify:

- [ ] GitHub Secrets
  - [ ] `PYPI_API_TOKEN` is set
  - [ ] Token is not expired
  - [ ] Token has correct permissions

- [ ] Version
  - [ ] Version in tag matches `pyproject.toml`
  - [ ] Version not already published

- [ ] Code Quality
  - [ ] No syntax errors
  - [ ] All imports resolve
  - [ ] No hardcoded paths

- [ ] Build
  - [ ] `python -m build` succeeds
  - [ ] Wheel is not corrupted
  - [ ] `twine check` passes

- [ ] Metadata
  - [ ] `project.name` is correct (dynamic-cbom)
  - [ ] `project.version` is correct
  - [ ] LICENSE file exists
  - [ ] README.md is readable

## Resources

- **PyPI**: https://pypi.org/
- **Test PyPI**: https://test.pypi.org/
- **Documentation**: See `PUBLISHING.md`, `DEVELOPMENT.md`
- **GitHub Actions**: `.github/workflows/*.yml`

---

**Last Updated**: 2025-01-06
**Status**: ✅ Ready for First Release
