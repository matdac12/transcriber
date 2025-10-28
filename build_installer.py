"""
Build script for creating Windows executables using PyInstaller.
Creates standalone .exe files for both the systray app and file transcriber.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def clean_build_folders():
    """Remove old build and dist folders."""
    folders_to_clean = ['build', 'dist']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"Cleaning {folder}/ folder...")
            shutil.rmtree(folder)
    print("✓ Build folders cleaned\n")


def build_systray_app():
    """Build the systray dictation app."""
    print("=" * 60)
    print("Building Systray Dictation App...")
    print("=" * 60)

    command = [
        'pyinstaller',
        '--name=WhisperDictation',
        '--onefile',
        '--windowed',  # No console window
        '--icon=NONE',  # Add your own icon file here if available
        '--add-data=run_systray.vbs;.',  # Include the VBS launcher
        '--hidden-import=faster_whisper',
        '--hidden-import=ctranslate2',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--hidden-import=sounddevice',
        '--hidden-import=pyperclip',
        '--hidden-import=keyboard',
        '--hidden-import=numpy',
        '--collect-all=faster_whisper',
        '--collect-all=ctranslate2',
        'systray_dictation.py'
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✓ Systray app built successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building systray app:")
        print(e.stderr)
        return False


def build_file_transcriber():
    """Build the file transcriber GUI app."""
    print("=" * 60)
    print("Building File Transcriber App...")
    print("=" * 60)

    command = [
        'pyinstaller',
        '--name=FileTranscriber',
        '--onefile',
        '--windowed',  # No console window
        '--icon=NONE',  # Add your own icon file here if available
        '--hidden-import=faster_whisper',
        '--hidden-import=ctranslate2',
        '--hidden-import=tkinter',
        '--hidden-import=soundfile',
        '--hidden-import=scipy',
        '--hidden-import=numpy',
        '--hidden-import=av',
        '--hidden-import=ttkbootstrap',
        '--hidden-import=requests',
        '--collect-all=faster_whisper',
        '--collect-all=ctranslate2',
        '--collect-all=soundfile',
        '--collect-all=av',
        '--collect-all=ttkbootstrap',
        'file_transcriber_ui.py'
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✓ File transcriber built successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building file transcriber:")
        print(e.stderr)
        return False


def check_dependencies():
    """
    Check that all required dependencies are installed.
    """
    print("=" * 60)
    print("Checking dependencies...")
    print("=" * 60)

    required = ['faster_whisper', 'soundfile', 'scipy', 'av', 'tkinter', 'pystray', 'ttkbootstrap', 'requests']
    missing = []

    for module in required:
        try:
            if module == 'tkinter':
                __import__('tkinter')
            else:
                __import__(module)
            print(f"✓ {module} installed")
        except ImportError:
            missing.append(module)
            print(f"❌ {module} missing")

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Install them with: pip install " + " ".join(missing))
        return False

    print("✓ All dependencies installed\n")
    return True


def create_dist_package():
    """Create the final distribution package."""
    print("=" * 60)
    print("Creating Distribution Package...")
    print("=" * 60)

    # Create a DictationApp folder in dist
    package_dir = os.path.join('dist', 'DictationApp')
    os.makedirs(package_dir, exist_ok=True)

    # Copy executables
    files_to_copy = [
        ('dist/WhisperDictation.exe', package_dir),
        ('dist/FileTranscriber.exe', package_dir),
        ('run_systray.vbs', package_dir),
        ('README.md', package_dir),
    ]

    for src, dst in files_to_copy:
        if os.path.exists(src):
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"✓ Copied {os.path.basename(src)}")
            else:
                shutil.copytree(src, os.path.join(dst, os.path.basename(src)))
                print(f"✓ Copied {os.path.basename(src)}/")
        else:
            print(f"⚠️  File not found: {src}")

    # Create a simple batch file to run the systray app
    batch_content = '''@echo off
echo Starting Whisper Dictation...
start "" "WhisperDictation.exe"
'''
    batch_path = os.path.join(package_dir, 'Start_Dictation.bat')
    with open(batch_path, 'w') as f:
        f.write(batch_content)
    print("✓ Created Start_Dictation.bat")

    print(f"\n✓ Distribution package created in: {package_dir}\n")


def create_readme_for_dist():
    """Create a quick start readme for the distribution."""
    readme_content = """# Whisper Dictation & File Transcriber

## Quick Start

### Dictation (Voice to Text)
1. Run `Start_Dictation.bat` or `WhisperDictation.exe`
2. Look for the blue microphone icon in your system tray
3. Right-click the icon and select "Start Listening"
4. Press and hold Alt Gr to record
5. Release Alt Gr to transcribe and auto-paste

### File Transcription
1. Run `FileTranscriber.exe`
2. Click "Browse..." to select an audio file
   - iPhone voice notes (.m4a) ✓
   - MP3, AAC, WAV, FLAC, OGG ✓
3. Choose a model size (base recommended)
4. Click "Transcribe"
5. Save the transcription to a text file

## Notes

- First run will download Whisper models (~150MB)
- Larger models are more accurate but slower
- Supports M4A, MP3, WAV, AAC, FLAC, OGG natively
- Both apps can run simultaneously
- iPhone voice memos work directly - no conversion needed!

## Troubleshooting

If transcription fails:
1. Ensure microphone/audio file is accessible
2. Supported audio formats: M4A, MP3, WAV, AAC, FLAC, OGG
3. Try a smaller model if running out of memory

For more information, see the full README.md
"""

    package_dir = os.path.join('dist', 'DictationApp')
    readme_path = os.path.join(package_dir, 'QUICKSTART.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✓ Created QUICKSTART.txt")


def main():
    """Main build process."""
    print("\n" + "=" * 60)
    print(" Whisper Dictation - Build Script")
    print("=" * 60 + "\n")

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✓ PyInstaller version: {PyInstaller.__version__}\n")
    except ImportError:
        print("❌ PyInstaller not found!")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)

    # Clean previous builds
    clean_build_folders()

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed!")
        sys.exit(1)

    # Build both applications
    systray_success = build_systray_app()
    transcriber_success = build_file_transcriber()

    if not (systray_success and transcriber_success):
        print("\n❌ Build failed!")
        sys.exit(1)

    # Create distribution package
    create_dist_package()
    create_readme_for_dist()

    print("=" * 60)
    print(" Build Complete!")
    print("=" * 60)
    print(f"\nFiles are ready in: dist/DictationApp/")
    print("\nNext steps:")
    print("1. Test the executables in dist/DictationApp/")
    print("2. Run the Inno Setup script (installer.iss) to create an installer")
    print("   - Install Inno Setup from: https://jrsoftware.org/isinfo.php")
    print("   - Right-click installer.iss and select 'Compile'")
    print("\n")


if __name__ == "__main__":
    main()
