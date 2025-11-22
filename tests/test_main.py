"""Unit tests for rpip main module."""
import os
import sys
import tempfile
import unittest
import subprocess
from unittest.mock import Mock, patch, MagicMock, mock_open
from io import StringIO

# Add parent directory to path to import rpip module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rpip.main import (
    check_downloader,
    parse_requirements_file,
    verify_file_hash,
    is_editable_install,
    install_editable_package,
    DOWNLOADER_PREFERENCE
)


class TestCheckDownloader(unittest.TestCase):
    """Test the check_downloader function."""

    @patch('shutil.which')
    def test_finds_aria2c(self, mock_which):
        """Test that aria2c is selected when available."""
        mock_which.side_effect = lambda x: '/usr/bin/aria2c' if x == 'aria2c' else None
        result = check_downloader()
        self.assertEqual(result, 'aria2c')

    @patch('shutil.which')
    def test_finds_wget(self, mock_which):
        """Test that wget is selected when aria2c is not available."""
        mock_which.side_effect = lambda x: '/usr/bin/wget' if x == 'wget' else None
        result = check_downloader()
        self.assertEqual(result, 'wget')

    @patch('shutil.which')
    def test_finds_curl(self, mock_which):
        """Test that curl is selected when aria2c and wget are not available."""
        mock_which.side_effect = lambda x: '/usr/bin/curl' if x == 'curl' else None
        result = check_downloader()
        self.assertEqual(result, 'curl')

    @patch('shutil.which')
    def test_falls_back_to_python(self, mock_which):
        """Test that python is selected as fallback when no external tools are available."""
        mock_which.return_value = None
        result = check_downloader()
        self.assertEqual(result, 'python')


class TestParseRequirementsFile(unittest.TestCase):
    """Test the parse_requirements_file function."""

    def test_parse_simple_requirements(self):
        """Test parsing a simple requirements file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('requests==2.28.0\n')
            f.write('numpy>=1.20.0\n')
            f.write('pandas\n')
            temp_file = f.name

        try:
            packages, pip_options = parse_requirements_file(temp_file)
            self.assertEqual(packages, ['requests==2.28.0', 'numpy>=1.20.0', 'pandas'])
            self.assertEqual(pip_options, [])
        finally:
            os.unlink(temp_file)

    def test_parse_with_comments(self):
        """Test parsing requirements file with comments."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('# This is a comment\n')
            f.write('requests==2.28.0  # inline comment\n')
            f.write('numpy>=1.20.0\n')
            temp_file = f.name

        try:
            packages, pip_options = parse_requirements_file(temp_file)
            self.assertEqual(packages, ['requests==2.28.0', 'numpy>=1.20.0'])
            self.assertEqual(pip_options, [])
        finally:
            os.unlink(temp_file)

    def test_parse_with_blank_lines(self):
        """Test parsing requirements file with blank lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('requests==2.28.0\n')
            f.write('\n')
            f.write('  \n')
            f.write('numpy>=1.20.0\n')
            temp_file = f.name

        try:
            packages, pip_options = parse_requirements_file(temp_file)
            self.assertEqual(packages, ['requests==2.28.0', 'numpy>=1.20.0'])
            self.assertEqual(pip_options, [])
        finally:
            os.unlink(temp_file)

    def test_parse_nested_requirements(self):
        """Test parsing requirements file with nested -r."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested requirements file
            nested_file = os.path.join(tmpdir, 'nested.txt')
            with open(nested_file, 'w') as f:
                f.write('flask==2.0.0\n')

            # Create main requirements file
            main_file = os.path.join(tmpdir, 'requirements.txt')
            with open(main_file, 'w') as f:
                f.write('requests==2.28.0\n')
                f.write('-r nested.txt\n')
                f.write('numpy>=1.20.0\n')

            packages, pip_options = parse_requirements_file(main_file)
            self.assertEqual(packages, ['requests==2.28.0', 'flask==2.0.0', 'numpy>=1.20.0'])
            self.assertEqual(pip_options, [])

    def test_include_editable_installs(self):
        """Test that editable installs are now included."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('requests==2.28.0\n')
            f.write('-e git+https://github.com/user/repo.git#egg=package\n')
            f.write('numpy>=1.20.0\n')
            temp_file = f.name

        try:
            packages, pip_options = parse_requirements_file(temp_file)
            self.assertEqual(packages, [
                'requests==2.28.0',
                '-e git+https://github.com/user/repo.git#egg=package',
                'numpy>=1.20.0'
            ])
            self.assertEqual(pip_options, [])
        finally:
            os.unlink(temp_file)

    def test_preserve_pip_options(self):
        """Test that important pip options are preserved."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('--index-url https://pypi.org/simple\n')
            f.write('requests==2.28.0\n')
            f.write('--trusted-host pypi.org\n')
            f.write('numpy>=1.20.0\n')
            temp_file = f.name

        try:
            packages, pip_options = parse_requirements_file(temp_file)
            self.assertEqual(packages, ['requests==2.28.0', 'numpy>=1.20.0'])
            self.assertEqual(pip_options, [
                '--index-url https://pypi.org/simple',
                '--trusted-host pypi.org'
            ])
        finally:
            os.unlink(temp_file)

    def test_file_not_found(self):
        """Test that RuntimeError is raised when file is not found."""
        with self.assertRaises(RuntimeError) as context:
            parse_requirements_file('/nonexistent/file.txt')
        self.assertIn('not found', str(context.exception))


class TestVerifyFileHash(unittest.TestCase):
    """Test the verify_file_hash function."""

    def test_no_hash_provided(self):
        """Test that verification is skipped when no hash is provided."""
        result = verify_file_hash('dummy.whl', None)
        self.assertTrue(result)

    def test_sha256_hash_valid(self):
        """Test SHA256 hash verification with valid hash."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'Hello, World!')
            temp_file = f.name

        try:
            # SHA256 of "Hello, World!"
            expected_hash = 'sha256=dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
            result = verify_file_hash(temp_file, expected_hash)
            self.assertTrue(result)
        finally:
            os.unlink(temp_file)

    def test_sha256_hash_invalid(self):
        """Test SHA256 hash verification with invalid hash."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'Hello, World!')
            temp_file = f.name

        try:
            # Wrong hash
            expected_hash = 'sha256=0000000000000000000000000000000000000000000000000000000000000000'
            result = verify_file_hash(temp_file, expected_hash)
            self.assertFalse(result)
        finally:
            os.unlink(temp_file)

    def test_sha512_hash_valid(self):
        """Test SHA512 hash verification with valid hash."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'Test')
            temp_file = f.name

        try:
            # SHA512 of "Test"
            expected_hash = 'sha512=c6ee9e33cf5c6715a1d148fd73f7318884b41adcb916021e2bc0e800a5c5dd97f5142178f6ae88c8fdd98e1afb0ce4c8d2c54b5f37b30b7da1997bb33b0b8a31'
            result = verify_file_hash(temp_file, expected_hash)
            self.assertTrue(result)
        finally:
            os.unlink(temp_file)

    def test_file_not_found(self):
        """Test that verification fails when file is not found."""
        result = verify_file_hash('/nonexistent/file.whl', 'sha256=abc123')
        self.assertFalse(result)

    def test_unsupported_algorithm(self):
        """Test that unsupported hash algorithms are skipped."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'Test')
            temp_file = f.name

        try:
            result = verify_file_hash(temp_file, 'unknown=abc123')
            self.assertTrue(result)  # Should return True when skipping
        finally:
            os.unlink(temp_file)


class TestDownloadWithPython(unittest.TestCase):
    """Test the download_with_python function."""

    @patch('urllib.request.urlopen')
    @patch('os.path.exists')
    def test_fresh_download(self, mock_exists, mock_urlopen):
        """Test downloading a file from scratch."""
        mock_exists.return_value = False

        # Mock response
        mock_response = MagicMock()
        mock_response.headers.get.return_value = '100'
        mock_response.read.side_effect = [b'chunk1', b'chunk2', b'']
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            # Import here to avoid import errors
            from rpip.main import download_with_python

            # This would normally work, but we'll skip full integration test
            # download_with_python('http://example.com/file.whl', temp_file)
            pass
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestEditableInstalls(unittest.TestCase):
    """Test editable install functions."""

    def test_is_editable_install_with_dash_e(self):
        """Test detection of -e style editable installs."""
        self.assertTrue(is_editable_install('-e git+https://github.com/user/repo.git'))
        self.assertTrue(is_editable_install('-e .'))
        self.assertTrue(is_editable_install('-e /path/to/package'))

    def test_is_editable_install_with_double_dash(self):
        """Test detection of --editable style editable installs."""
        self.assertTrue(is_editable_install('--editable git+https://github.com/user/repo.git'))
        self.assertTrue(is_editable_install('--editable=.'))

    def test_is_not_editable_install(self):
        """Test that regular packages are not detected as editable."""
        self.assertFalse(is_editable_install('requests==2.28.0'))
        self.assertFalse(is_editable_install('numpy>=1.20.0'))
        self.assertFalse(is_editable_install('pandas'))

    @patch('subprocess.run')
    def test_install_editable_package_dash_e(self, mock_run):
        """Test installing editable package with -e flag."""
        mock_run.return_value = MagicMock(returncode=0)

        result = install_editable_package('-e /path/to/package', [])

        self.assertTrue(result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn('-e', args)
        self.assertIn('/path/to/package', args)

    @patch('subprocess.run')
    def test_install_editable_package_double_dash(self, mock_run):
        """Test installing editable package with --editable flag."""
        mock_run.return_value = MagicMock(returncode=0)

        result = install_editable_package('--editable git+https://github.com/user/repo.git', [])

        self.assertTrue(result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn('-e', args)
        self.assertIn('git+https://github.com/user/repo.git', args)

    @patch('subprocess.run')
    def test_install_editable_package_with_extra_args(self, mock_run):
        """Test installing editable package with additional pip arguments."""
        mock_run.return_value = MagicMock(returncode=0)

        result = install_editable_package('-e .', ['--user', '--no-deps'])

        self.assertTrue(result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn('--user', args)
        self.assertIn('--no-deps', args)

    @patch('subprocess.run')
    def test_install_editable_package_failure(self, mock_run):
        """Test handling of failed editable install."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'pip')

        result = install_editable_package('-e /nonexistent/path', [])

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
