
import pytest
from rpip.main import download_resumable, resolve_package

@pytest.mark.download
def test_download_small_package():
    """Test downloading a small package from PyPI."""
    package_name = "is-odd"
    url, filename, sha256 = resolve_package(package_name)
    downloader = "python"  # Use the python downloader for simplicity
    download_resumable(url, filename, downloader)
