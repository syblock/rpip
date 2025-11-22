
import pytest
import os
import tempfile
import sys
from unittest.mock import patch, MagicMock
from rpip.main import download_resumable, resolve_package, parse_requirements_file, check_downloader, DOWNLOADER_PREFERENCE

@pytest.mark.download
def test_download_small_package():
    """Test downloading a small package from PyPI."""
    package_name = "is-odd"
    url, filename, sha256 = resolve_package(package_name)
    downloader = "python"  # Use the python downloader for simplicity
    download_resumable(url, filename, downloader)

@pytest.mark.download
def test_download_requirements_local_packages():
    """Test downloading all packages from requirements_local.txt."""
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        'fixtures',
        'requirements_local.txt'
    )

    packages, _ = parse_requirements_file(fixture_path)

    # Use a temporary directory for downloads to avoid polluting the workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir) # Change to temp directory for downloads
        try:
            for package_spec in packages:
                if package_spec.startswith('-e') or package_spec.startswith('--editable'):
                    # Editable installs are not downloaded in this flow
                    continue
                print(f"Attempting to download: {package_spec}")
                url, filename, sha256 = resolve_package(package_spec)
                downloader = "python"  # Use the python downloader for simplicity
                download_resumable(url, filename, downloader)
                assert os.path.exists(filename) and os.path.getsize(filename) > 0
                os.remove(filename) # Clean up after each download
        finally:
            os.chdir(original_cwd) # Change back to original directory

@pytest.mark.download_verbose_output # New marker for this test to distinguish it if needed
def test_external_downloader_non_interactive_output():
    """Test external downloaders generate log-friendly output in non-interactive mode."""
    package_name = "is-odd"
    url, filename, sha256 = resolve_package(package_name)

    # Mock sys.stdout.isatty to simulate a non-interactive environment
    with patch('sys.stdout.isatty', return_value=False):
        with patch('subprocess.run') as mock_subprocess_run:
            with patch('builtins.print') as mock_print:
                mock_subprocess_run.return_value = MagicMock(returncode=0)

                # Test each external downloader
                for downloader_tool in [d for d in DOWNLOADER_PREFERENCE if d != "python"]:
                    with patch('shutil.which', side_effect=lambda x: f"/usr/bin/{x}" if x == downloader_tool else None):
                        # Reset mocks for each loop
                        mock_subprocess_run.reset_mock()
                        mock_print.reset_mock()

                        # Create a dummy file for subprocess.run to 'download' into
                        temp_file = os.path.join(tempfile.gettempdir(), filename)
                        with open(temp_file, 'w') as f:
                            f.write('dummy content') # Simulate a downloaded file

                        download_resumable(url, temp_file, check_downloader())

                        # Verify that subprocess.run was called with correct quiet flags
                        mock_subprocess_run.assert_called_once()
                        called_cmd = mock_subprocess_run.call_args[0][0]

                        if downloader_tool == "aria2c":
                            assert "--quiet=true" in called_cmd
                        elif downloader_tool == "wget":
                            assert "-nv" in called_cmd
                        elif downloader_tool == "curl":
                            assert "-s" in called_cmd

                        # Verify rpip's own log-friendly messages
                        mock_print.assert_any_call(f"⬇️  Starting resumable download via {downloader_tool}...")
                        mock_print.assert_any_call(f"   Download complete: {temp_file}")

                        # Ensure no interactive progress (e.g., carriage returns) in the output of rpip's print statements
                        for call_arg in mock_print.call_args_list:
                            assert '\r' not in str(call_arg.args[0])

                        # Clean up dummy file
                        os.remove(temp_file)
