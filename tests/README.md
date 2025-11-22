# rpip Tests

This directory contains the test suite for rpip.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_main.py               # Unit tests for main module functions
├── test_integration.py        # Integration tests for complete workflows
├── fixtures/                  # Test fixtures and sample data
│   ├── requirements.txt       # Sample requirements file
│   ├── requirements-nested.txt # Requirements with nested -r
│   └── requirements-with-options.txt # Requirements with pip options
└── README.md                  # This file
```

## Running Tests

### Install test dependencies

```bash
# Install with test dependencies
pip install -e ".[test]"

# Or install with all dev dependencies
pip install -e ".[dev]"
```

### Run all tests

```bash
# Using pytest
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=. --cov-report=html
```

### Run specific test files

```bash
# Unit tests only
pytest tests/test_main.py

# Integration tests only
pytest tests/test_integration.py
```

### Run specific test classes or methods

```bash
# Specific test class
pytest tests/test_main.py::TestCheckDownloader

# Specific test method
pytest tests/test_main.py::TestCheckDownloader::test_finds_aria2c
```

## Test Categories

### Unit Tests (`test_main.py`)

Tests individual functions in isolation using mocks:

- **TestCheckDownloader**: Tests downloader detection logic
- **TestParseRequirementsFile**: Tests requirements file parsing
- **TestVerifyFileHash**: Tests file integrity verification
- **TestDownloadWithPython**: Tests native Python downloader

### Integration Tests (`test_integration.py`)

Tests complete workflows with multiple components:

- **TestInstallSinglePackage**: Tests single package installation flow
- **TestMainFunction**: Tests main CLI function
- **TestRequirementsFileIntegration**: Tests requirements file processing

## Test Fixtures

Located in `tests/fixtures/`:

- `requirements.txt` - Simple requirements file with comments
- `requirements-nested.txt` - Requirements file with `-r` directive
- `requirements-with-options.txt` - Requirements with pip options and editable installs

## Writing New Tests

### Unit Test Example

```python
import unittest
from unittest.mock import patch

class TestMyFunction(unittest.TestCase):
    @patch('main.some_dependency')
    def test_my_function(self, mock_dep):
        mock_dep.return_value = 'expected'
        result = my_function()
        self.assertEqual(result, 'expected')
```

### Integration Test Example

```python
@patch('main.multiple')
@patch('main.dependencies')
def test_workflow(self, mock1, mock2):
    # Setup
    mock1.return_value = True
    mock2.return_value = 'data'

    # Execute
    result = complete_workflow()

    # Verify
    self.assertTrue(result)
    mock1.assert_called_once()
```

## Coverage Reports

After running tests with coverage:

```bash
pytest --cov=. --cov-report=html
```

Open `htmlcov/index.html` in your browser to view the detailed coverage report.

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The test suite:

- Uses no external network calls (all mocked)
- Creates temporary files that are cleaned up
- Is platform-independent
- Runs quickly (<5 seconds)

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running tests from the project root:

```bash
cd /path/to/rpip
pytest
```

### Mock Issues

If mocks aren't working as expected, verify the import path:

```python
# Use the full path as seen from the module being tested
@patch('main.function_name')  # Not 'rpip.main.function_name'
```

## Contributing

When adding new features:

1. Write unit tests for individual functions
2. Write integration tests for workflows
3. Ensure all tests pass: `pytest`
4. Check coverage: `pytest --cov=.`
5. Aim for >80% code coverage
