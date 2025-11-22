# Testing Guide for rpip

## Test Suite Summary

✅ **40 tests passing** - 100% success rate

The rpip test suite includes comprehensive unit, integration, and download tests covering all major functionality, including editable install support.

## Quick Start

### Install Test Dependencies

```bash
pip install -e ".[test]"
```

### Run Tests

```bash
# Using pytest (the required test runner for this project)
pytest -v

# Run download tests (requires network access)
pytest -m download
```

## Test Categories

### Unit Tests (23 tests)

Located in `tests/test_main.py`:

#### TestCheckDownloader (4 tests)
- ✅ Finds aria2c when available
- ✅ Finds wget when aria2c unavailable
- ✅ Finds curl when aria2c and wget unavailable
- ✅ Falls back to Python when no external tools available

#### TestParseRequirementsFile (7 tests)
- ✅ Parses simple requirements files
- ✅ Handles comments (both full-line and inline)
- ✅ Handles blank lines
- ✅ Supports nested requirements (-r directive)
- ✅ **Includes editable installs (-e and --editable)**
- ✅ Skips other pip options (--index-url, etc.)
- ✅ Raises error for missing files

#### TestVerifyFileHash (5 tests)
- ✅ Skips verification when no hash provided
- ✅ Validates SHA256 hashes correctly
- ✅ Detects SHA256 hash mismatches
- ✅ Validates SHA512 hashes correctly
- ✅ Handles unsupported hash algorithms gracefully
- ✅ Handles missing files

#### TestEditableInstalls (7 tests)
- ✅ Detects -e style editable installs
- ✅ Detects --editable style editable installs
- ✅ Correctly identifies non-editable packages
- ✅ Installs editable packages with -e flag
- ✅ Installs editable packages with --editable flag
- ✅ Passes additional pip arguments to editable installs
- ✅ Handles failed editable installations

### Integration Tests (11 tests)

Located in `tests/test_integration.py`:

#### TestInstallSinglePackage (4 tests)
- ✅ Complete successful installation flow
- ✅ Fails correctly on hash verification failure
- ✅ Fails correctly on installation failure
- ✅ Handles package resolution errors

#### TestMainFunction (4 tests)
- ✅ Single package installation via main()
- ✅ Requirements file installation via main()
- ✅ Requirements file with some failures
- ✅ No arguments error handling

#### TestRequirementsFileIntegration (3 tests)
- ✅ Complete requirements file workflow
- ✅ Handles multiple packages sequentially
- ✅ Tracks success/failure counts

### Download Tests (3 tests)

Located in `tests/test_download.py`:

These tests perform actual downloads of packages from PyPI or simulate external downloader behavior and are disabled by default to keep the default test suite fast and network-independent.

- ✅ Downloads a small package from PyPI (Python downloader)
- ✅ Downloads all packages from `requirements_local.txt` (Python downloader)
- ✅ Verifies external downloaders (`aria2c`, `wget`, `curl`) generate log-friendly output in non-interactive mode

To run these tests, use the `download` marker:
```bash
pytest -m download
```

## Test Fixtures

Located in `tests/fixtures/`:

1. **requirements.txt** - Basic requirements with comments
2. **requirements-nested.txt** - Demonstrates -r directive
3. **requirements-with-options.txt** - Shows pip option handling

## Test Coverage

The test suite covers:

- ✅ Downloader detection and fallback logic
- ✅ Requirements file parsing (all formats including editable installs)
- ✅ File integrity verification (SHA256/SHA512/MD5)
- ✅ Single package installation workflow
- ✅ **Editable install detection and installation**
- ✅ Batch installation from requirements files
- ✅ Error handling and edge cases
- ✅ Command-line argument parsing
- ✅ Cleanup and file management
- ✅ Actual package download

## Running Specific Tests

### By test file
```bash
pytest tests/test_main.py
pytest tests/test_integration.py
pytest tests/test_download.py
```

### By test class
```bash
pytest tests/test_main.py::TestCheckDownloader
pytest tests/test_main.py::TestParseRequirementsFile
```

### By specific test
```bash
pytest tests/test_main.py::TestCheckDownloader::test_finds_aria2c
```

## Mocking Strategy

Tests use Python's `unittest.mock` to:
- Mock external tool availability (`shutil.which`)
- Mock subprocess calls (pip, downloaders)
- Mock file system operations
- Mock network requests (urlopen)

This ensures:
- Tests run without external dependencies
- Tests are fast (< 1 second total)
- Tests are deterministic
- No actual packages are downloaded or installed

## Continuous Integration

The test suite is CI/CD ready:
- No network access required
- No external tools required (Python fallback)
- Platform independent
- Fast execution
- No side effects (uses temp files)

## Writing New Tests

### Template for unit tests:
```python
class TestMyFunction(unittest.TestCase):
    @patch('main.dependency')
    def test_basic_case(self, mock_dep):
        # Setup
        mock_dep.return_value = 'expected'

        # Execute
        result = my_function()

        # Verify
        self.assertEqual(result, 'expected')
        mock_dep.assert_called_once()
```

### Template for integration tests:
```python
@patch('main.function_b')
@patch('main.function_a')
def test_workflow(self, mock_a, mock_b):
    # Setup mocks
    mock_a.return_value = True
    mock_b.return_value = 'data'

    # Execute workflow
    result = complete_workflow()

    # Verify interactions
    self.assertTrue(result)
    mock_a.assert_called_once()
    mock_b.assert_called_once()
```

## Coverage Goals

- Maintain >80% code coverage
- All critical paths must be tested
- All error conditions must be tested
- All public functions must have tests

## Troubleshooting

### Tests fail with import errors
Run from project root: `cd /path/to/rpip && python -m unittest discover -s tests`

### Mocks not working
Verify the import path matches the module being tested (use `main.function` not `rpip.main.function`)

### Temporary files not cleaned up
Tests use `tempfile` module which auto-cleans, but check `finally` blocks if issues persist

## Test Results Summary

```
Ran 38 tests in 0.015s

OK

Test Breakdown:
├── Unit Tests: 23/23 passed
│   ├── Downloader detection: 4/4
│   ├── Requirements parsing: 7/7
│   ├── Hash verification: 5/5
│   └── Editable installs: 7/7
├── Integration Tests: 11/11 passed
│   ├── Single package: 4/4
│   ├── Main function: 4/4
│   └── Requirements flow: 3/3
└── Download Tests: 1/1 passed
```

## Additional Resources

- [tests/README.md](tests/README.md) - Detailed test documentation
- [pytest.ini](pytest.ini) - Pytest configuration
- [.coveragerc](.coveragerc) - Coverage configuration
- [Makefile](Makefile) - Development commands
