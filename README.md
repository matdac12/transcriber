# Whisper Dictation - Windows Systray App

A lightweight Windows systray application for hands-free speech-to-text dictation using OpenAI's Whisper model. **Works completely offline** with no internet required.

Perfect for:
- Quick note-taking while working
- Voice dictation for emails and documents
- Capturing ideas without interrupting your workflow
- Privacy-conscious users (all processing local)

## Features

✨ **Core Features:**
- 🎤 **Global hotkey recording** - Press Alt Gr to start/stop recording from anywhere
- 📋 **Auto-copy to clipboard** - Transcribed text automatically copied, ready to paste
- 🔴 **Visual feedback** - Systray icon changes color: Blue (listening) → Red (recording)
- 📢 **Notifications** - Pop-up messages in bottom-right corner show recording status & results
- 📝 **Persistent logging** - All transcriptions saved with timestamp and duration
- 🔧 **No internet required** - Everything runs locally on your machine
- 🎯 **Minimal interference** - Runs silently in system tray, no terminal window
- ⚡ **Fast transcription** - Uses Whisper base model (~1GB RAM)

## Requirements

- **Windows 10/11**
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Microphone**
- **~1GB RAM** (with base model)
- **Administrator privileges** (for global hotkey)

## Installation

### 1. Clone or Download Repository

```bash
git clone https://github.com/matdac12/whisper-dictation.git
cd whisper-dictation
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The first time you run the app, Whisper will download the base model (~141MB) automatically.

### 4. Download Whisper Model

Download the base Whisper model (~141MB) before first run:

```bash
python -c "import whisper; whisper.load_model('base')"
```

This ensures the model is cached and ready. First run will be much faster!

**Note:** This step is optional - the model will download automatically on first launch if you skip it.

### 5. (Optional) GPU Support

For faster transcription with NVIDIA GPU:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Quick Start

### Option A: Single Launch
```bash
python systray_dictation.py
```

### Option B: Silent Launch (No Terminal)
Double-click: **`run_systray.vbs`**

This launches the app silently with no terminal window - just the systray icon.

## Usage

1. **Launch the app** (see Quick Start above)
2. **Right-click the blue systray icon** → "Start Listening"
3. **Press Alt Gr** to start recording
4. **Speak naturally**
5. **Press Alt Gr again** to stop and transcribe
6. **Text appears in a notification** and is copied to clipboard
7. **Paste anywhere** with Ctrl+V

### Systray Menu Options

- **Start Listening** - Activates the hotkey listener
- **Stop Listening** - Deactivates the hotkey (stops recording capability)
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

Edit `systray_dictation.py` line 24:

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

Edit `systray_dictation.py` line 207:

```python
dictation = WhisperDictation(model_size="base")
```

**Available models:**
| Model  | Speed    | Accuracy | VRAM | Latency |
|--------|----------|----------|------|---------|
| tiny   | ⚡⚡⚡    | ⭐       | ~1GB | ~1s     |
| base   | ⚡⚡     | ⭐⭐⭐   | ~1GB | ~3s     |
| small  | ⚡      | ⭐⭐⭐⭐  | ~2GB | ~10s    |
| medium | 🐌      | ⭐⭐⭐⭐⭐ | ~5GB | ~30s    |
| large  | 🐢      | ⭐⭐⭐⭐⭐ | ~10GB| ~60s    |

## Log File

All transcriptions are saved to `dictation_log.txt` in the app directory.

**Format:**
```
[2024-10-17 14:30:45] (2.34s) Hello this is a test message
[2024-10-17 14:31:12] (1.89s) Another dictation example
```

View it anytime by right-clicking the systray icon → "View Log"

## Troubleshooting

### ❌ Notifications don't appear
- Ensure you're running the app as Administrator
- Check Windows notification settings
- Try restarting the app

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
- Use a smaller model (tiny or base)
- Install GPU support (see Installation section)
- Close other memory-intensive applications
- Restart your computer

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

## File Structure

```
whisper-dictation/
├── systray_dictation.py      # Main application
├── run_systray.vbs           # Silent launcher
├── requirements.txt          # Python dependencies
├── dictation_log.txt         # Auto-generated transcription log
├── README.md                 # This file
└── venv/                     # Virtual environment (created locally)
```

## How It Works

1. **Recording** - Captures audio from your microphone in real-time
2. **Processing** - Whisper model converts audio to text (runs locally)
3. **Output** - Text is copied to clipboard and shown in notification
4. **Logging** - Everything is saved with timestamp and duration

No data is ever sent to external servers - it's 100% local processing!

## Performance Tips

- **First launch is slower** - Whisper model downloads and initializes
- **Subsequent launches are instant** - Model is cached
- **Longer recordings take longer** - Processing time scales with audio length
- **Keep sentences short** - Better accuracy with natural speech patterns
- **Quiet environment** - Better transcription accuracy

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
