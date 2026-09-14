import abc
import logging
import os
from typing import Optional
from app.core.config import settings

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

logger = logging.getLogger(__name__)


class STTProvider(abc.ABC):
    """Abstract base class for Speech-to-Text providers."""

    @abc.abstractmethod
    async def transcribe(self, file_path: str, lang: Optional[str] = None) -> str:
        """Transcribe an audio file to text.

        :param file_path: Absolute or relative path to the temporary audio file.
        :param lang: Optional language code (e.g. 'en', 'hi').
        :return: Transcribed text string.
        """
        pass


class LocalWhisperProvider(STTProvider):
    """Local Speech-to-Text provider using faster-whisper (CTranslate2)."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or getattr(settings, "stt_model_name", "tiny")
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading local Whisper model: {self.model_name}")
                self._model = WhisperModel(
                    self.model_name,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                )
            except Exception as e:
                logger.error(f"Failed to load local Whisper model '{self.model_name}': {e}", exc_info=True)
                raise RuntimeError(f"Failed to initialize local Whisper model: {e}") from e
        return self._model

    async def transcribe(self, file_path: str, lang: Optional[str] = None) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        import asyncio

        def _do_transcribe() -> str:
            model = self._get_model()
            segments, info = model.transcribe(
                file_path,
                beam_size=5,
                language=lang if lang and lang != "auto" else None,
                vad_filter=True,
            )
            transcript_parts = [segment.text.strip() for segment in segments if segment.text]
            transcript = " ".join(transcript_parts).strip()
            logger.info(
                f"[STT LocalWhisper] Transcribed {info.duration:.2f}s audio "
                f"(lang={info.language}, prob={info.language_probability:.2f}) -> {len(transcript)} chars"
            )
            return transcript

        try:
            return await asyncio.to_thread(_do_transcribe)
        except Exception as e:
            logger.error(f"[STT LocalWhisper] Error transcribing file {file_path}: {e}", exc_info=True)
            raise RuntimeError(f"Local Whisper transcription failed: {e}") from e


class FutureProductionSTTProvider(STTProvider):
    """Placeholder for future production cloud STT provider (e.g., Hosted Whisper / GCP Speech)."""

    async def transcribe(self, file_path: str, lang: Optional[str] = None) -> str:
        logger.error("[STT Production] Production STT provider called but not configured.")
        raise NotImplementedError(
            "Production STT provider is not configured. "
            "Please set STT_PROVIDER=local in your environment to use local Whisper for development."
        )


_provider_instance: Optional[STTProvider] = None


def get_stt_provider() -> STTProvider:
    """Factory function returning the configured STTProvider instance."""
    global _provider_instance
    if _provider_instance is None:
        provider_type = getattr(settings, "stt_provider", "local").lower()
        if provider_type == "local":
            _provider_instance = LocalWhisperProvider()
        elif provider_type == "production":
            _provider_instance = FutureProductionSTTProvider()
        else:
            logger.warning(f"Unknown STT_PROVIDER '{provider_type}', falling back to LocalWhisperProvider")
            _provider_instance = LocalWhisperProvider()
    return _provider_instance
