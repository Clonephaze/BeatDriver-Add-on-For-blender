import os
import numpy as np
import librosa
import csv
from scipy.signal import medfilt

def audio_to_csv(file_path, output_dir=None, fps=24):
    y, sr = librosa.load(file_path, sr=None)
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
        band_energy = S[idx, :].mean(axis=0)
        band_data.append(band_energy)

    # Normalize and apply EQ bias
    band_data = np.array(band_data)
    band_data *= band_weights[:band_data.shape[0], np.newaxis]
    band_data = band_data / np.max(band_data, axis=1, keepdims=True)
    band_data = medfilt(band_data, kernel_size=(1, 3))  # smoothing

    # Volume (RMS)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
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
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_name = f"{base_name}.csv"
    if output_dir:
        output_path = os.path.join(output_dir, output_name)
    else:
        output_path = output_name

    # Save CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_data[:total_frames])

    return output_path

if __name__ == "__main__":
    import sys
    input_path = sys.argv[1]
    output_dir = None
    fps = 24

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    if len(sys.argv) > 3:
        fps = int(sys.argv[3])

    output_file = audio_to_csv(input_path, output_dir=output_dir, fps=fps)
    print(f"\n✅ CSV exported to: {output_file}\n")


# Example usage (adjust this with actual file path and optional output dir):
# csv_file = audio_to_csv("example.mp3", output_dir=".", fps=24)
# print(f"Saved CSV to: {csv_file}")

