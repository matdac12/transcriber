"""
Download Ollama installer for local builds.
Run this before building the installer locally if you want to include Ollama.
"""

import os
import urllib.request
import sys

def download_ollama():
    """Download Ollama installer to installer_resources directory."""

    # Create directory if it doesn't exist
    os.makedirs('installer_resources', exist_ok=True)

    ollama_url = "https://ollama.com/download/OllamaSetup.exe"
    output_path = os.path.join('installer_resources', 'OllamaSetup.exe')

    if os.path.exists(output_path):
        print(f"✓ Ollama installer already exists at: {output_path}")
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"  Size: {file_size:.1f} MB")

        response = input("\nDownload again? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping download.")
            return

        os.remove(output_path)

    print(f"Downloading Ollama installer...")
    print(f"From: {ollama_url}")
    print(f"To: {output_path}")
    print("\nThis may take a few minutes (~300 MB)...\n")

    try:
        def progress_hook(count, block_size, total_size):
            """Show download progress."""
            percent = int(count * block_size * 100 / total_size)
            downloaded_mb = count * block_size / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)

            # Print progress bar
            bar_length = 50
            filled_length = int(bar_length * percent / 100)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)

            sys.stdout.write(f'\r[{bar}] {percent}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)')
            sys.stdout.flush()

        urllib.request.urlretrieve(ollama_url, output_path, progress_hook)
        print("\n\n✓ Download complete!")

        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✓ Ollama installer saved: {output_path}")
        print(f"  Size: {file_size:.1f} MB")

    except Exception as e:
        print(f"\n❌ Error downloading Ollama installer: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        sys.exit(1)


def create_model_script():
    """Create the install_ollama_models.py script."""

    script_path = os.path.join('installer_resources', 'install_ollama_models.py')

    script_content = '''#!/usr/bin/env python3
"""
Script to pull Ollama models during installation.
Called by Inno Setup installer.
"""
import subprocess
import sys

def main():
    model = "deepseek-r1:1.5b"
    print(f"Pulling Ollama model: {model}")

    try:
        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(f"Successfully pulled {model}")
            return 0
        else:
            print(f"Failed to pull {model}: {result.stderr}")
            return 1
    except subprocess.TimeoutExpired:
        print("Timeout while pulling model")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

    with open(script_path, 'w') as f:
        f.write(script_content)

    print(f"✓ Created: {script_path}")


if __name__ == "__main__":
    print("=" * 60)
    print(" Ollama Installer Download Script")
    print("=" * 60)
    print()

    download_ollama()
    create_model_script()

    print("\n" + "=" * 60)
    print(" Setup Complete!")
    print("=" * 60)
    print("\nYou can now run:")
    print("  python build_installer.py")
    print("  (then compile installer.iss with Inno Setup)")
    print()
