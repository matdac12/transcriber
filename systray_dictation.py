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
from collections import deque
try:
    from win10toast import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

class WhisperDictation:
    def __init__(self, model_size="base"):
        """Initialize the dictation system with a Whisper model."""
        print(f"Loading faster-whisper {model_size} model...")
        print("CTranslate2 will auto-detect best device (GPU if available, else CPU)")

        try:
            # Let CTranslate2/faster-whisper auto-detect the best device and compute type
            # It will use CUDA GPU if available, otherwise fall back to CPU
            self.model = WhisperModel(model_size)
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

        self.sample_rate = 16000
        self.is_recording = False
        self.audio_data = deque()  # Using deque for better performance
        self.hotkey = "alt gr"  # Alt Gr (Right Alt)
        self.debug = False
        self.listening = False
        self.record_thread = None
        self.icon = None

        # Initialize toast notifier for Windows notifications
        if TOAST_AVAILABLE:
            self.toaster = ToastNotifier()
        else:
            self.toaster = None

        # Log file setup
        self.log_file = os.path.join(os.path.dirname(__file__), "dictation_log.txt")

    def show_notification(self, title, message):
        """Show notification using Windows toast or pystray fallback."""
        if self.toaster and TOAST_AVAILABLE:
            try:
                self.toaster.show_toast(title, message, duration=3, threaded=True)
                return
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] Toast failed: {e}")
        # Fallback: pystray notification or console
        try:
            if self.icon:
                self.icon.notify(message, title)
            else:
                print(f"{title}: {message}")
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Fallback notify failed: {e}")

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

    def detect_voice_activity(self, audio_array, threshold=0.01):
        """Simple Voice Activity Detection to remove silence."""
        # Calculate energy in short frames
        frame_length = int(self.sample_rate * 0.02)  # 20ms frames

        # Handle case where audio is shorter than one frame
        if len(audio_array) < frame_length:
            # Treat entire buffer as one frame
            energy = np.array([np.sqrt(np.mean(audio_array**2))])
        else:
            # Process full frames, including the last complete frame
            energy = np.array([
                np.sqrt(np.mean(audio_array[i:i+frame_length]**2))
                for i in range(0, len(audio_array) - frame_length + 1, frame_length)
            ])

        # Find frames with energy above threshold
        active_frames = energy > threshold

        if not np.any(active_frames):
            return audio_array  # No voice detected, return original

        # Find start and end of voice activity
        active_indices = np.where(active_frames)[0]
        start_frame = max(0, active_indices[0] - 2)  # Include 2 frames before
        end_frame = min(len(active_frames), active_indices[-1] + 3)  # Include 2 frames after (+3 for exclusive slice end)

        # Convert frame indices to sample indices
        start_sample = start_frame * frame_length
        end_sample = min(len(audio_array), end_frame * frame_length)

        trimmed = audio_array[start_sample:end_sample]

        if self.debug:
            original_duration = len(audio_array) / self.sample_rate
            trimmed_duration = len(trimmed) / self.sample_rate
            print(f"[DEBUG] VAD: {original_duration:.2f}s -> {trimmed_duration:.2f}s")

        return trimmed

    def update_icon(self, recording=False):
        """Update the systray icon color based on recording state."""
        if not self.icon:
            return

        if recording:
            # Red icon for recording
            image = self.create_icon(color='red')
        else:
            # Blue icon for listening
            image = self.create_icon(color='blue')

        self.icon.icon = image

    def create_icon(self, color='blue'):
        """Create a colored icon for the system tray."""
        image = Image.new('RGB', (64, 64), color=color)
        draw = ImageDraw.Draw(image)
        # Draw a microphone-like symbol
        draw.rectangle([16, 8, 48, 40], outline='white', width=2)
        draw.rectangle([20, 40, 44, 56], outline='white', width=2)
        return image

    def start_listening(self):
        """Start the recording listener in a background thread."""
        if self.listening:
            return

        self.listening = True
        self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.record_thread.start()
        print("🎤 Listening started")
        self.show_notification("Whisper Dictation", "🎤 Listening activated!")

    def stop_listening(self):
        """Stop the recording listener."""
        self.listening = False
        if self.record_thread:
            self.record_thread.join(timeout=2)
        print("⏹️  Listening stopped")
        self.update_icon(recording=False)
        self.show_notification("Whisper Dictation", "⏹️ Listening deactivated")

    def _record_loop(self):
        """Main recording loop running in background thread."""
        print(f"Listening for hotkey: {self.hotkey}")

        def toggle_recording():
            if self.debug:
                print(f"[DEBUG] ⚡ HOTKEY PRESSED! is_recording={self.is_recording}")
            if not self.is_recording:
                # Start recording
                self.is_recording = True
                self.audio_data.clear()  # Clear deque efficiently
                print("🎤 Recording...")
                self.update_icon(recording=True)
                self.show_notification("Recording", "🎤 Recording started...")
                if self.debug:
                    print(f"[DEBUG] Started capturing audio")
            else:
                # Stop recording
                self.is_recording = False
                self.update_icon(recording=False)
                print("⏹️  Processing...")
                self.show_notification("Processing", "⏹️ Processing your audio...")
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
            with sd.InputStream(callback=audio_callback,
                               channels=1,
                               samplerate=self.sample_rate,
                               dtype=np.float32):
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
            self.show_notification("Error", "❌ No audio was recorded")
            return

        if self.debug:
            print(f"[DEBUG] Combining {len(self.audio_data)} audio chunks...")

        # Combine audio chunks from deque
        audio_array = np.concatenate(list(self.audio_data), axis=0).flatten()
        if self.debug:
            print(f"[DEBUG] Audio array shape: {audio_array.shape}, min: {audio_array.min():.4f}, max: {audio_array.max():.4f}")

        # Apply Voice Activity Detection to remove silence
        audio_array = self.detect_voice_activity(audio_array)

        if len(audio_array) < self.sample_rate * 0.1:  # Less than 0.1 seconds
            print("⚠️  Audio too short after VAD.")
            self.show_notification("No Speech", "⚠️ No speech was detected")
            return

        try:
            # Transcribe with faster-whisper
            if self.debug:
                print("[DEBUG] Starting transcription with faster-whisper...")
                print(f"[DEBUG] Audio duration: {len(audio_array) / self.sample_rate:.2f} seconds")

            # faster-whisper API returns segments and info
            segments, info = self.model.transcribe(
                audio_array,
                beam_size=5,  # Lower beam size for faster processing
                language="en",  # Set language if known for faster processing
                vad_filter=False  # We already applied VAD
            )

            # Collect all text from segments
            text = " ".join([segment.text for segment in segments]).strip()
            duration = len(audio_array) / self.sample_rate

            if self.debug:
                print(f"[DEBUG] Transcription complete. Result: '{text}'")
                print(f"[DEBUG] Detected language: {info.language} (probability: {info.language_probability:.2f})")

            if text:
                print(f"✓ Transcribed: {text}")
                pyperclip.copy(text)
                self.log_transcription(text, duration)
                self.show_notification("Transcribed", text)
                print("📋 Copied to clipboard!")
            else:
                print("⚠️  No speech detected in audio.")
                self.show_notification("No Speech", "⚠️ No speech was detected")

        except Exception as e:
            print(f"❌ Error during transcription: {e}")
            self.show_notification("Error", f"❌ Transcription error: {str(e)[:50]}")
            if self.debug:
                import traceback
                traceback.print_exc()


def main():
    print("=== Whisper Dictation Systray ===\n")

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
            dictation.show_notification("No Log", "No transcriptions yet")

    def on_clear_log(icon, item):
        """Clear the log file."""
        try:
            if os.path.exists(dictation.log_file):
                os.remove(dictation.log_file)
                dictation.show_notification("Log Cleared", "✓ Log file cleared")
                print("✓ Log cleared")
            else:
                dictation.show_notification("No Log", "No log file to clear")
        except Exception as e:
            dictation.show_notification("Error", f"Could not clear log: {str(e)[:30]}")

    def on_exit(icon, item):
        dictation.stop_listening()
        icon.stop()
        print("Exiting...")

    # Create the menu
    menu = Menu(
        MenuItem("Start Listening", on_start),
        MenuItem("Stop Listening", on_stop),
        Menu.SEPARATOR,
        MenuItem("View Log", on_open_log),
        MenuItem("Clear Log", on_clear_log),
        Menu.SEPARATOR,
        MenuItem("Exit", on_exit),
    )

    # Create and run the icon
    icon = Icon("Whisper Dictation", dictation.create_icon(color='blue'), menu=menu)
    dictation.icon = icon

    print("\n✓ Systray app started!")
    print("Look for the blue icon in your system tray.")
    print("Right-click it to start/stop listening, view logs, or exit.\n")

    icon.run()


if __name__ == "__main__":
    main()
