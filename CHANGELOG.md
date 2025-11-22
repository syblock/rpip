# Changelog

All notable changes to rpip will be documented in this file.

## [Unreleased]

### Added
- **Editable install support** - Full support for `-e` and `--editable` packages
  - Handles local paths (`-e .`, `-e /path/to/package`)
  - Handles git URLs (`-e git+https://github.com/user/repo.git#egg=package`)
  - Passes editable installs directly to pip (no download needed)
  - Added 7 new tests for editable install functionality

- **Pip options support** - Full support for important pip options in requirements files
  - `--index-url` - Custom PyPI servers for private packages
  - `--extra-index-url` - Additional package indexes
  - `--trusted-host` - HTTP (non-HTTPS) package sources
  - `--find-links` - Additional package discovery paths
  - `--no-index`, `--prefer-binary`, `--pre`, `--no-binary`, `--only-binary`
  - Options are extracted and applied to ALL package installations
  - Added tests for pip options preservation

### Changed
- **Improved comment handling** in requirements files
  - Now preserves `#` in URLs (e.g., `git+...#egg=package`)
  - Only strips `#` when preceded by whitespace (inline comments)
  - Comments at start of line are still skipped

- **Enhanced requirements parser**
  - Now returns tuple of (packages, pip_options)
  - Pip options are merged with command-line arguments
  - Nested requirements files inherit and combine pip options

### Fixed
- Requirements file parser now correctly includes editable installs
- Comment stripping no longer removes URL fragments
- Pip options from requirements files are now properly applied to installations

## [0.1.0] - Initial Release

### Added
- Resumable download support for Python packages
- Multiple downloader support (aria2c, wget, curl, native Python)
- Native Python downloader with HTTP Range request support
- File integrity verification (SHA256/SHA512/MD5)
- Requirements file support with nested `-r` directives
- Progress tracking for downloads
- Comprehensive test suite (34 tests)
- Cross-platform support (Windows, macOS, Linux)

### Features
- Platform-independent (no external dependencies required)
- Automatic downloader detection with intelligent fallback
- Real-time progress bar for Python downloader
- Batch installation with summary reporting
- Robust error handling and recovery instructions
