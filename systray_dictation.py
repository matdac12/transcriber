import whisper
import sounddevice as sd
import numpy as np
import pyperclip
import keyboard
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from datetime import datetime
import os
import tkinter as tk
from tkinter import messagebox

class WhisperDictation:
    def __init__(self, model_size="base"):
        """Initialize the dictation system with a Whisper model."""
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        print("Model loaded successfully!")

        self.sample_rate = 16000
        self.is_recording = False
        self.audio_data = []
        self.hotkey = "alt gr"  # Alt Gr (Right Alt)
        self.debug = False
        self.listening = False
        self.record_thread = None
        self.icon = None

        # Log file setup
        self.log_file = os.path.join(os.path.dirname(__file__), "dictation_log.txt")

    def show_notification(self, title, message):
        """Show a popup notification window in bottom right corner."""
        def show_popup():
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            # Create a custom popup window
            popup = tk.Toplevel(root)
            popup.title(title)
            width = 350
            height = 100
            popup.geometry(f"{width}x{height}")
            popup.attributes('-topmost', True)  # Always on top

            # Get screen dimensions
            screen_width = popup.winfo_screenwidth()
            screen_height = popup.winfo_screenheight()

            # Position in bottom right corner with small margin (20px from edges)
            x = screen_width - width - 20
            y = screen_height - height - 60

            popup.geometry(f"{width}x{height}+{x}+{y}")

            # Add message label
            label = tk.Label(popup, text=message, wraplength=330, justify="center", font=("Arial", 10))
            label.pack(expand=True, fill="both", padx=10, pady=10)

            # Auto-close after 3 seconds (3000 ms)
            popup.after(3000, popup.destroy)
            popup.after(3000, root.destroy)

            root.mainloop()

        # Run in a separate thread so it doesn't block
        threading.Thread(target=show_popup, daemon=True).start()

    def log_transcription(self, text):
        """Save transcription to log file."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            duration = len(self.audio_data) * len(self.audio_data[0]) / self.sample_rate if self.audio_data else 0
            log_entry = f"[{timestamp}] ({duration:.2f}s) {text}\n"

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

            if self.debug:
                print(f"[DEBUG] Logged: {log_entry.strip()}")
        except Exception as e:
            print(f"Error writing to log: {e}")

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
                self.audio_data = []
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

        # Combine audio chunks
        audio_array = np.concatenate(self.audio_data, axis=0).flatten()
        if self.debug:
            print(f"[DEBUG] Audio array shape: {audio_array.shape}, min: {audio_array.min():.4f}, max: {audio_array.max():.4f}")

        try:
            # Transcribe with Whisper
            if self.debug:
                print(f"[DEBUG] Starting transcription with Whisper...")
                print(f"[DEBUG] Audio duration: {len(audio_array) / self.sample_rate:.2f} seconds")

            result = self.model.transcribe(audio_array, fp16=False)
            text = result["text"].strip()

            if self.debug:
                print(f"[DEBUG] Transcription complete. Result: '{text}'")

            if text:
                print(f"✓ Transcribed: {text}")
                pyperclip.copy(text)
                self.log_transcription(text)
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
