"""
GUI window for file transcription feature.
Provides a user-friendly interface to upload and transcribe audio files.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
import threading
import os
import logging
from typing import Optional
from file_transcriber_core import FileTranscriber, get_supported_formats, format_file_duration


class FileTranscriberWindow:
    """Main window for file transcription."""

    def __init__(self, theme="darkly"):
        """Initialize the file transcriber window."""
        self.window = ttk.Window(themename=theme)
        self.window.title("Audio File Transcriber - Whisper")
        self.window.geometry("850x650")
        self.window.minsize(700, 500)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize transcriber (model loaded on demand)
        self.transcriber: Optional[FileTranscriber] = None
        self.current_file_path: Optional[str] = None
        self.is_transcribing = False

        # Setup UI
        self.setup_ui()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Setup the user interface components."""
        # Main container with padding
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.grid(row=0, column=0, sticky=(W, E, N, S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        # Configure grid weights for responsiveness
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # File selection section
        ttk.Label(main_frame, text="Audio File:", font=('Segoe UI', 11, 'bold')).grid(
            row=0, column=0, sticky=W, pady=(0, 10)
        )

        self.file_path_var = ttk.StringVar(value="No file selected")
        file_path_label = ttk.Label(
            main_frame,
            textvariable=self.file_path_var,
            bootstyle="inverse-secondary",
            padding=(10, 5)
        )
        file_path_label.grid(row=0, column=1, sticky=(W, E), padx=(10, 10), pady=(0, 10))

        self.select_file_btn = ttk.Button(
            main_frame,
            text="Browse...",
            command=self.select_file,
            bootstyle="primary"
        )
        self.select_file_btn.grid(row=0, column=2, padx=(0, 0), pady=(0, 10))

        # Model selection section
        ttk.Label(main_frame, text="Model:", font=('Segoe UI', 11, 'bold')).grid(
            row=1, column=0, sticky=W, pady=(5, 10)
        )

        self.model_var = ttk.StringVar(value="base")
        model_combo = ttk.Combobox(
            main_frame,
            textvariable=self.model_var,
            values=["tiny", "base", "small", "medium", "large"],
            state="readonly",
            width=15
        )
        model_combo.grid(row=1, column=1, sticky=W, padx=(10, 0), pady=(5, 10))
        model_combo.bind("<<ComboboxSelected>>", self.on_model_changed)

        ttk.Label(
            main_frame,
            text="(larger = more accurate but slower)",
            font=('Segoe UI', 9),
            bootstyle="secondary"
        ).grid(row=1, column=2, sticky=W, padx=(15, 0), pady=(5, 10))

        # Transcribe button
        self.transcribe_btn = ttk.Button(
            main_frame,
            text="▶ Transcribe",
            command=self.start_transcription,
            bootstyle="success",
            state=DISABLED,
            width=20
        )
        self.transcribe_btn.grid(row=2, column=0, columnspan=3, pady=(15, 10))

        # Progress section
        self.progress_var = ttk.StringVar(value="Ready to transcribe")
        progress_label = ttk.Label(
            main_frame,
            textvariable=self.progress_var,
            font=('Segoe UI', 10),
            bootstyle="info"
        )
        progress_label.grid(row=3, column=0, columnspan=3, sticky=(W, E), pady=(10, 5))

        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='determinate',
            maximum=100,
            bootstyle="success-striped"
        )
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(W, E), pady=(0, 10))

        # Transcription text area
        ttk.Label(main_frame, text="Transcription:", font=('Segoe UI', 11, 'bold')).grid(
            row=5, column=0, columnspan=3, sticky=W, pady=(15, 5)
        )

        # Frame for text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=6, column=0, columnspan=3, sticky=(W, E, N, S), pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

        self.transcription_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=WORD,
            width=80,
            height=15,
            font=('Consolas', 10)
        )
        self.transcription_text.grid(row=0, column=0, sticky=(W, E, N, S))

        # Buttons section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))

        self.save_btn = ttk.Button(
            button_frame,
            text="💾 Save Transcription",
            command=self.save_transcription,
            bootstyle="primary-outline",
            state=DISABLED,
            width=20
        )
        self.save_btn.pack(side=LEFT, padx=(0, 10))

        self.clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Clear",
            command=self.clear_transcription,
            bootstyle="secondary-outline",
            width=15
        )
        self.clear_btn.pack(side=LEFT, padx=(5, 0))

        # Status bar at bottom
        self.status_var = ttk.StringVar(value="Ready to transcribe audio files")
        status_bar = ttk.Label(
            self.window,
            textvariable=self.status_var,
            bootstyle="inverse-secondary",
            padding=(10, 5)
        )
        status_bar.grid(row=1, column=0, sticky=(W, E))

    def select_file(self):
        """Open file dialog to select audio file."""
        supported_formats = get_supported_formats()
        filetypes = [
            ("Audio Files", " ".join(f"*{ext}" for ext in supported_formats)),
            ("All Files", "*.*")
        ]

        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=filetypes
        )

        if file_path:
            self.current_file_path = file_path
            filename = os.path.basename(file_path)
            self.file_path_var.set(filename)
            self.transcribe_btn.config(state=NORMAL)
            self.status_var.set(f"File selected: {filename}")
            self.logger.info(f"Selected file: {file_path}")

    def on_model_changed(self, event=None):
        """Handle model selection change."""
        model_size = self.model_var.get()
        self.status_var.set(f"Model changed to: {model_size}")
        self.logger.info(f"Model changed to: {model_size}")

        # If transcriber exists, switch model
        if self.transcriber is not None:
            self.transcriber.switch_model(model_size)

    def start_transcription(self):
        """Start the transcription process in a background thread."""
        if self.current_file_path is None:
            messagebox.showwarning("No File", "Please select an audio file first.")
            return

        if self.is_transcribing:
            messagebox.showinfo("In Progress", "Transcription already in progress.")
            return

        # Clear previous transcription
        self.transcription_text.delete(1.0, END)

        # Disable controls
        self.is_transcribing = True
        self.transcribe_btn.config(state=DISABLED)
        self.select_file_btn.config(state=DISABLED)
        self.save_btn.config(state=DISABLED)
        self.progress_bar['value'] = 0

        # Initialize transcriber if needed
        if self.transcriber is None:
            model_size = self.model_var.get()
            self.transcriber = FileTranscriber(model_size=model_size)

        # Start transcription in background thread
        thread = threading.Thread(target=self.transcribe_thread, daemon=True)
        thread.start()

    def transcribe_thread(self):
        """Background thread for transcription."""
        try:
            # Callback for progress updates
            def progress_callback(current, total, message):
                # Calculate percentage
                if total > 0:
                    percentage = int((current / total) * 100)
                    self.window.after(0, lambda: self.update_progress(percentage, message))
                else:
                    self.window.after(0, lambda: self.update_progress(0, message))

            # Perform transcription
            transcription = self.transcriber.transcribe_file(
                self.current_file_path,
                language="en",
                beam_size=5,
                progress_callback=progress_callback
            )

            # Update UI with results
            self.window.after(0, lambda: self.transcription_complete(transcription))

        except Exception as e:
            error_msg = f"Error during transcription: {str(e)}"
            self.logger.error(error_msg)
            self.window.after(0, lambda: self.transcription_error(error_msg))

    def update_progress(self, percentage: int, message: str):
        """Update progress bar and status message."""
        self.progress_bar['value'] = percentage
        self.progress_var.set(message)
        self.window.update_idletasks()

    def transcription_complete(self, transcription: str):
        """Handle successful transcription completion."""
        # Display transcription
        self.transcription_text.delete(1.0, END)
        self.transcription_text.insert(1.0, transcription)

        # Update status
        self.progress_bar['value'] = 100
        self.progress_var.set("Transcription complete!")
        self.status_var.set(f"Transcribed {len(transcription)} characters")

        # Re-enable controls
        self.is_transcribing = False
        self.transcribe_btn.config(state=NORMAL)
        self.select_file_btn.config(state=NORMAL)
        self.save_btn.config(state=NORMAL)

        self.logger.info("Transcription completed successfully")

    def transcription_error(self, error_msg: str):
        """Handle transcription error."""
        self.progress_var.set("Transcription failed")
        self.status_var.set("Error occurred")

        # Re-enable controls
        self.is_transcribing = False
        self.transcribe_btn.config(state=NORMAL)
        self.select_file_btn.config(state=NORMAL)

        messagebox.showerror("Transcription Error", error_msg)

    def save_transcription(self):
        """Save transcription to a text file."""
        transcription = self.transcription_text.get(1.0, END).strip()

        if not transcription:
            messagebox.showwarning("No Transcription", "Nothing to save.")
            return

        # Suggest filename based on original audio file
        suggested_name = "transcription.txt"
        if self.current_file_path:
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
            suggested_name = f"{base_name}_transcription.txt"

        file_path = filedialog.asksaveasfilename(
            title="Save Transcription",
            defaultextension=".txt",
            initialfile=suggested_name,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                self.status_var.set(f"Saved to: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Transcription saved to:\n{file_path}")
                self.logger.info(f"Transcription saved to: {file_path}")
            except Exception as e:
                error_msg = f"Error saving file: {str(e)}"
                self.logger.error(error_msg)
                messagebox.showerror("Save Error", error_msg)

    def clear_transcription(self):
        """Clear the transcription text area."""
        if messagebox.askyesno("Clear", "Clear the current transcription?"):
            self.transcription_text.delete(1.0, END)
            self.progress_bar['value'] = 0
            self.progress_var.set("Ready")
            self.status_var.set("Cleared")
            self.logger.info("Transcription cleared")

    def on_closing(self):
        """Handle window close event."""
        if self.is_transcribing:
            if not messagebox.askyesno(
                "Transcription in Progress",
                "Transcription is still running. Close anyway?"
            ):
                return

        self.window.destroy()

    def run(self):
        """Start the GUI event loop."""
        self.window.mainloop()


def main():
    """Main entry point for the file transcriber window."""
    app = FileTranscriberWindow()
    app.run()


if __name__ == "__main__":
    main()
