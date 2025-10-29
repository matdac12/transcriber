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
from file_transcriber_core import FileTranscriber, get_supported_formats, format_file_duration, check_model_exists, get_model_download_size, get_models_path
from ollama_helper import OllamaHelper, format_combined_output
import time


class ModelDownloadDialog:
    """Dialog for downloading Whisper models with progress tracking."""

    def __init__(self, parent_window):
        """Initialize the model download dialog."""
        self.parent = parent_window
        self.dialog = ttk.Toplevel(parent_window)
        self.dialog.title("Download Whisper Models")
        self.dialog.geometry("550x450")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()  # Make modal

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Download state
        self.download_thread = None
        self.is_downloading = False
        self.download_cancelled = False

        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="Select Models to Download",
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=(0, 10))

        # Description
        ttk.Label(
            main_frame,
            text="Choose one or more Whisper models. Models are downloaded once and stored permanently.",
            font=('Segoe UI', 10),
            bootstyle="secondary",
            wraplength=500
        ).pack(pady=(0, 20))

        # Model selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Available Models", padding=15)
        selection_frame.pack(fill=X, pady=(0, 15))

        # Model checkboxes with size info
        self.model_vars = {}
        models = [
            ('tiny', '~39 MB', 'Fastest, basic accuracy'),
            ('base', '~141 MB', 'Recommended - good balance'),
            ('small', '~461 MB', 'Better accuracy, slower'),
        ]

        for model_name, size, description in models:
            # Check if model already exists
            model_exists = check_model_exists(model_name)

            var = ttk.BooleanVar(value=False)
            self.model_vars[model_name] = var

            frame = ttk.Frame(selection_frame)
            frame.pack(fill=X, pady=5)

            cb = ttk.Checkbutton(
                frame,
                text=f"{model_name.capitalize()} ({size})",
                variable=var,
                bootstyle="success-round-toggle",
                state=DISABLED if model_exists else NORMAL
            )
            cb.pack(side=LEFT)

            status_text = "✓ Installed" if model_exists else description
            status_style = "success" if model_exists else "secondary"

            ttk.Label(
                frame,
                text=status_text,
                font=('Segoe UI', 9),
                bootstyle=status_style
            ).pack(side=LEFT, padx=(10, 0))

        # Progress section
        self.progress_var = ttk.StringVar(value="Ready to download")
        self.progress_label = ttk.Label(
            main_frame,
            textvariable=self.progress_var,
            font=('Segoe UI', 10),
            bootstyle="info"
        )
        self.progress_label.pack(pady=(10, 5))

        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='determinate',
            maximum=100,
            bootstyle="success-striped"
        )
        self.progress_bar.pack(fill=X, pady=(0, 15))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))

        self.download_btn = ttk.Button(
            button_frame,
            text="📥 Download Selected",
            command=self.start_download,
            bootstyle="success",
            width=20
        )
        self.download_btn.pack(side=LEFT, padx=(0, 10))

        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_download,
            bootstyle="secondary",
            width=15
        )
        self.cancel_btn.pack(side=LEFT)

        ttk.Label(
            button_frame,
            text="(Models install to Program Files)",
            font=('Segoe UI', 9),
            bootstyle="secondary"
        ).pack(side=RIGHT)

    def start_download(self):
        """Start downloading selected models."""
        # Get selected models
        selected_models = [name for name, var in self.model_vars.items() if var.get()]

        if not selected_models:
            messagebox.showwarning("No Selection", "Please select at least one model to download.")
            return

        # Disable download button
        self.download_btn.config(state=DISABLED)
        self.is_downloading = True
        self.download_cancelled = False

        # Start download thread
        self.download_thread = threading.Thread(
            target=self._download_models,
            args=(selected_models,),
            daemon=True
        )
        self.download_thread.start()

    def _download_models(self, models):
        """Download models in background thread."""
        try:
            total_models = len(models)
            models_dir = get_models_path()

            if not models_dir:
                # Create default models directory
                import sys
                if getattr(sys, 'frozen', False):
                    exe_dir = os.path.dirname(sys.executable)
                    install_root = os.path.dirname(exe_dir)
                    models_dir = os.path.join(install_root, 'models')
                else:
                    models_dir = os.path.join(os.path.dirname(__file__), 'models')

                os.makedirs(models_dir, exist_ok=True)

            for idx, model_name in enumerate(models):
                if self.download_cancelled:
                    self.dialog.after(0, lambda: self.progress_var.set("Download cancelled"))
                    break

                # Update status
                self.dialog.after(0, lambda m=model_name, i=idx + 1, t=total_models:
                                  self.progress_var.set(f"Downloading {m} ({i}/{t})..."))

                # Download model
                try:
                    transcriber = FileTranscriber(model_size=model_name)
                    transcriber.load_model()

                    # Update progress
                    progress = int((idx + 1) / total_models * 100)
                    self.dialog.after(0, lambda p=progress: self.progress_bar.config(value=p))

                except Exception as e:
                    self.dialog.after(0, lambda m=model_name, err=str(e):
                                      messagebox.showerror("Download Error",
                                                           f"Failed to download {m}:\n{err}"))
                    continue

            # Download complete
            if not self.download_cancelled:
                self.dialog.after(0, lambda: self.progress_var.set("✓ Download complete!"))
                self.dialog.after(0, lambda: self.progress_bar.config(value=100))
                self.dialog.after(0, lambda: messagebox.showinfo("Success",
                                                                  "Models downloaded successfully!\n\nYou can now transcribe audio files."))
                self.dialog.after(500, self.dialog.destroy)
            else:
                self.dialog.after(0, lambda: self.download_btn.config(state=NORMAL))

        except Exception as e:
            self.dialog.after(0, lambda err=str(e): messagebox.showerror("Error", f"Download failed:\n{err}"))
            self.dialog.after(0, lambda: self.download_btn.config(state=NORMAL))

        finally:
            self.is_downloading = False

    def cancel_download(self):
        """Cancel the download."""
        if self.is_downloading:
            self.download_cancelled = True
            self.progress_var.set("Cancelling...")
        else:
            self.dialog.destroy()


class FileTranscriberWindow:
    """Main window for file transcription."""

    def __init__(self, theme="darkly"):
        """Initialize the file transcriber window."""
        self.window = ttk.Window(themename=theme)
        self.window.title("Trascrittore File Audio - Whisper")
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

        # Check if current model is installed
        self.update_model_warning_banner()

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
        ttk.Label(main_frame, text="File Audio:", font=('Segoe UI', 11, 'bold')).grid(
            row=0, column=0, sticky=W, pady=(0, 10)
        )

        self.file_path_var = ttk.StringVar(value="Nessun file selezionato")
        file_path_label = ttk.Label(
            main_frame,
            textvariable=self.file_path_var,
            bootstyle="inverse-secondary",
            padding=(10, 5)
        )
        file_path_label.grid(row=0, column=1, sticky=(W, E), padx=(10, 10), pady=(0, 10))

        self.select_file_btn = ttk.Button(
            main_frame,
            text="Sfoglia...",
            command=self.select_file,
            bootstyle="primary"
        )
        self.select_file_btn.grid(row=0, column=2, padx=(0, 0), pady=(0, 10))

        # Model selection section
        ttk.Label(main_frame, text="Modello:", font=('Segoe UI', 11, 'bold')).grid(
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
            text="(più grande = più preciso ma più lento)",
            font=('Segoe UI', 9),
            bootstyle="secondary"
        ).grid(row=1, column=2, sticky=W, padx=(15, 0), pady=(5, 10))

        # Theme selection section
        ttk.Label(main_frame, text="Tema:", font=('Segoe UI', 11, 'bold')).grid(
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
            text="(cambia aspetto istantaneamente)",
            font=('Segoe UI', 9),
            bootstyle="secondary"
        ).grid(row=2, column=2, sticky=W, padx=(15, 0), pady=(5, 10))

        # Ollama model selection section
        ttk.Label(main_frame, text="Modello Ollama:", font=('Segoe UI', 11, 'bold')).grid(
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
            text="(per generazione riassunto)",
            font=('Segoe UI', 9),
            bootstyle="secondary"
        ).grid(row=3, column=2, sticky=W, padx=(15, 0), pady=(5, 10))

        # Info banner for missing models (initially hidden)
        self.info_banner = ttk.Frame(main_frame, bootstyle="info", padding=10)
        self.info_banner.grid(row=4, column=0, columnspan=3, sticky=(W, E), pady=(15, 10))
        self.info_banner.grid_remove()  # Hidden by default

        self.info_banner.columnconfigure(1, weight=1)

        ttk.Label(
            self.info_banner,
            text="ℹ️",
            font=('Segoe UI', 16),
            bootstyle="info"
        ).grid(row=0, column=0, padx=(0, 10))

        self.info_label = ttk.Label(
            self.info_banner,
            text="Modello non ancora installato. Clicca per scaricare e iniziare.",
            font=('Segoe UI', 10),
            bootstyle="info"
        )
        self.info_label.grid(row=0, column=1, sticky=W)

        self.download_models_btn = ttk.Button(
            self.info_banner,
            text="📥 Scarica Modelli",
            command=self.open_model_download_dialog,
            bootstyle="primary"
        )
        self.download_models_btn.grid(row=0, column=2, padx=(10, 0))

        # Transcribe button
        self.transcribe_btn = ttk.Button(
            main_frame,
            text="▶ Trascrivi",
            command=self.start_transcription,
            bootstyle="success",
            state=DISABLED,
            width=20
        )
        self.transcribe_btn.grid(row=5, column=0, columnspan=3, pady=(15, 10))

        # Progress section
        self.progress_var = ttk.StringVar(value="Pronto per trascrivere")
        progress_label = ttk.Label(
            main_frame,
            textvariable=self.progress_var,
            font=('Segoe UI', 10),
            bootstyle="info"
        )
        progress_label.grid(row=6, column=0, columnspan=3, sticky=(W, E), pady=(10, 5))

        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='determinate',
            maximum=100,
            bootstyle="success-striped"
        )
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(W, E), pady=(0, 15))

        # Summary section
        summary_header_frame = ttk.Frame(main_frame)
        summary_header_frame.grid(row=8, column=0, columnspan=3, sticky=(W, E), pady=(10, 5))

        ttk.Label(summary_header_frame, text="Riassunto:", font=('Segoe UI', 11, 'bold')).pack(side=LEFT)

        self.generate_summary_btn = ttk.Button(
            summary_header_frame,
            text="🤖 Genera Riassunto",
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
        summary_frame.grid(row=9, column=0, columnspan=3, sticky=(W, E), pady=(5, 10))
        summary_frame.columnconfigure(0, weight=1)

        # Placeholder label (shown when no summary yet)
        self.summary_placeholder = ttk.Label(
            summary_frame,
            text="Il riassunto apparirà qui dopo la generazione...",
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
        ttk.Label(main_frame, text="Trascrizione:", font=('Segoe UI', 11, 'bold')).grid(
            row=10, column=0, columnspan=3, sticky=W, pady=(10, 5)
        )

        # Frame for text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=11, column=0, columnspan=3, sticky=(W, E, N, S), pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(11, weight=1)

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
        button_frame.grid(row=12, column=0, columnspan=3, pady=(10, 0))

        self.save_summary_btn = ttk.Button(
            button_frame,
            text="💾 Salva Riassunto",
            command=self.save_summary_only,
            bootstyle="info-outline",
            state=DISABLED,
            width=18
        )
        self.save_summary_btn.pack(side=LEFT, padx=(0, 8))

        self.save_transcription_btn = ttk.Button(
            button_frame,
            text="💾 Salva Trascrizione",
            command=self.save_transcription_only,
            bootstyle="primary-outline",
            state=DISABLED,
            width=20
        )
        self.save_transcription_btn.pack(side=LEFT, padx=(0, 8))

        self.save_both_btn = ttk.Button(
            button_frame,
            text="💾 Salva Entrambi",
            command=self.save_both,
            bootstyle="success-outline",
            state=DISABLED,
            width=18
        )
        self.save_both_btn.pack(side=LEFT, padx=(0, 10))

        self.clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Cancella Tutto",
            command=self.clear_all,
            bootstyle="secondary-outline",
            width=15
        )
        self.clear_btn.pack(side=LEFT, padx=(5, 0))

        # Status bar at bottom
        self.status_var = ttk.StringVar(value="Pronto per trascrivere file audio")
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

        # Check if new model is installed
        self.update_model_warning_banner()

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

    def update_model_warning_banner(self):
        """Check if current model is installed and show/hide info banner."""
        model_size = self.model_var.get()
        model_installed = check_model_exists(model_size)

        if model_installed:
            # Model is installed - hide info banner
            self.info_banner.grid_remove()
            self.logger.info(f"Model {model_size} is installed")
        else:
            # Model not installed - show info banner
            self.info_banner.grid()
            self.info_label.config(text=f"{model_size.capitalize()} model not yet installed. Click to download and get started.")
            self.logger.info(f"Model {model_size} is not installed")

    def open_model_download_dialog(self):
        """Open the model download dialog."""
        dialog = ModelDownloadDialog(self.window)
        # Wait for dialog to close, then refresh model check
        self.window.wait_window(dialog.dialog)
        # Update banner after download completes
        self.update_model_warning_banner()

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
