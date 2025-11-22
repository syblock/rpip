import argparse
import subprocess
import json
import os
import shutil
import sys
from typing import List, Tuple, Optional
from urllib.parse import urlparse, unquote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import hashlib

# Force unbuffered output for Docker/CI environments
# This ensures print statements appear immediately
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

# --- Constants ---
# Downloader Preference: external tools are faster, Python fallback is always available
DOWNLOADER_PREFERENCE = ["aria2c", "wget", "curl", "python"]

# --- Helper Functions ---

def check_downloader() -> str:
    """Checks for the presence of a preferred resumable downloader."""
    for tool in DOWNLOADER_PREFERENCE:
        if tool == "python":
            return tool  # Python urllib is always available
        if shutil.which(tool):
            return tool
    # This should never happen since python is in the list
    return "python"

def resolve_package(package_spec: str) -> Tuple[str, str, Optional[str]]:
    """Uses 'pip install --dry-run --report' to find the best URL, filename, and hash."""
    print(f"🔍 Resolving package: {package_spec}")

    # We use a known-good command to force pip to resolve the candidate wheel
    cmd = [
        sys.executable, "-m", "pip", "install",
        package_spec, "--ignore-installed",
        "--dry-run", "--no-deps", "--report", "-"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Extract only the JSON part from stdout
        stdout_str = result.stdout
        json_start = stdout_str.find('{')
        json_end = stdout_str.rfind('}')
        if json_start == -1 or json_end == -1:
            raise RuntimeError("Could not find JSON report in pip output.")
        json_report_str = stdout_str[json_start : json_end + 1]
        report = json.loads(json_report_str)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during pip resolution (Code {e.returncode}):\n{e.stderr}", file=sys.stderr)
        raise RuntimeError(f"Could not resolve package '{package_spec}'.")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Could not parse JSON report from pip: {e}", file=sys.stderr)
        raise RuntimeError(f"Could not resolve package '{package_spec}'.")

    # Safely extract URL, filename, and hash from the report
    try:
        download_info = report['install'][0]['download_info']
        url = download_info['url']

        # Properly extract filename from URL using urlparse
        parsed_url = urlparse(url)
        filename = unquote(os.path.basename(parsed_url.path))

        # Extract hash if available for integrity checking
        archive_info = download_info.get('archive_info', {})
        file_hash = archive_info.get('hash', None)

        return url, filename, file_hash
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Could not find a valid download URL for '{package_spec}': {e}")

def download_with_python(url: str, filename: str):
    """Native Python downloader with resume support using urllib."""

    is_interactive = sys.stdout.isatty()

    # Check if file exists and get its size for resume
    resume_pos = 0
    mode = 'wb'
    if os.path.exists(filename):
        resume_pos = os.path.getsize(filename)
        mode = 'ab'
        if is_interactive:
            print(f"   Resuming from byte {resume_pos}")
        else:
            print(f"   Resuming download for {filename} from byte {resume_pos}...")

    try:
        if not is_interactive:
            print(f"   Downloading {filename}...")

        # Create request with Range header for resume support
        headers = {'User-Agent': 'rpip/1.0'}
        if resume_pos > 0:
            headers['Range'] = f'bytes={resume_pos}-'

        req = Request(url, headers=headers)

        with urlopen(req, timeout=30) as response:
            # Get total file size
            if resume_pos > 0:
                # For resumed downloads, Content-Range header tells us the total
                content_range = response.headers.get('Content-Range')
                if content_range:
                    total_size = int(content_range.split('/')[-1])
                else:
                    # Server doesn't support resume, start over
                    if is_interactive:
                        print("   Server doesn't support resume, starting from beginning...")
                    else:
                        print(f"   Server doesn't support resume for {filename}, starting from beginning...")
                    resume_pos = 0
                    mode = 'wb'
                    total_size = int(response.headers.get('Content-Length', 0))
            else:
                total_size = int(response.headers.get('Content-Length', 0))

            # Download with progress indication
            downloaded = resume_pos
            chunk_size = 8192

            with open(filename, mode) as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Show progress only if interactive
                    if is_interactive and total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(f"\r   Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='', flush=True)

            if is_interactive:
                print()  # New line after progress
            else:
                print(f"   Download complete: {filename}")

    except HTTPError as e:
        if e.code == 416:  # Range Not Satisfiable - file already complete
            print("   File already complete!")
            return
        print(f"\n❌ HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        print(f"   Run the same command again to RESUME the download.", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"\n❌ Network error: {e.reason}", file=sys.stderr)
        print(f"   Run the same command again to RESUME the download.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted. Run the same command to resume.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Download failed: {e}", file=sys.stderr)
        print(f"   Run the same command again to RESUME the download.", file=sys.stderr)
        sys.exit(1)

def download_resumable(url: str, filename: str, downloader: str):
    """Executes the downloader (external tool or Python) with resume flags."""

    is_interactive = sys.stdout.isatty()

    print(f"⬇️  Starting resumable download via {downloader}...")
    if is_interactive:
        print(f"   Target URL: {url}")
        print(f"   Saving as: {filename}")

    # Use native Python downloader
    if downloader == "python":
        download_with_python(url, filename)
        return

    # Base commands for external downloaders
    if downloader == "aria2c":
        cmd = [downloader, "-c", url, "-o", filename]
        if not is_interactive:
            cmd.extend(["--summary-interval=0", "--quiet=true"])
    elif downloader == "wget":
        cmd = [downloader, "-c", url, "-O", filename]
        if not is_interactive:
            cmd.append("-nv")  # Non-verbose
    else:  # curl
        cmd = [downloader, "-C", "-", "-L", "-o", filename, url]
        if not is_interactive:
            cmd.extend(["-s", "-S"])  # Silent but show errors

    try:
        subprocess.run(cmd, check=True)
        if not is_interactive:
            print(f"   Download complete: {filename}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Download failed with exit code {e.returncode}.", file=sys.stderr)
        print(f"   Run the same command again to RESUME the download.", file=sys.stderr)
        sys.exit(1)
        
def verify_file_hash(filename: str, expected_hash: Optional[str]) -> bool:
    """Verifies the SHA256 hash of the downloaded file if hash is provided."""
    if not expected_hash:
        print("⚠️  No hash provided, skipping integrity check.")
        return True

    # Parse hash format (usually "sha256=...")
    if '=' in expected_hash:
        algorithm, hash_value = expected_hash.split('=', 1)
    else:
        algorithm = 'sha256'
        hash_value = expected_hash

    print(f"🔐 Verifying file integrity ({algorithm})...")

    try:
        if algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'sha512':
            hasher = hashlib.sha512()
        elif algorithm == 'md5':
            hasher = hashlib.md5()
        else:
            print(f"⚠️  Unsupported hash algorithm: {algorithm}, skipping verification.", file=sys.stderr)
            return True

        with open(filename, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)

        computed_hash = hasher.hexdigest()

        if computed_hash == hash_value:
            print("✅ File integrity verified.")
            return True
        else:
            print(f"❌ Hash mismatch!", file=sys.stderr)
            print(f"   Expected: {hash_value}", file=sys.stderr)
            print(f"   Got:      {computed_hash}", file=sys.stderr)
            return False

    except FileNotFoundError:
        print(f"❌ File not found: {filename}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️  Error during hash verification: {e}", file=sys.stderr)
        return False

def install_package(filename: str, install_args: List[str]) -> bool:
    """Installs the downloaded wheel file using pip. Returns True if successful."""

    print("📦 Download complete. Installing via pip...")

    # Construct the final pip install command
    final_cmd = [sys.executable, "-m", "pip", "install", filename] + install_args

    try:
        subprocess.run(final_cmd, check=True)
        print("✅ Installation successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n⚠️  Installation failed with exit code {e.returncode}.", file=sys.stderr)
        print(f"   The downloaded file is preserved: {filename}", file=sys.stderr)
        return False

def cleanup(filename: str):
    """Removes the downloaded wheel file."""
    try:
        os.remove(filename)
        print(f"🧹 Cleaned up temporary file: {filename}")
    except OSError as e:
        print(f"⚠️ Warning: Could not remove file {filename}: {e}", file=sys.stderr)

def parse_requirements_file(filepath: str) -> Tuple[List[str], List[str]]:
    """Parse a requirements file and return packages and pip options.

    Returns:
        Tuple of (packages, pip_options) where:
        - packages: List of package specs (including editable installs)
        - pip_options: List of pip options to apply globally (--index-url, etc.)
    """
    packages = []
    pip_options = []

    # Pip options that should be preserved
    PRESERVED_OPTIONS = [
        '--index-url', '--extra-index-url', '--trusted-host',
        '--find-links', '--no-index', '--prefer-binary',
        '--pre', '--no-binary', '--only-binary'
    ]

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Strip whitespace
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Strip comments (but not # in URLs like git+https://...#egg=package)
                # Only strip # if it's preceded by whitespace or at start of line
                if ' #' in line:
                    line = line[:line.index(' #')].strip()
                elif line.startswith('#'):
                    continue

                # Handle -r for nested requirements (recursive)
                if line.startswith('-r') or line.startswith('--requirement'):
                    nested_file = line.split(None, 1)[1] if ' ' in line else line[2:].strip()
                    # Resolve relative path
                    nested_path = os.path.join(os.path.dirname(filepath), nested_file)
                    if os.path.exists(nested_path):
                        nested_packages, nested_options = parse_requirements_file(nested_path)
                        packages.extend(nested_packages)
                        pip_options.extend(nested_options)
                    else:
                        print(f"⚠️  Warning: Nested requirements file not found: {nested_path}", file=sys.stderr)
                    continue

                # Handle -e for editable installs (include them)
                if line.startswith('-e ') or line.startswith('--editable'):
                    packages.append(line)
                    continue

                # Check if this is a pip option we should preserve
                is_preserved_option = False
                for opt in PRESERVED_OPTIONS:
                    if line.startswith(opt):
                        pip_options.append(line)
                        is_preserved_option = True
                        break

                if is_preserved_option:
                    continue

                # Skip other pip options that start with dash
                if line.startswith('-'):
                    continue

                # Add regular packages
                packages.append(line)

    except FileNotFoundError:
        raise RuntimeError(f"Requirements file not found: {filepath}")
    except Exception as e:
        raise RuntimeError(f"Error reading requirements file: {e}")

    return packages, pip_options

def is_editable_install(package_spec: str) -> bool:
    """Check if a package spec is an editable install."""
    return package_spec.startswith('-e ') or package_spec.startswith('--editable')

def install_editable_package(package_spec: str, install_args: List[str]) -> bool:
    """Install an editable package directly via pip (no download needed). Returns True if successful."""
    print(f"📝 Installing editable package: {package_spec}")

    # Parse the package spec to get the actual path/URL
    if package_spec.startswith('-e '):
        editable_spec = package_spec[3:].strip()
    elif package_spec.startswith('--editable '):
        editable_spec = package_spec[11:].strip()
    elif package_spec.startswith('--editable='):
        editable_spec = package_spec[11:].strip()
    else:
        editable_spec = package_spec

    print(f"   Source: {editable_spec}")

    # Construct pip install command for editable package
    cmd = [sys.executable, "-m", "pip", "install", "-e", editable_spec] + install_args

    try:
        subprocess.run(cmd, check=True)
        print("✅ Editable package installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n⚠️  Editable install failed with exit code {e.returncode}.", file=sys.stderr)
        return False

def install_single_package(package_spec: str, install_args: List[str], downloader: str) -> bool:
    """Install a single package with resumable download. Returns True if successful."""
    try:
        # Check if this is an editable install
        if is_editable_install(package_spec):
            return install_editable_package(package_spec, install_args)

        # Regular package installation with resumable download
        # Resolve URL and hash
        url, filename, file_hash = resolve_package(package_spec)

        # Download Resumable
        download_resumable(url, filename, downloader)

        # Verify file integrity
        if not verify_file_hash(filename, file_hash):
            print(f"❌ File integrity check failed for {package_spec}.", file=sys.stderr)
            return False

        # Install Package
        success = install_package(filename, install_args)

        # Cleanup on success
        if success and os.path.exists(filename):
            cleanup(filename)

        return success

    except (RuntimeError, EnvironmentError) as e:
        print(f"❌ Failed to install {package_spec}: {e}", file=sys.stderr)
        return False


# --- Main Logic ---

def main():
    # 1. Argument Parsing (Mimicking pip's basic structure)
    parser = argparse.ArgumentParser(
        description="rpip: Resumable package installer (pip + resumable download).",
        usage="%(prog)s <package_or_file> [pip_install_options]\n"
              "       %(prog)s -r requirements.txt [pip_install_options]"
    )
    # Support both single package and requirements file
    parser.add_argument('target', nargs='?', help="The package name, spec, or requirements file.")
    parser.add_argument('-r', '--requirement', dest='requirements_file',
                       help="Install from the given requirements file.")

    # We use parse_known_args to capture all unhandled flags for pip
    args, unknown_args = parser.parse_known_args()

    # Determine if we're installing from requirements file or single package
    requirements_file = None
    single_package = None

    if args.requirements_file:
        requirements_file = args.requirements_file
    elif args.target:
        # Check if target is a requirements file
        if args.target.endswith(('.txt', '.in')) and os.path.isfile(args.target):
            requirements_file = args.target
        else:
            single_package = args.target
    else:
        parser.print_help()
        sys.exit(1)

    try:
        # Check Downloader
        downloader = check_downloader()

        # Handle requirements file installation
        if requirements_file:
            print(f"📋 Processing requirements file: {requirements_file}")
            packages, pip_options = parse_requirements_file(requirements_file)

            if not packages:
                print("⚠️  No packages found in requirements file.", file=sys.stderr)
                sys.exit(0)

            # Display pip options if any
            if pip_options:
                print(f"🔧 Applying pip options: {' '.join(pip_options)}")

            print(f"📦 Found {len(packages)} package(s) to install\n")

            # Merge pip options from requirements file with command-line args
            combined_args = pip_options + unknown_args

            failed_packages = []
            successful_count = 0

            for idx, package in enumerate(packages, 1):
                print(f"\n{'='*60}")
                print(f"[{idx}/{len(packages)}] Installing: {package}")
                print(f"{'='*60}")

                if install_single_package(package, combined_args, downloader):
                    successful_count += 1
                    print(f"✅ [{idx}/{len(packages)}] Successfully installed: {package}")
                else:
                    failed_packages.append(package)
                    print(f"❌ [{idx}/{len(packages)}] Failed to install: {package}")

            # Summary
            print(f"\n{'='*60}")
            print(f"📊 Installation Summary")
            print(f"{'='*60}")
            print(f"✅ Successful: {successful_count}/{len(packages)}")
            if failed_packages:
                print(f"❌ Failed: {len(failed_packages)}/{len(packages)}")
                print(f"\nFailed packages:")
                for pkg in failed_packages:
                    print(f"  - {pkg}")
                sys.exit(1)
            else:
                print("🎉 All packages installed successfully!")

        # Handle single package installation
        else:
            installation_successful = False
            filename = None

            try:
                # Resolve URL and hash
                url, filename, file_hash = resolve_package(single_package)

                # Download Resumable
                download_resumable(url, filename, downloader)

                # Verify file integrity
                if not verify_file_hash(filename, file_hash):
                    print("❌ File integrity check failed. Please re-download.", file=sys.stderr)
                    sys.exit(1)

                # Install Package
                installation_successful = install_package(filename, unknown_args)

                if not installation_successful:
                    sys.exit(1)

            finally:
                # Cleanup (only if the file exists and installation was successful)
                if filename and os.path.exists(filename) and installation_successful:
                    cleanup(filename)

    except (RuntimeError, EnvironmentError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()