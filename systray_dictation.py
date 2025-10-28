from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import pyperclip
import keyboard
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from datetime import datetime
import os
import sys
import warnings
from collections import deque

# Suppress pystray Windows warnings
warnings.filterwarnings("ignore", category=UserWarning)
if sys.platform == "win32":
    import ctypes

    # Suppress ctypes errors from pystray
    ctypes.pythonapi.PyErr_WriteUnraisable.argtypes = [ctypes.py_object]

# Toast notifications removed - using icon color feedback instead


class WhisperDictation:
    def __init__(self, model_size="base"):
        """Initialize the dictation system with a Whisper model."""
        # Initialize basic attributes first
        self.sample_rate = 16000
        self.is_recording = False
        self.audio_data = deque()  # Using deque for better performance
        self.hotkey = "alt gr"  # Alt Gr (Right Alt)
        self.debug = False
        self.vad_threshold = 0.01  # Voice activity detection threshold (configurable)
        self.listening = False
        self.record_thread = None
        self.icon = None
        self.model_size = model_size  # Track current model size
        self.device = "auto"
        self.compute_type = "int8"  # int8 for CPU compatibility

        self.load_model(model_size)

        # Log file setup - use AppData for user-writable location
        log_dir = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
        app_dir = os.path.join(log_dir, "WhisperDictation")
        os.makedirs(app_dir, exist_ok=True)
        self.log_file = os.path.join(app_dir, "dictation_log.txt")

    def load_model(self, model_size):
        """Load or reload the Whisper model."""
        print(f"Loading faster-whisper {model_size} model...")
        print("CTranslate2 will auto-detect best device (GPU if available, else CPU)")

        try:
            self.model = WhisperModel(
                model_size, device=self.device, compute_type=self.compute_type
            )
            self.model_size = model_size
            if self.debug:
                print(
                    f"[DEBUG] faster-whisper loaded (device={self.device}, compute_type={self.compute_type})"
                )
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def switch_model(self, model_size):
        """Switch to a different model size."""
        print(f"[SWITCH] Attempting to switch from {self.model_size} to {model_size}")

        if self.is_recording:
            print("⚠️  Cannot switch model while recording. Please stop recording first.")
            return False

        if model_size == self.model_size:
            print(f"ℹ️  Already using {model_size} model.")
            return True

        try:
            self.load_model(model_size)
            print(f"✓ Switched to {model_size} model (self.model_size = {self.model_size})")
            return True
        except Exception as e:
            print(f"❌ Failed to switch model: {e}")
            import traceback
            traceback.print_exc()
            return False

    def log_transcription(self, text, duration):
        """Save transcription to log file."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] ({duration:.2f}s) {text}\n"

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

            if self.debug:
                print(f"[DEBUG] Logged: {log_entry.strip()}")
        except Exception as e:
            print(f"Error writing to log: {e}")

    def detect_voice_activity(self, audio_array, threshold=None):
        """Simple Voice Activity Detection to remove silence."""
        if threshold is None:
            threshold = getattr(self, "vad_threshold", 0.01)

        # Calculate energy in short frames
        frame_length = int(self.sample_rate * 0.02)  # 20ms frames

        # Handle case where audio is shorter than one frame
        if len(audio_array) < frame_length:
            # Treat entire buffer as one frame
            energy = np.array([np.sqrt(np.mean(audio_array**2))])
        else:
            # Process full frames, including the last complete frame
            energy = np.array(
                [
                    np.sqrt(np.mean(audio_array[i : i + frame_length] ** 2))
                    for i in range(0, len(audio_array) - frame_length + 1, frame_length)
                ]
            )

        # Find frames with energy above threshold
        active_frames = energy > threshold

        if not np.any(active_frames):
            return audio_array  # No voice detected, return original

        # Find start and end of voice activity
        active_indices = np.where(active_frames)[0]
        start_frame = max(0, active_indices[0] - 2)  # Include 2 frames before
        end_frame = min(
            len(active_frames), active_indices[-1] + 3
        )  # Include 2 frames after (+3 for exclusive slice end)

        # Convert frame indices to sample indices
        start_sample = start_frame * frame_length
        end_sample = min(len(audio_array), end_frame * frame_length)

        trimmed = audio_array[start_sample:end_sample]

        if self.debug:
            original_duration = len(audio_array) / self.sample_rate
            trimmed_duration = len(trimmed) / self.sample_rate
            print(f"[DEBUG] VAD: {original_duration:.2f}s -> {trimmed_duration:.2f}s")

        return trimmed

    def update_icon(self, state="idle"):
        """Update the systray icon color based on state.

        Args:
            state: 'idle' (blue), 'recording' (red), or 'done' (green)
        """
        if not self.icon:
            return

        color_map = {
            "idle": "blue",  # Ready to record
            "recording": "red",  # Currently recording
            "done": "green",  # Transcription complete
        }

        color = color_map.get(state, "blue")
        image = self.create_icon(color=color)
        self.icon.icon = image

    def create_icon(self, color="blue"):
        """Create a colored icon for the system tray."""
        image = Image.new("RGB", (64, 64), color=color)
        draw = ImageDraw.Draw(image)
        # Draw a microphone-like symbol
        draw.rectangle([16, 8, 48, 40], outline="white", width=2)
        draw.rectangle([20, 40, 44, 56], outline="white", width=2)
        return image

    def start_listening(self):
        """Start the recording listener in a background thread."""
        if self.listening:
            return

        self.listening = True
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.record_thread.start()
        print("🎤 Listening started")

    def stop_listening(self):
        """Stop the recording listener."""
        self.listening = False
        if self.record_thread:
            self.record_thread.join(timeout=2)
        print("⏹️  Listening stopped")
        self.update_icon(state="idle")

    def _record_loop(self):
        """Main recording loop running in background thread."""
        print(f"Listening for hotkey: {self.hotkey}")

        def toggle_recording():
            if self.debug:
                print(f"[DEBUG] ⚡ HOTKEY PRESSED! is_recording={self.is_recording}")
            if not self.is_recording:
                # Start recording
                self.audio_data.clear()  # Clear deque before setting flag to avoid race
                self.is_recording = True
                print("🎤 Recording...")
                self.update_icon(state="recording")
                if self.debug:
                    print(f"[DEBUG] Started capturing audio")
            else:
                # Stop recording
                self.is_recording = False
                self.update_icon(state="idle")  # Back to blue while processing
                print("⏹️  Processing...")
                if self.debug:
                    print(f"[DEBUG] Recorded {len(self.audio_data)} audio chunks")
                self.transcribe_and_paste()

        keyboard.on_press_key(self.hotkey, lambda _: toggle_recording())

        # Audio recording loop
        frames_counted = [0]

        def audio_callback(indata, frames, time, status):
            if status and self.debug:
                print(f"[DEBUG] Audio status: {status}")
            frames_counted[0] += 1
            if self.is_recording:
                self.audio_data.append(indata.copy())

        try:
            with sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                dtype=np.float32,
            ):
                # Keep the stream running while listening is active
                while self.listening:
                    threading.Event().wait(0.1)
        except Exception as e:
            print(f"Error in audio stream: {e}")
        finally:
            try:
                keyboard.remove_hotkey(self.hotkey)
            except:
                pass
            print("Recording loop stopped")

    def transcribe_and_paste(self):
        """Transcribe recorded audio and paste to clipboard."""
        if not self.audio_data:
            print("❌ No audio recorded.")
            return

        if self.debug:
            print(f"[DEBUG] Combining {len(self.audio_data)} audio chunks...")

        # Combine audio chunks from deque
        audio_array = np.concatenate(list(self.audio_data), axis=0).flatten()
        if self.debug:
            print(
                f"[DEBUG] Audio array shape: {audio_array.shape}, min: {audio_array.min():.4f}, max: {audio_array.max():.4f}"
            )

        # Apply Voice Activity Detection to remove silence
        audio_array = self.detect_voice_activity(
            audio_array, threshold=self.vad_threshold
        )

        if len(audio_array) < self.sample_rate * 0.2:  # Less than 0.2 seconds
            print("⚠️  Audio too short after VAD.")
            return

        try:
            # Transcribe with faster-whisper
            if self.debug:
                print("[DEBUG] Starting transcription with faster-whisper...")
                print(
                    f"[DEBUG] Audio duration: {len(audio_array) / self.sample_rate:.2f} seconds"
                )

            # faster-whisper API returns segments and info
            segments, info = self.model.transcribe(
                audio_array,
                beam_size=2,  # Favor latency over quality for real-time dictation
                language="en",  # Set language if known for faster processing
                vad_filter=False,  # We already applied VAD
            )

            # Collect all text from segments
            text = " ".join([segment.text for segment in segments]).strip()
            duration = len(audio_array) / self.sample_rate

            if self.debug:
                print(f"[DEBUG] Transcription complete. Result: '{text}'")
                print(
                    f"[DEBUG] Detected language: {info.language} (probability: {info.language_probability:.2f})"
                )

            if text:
                print(f"✓ Transcribed: {text}")
                pyperclip.copy(text)
                self.log_transcription(text, duration)

                # Turn icon GREEN to show completion
                self.update_icon(state="done")
                print("📋 Copied to clipboard!")

                # Auto-paste the text at cursor position
                import time

                time.sleep(0.02)  # 20ms is sufficient for clipboard sync
                keyboard.press_and_release("ctrl+v")
                print("✨ Auto-pasted!")

                # Return to blue (idle) after 2 seconds
                threading.Timer(2.0, lambda: self.update_icon(state="idle")).start()
            else:
                print("⚠️  No speech detected in audio.")
                self.update_icon(state="idle")

        except Exception as e:
            print(f"❌ Error during transcription: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()


def main():
    print("=== Whisper Dictation Systray ===\n")

    # Suppress pystray WNDPROC error messages (they're harmless cosmetic issues)
    if sys.platform == "win32":
        import io

        # Create a custom stderr that filters out specific pystray errors
        class FilteredStderr:
            def __init__(self, original):
                self.original = original

            def write(self, text):
                # Only suppress specific pystray WNDPROC errors
                if "WNDPROC" not in text and "WPARAM" not in text:
                    self.original.write(text)

            def flush(self):
                self.original.flush()

        sys.stderr = FilteredStderr(sys.stderr)

    dictation = WhisperDictation(model_size="base")

    def on_start(icon, item):
        dictation.start_listening()
        print("✓ Dictation started")

    def on_stop(icon, item):
        dictation.stop_listening()
        print("✓ Dictation stopped")

    def on_open_log(icon, item):
        """Open the log file with default text editor."""
        if os.path.exists(dictation.log_file):
            os.startfile(dictation.log_file)
        else:
            print("⚠️  No transcriptions yet")

    def on_clear_log(icon, item):
        """Clear the log file."""
        try:
            if os.path.exists(dictation.log_file):
                os.remove(dictation.log_file)
                print("✓ Log cleared")
            else:
                print("⚠️  No log file to clear")
        except Exception as e:
            print(f"❌ Could not clear log: {e}")

    def on_exit(icon, item):
        dictation.stop_listening()
        icon.stop()
        print("Exiting...")

    def on_switch_tiny(icon, item):
        """Switch to Tiny model."""
        print(f"[MENU] Switching to tiny model (current: {dictation.model_size})")
        result = dictation.switch_model("tiny")
        print(f"[MENU] Switch result: {result}, new model: {dictation.model_size}")
        # Always update the menu to refresh checkmarks
        icon.menu = create_menu()
        print(f"[MENU] Menu updated")

    def on_switch_base(icon, item):
        """Switch to Base model."""
        print(f"[MENU] Switching to base model (current: {dictation.model_size})")
        result = dictation.switch_model("base")
        print(f"[MENU] Switch result: {result}, new model: {dictation.model_size}")
        # Always update the menu to refresh checkmarks
        icon.menu = create_menu()
        print(f"[MENU] Menu updated")

    def model_is_tiny(item):
        """Check if current model is tiny (for menu checkmark)."""
        return dictation.model_size == "tiny"

    def model_is_base(item):
        """Check if current model is base (for menu checkmark)."""
        return dictation.model_size == "base"

    def create_menu():
        """Create the menu dynamically to allow updates."""
        # Show which model is active in the label
        tiny_label = "✓ Tiny Model" if dictation.model_size == "tiny" else "  Tiny Model"
        base_label = "✓ Base Model" if dictation.model_size == "base" else "  Base Model"

        return Menu(
            MenuItem("Start Listening", on_start),
            MenuItem("Stop Listening", on_stop),
            Menu.SEPARATOR,
            MenuItem(tiny_label, on_switch_tiny),
            MenuItem(base_label, on_switch_base),
            Menu.SEPARATOR,
            MenuItem("View Log", on_open_log),
            MenuItem("Clear Log", on_clear_log),
            Menu.SEPARATOR,
            MenuItem("Exit", on_exit),
        )

    # Create and run the icon
    icon = Icon("Whisper Dictation", dictation.create_icon(color="blue"), menu=create_menu())
    dictation.icon = icon

    print("\n✓ Systray app started!")
    print("Look for the blue icon in your system tray.")
    print("Right-click it to start/stop listening, view logs, or exit.\n")

    icon.run()


if __name__ == "__main__":
    main()
