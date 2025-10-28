"""
Ollama integration helper for generating transcription summaries.
Handles communication with local Ollama instance.
"""

import requests
import logging
from typing import Optional, Tuple


class OllamaHelper:
    """Helper class for interacting with Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        """
        Initialize Ollama helper.

        Args:
            base_url: Base URL for Ollama API
            model: Model name to use for summaries
        """
        self.base_url = base_url
        self.model = model
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> Tuple[bool, str]:
        """
        Check if Ollama is running and accessible.

        Returns:
            Tuple of (is_available: bool, message: str)
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_names = [m.get('name', '') for m in models]

                # Check if our preferred model is available
                model_available = any(self.model in name for name in model_names)

                if model_available:
                    return True, f"Ollama is running with {self.model} model"
                else:
                    available_models = ', '.join([m.split(':')[0] for m in model_names[:3]])
                    return False, f"Ollama is running but {self.model} model not found. Available: {available_models}"

            return False, f"Ollama returned status {response.status_code}"

        except requests.exceptions.ConnectionError:
            return False, "Ollama is not running. Start it with: ollama serve"
        except requests.exceptions.Timeout:
            return False, "Ollama connection timeout"
        except Exception as e:
            return False, f"Error checking Ollama: {str(e)}"

    def generate_summary(
        self,
        transcription: str,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, str]:
        """
        Generate a summary of the transcription using Ollama.

        Args:
            transcription: The full transcription text
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success: bool, result: str)
            If success=True, result is the summary
            If success=False, result is the error message
        """
        try:
            # Check if available first
            is_available, message = self.is_available()
            if not is_available:
                return False, message

            if progress_callback:
                progress_callback("Sending request to Ollama...")

            # Prepare the prompt
            prompt = f"""Fornisci un riassunto conciso della seguente trascrizione. Concentrati sui punti principali e le informazioni chiave:

Trascrizione:
{transcription}

Riassunto:"""

            # Make request to Ollama
            self.logger.info(f"Generating summary with {self.model}")

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=120  # 2 minute timeout for generation
            )

            if response.status_code == 200:
                data = response.json()
                summary = data.get('response', '').strip()

                if summary:
                    self.logger.info(f"Summary generated: {len(summary)} characters")
                    return True, summary
                else:
                    return False, "Ollama returned empty response"

            else:
                return False, f"Ollama returned status {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Summary generation timed out (>2 minutes)"
        except requests.exceptions.ConnectionError:
            return False, "Lost connection to Ollama"
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return False, f"Error: {str(e)}"


def format_combined_output(summary: str, transcription: str) -> str:
    """
    Format summary and transcription for combined output.

    Args:
        summary: Summary text
        transcription: Full transcription text

    Returns:
        Formatted markdown text
    """
    return f"""# Riassunto

{summary}

# Trascrizione

{transcription}
"""


def check_ollama_quick() -> bool:
    """
    Quick check if Ollama is running (no model check).

    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=1)
        return response.status_code == 200
    except:
        return False
