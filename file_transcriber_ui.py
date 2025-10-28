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
from ollama_helper import OllamaHelper, format_combined_output


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
        self.current_summary: Optional[str] = None

        # Initialize Ollama helper
        self.ollama = OllamaHelper()
        self.ollama_available = False
        self.ollama_status_message = ""

        # Store style for theme switching
        self.style = ttk.Style()

        # Setup UI
        self.setup_ui()

        # Check Ollama availability after UI is setup
        self.check_ollama_availability()

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
        main_frame.rowconfigure(10, weight=1)  # Transcription text area row gets extra space

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

        # Theme selection section
        ttk.Label(main_frame, text="Theme:", font=('Segoe UI', 11, 'bold')).grid(
            row=2, column=0, sticky=W, pady=(5, 10)
        )

        # Get available themes
        available_themes = sorted(self.style.theme_names())
        current_theme = self.style.theme_use()

        self.theme_var = ttk.StringVar(value=current_theme)
        theme_combo = ttk.Combobox(
            main_frame,
            textvariable=self.theme_var,
            values=available_themes,
            state="readonly",
            width=15
        )
        theme_combo.grid(row=2, column=1, sticky=W, padx=(10, 0), pady=(5, 10))
        theme_combo.bind("<<ComboboxSelected>>", self.on_theme_changed)

        ttk.Label(
            main_frame,
            text="(change appearance instantly)",
            font=('Segoe UI', 9),
            bootstyle="secondary"
        ).grid(row=2, column=2, sticky=W, padx=(15, 0), pady=(5, 10))

        # Ollama model selection section
        ttk.Label(main_frame, text="Ollama Model:", font=('Segoe UI', 11, 'bold')).grid(
            row=3, column=0, sticky=W, pady=(5, 10)
        )

        ollama_models = ["llama3.2:3b", "llama3.1:8b", "deepseek-r1:1.5b"]
        self.ollama_model_var = ttk.StringVar(value=self.ollama.model)
        ollama_model_combo = ttk.Combobox(
            main_frame,
            textvariable=self.ollama_model_var,
            values=ollama_models,
            state="readonly",
            width=15
        )
        ollama_model_combo.grid(row=3, column=1, sticky=W, padx=(10, 0), pady=(5, 10))
        ollama_model_combo.bind("<<ComboboxSelected>>", self.on_ollama_model_changed)

        ttk.Label(
            main_frame,
            text="(for summary generation)",
            font=('Segoe UI', 9),
            bootstyle="secondary"
        ).grid(row=3, column=2, sticky=W, padx=(15, 0), pady=(5, 10))

        # Transcribe button
        self.transcribe_btn = ttk.Button(
            main_frame,
            text="▶ Transcribe",
            command=self.start_transcription,
            bootstyle="success",
            state=DISABLED,
            width=20
        )
        self.transcribe_btn.grid(row=4, column=0, columnspan=3, pady=(15, 10))

        # Progress section
        self.progress_var = ttk.StringVar(value="Ready to transcribe")
        progress_label = ttk.Label(
            main_frame,
            textvariable=self.progress_var,
            font=('Segoe UI', 10),
            bootstyle="info"
        )
        progress_label.grid(row=5, column=0, columnspan=3, sticky=(W, E), pady=(10, 5))

        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='determinate',
            maximum=100,
            bootstyle="success-striped"
        )
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(W, E), pady=(0, 15))

        # Summary section
        summary_header_frame = ttk.Frame(main_frame)
        summary_header_frame.grid(row=7, column=0, columnspan=3, sticky=(W, E), pady=(10, 5))

        ttk.Label(summary_header_frame, text="Summary:", font=('Segoe UI', 11, 'bold')).pack(side=LEFT)

        self.generate_summary_btn = ttk.Button(
            summary_header_frame,
            text="🤖 Generate Summary",
            command=self.generate_summary,
            bootstyle="info-outline",
            state=DISABLED,
            width=20
        )
        self.generate_summary_btn.pack(side=LEFT, padx=(15, 0))

        # Ollama status label
        self.ollama_status_label = ttk.Label(
            summary_header_frame,
            text="",
            font=('Segoe UI', 9),
            bootstyle="secondary"
        )
        self.ollama_status_label.pack(side=LEFT, padx=(10, 0))

        # Frame for summary text area
        summary_frame = ttk.Frame(main_frame)
        summary_frame.grid(row=8, column=0, columnspan=3, sticky=(W, E), pady=(5, 10))
        summary_frame.columnconfigure(0, weight=1)

        # Placeholder label (shown when no summary yet)
        self.summary_placeholder = ttk.Label(
            summary_frame,
            text="Summary will appear here after generation...",
            font=('Segoe UI', 10, 'italic'),
            bootstyle="secondary"
        )
        self.summary_placeholder.grid(row=0, column=0, sticky=(W, E), pady=20)

        self.summary_text = scrolledtext.ScrolledText(
            summary_frame,
            wrap=WORD,
            width=80,
            height=6,
            font=('Consolas', 10)
        )
        self.summary_text.grid(row=0, column=0, sticky=(W, E))
        self.summary_text.grid_remove()  # Hide initially

        # Transcription text area
        ttk.Label(main_frame, text="Transcription:", font=('Segoe UI', 11, 'bold')).grid(
            row=9, column=0, columnspan=3, sticky=W, pady=(10, 5)
        )

        # Frame for text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=10, column=0, columnspan=3, sticky=(W, E, N, S), pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(10, weight=1)

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
        button_frame.grid(row=11, column=0, columnspan=3, pady=(10, 0))

        self.save_summary_btn = ttk.Button(
            button_frame,
            text="💾 Save Summary",
            command=self.save_summary_only,
            bootstyle="info-outline",
            state=DISABLED,
            width=18
        )
        self.save_summary_btn.pack(side=LEFT, padx=(0, 8))

        self.save_transcription_btn = ttk.Button(
            button_frame,
            text="💾 Save Transcription",
            command=self.save_transcription_only,
            bootstyle="primary-outline",
            state=DISABLED,
            width=20
        )
        self.save_transcription_btn.pack(side=LEFT, padx=(0, 8))

        self.save_both_btn = ttk.Button(
            button_frame,
            text="💾 Save Both",
            command=self.save_both,
            bootstyle="success-outline",
            state=DISABLED,
            width=18
        )
        self.save_both_btn.pack(side=LEFT, padx=(0, 10))

        self.clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Clear All",
            command=self.clear_all,
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

    def on_theme_changed(self, event=None):
        """Handle theme selection change."""
        new_theme = self.theme_var.get()
        self.style.theme_use(new_theme)
        self.status_var.set(f"Theme changed to: {new_theme}")
        self.logger.info(f"Theme changed to: {new_theme}")

    def on_ollama_model_changed(self, event=None):
        """Handle Ollama model selection change."""
        new_model = self.ollama_model_var.get()
        self.ollama.model = new_model
        self.status_var.set(f"Ollama model changed to: {new_model}")
        self.logger.info(f"Ollama model changed to: {new_model}")

        # Re-check availability with new model
        self.check_ollama_availability()

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
        self.save_summary_btn.config(state=DISABLED)
        self.save_transcription_btn.config(state=DISABLED)
        self.save_both_btn.config(state=DISABLED)
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
            # Clear transcription text at start
            self.window.after(0, lambda: self.clear_transcription_text())

            # Callback for progress updates with partial transcription
            def progress_callback(current, total, message, partial_transcription):
                # Calculate percentage
                if total > 0:
                    percentage = int((current / total) * 100)
                    self.window.after(0, lambda m=message, p=percentage, pt=partial_transcription:
                                      self.update_progress_with_partial(p, m, pt))
                else:
                    self.window.after(0, lambda m=message, pt=partial_transcription:
                                      self.update_progress_with_partial(0, m, pt))

            # Perform transcription
            transcription = self.transcriber.transcribe_file(
                self.current_file_path,
                language="it",
                beam_size=5,
                progress_callback=progress_callback
            )

            # Update UI with results (transcription already displayed progressively)
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

    def clear_transcription_text(self):
        """Clear the transcription text area."""
        self.transcription_text.delete(1.0, END)

    def update_progress_with_partial(self, percentage: int, message: str, partial_transcription: str):
        """Update progress bar, status message, and display partial transcription."""
        self.progress_bar['value'] = percentage
        self.progress_var.set(message)

        # Update transcription text area with partial result
        if partial_transcription:
            self.transcription_text.delete(1.0, END)
            self.transcription_text.insert(1.0, partial_transcription)

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
        self.save_transcription_btn.config(state=NORMAL)  # Can save transcription now

        # Enable generate summary button if Ollama is available
        if self.ollama_available:
            self.generate_summary_btn.config(state=NORMAL)

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

    def check_ollama_availability(self):
        """Check if Ollama is available and update UI accordingly."""
        is_available, message = self.ollama.is_available()
        self.ollama_available = is_available
        self.ollama_status_message = message

        if is_available:
            self.ollama_status_label.config(text="✓ Ollama ready", bootstyle="success")
            self.logger.info(f"Ollama is available: {message}")
        else:
            self.ollama_status_label.config(text="⚠ Ollama unavailable", bootstyle="warning")
            self.generate_summary_btn.config(state=DISABLED)
            self.logger.warning(f"Ollama not available: {message}")
            self.status_var.set(f"Ollama not available - {message}")

    def generate_summary(self):
        """Generate summary using Ollama."""
        transcription = self.transcription_text.get(1.0, END).strip()

        if not transcription:
            messagebox.showwarning("No Transcription", "Please transcribe an audio file first.")
            return

        # Disable button during generation
        self.generate_summary_btn.config(state=DISABLED)
        self.status_var.set("Generating summary with Ollama...")

        # Run in background thread
        thread = threading.Thread(target=self.generate_summary_thread, args=(transcription,), daemon=True)
        thread.start()

    def generate_summary_thread(self, transcription: str):
        """Background thread for summary generation."""
        def progress_callback(message):
            self.window.after(0, lambda: self.status_var.set(message))

        success, result = self.ollama.generate_summary(transcription, progress_callback)

        if success:
            # Update UI on main thread
            self.window.after(0, lambda: self.summary_generation_complete(result))
        else:
            # Show error on main thread
            self.window.after(0, lambda: self.summary_generation_error(result))

    def summary_generation_complete(self, summary: str):
        """Handle successful summary generation."""
        self.current_summary = summary

        # Hide placeholder and show summary text box
        self.summary_placeholder.grid_remove()
        self.summary_text.grid()

        # Update summary text
        self.summary_text.delete(1.0, END)
        self.summary_text.insert(1.0, summary)
        self.status_var.set("Summary generated successfully!")

        # Enable save buttons
        self.save_summary_btn.config(state=NORMAL)
        self.save_both_btn.config(state=NORMAL)
        self.generate_summary_btn.config(state=NORMAL)

        self.logger.info("Summary generated successfully")

    def summary_generation_error(self, error_msg: str):
        """Handle summary generation error."""
        self.status_var.set(f"Summary generation failed: {error_msg}")
        self.generate_summary_btn.config(state=NORMAL)
        messagebox.showerror("Summary Generation Error", error_msg)

    def save_summary_only(self):
        """Save only the summary to a text file."""
        summary = self.summary_text.get(1.0, END).strip()

        if not summary:
            messagebox.showwarning("No Summary", "Please generate a summary first.")
            return

        # Suggest filename
        suggested_name = "summary.txt"
        if self.current_file_path:
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
            suggested_name = f"{base_name}_summary.txt"

        file_path = filedialog.asksaveasfilename(
            title="Save Summary",
            defaultextension=".txt",
            initialfile=suggested_name,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                self.status_var.set(f"Summary saved to: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Summary saved to:\n{file_path}")
                self.logger.info(f"Summary saved to: {file_path}")
            except Exception as e:
                error_msg = f"Error saving file: {str(e)}"
                self.logger.error(error_msg)
                messagebox.showerror("Save Error", error_msg)

    def save_transcription_only(self):
        """Save only the transcription to a text file."""
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
                self.status_var.set(f"Transcription saved to: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Transcription saved to:\n{file_path}")
                self.logger.info(f"Transcription saved to: {file_path}")
            except Exception as e:
                error_msg = f"Error saving file: {str(e)}"
                self.logger.error(error_msg)
                messagebox.showerror("Save Error", error_msg)

    def save_both(self):
        """Save both summary and transcription to a single file."""
        summary = self.summary_text.get(1.0, END).strip()
        transcription = self.transcription_text.get(1.0, END).strip()

        if not summary or not transcription:
            messagebox.showwarning("Missing Content", "Please generate both summary and transcription first.")
            return

        # Suggest filename
        suggested_name = "transcription_with_summary.txt"
        if self.current_file_path:
            base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
            suggested_name = f"{base_name}_complete.txt"

        file_path = filedialog.asksaveasfilename(
            title="Save Summary and Transcription",
            defaultextension=".txt",
            initialfile=suggested_name,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                # Use the format_combined_output helper
                combined_content = format_combined_output(summary, transcription)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(combined_content)
                self.status_var.set(f"Summary and transcription saved to: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Both summary and transcription saved to:\n{file_path}")
                self.logger.info(f"Summary and transcription saved to: {file_path}")
            except Exception as e:
                error_msg = f"Error saving file: {str(e)}"
                self.logger.error(error_msg)
                messagebox.showerror("Save Error", error_msg)

    def clear_all(self):
        """Clear both summary and transcription text areas."""
        if messagebox.askyesno("Clear All", "Clear both summary and transcription?"):
            self.transcription_text.delete(1.0, END)
            self.summary_text.delete(1.0, END)
            self.current_summary = None

            # Hide summary text box and show placeholder
            self.summary_text.grid_remove()
            self.summary_placeholder.grid()

            self.progress_bar['value'] = 0
            self.progress_var.set("Ready to transcribe")
            self.status_var.set("Cleared")

            # Disable save buttons
            self.save_summary_btn.config(state=DISABLED)
            self.save_transcription_btn.config(state=DISABLED)
            self.save_both_btn.config(state=DISABLED)
            self.generate_summary_btn.config(state=DISABLED)

            self.logger.info("Summary and transcription cleared")

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
