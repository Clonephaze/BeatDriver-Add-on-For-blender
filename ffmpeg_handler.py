import os
import sys
import platform
import subprocess
import tempfile
import shutil
import urllib.request
import zipfile
import tarfile

def is_ffmpeg_available():
    """Check if FFmpeg is already available on the system."""
    try:
        # Try to run ffmpeg -version
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=3
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return False

def get_ffmpeg_download_url():
    """Get the appropriate FFmpeg download URL for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == 'windows':
        if 'amd64' in machine or 'x86_64' in machine:
            return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        else:
            return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win32-gpl.zip"
    elif system == 'darwin':  # macOS
        return "https://evermeet.cx/ffmpeg/getrelease/zip"
    elif system == 'linux':
        if 'amd64' in machine or 'x86_64' in machine:
            return "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        elif 'aarch64' in machine or 'arm64' in machine:
            return "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
    
    raise RuntimeError(f"Unsupported platform: {system} {machine}")

def download_and_setup_ffmpeg(target_dir):
    """Download and extract FFmpeg to the target directory."""
    url = get_ffmpeg_download_url()
    temp_dir = tempfile.mkdtemp()
    download_path = os.path.join(temp_dir, "ffmpeg.archive")
    
    try:
        print(f"Downloading FFmpeg from {url}...")
        urllib.request.urlretrieve(url, download_path)
        
        print("Extracting FFmpeg...")
        if url.endswith('.zip'):
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        elif url.endswith('.tar.xz') or url.endswith('.tar.gz'):
            with tarfile.open(download_path) as tar_ref:
                tar_ref.extractall(temp_dir)
        
        # Find the ffmpeg executable
        ffmpeg_exe = None
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.startswith('ffmpeg') and (file.endswith('.exe') or '.' not in file):
                    ffmpeg_exe = os.path.join(root, file)
                    break
            if ffmpeg_exe:
                break
        
        if not ffmpeg_exe:
            raise RuntimeError("Could not find ffmpeg executable in the downloaded archive")
        
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy ffmpeg to the target directory
        target_path = os.path.join(target_dir, os.path.basename(ffmpeg_exe))
        shutil.copy2(ffmpeg_exe, target_path)
        
        # Make executable on Unix-like systems
        if platform.system() != 'Windows':
            os.chmod(target_path, 0o755)
        
        return target_path
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

def configure_librosa_to_use_local_ffmpeg(ffmpeg_path):
    """Configure the environment to make librosa use our local FFmpeg."""
    os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ["PATH"]
    # Some versions of audioread/librosa check specific env vars
    os.environ["AUDIOREAD_FFMPEG_EXE"] = ffmpeg_path