"""
Core file transcription logic for audio file processing.
Handles loading, format conversion, chunking, and transcription of audio files.
"""

import numpy as np
import os
import logging
from typing import Callable, Optional, Tuple, List
from faster_whisper import WhisperModel


class FileTranscriber:
    """Handles transcription of audio files using Whisper models."""

    def __init__(self, model_size: str = "base", device: str = "auto", compute_type: str = "int8"):
        """
        Initialize the file transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (auto, cpu, cuda)
            compute_type: Compute type for inference (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self.logger = logging.getLogger(__name__)

    def load_model(self) -> None:
        """Load the Whisper model."""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            self.logger.info("Model loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise

    def switch_model(self, model_size: str) -> None:
        """
        Switch to a different model size.

        Args:
            model_size: New model size to load
        """
        self.model_size = model_size
        self.load_model()

    def load_audio_file(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load an audio file and convert it to the format required by Whisper.

        Args:
            file_path: Path to the audio file

        Returns:
            Tuple of (audio_array as float32, sample_rate)

        Raises:
            Exception if file cannot be loaded
        """
        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower()

        # Try soundfile first for WAV, FLAC, OGG (faster and simpler)
        if file_ext in ['.wav', '.flac', '.ogg']:
            return self._load_with_soundfile(file_path)

        # Use PyAV for M4A, MP3, AAC (iPhone voice notes, etc.)
        elif file_ext in ['.m4a', '.mp3', '.aac', '.mp4']:
            return self._load_with_pyav(file_path)

        else:
            # Try both methods
            try:
                return self._load_with_soundfile(file_path)
            except:
                return self._load_with_pyav(file_path)

    def _load_with_soundfile(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio using soundfile (WAV, FLAC, OGG)."""
        try:
            import soundfile as sf
            from scipy import signal

            self.logger.info(f"Loading with soundfile: {file_path}")

            # Load the audio file
            audio_data, sample_rate = sf.read(file_path, dtype='float32')

            # Convert stereo to mono if needed
            if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Resample to 16kHz if needed
            if sample_rate != 16000:
                self.logger.info(f"Resampling from {sample_rate}Hz to 16000Hz")
                num_samples = int(len(audio_data) * 16000 / sample_rate)
                audio_data = signal.resample(audio_data, num_samples)

            self.logger.info(f"Audio loaded: {len(audio_data)} samples, {len(audio_data)/16000:.2f} seconds")
            return audio_data, 16000

        except Exception as e:
            self.logger.error(f"soundfile failed: {e}")
            raise

    def _load_with_pyav(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio using PyAV (M4A, MP3, AAC, MP4)."""
        try:
            import av
            from scipy import signal

            self.logger.info(f"Loading with PyAV: {file_path}")

            # Open the audio file
            container = av.open(file_path)
            audio_stream = container.streams.audio[0]

            # Collect audio frames
            audio_frames = []
            for frame in container.decode(audio_stream):
                array = frame.to_ndarray()
                # Convert to mono if stereo
                if len(array.shape) > 1:
                    array = np.mean(array, axis=0)
                audio_frames.append(array)

            # Concatenate all frames
            audio_data = np.concatenate(audio_frames)

            # Get sample rate
            sample_rate = audio_stream.rate

            # Convert to float32 and normalize
            if audio_data.dtype != np.float32:
                # Normalize based on data type
                if audio_data.dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                elif audio_data.dtype == np.int32:
                    audio_data = audio_data.astype(np.float32) / 2147483648.0
                else:
                    audio_data = audio_data.astype(np.float32)

            # Resample to 16kHz if needed
            if sample_rate != 16000:
                self.logger.info(f"Resampling from {sample_rate}Hz to 16000Hz")
                num_samples = int(len(audio_data) * 16000 / sample_rate)
                audio_data = signal.resample(audio_data, num_samples)

            container.close()

            self.logger.info(f"Audio loaded: {len(audio_data)} samples, {len(audio_data)/16000:.2f} seconds")
            return audio_data, 16000

        except ImportError:
            self.logger.error("PyAV not installed. Install with: pip install av")
            raise Exception(
                "PyAV is required for M4A/MP3 files.\n"
                "Install it with: pip install av"
            )
        except Exception as e:
            self.logger.error(f"PyAV failed: {e}")
            raise

    def chunk_audio(self, audio_array: np.ndarray, chunk_duration_seconds: int = 90) -> List[np.ndarray]:
        """
        Split audio into chunks for processing long files.

        Args:
            audio_array: Audio data as numpy array
            chunk_duration_seconds: Duration of each chunk in seconds (default: 90 seconds)

        Returns:
            List of audio chunks
        """
        sample_rate = 16000
        chunk_size = chunk_duration_seconds * sample_rate
        total_samples = len(audio_array)

        # If audio is shorter than chunk size, return as single chunk
        if total_samples <= chunk_size:
            return [audio_array]

        # Split into chunks
        chunks = []
        for i in range(0, total_samples, chunk_size):
            chunk = audio_array[i:i + chunk_size]
            chunks.append(chunk)
            self.logger.info(f"Created chunk {len(chunks)}: {len(chunk)/sample_rate:.2f} seconds")

        return chunks

    def transcribe_chunk(
        self,
        audio_chunk: np.ndarray,
        language: str = "en",
        beam_size: int = 5
    ) -> str:
        """
        Transcribe a single audio chunk.

        Args:
            audio_chunk: Audio data as numpy array
            language: Language code (default: en)
            beam_size: Beam size for decoding (higher = more accurate but slower)

        Returns:
            Transcribed text
        """
        if self.model is None:
            self.load_model()

        try:
            self.logger.info(f"Transcribing chunk ({len(audio_chunk)/16000:.2f} seconds)")

            segments, info = self.model.transcribe(
                audio_chunk,
                beam_size=beam_size,
                language=language,
                vad_filter=True  # Use built-in VAD for file transcription
            )

            # Collect all text segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)

            text = " ".join(text_parts).strip()
            self.logger.info(f"Transcription complete: {len(text)} characters")

            return text

        except Exception as e:
            self.logger.error(f"Error transcribing chunk: {e}")
            raise

    def transcribe_file(
        self,
        file_path: str,
        language: str = "en",
        beam_size: int = 5,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None
    ) -> str:
        """
        Transcribe an entire audio file.

        Args:
            file_path: Path to the audio file
            language: Language code (default: en)
            beam_size: Beam size for decoding
            progress_callback: Optional callback function(current_chunk, total_chunks, status_message, partial_transcription)

        Returns:
            Complete transcription as string
        """
        try:
            # Load the audio file
            if progress_callback:
                progress_callback(0, 1, "Loading audio file...", "")

            audio_array, sample_rate = self.load_audio_file(file_path)

            # Chunk the audio
            if progress_callback:
                progress_callback(0, 1, "Preparing chunks...", "")

            chunks = self.chunk_audio(audio_array)
            total_chunks = len(chunks)

            self.logger.info(f"Processing {total_chunks} chunk(s)")

            # Transcribe each chunk
            transcriptions = []
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_callback(
                        i,
                        total_chunks,
                        f"Transcribing chunk {i+1}/{total_chunks}...",
                        " ".join(transcriptions)  # Send partial result so far
                    )

                text = self.transcribe_chunk(chunk, language=language, beam_size=beam_size)
                transcriptions.append(text)

                # Send partial transcription after completing this chunk
                if progress_callback:
                    progress_callback(
                        i + 1,
                        total_chunks,
                        f"Completed chunk {i+1}/{total_chunks}",
                        " ".join(transcriptions)  # Send updated partial result
                    )

            # Combine all transcriptions
            full_transcription = " ".join(transcriptions)

            if progress_callback:
                progress_callback(total_chunks, total_chunks, "Transcription complete!", full_transcription)

            self.logger.info(f"Full transcription: {len(full_transcription)} characters")

            return full_transcription

        except Exception as e:
            self.logger.error(f"Error transcribing file: {e}")
            if progress_callback:
                progress_callback(0, 1, f"Error: {str(e)}", "")
            raise

    def save_transcription(self, text: str, output_path: str) -> None:
        """
        Save transcription to a text file.

        Args:
            text: Transcription text
            output_path: Path to save the text file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            self.logger.info(f"Transcription saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving transcription: {e}")
            raise


def get_supported_formats() -> List[str]:
    """
    Get list of supported audio file formats.

    Returns:
        List of file extensions (with dot)
    """
    # All supported formats (soundfile + PyAV)
    return ['.m4a', '.mp3', '.wav', '.aac', '.flac', '.ogg', '.mp4']


def format_file_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)
