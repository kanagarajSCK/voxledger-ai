import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient
from unittest.mock import patch, AsyncMock, PropertyMock
from app.main import app


@pytest.mark.asyncio
async def test_voice_status_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/voice/status")
    assert response.status_code == 200
    data = response.json()
    assert "stt_enabled" in data
    assert "tts_enabled" in data
    assert "stt_model" in data
    assert "supported_languages" in data
    assert "hi-IN" in data["supported_languages"]
    assert "ta-IN" in data["supported_languages"]
    assert "kn-IN" in data["supported_languages"]
    assert "en-IN" in data["supported_languages"]


@pytest.mark.asyncio
async def test_tts_endpoint_mocked(async_client: AsyncClient):
    dummy_wav = b"RIFF....WAVEfmt ...."
    with patch(
        "app.services.gnani_tts_service.GnaniTTSService.is_configured",
        new_callable=PropertyMock,
        return_value=True,
    ), patch(
        "app.services.gnani_tts_service.GnaniTTSService.synthesize",
        new_callable=AsyncMock,
        return_value=dummy_wav,
    ):
        # POST /api/v1/voice/tts
        resp = await async_client.post(
            "/api/v1/voice/tts",
            json={"text": "Hello kirana", "language": "en-IN"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        assert resp.content == dummy_wav

        # GET /api/v1/voice/tts
        resp_get = await async_client.get("/api/v1/voice/tts?text=Hello&language=en-IN")
        assert resp_get.status_code == 200
        assert resp_get.content == dummy_wav


def test_websocket_voice_connection_lifecycle(sync_client: TestClient):
    with sync_client.websocket_connect("/api/v1/ws/voice") as websocket:
        # 1. Connection Ack
        initial = websocket.receive_json()
        assert initial["type"] == "connection_ack"
        assert initial["status"] == "connected"

        # 2. Ping / Pong
        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"

        # 3. Change Language
        websocket.send_json({"type": "set_language", "language": "ta-IN"})
        lang_res = websocket.receive_json()
        assert lang_res["type"] == "language_changed"
        assert lang_res["language"] == "ta-IN"
