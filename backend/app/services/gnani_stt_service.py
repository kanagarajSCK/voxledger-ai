import asyncio
import json
import logging
from typing import Optional, Callable, Awaitable
import websockets
from app.core.config import settings

logger = logging.getLogger("voxledger.stt")


class GnaniSTTSession:
    """Manages an active real-time upstream connection to Gnani Prisma v3.0 STT WebSocket."""

    def __init__(
        self,
        language: str = "hi-IN",
        sample_rate: int = 16000,
        on_transcript: Optional[Callable[[dict], Awaitable[None]]] = None,
        on_speech_start: Optional[Callable[[dict], Awaitable[None]]] = None,
    ):
        self.language = language
        self.sample_rate = sample_rate
        self.on_transcript = on_transcript
        self.on_speech_start = on_speech_start
        self.ws = None
        self._recv_task = None
        self.is_connected = False
        self._api_key = settings.GNANI_API_KEY.get_secret_value()
        self._url = settings.GNANI_STT_WS_URL or "wss://api.vachana.ai/stt/v3/stream"
        self._model = settings.GNANI_STT_MODEL or "prisma-v3.0"

    async def connect(self) -> bool:
        if not settings.GNANI_STT_ENABLED or not self._api_key or len(self._api_key) < 10:
            logger.warning("Gnani STT is not configured or disabled.")
            return False

        headers = {
            "x-api-key-id": self._api_key,
            "language_code": self.language,
            "x-sample-rate": str(self.sample_rate),
            "model": self._model,
        }

        try:
            self.ws = await websockets.connect(
                self._url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            )
            self.is_connected = True
            logger.info("Connected to Gnani STT WebSocket (lang=%s, model=%s)", self.language, self._model)

            # Start background reader task
            self._recv_task = asyncio.create_task(self._reader_loop())
            return True
        except Exception as e:
            logger.error("Failed to connect to Gnani STT WebSocket: %s", e)
            self.is_connected = False
            return False

    async def send_audio_chunk(self, chunk: bytes):
        """Send raw PCM binary frame to Gnani STT."""
        if self.is_connected and self.ws:
            try:
                await self.ws.send(chunk)
            except Exception as e:
                logger.error("Error sending audio chunk to Gnani STT: %s", e)
                self.is_connected = False

    async def flush_and_close(self):
        """Send trailing silence to allow VAD to finalize speech, then close connection."""
        if self.is_connected and self.ws:
            try:
                # Send 500ms of silence (16000 samples/sec * 2 bytes * 0.5s = 16000 bytes)
                silence = b"\x00" * 1024
                for _ in range(8):
                    await self.ws.send(silence)
                    await asyncio.sleep(0.016)
            except Exception:
                pass
            finally:
                await self.close()

    async def close(self):
        self.is_connected = False
        if self._recv_task:
            self._recv_task.cancel()
            self._recv_task = None
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
        logger.info("Gnani STT session closed.")

    async def _reader_loop(self):
        """Receive messages from Gnani STT and dispatch to callbacks."""
        try:
            async for raw_msg in self.ws:
                try:
                    data = json.loads(raw_msg)
                    msg_type = data.get("type") or data.get("event")

                    if msg_type == "speech_start" and self.on_speech_start:
                        await self.on_speech_start(data)
                    elif msg_type in ("transcript", "final_transcript") and self.on_transcript:
                        await self.on_transcript(data)
                    elif msg_type == "error":
                        logger.error("Gnani STT returned error frame: %s", data)
                except Exception as parse_err:
                    logger.warning("Error handling STT frame: %s", parse_err)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Gnani STT reader loop terminated: %s", e)
        finally:
            self.is_connected = False
