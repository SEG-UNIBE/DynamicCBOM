# GitHub Actions PyPI Publishing Setup

This guide explains how to set up automated publishing to PyPI using GitHub Actions.

## 1. Create PyPI API Token

1. Go to https://pypi.org/account/
2. Log in with your PyPI account (create one if needed)
3. Navigate to **API tokens** in your account settings
4. Click **Add API token**
5. Name it: `dynamic-cbom-github-actions`
6. Set scope: **Entire PyPI**
7. Click **Create token**
8. **Copy the entire token** (starts with `pypi_`)

## 2. Add Secret to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. **Name**: `PYPI_API_TOKEN`
5. **Secret**: Paste the token from step 1
6. Click **Add secret**

⚠️ **Security**: Never share this token or commit it to git!

## 3. Verify Workflows are in Place

Check that these files exist:

```
.github/
└── workflows/
    ├── test.yml      # Runs on every push/PR
    └── publish.yml   # Runs on release
```

The test workflow ensures code quality before publishing.
The publish workflow automatically publishes to PyPI on release.

## 4. First Release

1. **Update version** in `pyproject.toml`:
   ```toml
   [project]
   version = "0.1.0"
   ```

2. **Update CHANGELOG.md** with changes

3. **Commit changes**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 0.1.0"
   git push
   ```

4. **Create a tag**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

5. **Create GitHub Release**:
   - Go to Releases → Draft a new release
   - Tag version: `v0.1.0`
   - Release title: `v0.1.0 - Initial Release`
   - Description: Copy from CHANGELOG.md
   - Click **Publish release**

6. **Monitor the workflow**:
   - Go to **Actions** tab
   - Click **Publish to PyPI** workflow
   - Wait for completion (usually 1-2 minutes)
   - Verify package on https://pypi.org/project/dynamic-cbom/

## 5. Testing with TestPyPI (Optional but Recommended)

Before publishing to production PyPI, test on TestPyPI:

1. Create a TestPyPI API token on https://test.pypi.org/
2. Create a `TESTPYPI_API_TOKEN` secret in GitHub
3. Modify `.github/workflows/publish.yml` to publish to TestPyPI first:

```yaml
- name: Publish to TestPyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
    password: ${{ secrets.TESTPYPI_API_TOKEN }}
```

4. Test installation:
   ```bash
   pip install -i https://test.pypi.org/simple/ dynamic-cbom==0.1.0
   ```

## 6. Future Releases

For subsequent releases, just follow steps 1-5 above with new version numbers.

Example:
```bash
# Update version to 0.2.0
# Update CHANGELOG.md
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump to v0.2.0"
git push

# Tag and create release
git tag v0.2.0
git push origin v0.2.0

# Create release on GitHub
# (automated publishing will trigger)
```

## 7. Troubleshooting

### Workflow fails with "Unauthorized"

The PyPI token may be invalid or expired:
- Verify token in GitHub Secrets is correct
- Check token hasn't been revoked on PyPI
- Create a new token if needed

### Package not appearing on PyPI

- Check the **Actions** tab for errors
- Verify version in `pyproject.toml` matches the tag
- PyPI doesn't allow re-uploading the same version

### "File already exists" error

PyPI doesn't allow re-uploading files. Solutions:
- Increment version (0.1.0 → 0.1.1)
- Create a new release with updated version
- Delete the release on GitHub and retry

### Tests fail before publishing

The test workflow runs first to ensure quality:
- Check **Actions** for lint/format errors
- Fix issues locally and push
- Tests will re-run automatically

## 8. Monitoring and Maintenance

### Check Release Status

- PyPI: https://pypi.org/project/dynamic-cbom/
- GitHub: Releases → View details

### Monitor Downloads

- PyPI project page shows download statistics
- GitHub can track release downloads

### Update Documentation

After each release:
- Update README.md if needed
- Update CHANGELOG.md with next unreleased section
- Commit and push

## 9. Advanced Topics

### Conditional Publishing

To only publish on specific branches or conditions, edit `publish.yml`:

```yaml
on:
  release:
    types: [created]
    
jobs:
  deploy:
    # ... existing config ...
    steps:
      # ... existing steps ...
      - name: Publish to PyPI
        if: startsWith(github.ref, 'refs/tags/v')  # Only v-prefixed tags
        uses: pypa/gh-action-pypi-publish@release/v1
```

### Sign Releases

To GPG sign your releases (optional):

```bash
# Generate GPG key if needed
gpg --full-generate-key

# Sign tag
git tag -s v0.2.0 -m "Release v0.2.0"

# Push signed tag
git push origin v0.2.0
```

## References

- [PyPI Help - Publishing](https://pypi.org/help/#publishing)
- [GitHub Actions - pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [Official Python Packaging Guide](https://packaging.python.org/)
