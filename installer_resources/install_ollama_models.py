"""
Script to download Ollama models during installation.
This script is called by the Inno Setup installer after Ollama is installed.
"""

import subprocess
import sys
import time
import os


def check_ollama_running():
    """Check if Ollama service is running."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def start_ollama_service():
    """Start Ollama service in background."""
    try:
        print("Starting Ollama service...")
        # Start ollama serve in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        # Wait for service to start (max 30 seconds)
        for i in range(30):
            time.sleep(1)
            if check_ollama_running():
                print("✓ Ollama service started")
                return True
            print(f"  Waiting for Ollama to start... ({i+1}/30)")

        print("✗ Ollama service did not start in time")
        return False
    except Exception as e:
        print(f"✗ Error starting Ollama: {e}")
        return False


def pull_model(model_name):
    """
    Pull an Ollama model (only if not already installed).

    Args:
        model_name: Name of the model to pull (e.g., "deepseek-r1:1.5b")

    Returns:
        True if successful or already installed, False otherwise
    """
    try:
        # First check if model already exists
        if verify_model_installed(model_name):
            print(f"✓ {model_name} model already installed, skipping download")
            return True

        print(f"\nDownloading {model_name} model...")
        print("This may take a few minutes depending on your internet speed...")

        # Run ollama pull with real-time output
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Print output in real-time
        for line in process.stdout:
            print(line.rstrip())

        process.wait()

        if process.returncode == 0:
            print(f"✓ {model_name} model downloaded successfully!")
            return True
        else:
            print(f"✗ Failed to download {model_name} model")
            return False

    except Exception as e:
        print(f"✗ Error downloading model: {e}")
        return False


def verify_model_installed(model_name):
    """Verify that a model is installed."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Check if model name appears in output
            return model_name.split(':')[0] in result.stdout
        return False
    except Exception:
        return False


def main():
    """Main installation process."""
    print("\n" + "="*60)
    print(" Ollama Model Installer")
    print("="*60 + "\n")

    # Check if Ollama is installed
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("✗ Ollama is not installed or not in PATH")
            print("Please ensure Ollama installation completed successfully")
            sys.exit(1)
        print(f"✓ Ollama found: {result.stdout.strip()}")
    except FileNotFoundError:
        print("✗ Ollama is not installed or not in PATH")
        print("Please ensure Ollama installation completed successfully")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error checking Ollama: {e}")
        sys.exit(1)

    # Check if Ollama service is running, start if not
    if not check_ollama_running():
        print("Ollama service not running, attempting to start...")
        if not start_ollama_service():
            print("\n✗ Could not start Ollama service")
            print("You may need to start it manually: ollama serve")
            sys.exit(1)
    else:
        print("✓ Ollama service is running")

    # Models to install
    models_to_install = [
        "deepseek-r1:1.5b"  # Default model for summarization
    ]

    print(f"\nModels to install: {', '.join(models_to_install)}")
    print("Total download size: ~300-400 MB")

    # Install each model
    success_count = 0
    for model in models_to_install:
        if pull_model(model):
            success_count += 1

    # Summary
    print("\n" + "="*60)
    print(" Installation Complete")
    print("="*60)
    print(f"\n✓ Successfully installed {success_count}/{len(models_to_install)} model(s)")

    if success_count == len(models_to_install):
        print("\nAll models are ready!")
        print("WhisperDictation File Transcriber can now generate summaries.")
        return 0
    else:
        print("\n⚠ Some models failed to install")
        print("The app will work, but AI summaries won't be available.")
        print("You can install models later by running:")
        for model in models_to_install:
            if not verify_model_installed(model):
                print(f"  ollama pull {model}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n✗ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
