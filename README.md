# Whisper Dictation & File Transcriber

[![Download Latest Release](https://img.shields.io/github/v/release/matdac12/transcriber?label=Download&style=for-the-badge&logo=windows&logoColor=white)](https://github.com/matdac12/transcriber/releases/latest)
[![Total Downloads](https://img.shields.io/github/downloads/matdac12/transcriber/total?style=for-the-badge&logo=github)](https://github.com/matdac12/transcriber/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)](LICENSE)

A comprehensive Windows application suite featuring real-time speech-to-text dictation and audio file transcription using OpenAI's Whisper model. **Works completely offline** with no internet required.

Perfect for:
- Quick note-taking while working
- Voice dictation for emails and documents
- Transcribing interviews, podcasts, and recordings
- Converting meeting recordings to text
- Capturing ideas without interrupting your workflow
- Privacy-conscious users (all processing local)

## Features

✨ **Real-Time Dictation Features:**
- 🎤 **Global hotkey recording** - Press Alt Gr to start/stop recording from anywhere
- ✨ **Auto-paste** - Transcribed text automatically pastes at your cursor position
- 📋 **Clipboard integration** - Text also copied to clipboard for manual pasting
- 🎨 **Color-coded visual feedback** - Systray icon shows status: 🔵 Blue (ready) → 🔴 Red (recording) → 🟢 Green (done!)
- 📝 **Persistent logging** - All transcriptions saved with timestamp and duration
- 🎯 **Minimal interference** - Runs silently in system tray, no terminal window

🎬 **File Transcription Features (NEW!):**
- 📁 **Upload audio files** - Support for M4A, MP3, WAV, AAC, FLAC, OGG (iPhone voice notes ready!)
- 📱 **iPhone compatible** - Direct support for iPhone voice memos (.m4a)
- 📄 **Easy-to-use GUI** - Simple window interface for file selection and transcription
- ⚙️ **Model selection** - Choose from tiny, base, small, medium, or large models
- 📊 **Progress tracking** - Real-time progress bar for long files
- 💾 **Save transcriptions** - Export to .txt files with auto-naming
- 🔄 **Smart chunking** - Automatically divides long files for efficient processing
- 🖥️ **Dual operation** - Run file transcription and dictation simultaneously
- ✅ **Zero setup** - Works immediately, no FFmpeg or external tools needed

🚀 **Performance Features:**
- ⚡ **Blazing fast transcription** - Uses faster-whisper (4-8x faster than original)
- 🎮 **GPU acceleration** - Auto-detects NVIDIA GPU for 10-20x speedup
- 🗣️ **Smart VAD** - Voice Activity Detection removes silence for faster processing
- 🔧 **No internet required** - Everything runs locally on your machine

## Requirements

- **Windows 10/11**
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Microphone**
- **~1GB RAM** (with base model)
- **Administrator privileges** (for global hotkey)

## Installation

### ⚡ Quick Install (Recommended)

**[📥 Download WhisperDictation_Setup.exe](https://github.com/matdac12/transcriber/releases/latest)**

The installer includes:
- ✅ Both dictation and file transcription apps
- ✅ All dependencies pre-configured
- ✅ Start Menu shortcuts
- ✅ Optional desktop shortcuts
- ✅ Optional auto-start on Windows login
- ✅ Optional Ollama AI integration for summaries
- ✅ No external tools required

**Installation steps:**
1. Download the latest `WhisperDictation_Setup.exe` from the [Releases page](https://github.com/matdac12/transcriber/releases/latest)
2. Run the installer (requires administrator privileges)
3. Follow the setup wizard
4. Launch "Whisper Dettatura" from Start Menu or desktop
5. AI models (~150MB) download automatically on first use

**System Requirements:**
- Windows 10/11 (64-bit)
- ~1GB available disk space (plus ~150MB for models)
- Microphone for dictation
- Internet connection for first-time model download

### Option 2: Development Setup

For developers or users who want to run from source:

#### 1. Clone or Download Repository

```bash
git clone https://github.com/matdac12/whisper-dictation.git
cd whisper-dictation
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The first time you run the app, Whisper will download the base model (~141MB) automatically.

#### 4. GPU Support (Optional - Recommended for Best Performance)

For **10-20x faster** transcription with NVIDIA GPU, you'll need CUDA 12.x and cuDNN 9 installed, plus CTranslate2 with GPU support.

**Installation:**
- **System requirements:** NVIDIA GPU driver + CUDA 12.x + cuDNN 9 (download from NVIDIA website)
- See the [faster-whisper documentation](https://github.com/SYSTRAN/faster-whisper#gpu) for current GPU installation instructions
- See the [CTranslate2 installation guide](https://opennmt.net/CTranslate2/installation.html) for CUDA requirements and compatible versions
- [NVIDIA CUDA Toolkit download](https://developer.nvidia.com/cuda-downloads)

CTranslate2 will automatically detect and use your GPU if CUDA is properly installed. CPU-only mode still works great with the optimizations!

**Note:** The model will download automatically on first launch (~141MB for base model)

## Quick Start

### Real-Time Dictation

**Option A: Single Launch**
```bash
python systray_dictation.py
```

**Option B: Silent Launch (No Terminal)**
Double-click: **`run_systray.vbs`**

This launches the app silently with no terminal window - just the systray icon.

### File Transcription

```bash
python file_transcriber_ui.py
```

Or from the systray app: Right-click the icon → **"Open File Transcriber..."**

## Usage

### Real-Time Dictation

1. **Launch the app** (see Quick Start above)
2. **Right-click the blue systray icon** → "Start Listening"
3. **Click where you want the text to appear** (Word, email, notepad, etc.)
4. **Press Alt Gr** to start recording (icon turns 🔴 RED)
5. **Speak naturally**
6. **Press Alt Gr again** to stop and transcribe
7. **Icon turns 🟢 GREEN** and text **automatically pastes** at your cursor!

**That's it!** No need to manually paste - your words appear instantly wherever your cursor is positioned.

### File Transcription

1. **Launch the File Transcriber** (see Quick Start above)
2. **Click "Browse..."** to select your audio file
   - iPhone voice notes (.m4a) ✅
   - MP3, AAC, WAV, FLAC, OGG ✅
3. **Choose a model** from the dropdown (base recommended for balance)
4. **Click "Transcribe"** and watch the progress bar
5. **Review the transcription** in the text area
6. **Click "Save Transcription"** to export as .txt file

**Pro Tips:**
- Larger models (medium, large) are more accurate but slower
- Tiny model is great for quick transcriptions and testing
- Long files are automatically chunked for efficient processing
- You can run dictation and file transcription simultaneously!
- **iPhone users:** Just transfer your voice memos and transcribe directly - no conversion needed!

### Visual Feedback System

**Pin the systray icon to your taskbar** (drag to bottom-right corner) for easy visibility:

- 🔵 **BLUE** = Ready to record (listening for Alt Gr)
- 🔴 **RED** = Recording in progress
- 🟢 **GREEN** = Transcription complete! (text copied to clipboard)
  - Automatically returns to blue after 2 seconds

No pop-up notifications needed - just watch the icon color!

### Systray Menu Options

- **Start Listening** - Activates the hotkey listener
- **Stop Listening** - Deactivates the hotkey (stops recording capability)
- **✓ Tiny Model / ✓ Base Model** - Switch between model sizes
- **Open File Transcriber...** - Launch the file transcription window
- **View Log** - Opens `dictation_log.txt` in your default text editor
- **Clear Log** - Deletes all transcription history
- **Exit** - Closes the application

## Setup Auto-Start (Windows Startup)

Run the app automatically when Windows starts:

### Method 1: Windows Task Scheduler (Recommended)

1. Press `Win + R` → type `taskschd.msc` → Enter
2. Click **"Create Task"** in the right panel
3. **General tab:**
   - Name: `WhisperDictation`
   - ✓ Check "Run with highest privileges"
4. **Triggers tab:**
   - Click "New..." → Select "At startup" → OK
5. **Actions tab:**
   - Click "New..."
   - Browse to: `C:\path\to\whisper-dictation\run_systray.vbs`
   - Click OK
6. Click **OK** to save

Now the app will launch automatically at startup in the background!

### Method 2: Startup Folder

1. Go to: `C:\Users\[YourUsername]\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
2. Create a shortcut to `run_systray.vbs` and place it here

## Configuration

### Change the Hotkey

Edit `systray_dictation.py` line 36:

```python
self.hotkey = "alt gr"  # Change to your preferred hotkey
```

**Common hotkey options:**
- `"alt gr"` - Alt Gr/Right Alt (default)
- `"scroll lock"` - Scroll Lock key (dedicated key)
- `"pause"` - Pause/Break key (dedicated key)
- `"shift+f12"` - Shift + F12
- `"f12"` - Function key
- `"insert"` - Insert key

For more options, see: [keyboard library docs](https://github.com/boppreh/keyboard#api)

### Change the Model

Edit `systray_dictation.py` line 281:

```python
dictation = WhisperDictation(model_size="base")
```

**Available models:**

| Model  | Speed    | Accuracy | VRAM | CPU Latency* | GPU Latency* |
|--------|----------|----------|------|-------------|-------------|
| tiny   | ⚡⚡⚡⚡   | ⭐       | ~1GB | ~0.3s       | ~0.1s       |
| base   | ⚡⚡⚡    | ⭐⭐⭐   | ~1GB | ~0.8s       | ~0.2s       |
| small  | ⚡⚡     | ⭐⭐⭐⭐  | ~2GB | ~2s         | ~0.5s       |
| medium | ⚡       | ⭐⭐⭐⭐⭐ | ~5GB | ~6s         | ~1.5s       |
| large  | 🐌      | ⭐⭐⭐⭐⭐ | ~10GB| ~12s        | ~3s         |

*Approximate latency for 10 seconds of audio with optimizations enabled

## Log File

All transcriptions are saved to `dictation_log.txt` in the app directory.

**Format:**
```
[2024-10-17 14:30:45] (2.34s) Hello this is a test message
[2024-10-17 14:31:12] (1.89s) Another dictation example
```

View it anytime by right-clicking the systray icon → "View Log"

## Troubleshooting

### ❌ Microphone not being detected
- Check Windows Sound Settings (right-click speaker icon → Sound settings)
- Ensure your microphone is set as the default recording device
- Test with Windows Sound Recorder
- Restart the app

### ❌ Hotkey doesn't work
- Make sure you're running as Administrator
- Some applications may hijack global hotkeys
- Try a different hotkey key combination
- Close other hotkey-binding apps (Discord overlays, etc.)

### ❌ Slow transcription
- First run downloads the model (~141MB) - this is normal
- **Install GPU support** for 10-20x speedup - see [GPU Support section](#4-gpu-support-optional---recommended-for-best-performance) for installation links
- Use a smaller model (tiny or base) - edit line 281 in `systray_dictation.py`
- Check CTranslate2 logs on startup to see if GPU was detected
- Close other memory-intensive applications
- Ensure you have the latest version with all optimizations

### ❌ "No module named..." error
```bash
# Make sure venv is activated:
venv\Scripts\activate

# Reinstall dependencies:
pip install -r requirements.txt
```

### ❌ App crashes immediately
- Run from PowerShell with error messages: `python systray_dictation.py`
- Check your microphone is working
- Ensure Python 3.8+ installed

### ❌ File transcription fails with audio format error
- Supported formats: M4A, MP3, WAV, AAC, FLAC, OGG, MP4 (all included!)
- Ensure dependencies are installed: `pip install av soundfile scipy`
- For corrupted files: Try converting with a free tool like [Audacity](https://www.audacityteam.org/)

## Building the Windows Installer

Want to create a standalone Windows installer? Follow these steps:

### Prerequisites

1. **Python environment** with all dependencies installed
2. **PyInstaller**: `pip install pyinstaller`
3. **Inno Setup**: Download from https://jrsoftware.org/isinfo.php

### Build Steps

1. **Build the executables:**
   ```bash
   python build_installer.py
   ```

   This creates:
   - `dist/DictationApp/WhisperDictation.exe` - Systray dictation app
   - `dist/DictationApp/FileTranscriber.exe` - File transcription GUI
   - Supporting files and documentation

2. **Create the installer:**
   - Open `installer.iss` in Inno Setup
   - Click **Compile** (or right-click → Compile)
   - The installer will be created in `installer_output/`

3. **Distribute:**
   - Share `WhisperDictation_Setup.exe` with users
   - ~50-100MB (includes both apps and dependencies)
   - First run will download AI models (~150MB)

The installer includes:
- Start Menu shortcuts for both apps
- Optional desktop shortcut
- Optional auto-start on Windows login
- Uninstaller
- Quick start documentation

## File Structure

```
whisper-dictation/
├── systray_dictation.py      # Real-time dictation app (systray)
├── file_transcriber_ui.py    # File transcription GUI
├── file_transcriber_core.py  # File transcription logic
├── run_systray.vbs           # Silent launcher for systray app
├── build_installer.py        # PyInstaller build script
├── installer.iss             # Inno Setup installer script
├── requirements.txt          # Python dependencies
├── dictation_log.txt         # Auto-generated transcription log
├── README.md                 # This file
└── venv/                     # Virtual environment (created locally)
```

## How It Works

### Real-Time Dictation

1. **Recording** - Captures audio from your microphone in real-time (🔴 red icon)
2. **Processing** - Whisper model converts audio to text (runs locally)
3. **Output** - Text auto-pastes at cursor position, icon turns 🟢 green
4. **Logging** - Everything is saved with timestamp and duration

### File Transcription

1. **File Loading** - FFmpeg converts audio file to 16kHz mono format
2. **Chunking** - Long files divided into 30-minute segments
3. **Processing** - Each chunk transcribed with Whisper model
4. **Assembly** - Chunks combined into complete transcription
5. **Export** - Save as .txt file with automatic naming

No data is ever sent to external servers - it's 100% local processing!

## Performance Optimizations

This app includes several optimizations for Windows:

1. **faster-whisper** - Uses CTranslate2 for 4-8x faster CPU inference
2. **Auto GPU detection** - Automatically uses NVIDIA GPU if available (10-20x speedup)
3. **Voice Activity Detection (VAD)** - Removes silence before/after speech for faster processing
4. **Smart chunking** - Long audio files automatically divided for efficient processing
5. **Color-coded visual feedback** - No popup notifications to distract you
6. **Optimized audio buffering** - Uses deque for efficient memory management
7. **Shared model loading** - Both apps can use same model instance to save memory

### Performance Tips

- **Install CUDA support** - Get massive speedup on NVIDIA GPUs (see GPU Support section above)
- **Use 'tiny' or 'base' model** - Best balance of speed and accuracy for most use cases
- **First launch is slower** - Model downloads and initializes (~141MB)
- **Subsequent launches are instant** - Model is cached locally
- **Speak clearly with pauses** - Better accuracy and natural speech patterns
- **Quiet environment** - Reduces background noise for better transcription

## Contributing

Found a bug or have a feature request? Feel free to open an issue or submit a pull request!

## License

MIT License - Feel free to use and modify for personal or commercial use.

## Disclaimer

This tool uses OpenAI's Whisper model. Audio processing happens entirely on your local machine. No data is sent to external servers or OpenAI.

## Credits

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [pystray](https://github.com/moses-palmer/pystray) - System tray integration
- [sounddevice](https://github.com/spatialaudio/python-sounddevice) - Audio recording
- [keyboard](https://github.com/boppreh/keyboard) - Global hotkey support

## Support

If you encounter issues:

1. **Check Troubleshooting section** above
2. **Run with error messages**: `python systray_dictation.py`
3. **Open an issue** with error details and your setup

---

**Happy Dictating!** 🎤✨
