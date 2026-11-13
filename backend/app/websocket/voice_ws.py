import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.websocket.connection_manager import manager
from app.services.gnani_stt_service import GnaniSTTSession
from app.services.voice_workflow_service import voice_workflow

logger = logging.getLogger("voxledger.voice_ws")

router = APIRouter()


@router.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """Real-time voice streaming WebSocket endpoint.
    Handles bidirectional client audio streaming, Gnani Prisma v3.0 STT upstream bridge,
    voice command parsing, and financial confirmation workflows.
    """
    client_id = str(uuid.uuid4())
    await manager.connect(client_id, websocket)

    current_language = settings.GNANI_DEFAULT_LANGUAGE or "hi-IN"
    session = voice_workflow.get_or_create_session(client_id, current_language)
    stt_session: Optional[GnaniSTTSession] = None

    # Send initial connection handshake
    await manager.send_json(
        client_id,
        {
            "type": "connection_ack",
            "client_id": client_id,
            "session_id": client_id,
            "status": "connected",
            "language": current_language,
            "stt_configured": settings.has_gnani_credentials and settings.GNANI_STT_ENABLED,
            "tts_configured": settings.has_gnani_credentials and settings.GNANI_TTS_ENABLED,
            "sample_rate": settings.VOICE_STREAM_SAMPLE_RATE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "VoxLedger AI Realtime Voice Stream Gateway Ready",
        },
    )

    # Transcript callback for upstream Gnani STT events
    async def handle_stt_transcript(data: dict):
        text = data.get("text", "").strip()
        is_final = data.get("is_final", False)
        if not text:
            return

        # Forward transcript event to client
        if websocket.client_state == WebSocketState.CONNECTED:
            await manager.send_json(
                client_id,
                {
                    "type": "transcript",
                    "text": text,
                    "is_final": is_final,
                    "language": data.get("detected_language_code") or current_language,
                },
            )

        # Process final transcripts through safety workflow
        if is_final:
            async with AsyncSessionLocal() as db:
                try:
                    result = await voice_workflow.handle_transcript(
                        db=db,
                        session_id=client_id,
                        transcript=text,
                        language=current_language,
                    )
                    await db.commit()
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await manager.send_json(client_id, result)
                except Exception as e:
                    await db.rollback()
                    logger.error("Error processing transcript workflow: %s", e)

    # Speech start callback
    async def handle_speech_start(_data: dict):
        if websocket.client_state == WebSocketState.CONNECTED:
            await manager.send_json(client_id, {"type": "speech_start"})

    try:
        while True:
            raw_message = await websocket.receive()
            if "bytes" in raw_message and raw_message["bytes"]:
                # Binary frame: stream raw PCM audio chunk upstream to Gnani STT
                audio_bytes = raw_message["bytes"]
                if stt_session and stt_session.is_connected:
                    await stt_session.send_audio_chunk(audio_bytes)
                continue

            if "text" in raw_message and raw_message["text"]:
                try:
                    data = json.loads(raw_message["text"])
                except Exception:
                    continue

                msg_type = data.get("type", "unknown")

                # 1. Ping / Heartbeat
                if msg_type == "ping":
                    await manager.send_json(
                        client_id,
                        {
                            "type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                # 2. Start audio stream
                elif msg_type in ("start_stream", "stream_init"):
                    if "language" in data:
                        current_language = data["language"]
                        session["language"] = current_language

                    sample_rate = data.get("sample_rate", settings.VOICE_STREAM_SAMPLE_RATE)

                    # Close existing STT session if any
                    if stt_session:
                        await stt_session.close()

                    stt_session = GnaniSTTSession(
                        language=current_language,
                        sample_rate=sample_rate,
                        on_transcript=handle_stt_transcript,
                        on_speech_start=handle_speech_start,
                    )

                    connected = await stt_session.connect()
                    await manager.send_json(
                        client_id,
                        {
                            "type": "stream_ready",
                            "session_id": client_id,
                            "language": current_language,
                            "sample_rate": sample_rate,
                            "status": "ready_for_audio",
                            "upstream_connected": connected,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                # 3. Audio chunk acknowledgement (for envelope testing/scenarios)
                elif msg_type == "audio_chunk":
                    seq = data.get("sequence", 0)
                    await manager.send_json(
                        client_id,
                        {
                            "type": "chunk_received",
                            "sequence": seq,
                            "status": "buffered",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                # 4. Stop audio stream
                elif msg_type == "stop_stream":
                    if stt_session:
                        await stt_session.flush_and_close()
                        stt_session = None
                    await manager.send_json(
                        client_id,
                        {
                            "type": "stream_stopped",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                # 4. Text command (for testing or direct typed voice queries)
                elif msg_type == "text_command":
                    text = data.get("text", "").strip()
                    lang = data.get("language", current_language)
                    if text:
                        async with AsyncSessionLocal() as db:
                            try:
                                result = await voice_workflow.handle_transcript(
                                    db=db,
                                    session_id=client_id,
                                    transcript=text,
                                    language=lang,
                                )
                                await db.commit()
                                await manager.send_json(client_id, result)
                            except Exception as e:
                                await db.rollback()
                                logger.error("Error in text command workflow: %s", e)

                # 5. Explicit action confirmation
                elif msg_type == "confirm_action":
                    async with AsyncSessionLocal() as db:
                        try:
                            result = await voice_workflow._execute_pending_action(db, session)
                            await db.commit()
                            await manager.send_json(client_id, result)
                        except Exception as e:
                            await db.rollback()
                            logger.error("Error confirming action: %s", e)

                # 6. Explicit action cancellation
                elif msg_type == "cancel_action":
                    result = await voice_workflow._cancel_pending_action(session)
                    await manager.send_json(client_id, result)

                # 7. Set Language
                elif msg_type == "set_language":
                    new_lang = data.get("language")
                    if new_lang:
                        current_language = new_lang
                        session["language"] = new_lang
                        await manager.send_json(
                            client_id,
                            {
                                "type": "language_changed",
                                "language": current_language,
                            },
                        )

    except WebSocketDisconnect:
        logger.info("Client %s disconnected from voice WebSocket.", client_id)
    except Exception as e:
        logger.warning("Voice WebSocket exception for client %s: %s", client_id, e)
    finally:
        if stt_session:
            await stt_session.close()
        manager.disconnect(client_id)
        voice_workflow.clear_session(client_id)
