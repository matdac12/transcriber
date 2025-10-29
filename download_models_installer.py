"""
Model downloader script for installer.
Downloads selected Whisper models to installation directory.
Called by Inno Setup installer during installation process.
"""

import os
import sys
import argparse
from faster_whisper import WhisperModel


# Model sizes and their approximate download sizes
MODEL_INFO = {
    'tiny': {'size': '~39 MB', 'description': 'Fastest, least accurate'},
    'base': {'size': '~141 MB', 'description': 'Good balance of speed and accuracy'},
    'small': {'size': '~461 MB', 'description': 'Better accuracy, slower'},
}


def print_progress(message, newline=True):
    """Print progress message (flushes immediately for installer to see)."""
    if newline:
        print(message, flush=True)
    else:
        print(message, end='', flush=True)


def download_model(model_name: str, target_dir: str) -> bool:
    """
    Download a single Whisper model.

    Args:
        model_name: Name of the model (tiny, base, small, etc.)
        target_dir: Directory to download the model to

    Returns:
        True if successful, False otherwise
    """
    try:
        print_progress(f"\n{'='*60}")
        print_progress(f"Downloading {model_name} model...")
        print_progress(f"Size: {MODEL_INFO.get(model_name, {}).get('size', 'Unknown')}")
        print_progress(f"Target: {target_dir}")
        print_progress(f"{'='*60}")

        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Download the model
        # faster_whisper will download to the specified directory
        print_progress(f"\nInitializing download for '{model_name}'...")

        model = WhisperModel(
            model_name,
            device="cpu",  # Use CPU during installation
            compute_type="int8",
            download_root=target_dir
        )

        print_progress(f"✓ {model_name} model downloaded successfully!")

        # Verify the model directory exists
        model_dir = os.path.join(target_dir, f"faster-whisper-{model_name}")
        if os.path.exists(model_dir):
            print_progress(f"✓ Model files verified at: {model_dir}")
            return True
        else:
            print_progress(f"⚠ Model directory not found at expected location: {model_dir}")
            print_progress(f"⚠ Model may have been downloaded to cache instead")
            # Still return True as model was loaded successfully
            return True

    except Exception as e:
        print_progress(f"✗ Error downloading {model_name} model: {e}")
        print_progress(f"✗ Model download failed - you can download it later from the app")
        return False


def main():
    """Main installer script."""
    parser = argparse.ArgumentParser(
        description='Download Whisper models for WhisperDictation installation'
    )
    parser.add_argument(
        '--models',
        type=str,
        required=True,
        help='Comma-separated list of models to download (e.g., "tiny,base")'
    )
    parser.add_argument(
        '--target-dir',
        type=str,
        required=True,
        help='Target directory to download models to'
    )

    args = parser.parse_args()

    # Parse model list
    models_to_download = [m.strip() for m in args.models.split(',') if m.strip()]

    if not models_to_download:
        print_progress("✗ Error: No models specified")
        sys.exit(1)

    print_progress("\n" + "="*60)
    print_progress("WhisperDictation - Model Downloader")
    print_progress("="*60)
    print_progress(f"\nModels to download: {', '.join(models_to_download)}")
    print_progress(f"Target directory: {args.target_dir}")
    print_progress("")

    # Track success/failure
    results = {}

    # Download each model
    for model_name in models_to_download:
        if model_name not in MODEL_INFO:
            print_progress(f"⚠ Warning: Unknown model '{model_name}', skipping...")
            results[model_name] = False
            continue

        success = download_model(model_name, args.target_dir)
        results[model_name] = success

    # Print summary
    print_progress("\n" + "="*60)
    print_progress("Download Summary")
    print_progress("="*60)

    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    for model_name, success in results.items():
        status = "✓" if success else "✗"
        print_progress(f"{status} {model_name}: {'Success' if success else 'Failed'}")

    print_progress("")
    print_progress(f"Total: {success_count}/{total_count} models downloaded successfully")

    # Exit with appropriate code
    if success_count == 0:
        print_progress("\n✗ All downloads failed!")
        sys.exit(1)
    elif success_count < total_count:
        print_progress("\n⚠ Some downloads failed - you can download missing models later")
        sys.exit(0)  # Don't fail installation for partial success
    else:
        print_progress("\n✓ All models downloaded successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
