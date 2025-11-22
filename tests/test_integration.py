"""Integration tests for rpip."""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rpip.main import install_single_package, main


class TestInstallSinglePackage(unittest.TestCase):
    """Integration tests for single package installation."""

    @patch('rpip.main.cleanup')
    @patch('rpip.main.install_package')
    @patch('rpip.main.verify_file_hash')
    @patch('rpip.main.download_resumable')
    @patch('rpip.main.resolve_package')
    def test_successful_installation(self, mock_resolve, mock_download,
                                     mock_verify, mock_install, mock_cleanup):
        """Test successful package installation flow."""
        # Setup mocks
        mock_resolve.return_value = ('http://example.com/pkg.whl', 'pkg.whl', 'sha256=abc123')
        mock_verify.return_value = True
        mock_install.return_value = True

        # Run installation
        result = install_single_package('test-package', [], 'python')

        # Verify
        self.assertTrue(result)
        mock_resolve.assert_called_once_with('test-package')
        mock_download.assert_called_once_with('http://example.com/pkg.whl', 'pkg.whl', 'python')
        mock_verify.assert_called_once_with('pkg.whl', 'sha256=abc123')
        mock_install.assert_called_once_with('pkg.whl', [])

    @patch('rpip.main.cleanup')
    @patch('rpip.main.install_package')
    @patch('rpip.main.verify_file_hash')
    @patch('rpip.main.download_resumable')
    @patch('rpip.main.resolve_package')
    def test_failed_hash_verification(self, mock_resolve, mock_download,
                                      mock_verify, mock_install, mock_cleanup):
        """Test installation fails when hash verification fails."""
        # Setup mocks
        mock_resolve.return_value = ('http://example.com/pkg.whl', 'pkg.whl', 'sha256=abc123')
        mock_verify.return_value = False

        # Run installation
        result = install_single_package('test-package', [], 'python')

        # Verify
        self.assertFalse(result)
        mock_install.assert_not_called()
        mock_cleanup.assert_not_called()

    @patch('rpip.main.cleanup')
    @patch('rpip.main.install_package')
    @patch('rpip.main.verify_file_hash')
    @patch('rpip.main.download_resumable')
    @patch('rpip.main.resolve_package')
    def test_failed_installation(self, mock_resolve, mock_download,
                                 mock_verify, mock_install, mock_cleanup):
        """Test when package installation fails."""
        # Setup mocks
        mock_resolve.return_value = ('http://example.com/pkg.whl', 'pkg.whl', 'sha256=abc123')
        mock_verify.return_value = True
        mock_install.return_value = False

        # Run installation
        result = install_single_package('test-package', [], 'python')

        # Verify
        self.assertFalse(result)
        mock_cleanup.assert_not_called()

    @patch('rpip.main.resolve_package')
    def test_resolve_failure(self, mock_resolve):
        """Test when package resolution fails."""
        # Setup mock to raise exception
        mock_resolve.side_effect = RuntimeError('Package not found')

        # Run installation
        result = install_single_package('nonexistent-package', [], 'python')

        # Verify
        self.assertFalse(result)


class TestMainFunction(unittest.TestCase):
    """Integration tests for main function."""

    @patch('rpip.main.cleanup')
    @patch('rpip.main.install_package')
    @patch('rpip.main.verify_file_hash')
    @patch('rpip.main.download_resumable')
    @patch('rpip.main.resolve_package')
    @patch('rpip.main.check_downloader')
    @patch('sys.argv', ['rpip', 'test-package'])
    def test_main_single_package(self, mock_check_downloader, mock_resolve,
                                 mock_download, mock_verify, mock_install, mock_cleanup):
        """Test main function with single package."""
        # Setup mocks
        mock_check_downloader.return_value = 'python'
        mock_resolve.return_value = ('http://example.com/pkg.whl', 'pkg.whl', 'sha256=abc123')
        mock_verify.return_value = True
        mock_install.return_value = True

        # Run main (should not raise exception)
        try:
            main()
        except SystemExit as e:
            # Should exit with 0
            self.assertEqual(e.code, 0)

    @patch('rpip.main.parse_requirements_file')
    @patch('rpip.main.install_single_package')
    @patch('rpip.main.check_downloader')
    @patch('sys.argv', ['rpip', '-r', 'requirements.txt'])
    def test_main_requirements_file(self, mock_check_downloader,
                                   mock_install_single, mock_parse):
        """Test main function with requirements file."""
        # Setup mocks
        mock_check_downloader.return_value = 'python'
        # Return tuple of (packages, pip_options)
        mock_parse.return_value = (['package1', 'package2', 'package3'], [])
        mock_install_single.return_value = True

        # Run main
        try:
            main()
        except SystemExit as e:
            # Should exit with 0 on success
            self.assertEqual(e.code, 0)

        # Verify all packages were installed
        self.assertEqual(mock_install_single.call_count, 3)

    @patch('rpip.main.parse_requirements_file')
    @patch('rpip.main.install_single_package')
    @patch('rpip.main.check_downloader')
    @patch('sys.argv', ['rpip', '-r', 'requirements.txt'])
    def test_main_requirements_file_with_failures(self, mock_check_downloader,
                                                  mock_install_single, mock_parse):
        """Test main function with requirements file where some packages fail."""
        # Setup mocks
        mock_check_downloader.return_value = 'python'
        # Return tuple of (packages, pip_options)
        mock_parse.return_value = (['package1', 'package2', 'package3'], [])
        # package2 fails
        mock_install_single.side_effect = [True, False, True]

        # Run main
        with self.assertRaises(SystemExit) as context:
            main()

        # Should exit with 1 on failure
        self.assertEqual(context.exception.code, 1)

    @patch('sys.argv', ['rpip'])
    def test_main_no_arguments(self):
        """Test main function with no arguments."""
        with self.assertRaises(SystemExit) as context:
            main()
        # Should exit with 1
        self.assertEqual(context.exception.code, 1)


class TestRequirementsFileIntegration(unittest.TestCase):
    """Integration tests for requirements file processing."""

    @patch('rpip.main.install_single_package')
    @patch('rpip.main.check_downloader')
    def test_full_requirements_flow(self, mock_check_downloader, mock_install_single):
        """Test complete flow of installing from requirements file."""
        mock_check_downloader.return_value = 'python'
        mock_install_single.return_value = True

        # Create a temporary requirements file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('# Test requirements\n')
            f.write('requests==2.28.0\n')
            f.write('numpy>=1.20.0\n')
            f.write('\n')
            f.write('pandas  # for data analysis\n')
            temp_file = f.name

        try:
            # Simulate running main with this requirements file
            with patch('sys.argv', ['rpip', '-r', temp_file]):
                try:
                    main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)

            # Verify all 3 packages were installed
            self.assertEqual(mock_install_single.call_count, 3)

            # Verify the packages that were passed
            calls = mock_install_single.call_args_list
            installed_packages = [call[0][0] for call in calls]
            self.assertIn('requests==2.28.0', installed_packages)
            self.assertIn('numpy>=1.20.0', installed_packages)
            self.assertIn('pandas', installed_packages)

        finally:
            os.unlink(temp_file)


class TestRequirementsLocalFile(unittest.TestCase):
    """Test installation of specific requirements_local.txt with ML packages."""

    @patch('rpip.main.install_single_package')
    @patch('rpip.main.check_downloader')
    def test_requirements_local_ml_packages(self, mock_check_downloader, mock_install_single):
        """Test installing from requirements_local.txt with ML/CV packages."""
        mock_check_downloader.return_value = 'python'
        mock_install_single.return_value = True

        # Use the fixture file
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'requirements_local.txt'
        )

        # Simulate running main with this requirements file
        with patch('sys.argv', ['rpip', '-r', fixture_path]):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        # Verify all 6 packages were installed
        self.assertEqual(mock_install_single.call_count, 6)

        # Verify the exact packages that were passed
        calls = mock_install_single.call_args_list
        installed_packages = [call[0][0] for call in calls]

        expected_packages = [
            'numpy==1.22.3',
            'pandas==2.0.3',
            'Pillow==9.0.0',
            'opencv-python==4.9.0.80',
            'tensorflow==2.11.0',
            'keras==2.11.0'
        ]

        for expected_pkg in expected_packages:
            self.assertIn(expected_pkg, installed_packages,
                         f"Package {expected_pkg} was not installed")

    @patch('rpip.main.install_single_package')
    @patch('rpip.main.check_downloader')
    def test_requirements_local_partial_failure(self, mock_check_downloader, mock_install_single):
        """Test handling when some packages in requirements_local.txt fail."""
        mock_check_downloader.return_value = 'python'

        # Simulate tensorflow failing (index 4)
        mock_install_single.side_effect = [True, True, True, True, False, True]

        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'requirements_local.txt'
        )

        with patch('sys.argv', ['rpip', '-r', fixture_path]):
            with self.assertRaises(SystemExit) as context:
                main()

            # Should exit with 1 on failure
            self.assertEqual(context.exception.code, 1)

        # All 6 packages should have been attempted
        self.assertEqual(mock_install_single.call_count, 6)

    @patch('rpip.main.resolve_package')
    @patch('rpip.main.download_resumable')
    @patch('rpip.main.verify_file_hash')
    @patch('rpip.main.install_package')
    @patch('rpip.main.cleanup')
    @patch('rpip.main.check_downloader')
    def test_requirements_local_with_actual_resolution(
        self, mock_check_downloader, mock_cleanup, mock_install,
        mock_verify, mock_download, mock_resolve
    ):
        """Test requirements_local.txt with mocked resolution and download."""
        mock_check_downloader.return_value = 'python'

        # Mock resolve_package to return different URLs for each package
        def mock_resolve_func(package_spec):
            pkg_name = package_spec.split('==')[0].lower()
            return (
                f'https://files.pythonhosted.org/packages/{pkg_name}.whl',
                f'{pkg_name}.whl',
                f'sha256={"a" * 64}'
            )

        mock_resolve.side_effect = mock_resolve_func
        mock_verify.return_value = True
        mock_install.return_value = True

        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'requirements_local.txt'
        )

        with patch('sys.argv', ['rpip', '-r', fixture_path]):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        # Verify resolve was called for each package
        self.assertEqual(mock_resolve.call_count, 6)

        # Verify download was called for each package
        self.assertEqual(mock_download.call_count, 6)

        # Verify install was called for each package
        self.assertEqual(mock_install.call_count, 6)


if __name__ == '__main__':
    unittest.main()
