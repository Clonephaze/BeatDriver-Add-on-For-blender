import os
import sys
import importlib.util
import subprocess
import shutil

# Determine script directory for storing local dependencies
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DEPS_DIR = os.path.join(SCRIPT_DIR, ".local_deps")
FFMPEG_DIR = os.path.join(LOCAL_DEPS_DIR, "ffmpeg")

def check_and_install_dependencies():
    """Check for required packages and install if missing."""
    required_packages = ['numpy', 'librosa', 'scipy']
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing missing dependencies: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ Dependencies installed successfully")
            
            # Force reload modules in case they're partially imported
            for package in missing_packages:
                if package in sys.modules:
                    del sys.modules[package]
                    
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("Please install them manually: pip install " + " ".join(missing_packages))
            return False
    return True

def setup_environment():
    """Set up the environment with all required dependencies."""
    os.makedirs(LOCAL_DEPS_DIR, exist_ok=True)
    
    # Check and install Python dependencies
    if not check_and_install_dependencies():
        return False
    
    # Import the ffmpeg handler module
    try:
        # First check if FFmpeg is already available on the system
        from ffmpeg_handler import is_ffmpeg_available, download_and_setup_ffmpeg, configure_librosa_to_use_local_ffmpeg
        
        if is_ffmpeg_available():
            print("✅ System FFmpeg detected, using system installation")
        else:
            # Check if we have a local copy
            local_ffmpeg = os.path.join(FFMPEG_DIR, "ffmpeg" + (".exe" if sys.platform == "win32" else ""))
            
            if os.path.exists(local_ffmpeg) and os.access(local_ffmpeg, os.X_OK):
                print(f"✅ Using local FFmpeg from: {local_ffmpeg}")
                configure_librosa_to_use_local_ffmpeg(local_ffmpeg)
            else:
                # Download and install FFmpeg locally
                print("⚙️ FFmpeg not found. Downloading local copy (one-time setup)...")
                ffmpeg_path = download_and_setup_ffmpeg(FFMPEG_DIR)
                configure_librosa_to_use_local_ffmpeg(ffmpeg_path)
                print(f"✅ FFmpeg installed locally at: {ffmpeg_path}")
    except Exception as e:
        print(f"⚠️ Warning: FFmpeg setup encountered an issue: {e}")
        print("Some audio formats (MP3, AAC, OGG) may not be supported.")
        print("WAV and AIFF formats will still work.")
    
    return True

def audio_to_csv(file_path, output_path=None, fps=24):
    """Convert audio file to CSV with frequency band data."""
    # Import dependencies here (after they've been installed if needed)
    import numpy as np
    import librosa
    import csv
    from scipy.signal import medfilt

    try:
        # Try to load the audio file
        y, sr = librosa.load(file_path, sr=None)
        
        # Rest of your original function code
        duration = librosa.get_duration(y=y, sr=sr)
        total_frames = int(duration * fps)
        hop_length = int(sr / fps)

        # EQ Bias (can be tuned further)
        band_weights = np.array([1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.5, 0.3])

        # FFT for frequency bands
        S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop_length))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

        band_ranges = [
            (20, 60),     # sub_bass
            (60, 120),    # bass
            (120, 250),   # low_mid
            (250, 2000),  # mid
            (2000, 4000), # high_mid
            (4000, 6000), # presence
            (6000, 12000) # brilliance
        ]

        band_data = []
        for band in band_ranges:
            idx = np.where((freqs >= band[0]) & (freqs < band[1]))[0]
            if len(idx) > 0:  # Check to avoid empty bands
                band_energy = S[idx, :].mean(axis=0)
                band_data.append(band_energy)
            else:
                # Empty band, fill with zeros
                band_data.append(np.zeros(S.shape[1]))

        # Normalize and apply EQ bias
        band_data = np.array(band_data)
        band_data *= band_weights[:band_data.shape[0], np.newaxis]
        
        # Avoid division by zero
        max_values = np.max(band_data, axis=1, keepdims=True)
        max_values[max_values == 0] = 1.0  # Replace zeros with ones to avoid division by zero
        band_data = band_data / max_values
        
        band_data = medfilt(band_data, kernel_size=(1, 3))  # smoothing

        # Volume (RMS)
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
        if np.max(rms) > 0:
            rms /= np.max(rms)
        rms = medfilt(rms, kernel_size=3)

        # Onset detection
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop_length, backtrack=False)
        pulse = np.zeros_like(rms)
        pulse[onsets] = 1

        # Combine all data
        all_data = np.vstack([rms, band_data, pulse]).T

        headers = [
            "loudness", "sub_bass", "bass", "low_mid", "mid",
            "high_mid", "presence", "brilliance", "pulse"
        ]

        # Determine output path
        if output_path:
            # Use the provided output path directly
            final_output_path = output_path
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
        else:
            # Generate default output path based on input filename
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            final_output_path = f"{base_name}.csv"

        # Save CSV
        with open(final_output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(all_data[:total_frames])

        return final_output_path
        
    except Exception as e:
        # Check if the error suggests an ffmpeg issue
        error_msg = str(e).lower()
        if "ffmpeg" in error_msg or "audioread" in error_msg:
            print("❌ Error: This audio format requires FFmpeg, which wasn't found or failed.")
            print("The script will attempt to download FFmpeg automatically next time.")
            # Delete local ffmpeg to force re-download on next run
            if os.path.exists(FFMPEG_DIR):
                shutil.rmtree(FFMPEG_DIR, ignore_errors=True)
        else:
            print(f"❌ Error processing audio file: {e}")
        return None

if __name__ == "__main__":
    # First set up the environment
    if not setup_environment():
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python audio_analysis.py <input_audio_path> [output_csv_path] [fps]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = None
    fps = 24

    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    if len(sys.argv) > 3:
        fps = int(sys.argv[3])

    output_file = audio_to_csv(input_path, output_path=output_path, fps=fps)
    if output_file:
        print(f"\n✅ CSV exported to: {output_file}\n")
    else:
        print("\n❌ Failed to process audio file\n")
        sys.exit(1)