# Resumable PIP

A Command-Line Interface (CLI) tool that wraps `pip` to provide **resumable downloads** for Python packages, especially useful for large packages (like PyTorch or TensorFlow) on flaky internet connections.

## Features

- **Resumable Downloads**: Automatically resume interrupted downloads
- **Platform Independent**: Works on Windows, macOS, and Linux without external dependencies
- **Multiple Downloaders**: Supports aria2c, wget, curl, or native Python (automatic fallback)
- **File Integrity**: SHA256/SHA512 hash verification for downloaded packages
- **Progress Tracking**: Real-time download progress with speed and size information
- **Robust Error Handling**: Informative error messages with recovery instructions

## Installation

```bash
pipx install syblock-rpip
# OR
pip install syblock-rpip
```

## Prerequisites

**No external dependencies required!** The tool includes a native Python downloader with full resume support.

For better performance, you can optionally install:
- **aria2c** (recommended for best performance and speed)
- **wget**
- **curl**

If none are available, rpip automatically uses the built-in Python downloader.

## Usage

```bash
# Single package installation
rpip package-name

# With version specifier
rpip "package-name==1.2.3"

# With pip options
rpip package-name --user

# Install from requirements file
rpip -r requirements.txt
rpip --requirement requirements.txt

# Auto-detect requirements file
rpip requirements.txt

# Examples
rpip torch
rpip "tensorflow>=2.0"
rpip numpy --upgrade
rpip -r requirements.txt --user
```

## How It Works

### Single Package
1. Uses pip's resolution engine to find the correct package URL
2. Selects the best available downloader (aria2c > wget > curl > native Python)
3. Downloads the package file with full resume support via HTTP Range requests
4. Verifies file integrity using SHA256/SHA512 hash (if available)
5. Installs the package using pip
6. Cleans up the downloaded file on success

### Requirements File
1. Parses the requirements file (supports comments, nested -r, and most pip syntax)
2. Installs each package sequentially with full resumable download support
3. Tracks successful and failed installations
4. Provides a detailed summary at the end

## Download Methods

The tool automatically selects the best available downloader:

1. **aria2c** - Multi-connection downloads, fastest performance
2. **wget** - Reliable, widely available on Linux/macOS
3. **curl** - Built-in on most systems
4. **Python urllib** - Native fallback, works everywhere, includes progress bar

## Requirements File Support

rpip supports standard requirements.txt syntax including:
- ✅ Package names with version specifiers (`package==1.0.0`, `package>=2.0`)
- ✅ Comments (lines starting with `#` or inline with ` #`)
- ✅ Nested requirements files (`-r other-requirements.txt`)
- ✅ Blank lines
- ✅ **Editable installs** (`-e .`, `-e git+https://...#egg=package`)
- ✅ **Pip options** (`--index-url`, `--extra-index-url`, `--trusted-host`, etc.)

### Editable Installs

Editable installs are **fully supported**! These are installed directly via pip (no download/resume needed since git has its own resume capability):

```bash
# In requirements.txt:
-e .
-e /path/to/local/package
-e git+https://github.com/user/repo.git#egg=package
--editable git+https://github.com/user/repo.git@branch#egg=package
```

When rpip encounters an editable install, it passes it directly to pip for installation.

### Pip Options

Important pip options are **fully supported** and applied to all package installations:

```bash
# In requirements.txt:
--index-url https://my-private-pypi.org/simple
--extra-index-url https://pypi.org/simple
--trusted-host my-private-pypi.org
--find-links https://download.pytorch.org/whl/torch_stable.html

requests==2.28.0
numpy>=1.20.0
```

Supported options:
- `--index-url` - Custom PyPI server
- `--extra-index-url` - Additional package indexes
- `--trusted-host` - Allow HTTP (non-HTTPS) hosts
- `--find-links` - Additional package sources
- `--no-index`, `--prefer-binary`, `--pre`, `--no-binary`, `--only-binary`

These options are extracted from the requirements file and applied to ALL package installations in that file.

## Limitations

- Packages are installed sequentially (not in parallel) to ensure resumability

## Development

### Running Tests

Install with test dependencies:
```bash
pip install -e ".[test]"
# or with all dev dependencies
pip install -e ".[dev]"
```

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Using make (if available)
make test
make test-coverage
```

### Test Coverage

The project includes comprehensive unit and integration tests (34 tests):
- **Unit tests** - Test individual functions in isolation
- **Integration tests** - Test complete workflows
- **Editable install tests** - Test -e and --editable support
- **Fixtures** - Sample requirements files for testing

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License
