# Publishing rpip to PyPI

This guide explains how to publish rpip to PyPI so users can install it with `pipx install rpip` or `pip install rpip`.

## Prerequisites

### 1. Create PyPI Account

1. **Register on PyPI**: https://pypi.org/account/register/
2. **Register on TestPyPI** (for testing): https://test.pypi.org/account/register/
3. **Verify your email** for both accounts

### 2. Install Build Tools

```bash
pip install --upgrade build twine
```

- `build` - Creates distribution packages (wheel and sdist)
- `twine` - Uploads packages to PyPI securely

### 3. Set Up API Tokens (Recommended)

Instead of passwords, use API tokens for secure uploads:

#### For PyPI (Production):
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `rpip-upload`
4. Scope: Choose "Entire account" or specific project
5. Copy the token (starts with `pypi-`)

#### For TestPyPI (Testing):
1. Go to https://test.pypi.org/manage/account/token/
2. Create token same as above
3. Copy the token (starts with `pypi-`)

#### Configure tokens:

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN_HERE
```

Set permissions:
```bash
chmod 600 ~/.pypirc
```

## Publishing Steps

### Step 1: Update Version Number

Edit `setup.cfg` and bump the version:
```ini
[metadata]
version = 0.1.0  # Change to 0.1.1, 0.2.0, etc.
```

Follow [Semantic Versioning](https://semver.org/):
- `0.1.0` → `0.1.1` - Bug fixes
- `0.1.0` → `0.2.0` - New features (backwards compatible)
- `0.1.0` → `1.0.0` - Major changes (breaking changes)

### Step 2: Update CHANGELOG

Add release notes to `CHANGELOG.md`:
```markdown
## [0.1.0] - 2025-01-XX

### Added
- Feature descriptions

### Changed
- Change descriptions

### Fixed
- Bug fix descriptions
```

### Step 3: Clean Previous Builds

```bash
# Remove old builds
rm -rf build/ dist/ *.egg-info/
```

### Step 4: Run Tests

Ensure all tests pass:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

Expected output:
```
Ran 34 tests in 0.015s
OK
```

### Step 5: Build Distribution Packages

```bash
python -m build
```

This creates:
- `dist/rpip-0.1.0.tar.gz` (source distribution)
- `dist/rpip-0.1.0-py3-none-any.whl` (wheel)

### Step 6: Test Upload to TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps rpip

# Test the command
rpip --help

# Uninstall test version
pip uninstall rpip
```

### Step 7: Upload to PyPI (Production)

```bash
# Upload to PyPI
twine upload dist/*
```

You'll see output like:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading rpip-0.1.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 15.2/15.2 kB • 00:00 • ?
Uploading rpip-0.1.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 18.4/18.4 kB • 00:00 • ?

View at:
https://pypi.org/project/rpip/0.1.0/
```

### Step 8: Verify Installation

Wait 1-2 minutes for PyPI to index, then:

```bash
# Install with pip
pip install rpip

# Or with pipx (recommended for CLI tools)
pipx install rpip

# Test it works
rpip --help
rpip torch  # Try installing a package
```

### Step 9: Tag the Release on GitHub

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

Create a GitHub release:
1. Go to https://github.com/syblock/rpip/releases
2. Click "Draft a new release"
3. Choose tag: `v0.1.0`
4. Title: `rpip v0.1.0`
5. Description: Copy from CHANGELOG.md
6. Publish release

## Quick Release Checklist

- [ ] All tests pass (`python -m unittest discover -s tests`)
- [ ] Version bumped in `setup.cfg`
- [ ] CHANGELOG.md updated
- [ ] Previous builds cleaned (`rm -rf dist/ build/ *.egg-info/`)
- [ ] Built distributions (`python -m build`)
- [ ] Tested on TestPyPI (optional)
- [ ] Uploaded to PyPI (`twine upload dist/*`)
- [ ] Verified installation (`pipx install rpip`)
- [ ] Tagged release on GitHub
- [ ] Created GitHub release

## Troubleshooting

### "Package already exists"
You can't re-upload the same version. Bump the version number and rebuild.

### "Invalid distribution"
Make sure `setup.cfg` is properly formatted and all required fields are present.

### "Authentication failed"
- Check your API token in `~/.pypirc`
- Ensure token has correct permissions
- Token should start with `pypi-`

### "README rendering issues"
- Test markdown: https://pypi.org/help/#rendering
- Ensure `long_description_content_type = text/markdown` in setup.cfg

### Package not found after upload
Wait 1-2 minutes for PyPI to index the package.

## Automation with GitHub Actions (Optional)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Run tests
      run: python -m unittest discover -s tests -p "test_*.py"

    - name: Build package
      run: python -m build

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Add `PYPI_API_TOKEN` to GitHub repository secrets.

## Resources

- **PyPI**: https://pypi.org/
- **TestPyPI**: https://test.pypi.org/
- **Python Packaging Guide**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **Semantic Versioning**: https://semver.org/
