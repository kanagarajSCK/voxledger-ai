import io
from typing import Optional
from fastapi import APIRouter, Query, Response, HTTPException, status
from pydantic import BaseModel, Field
from app.services.gnani_tts_service import tts_service
from app.core.config import settings

router = APIRouter(prefix="/voice", tags=["Voice Engine"])


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Text to synthesize")
    language: str = Field("hi-IN", description="Language code: hi-IN, en-IN, ta-IN, kn-IN")
    voice: Optional[str] = Field("Shivani", description="Voice identifier")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech rate speed factor")


class VoiceStatusResponse(BaseModel):
    stt_enabled: bool
    tts_enabled: bool
    stt_configured: bool
    tts_configured: bool
    stt_model: str
    tts_model: str
    supported_languages: dict[str, str]
    supported_voices: list[str]


@router.get("/status", response_model=VoiceStatusResponse)
async def get_voice_status():
    """Get the current configuration status and capabilities of Gnani voice engine."""
    has_creds = settings.has_gnani_credentials
    return VoiceStatusResponse(
        stt_enabled=settings.GNANI_STT_ENABLED,
        tts_enabled=settings.GNANI_TTS_ENABLED,
        stt_configured=has_creds and settings.GNANI_STT_ENABLED,
        tts_configured=has_creds and settings.GNANI_TTS_ENABLED,
        stt_model=settings.GNANI_STT_MODEL,
        tts_model=settings.GNANI_TTS_MODEL,
        supported_languages=tts_service.SUPPORTED_LANGUAGES,
        supported_voices=tts_service.SUPPORTED_VOICES,
    )


@router.post("/tts")
async def synthesize_speech_post(payload: TTSRequest):
    """Synthesize text to speech using Gnani Timbre v3.0 and stream WAV audio back."""
    if not tts_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gnani TTS service is not configured or enabled.",
        )

    wav_bytes = await tts_service.synthesize(
        text=payload.text,
        language=payload.language,
        voice=payload.voice,
        speed=payload.speed,
    )

    if not wav_bytes:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate speech audio from provider.",
        )

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "inline; filename=speech.wav",
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.get("/tts")
async def synthesize_speech_get(
    text: str = Query(..., min_length=1, max_length=1000),
    language: str = Query("hi-IN"),
    voice: Optional[str] = Query("Shivani"),
    speed: float = Query(1.0, ge=0.5, le=2.0),
):
    """GET endpoint for easy HTML5 `<audio src="...">` streaming playback."""
    if not tts_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gnani TTS service is not configured or enabled.",
        )

    wav_bytes = await tts_service.synthesize(
        text=text,
        language=language,
        voice=voice,
        speed=speed,
    )

    if not wav_bytes:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate speech audio from provider.",
        )

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "inline; filename=speech.wav",
            "Cache-Control": "public, max-age=3600",
        },
    )
