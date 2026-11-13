import logging
from typing import Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("voxledger.tts")


class GnaniTTSService:
    """Gnani Timbre v3.0 Text-to-Speech integration service."""

    SUPPORTED_LANGUAGES = {
        "hi-IN": "Hindi",
        "en-IN": "English (India)",
        "ta-IN": "Tamil",
        "kn-IN": "Kannada",
    }

    # Verified supported voices for timbre-v3.0 from Gnani API:
    # Avinash, Shivani, Lakshmi, Kalpana, Shubham, Prakash, Devansh, Yashraj, Chetana, Vasudha, Harshad, Riyaa, Tarika
    SUPPORTED_VOICES = [
        "Shivani",
        "Avinash",
        "Lakshmi",
        "Kalpana",
        "Shubham",
        "Prakash",
        "Devansh",
        "Yashraj",
        "Chetana",
        "Vasudha",
        "Harshad",
        "Riyaa",
        "Tarika",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        default_voice: Optional[str] = None,
    ):
        self.api_key = api_key or settings.GNANI_API_KEY.get_secret_value()
        self.model = model or settings.GNANI_TTS_MODEL or "timbre-v3.0"
        self.default_voice = default_voice or settings.GNANI_TTS_DEFAULT_VOICE or "Shivani"
        self.api_url = settings.GNANI_TTS_API_URL or "https://api.vachana.ai/api/v1/tts/inference"
        self.timeout = settings.GNANI_TIMEOUT_SECONDS

    @property
    def is_configured(self) -> bool:
        return bool(
            settings.GNANI_TTS_ENABLED
            and self.api_key
            and len(self.api_key) > 10
            and not self.api_key.lower().startswith("your_")
        )

    async def synthesize(
        self,
        text: str,
        language: str = "hi-IN",
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """Synthesize text into WAV audio using Gnani Timbre v3.0."""
        if not self.is_configured:
            logger.warning("Gnani TTS synthesis requested but credentials not configured.")
            return None

        if not text or not text.strip():
            return None

        selected_voice = voice or self.default_voice
        if selected_voice not in self.SUPPORTED_VOICES:
            selected_voice = "Shivani"

        # Validate language code
        if language not in self.SUPPORTED_LANGUAGES:
            language = settings.GNANI_DEFAULT_LANGUAGE or "hi-IN"

        headers = {
            "X-API-Key-ID": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "text": text.strip(),
            "voice": selected_voice,
            "model": self.model,
            "language": language,
            "speed": float(speed),
            "audio_config": {
                "encoding": "linear_pcm",
                "container": "wav",
                "num_channels": 1,
                "sample_rate": 24000,
                "sample_width": 2,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(
                        "Gnani TTS API returned status %s: %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return None
        except Exception as e:
            logger.error("Gnani TTS request error: %s", e)
            return None


tts_service = GnaniTTSService()
