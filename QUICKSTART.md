# Quick Start Guide - Publishing rpip to PyPI

## TL;DR - Fast Track to PyPI

### 1. One-Time Setup (5 minutes)

```bash
# Install build tools
pip install --upgrade build twine

# Create PyPI account at https://pypi.org/account/register/
# Get API token at https://pypi.org/manage/account/token/

# Create ~/.pypirc with your token
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
EOF

chmod 600 ~/.pypirc
```

### 2. Every Release (2 minutes)

```bash
# Clean, build, and publish
rm -rf build/ dist/ *.egg-info/
python -m build
twine upload dist/*
```

That's it! Your package is now on PyPI.

Users can install with:
```bash
pipx install syblock-rpip
# or
pip install syblock-rpip
```

## Detailed Steps

### Before First Publish

**1. Create accounts:**
- PyPI: https://pypi.org/account/register/
- TestPyPI (optional): https://test.pypi.org/account/register/

**2. Get API token:**
- Go to https://pypi.org/manage/account/token/
- Click "Add API token"
- Scope: "Entire account" (or create after first upload)
- Copy token (starts with `pypi-`)

**3. Install tools:**
```bash
pip install --upgrade build twine
```

**4. Configure token:**
```bash
# Create ~/.pypirc
nano ~/.pypirc

# Add:
[pypi]
username = __token__
password = pypi-YOUR_ACTUAL_TOKEN_HERE

# Secure it
chmod 600 ~/.pypirc
```

### Publishing Workflow

**Every time you want to release:**

```bash
# 1. Update version in setup.cfg
#    Change: version = 0.1.0 → 0.1.1

# 2. Run tests
python -m unittest discover -s tests

# 3. Clean old builds
rm -rf build/ dist/ *.egg-info/

# 4. Build
python -m build

# 5. Upload
twine upload dist/*

# 6. Verify
pipx install syblock-rpip --force
rpip --help
```

**Done!** Package is live at: https://pypi.org/project/syblock-rpip/

### Testing Before Production (Optional)

Test on TestPyPI first:

```bash
# Upload to test server
twine upload --repository testpypi dist/*

# Install from test server
pip install --index-url https://test.pypi.org/simple/ syblock-rpip

# Test it works
rpip --help

# Clean up
pip uninstall syblock-rpip
```

## Common Issues

**"Package already exists"**
- Can't re-upload same version
- Bump version in setup.cfg and rebuild

**"Invalid credentials"**
- Check ~/.pypirc has correct token
- Token should start with `pypi-`
- No spaces or quotes around token

**Import errors after install**
- Check `rpip/__init__.py` exists
- Check `console_scripts` in setup.cfg

**Package not showing after upload**
- Wait 1-2 minutes for PyPI indexing
- Check https://pypi.org/project/syblock-rpip/

## File Checklist

Required files for PyPI:
- ✅ `setup.cfg` - Package metadata
- ✅ `pyproject.toml` - Build system config
- ✅ `README.md` - Project description
- ✅ `LICENSE` - License file
- ✅ `rpip/__init__.py` - Package init with `__version__`
- ✅ `rpip/main.py` - Main code

All files are already created and ready!

## GitHub Integration (Optional)

After publishing to PyPI:

```bash
# Tag the release
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Create release on GitHub at:
# https://github.com/syblock/rpip/releases
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- `0.1.0` → `0.1.1` - Bug fixes only
- `0.1.0` → `0.2.0` - New features (backwards compatible)
- `0.1.0` → `1.0.0` - Breaking changes

## Resources

- **PyPI Project Page**: https://pypi.org/project/syblock-rpip/
- **Package Statistics**: https://pypistats.org/packages/syblock-rpip
- **Full Guide**: See `PUBLISHING.md`

## Status Check

Your package is ready to publish! All required files are in place:

```
rpip/
├── setup.cfg          ✅ Configured
├── pyproject.toml     ✅ Created
├── LICENSE            ✅ MIT License
├── README.md          ✅ Comprehensive docs
├── CHANGELOG.md       ✅ Release notes
├── MANIFEST.in        ✅ File inclusion rules
├── .gitignore         ✅ Git exclusions
├── rpip/
│   ├── __init__.py    ✅ Version 0.1.0
│   └── main.py        ✅ Main code (438 lines)
└── tests/             ✅ 34 tests passing
```

**Next step:** Get PyPI token and run `python -m build && twine upload dist/*`
