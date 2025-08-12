# BeatDriver

**Turn any audio file into animation-ready data inside Blender — instantly.**

BeatDriver is a Blender add-on that processes audio into normalized float values, auto-configures your scene for synced playback, and applies a ready-to-use Geometry Nodes modifier so your objects react to music in real time.

---

## ✨ Features

- **Multi-band audio analysis** — Outputs normalized float values for:
  - Sub Bass
  - Bass
  - Low Mid
  - Mid
  - High Mid
  - Presence
  - Brilliance
- **Beat/onset detection** — Trigger events when transient peaks occur in any band.
- **Pulse field output** — Generates an intensity spike when a beat happens near a sound event.
- **Automatic scene setup**:
  - Imports your chosen audio file into Blender
  - Adjusts scene settings for perfect audio sync
  - Adds and wires a Geometry Nodes modifier for animation control
- **Common audio format support** — MP3, WAV, FLAC, and more.

---

## 📦 Installation

1. Download the latest release `.zip` from [Releases](../../releases).
2. In Blender, go to:
   - **Edit > Preferences > Add-ons > Install**
3. Select the downloaded `.zip` file.
4. Enable **BeatDriver** in the add-ons list.
5. You’re ready to roll.

---

## 🚀 Usage

1. **Add an object** in your scene you want to animate.
2. Go to **BeatDriver Panel** in the *N-Panel*.
3. Select an audio file (MP3, WAV, FLAC, etc.).
4. Click **Process Audio**.
5. BeatDriver will:
   - Convert the audio into a multi-band dataset
   - Set up the scene for synced playback
   - Apply the “Audio CSV Driver” Geometry Nodes group to your selected object
6. Play the timeline — your object now reacts to the music.

---

## ⚙️ Technical Details

- **Audio Processing**  
  Uses a Python-based analysis pipeline to extract frequency band RMS levels and onset events per frame.  
  Data is normalized (0–1) for consistent animation scaling regardless of input volume.

- **Band Mapping**  
  Default frequency ranges (Hz):  
  - Sub Bass: 20–60  
  - Bass: 60–250  
  - Low Mid: 250–500  
  - Mid: 500–2000  
  - High Mid: 2k–4k  
  - Presence: 4k–6k  
  - Brilliance: 6k–20k  

- **Beat Detection**  
  Peaks are detected using an adaptive threshold algorithm across all bands, producing a boolean flag that can be mapped to animation events or triggers.

- **Geometry Nodes Integration**  
  The included node group uses `Scene Time` → `Sample Index` to pull the correct frame’s data from an internally imported CSV, allowing easy multiplier-based control over animation strength.

---

## 📂 File Structure

BeatDriver/
├── init.py
├── audio_processing.py
├── node_setup.py
├── utils.py
├── blender_manifest.toml
└── README.md

---

## 🖼 Example

![BeatDriver Demo](https://youtu.be/zv0VqOOstxY)  

## 📄 License

GPL-3.0-or-later — See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repo
2. Create a new branch for your feature/fix
3. Submit a pull request with clear notes on your changes

---

## 🙌 Credits

Created by **Clonephaze**  
If you use BeatDriver in your projects, I’d love to see it! Tag me or share your work.

---
