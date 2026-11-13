import pytest
from starlette.testclient import TestClient


def test_websocket_connection_and_handshake(sync_client: TestClient):
    with sync_client.websocket_connect("/api/v1/ws/voice") as websocket:
        # 1. Check initial connection acknowledgement
        initial_data = websocket.receive_json()
        assert initial_data["type"] == "connection_ack"
        assert initial_data["status"] == "connected"
        assert "client_id" in initial_data
        assert "VoxLedger" in initial_data["message"]

        # 2. Test ping / pong heartbeat
        websocket.send_json({"type": "ping"})
        pong_data = websocket.receive_json()
        assert pong_data["type"] == "pong"
        assert "timestamp" in pong_data

        # 3. Test stream_init handshake
        websocket.send_json({
            "type": "stream_init",
            "language": "hi-IN",
            "sample_rate": 16000,
        })
        stream_ready = websocket.receive_json()
        assert stream_ready["type"] == "stream_ready"
        assert stream_ready["language"] == "hi-IN"
        assert stream_ready["sample_rate"] == 16000
        assert stream_ready["status"] == "ready_for_audio"

        # 4. Test audio chunk envelope
        websocket.send_json({
            "type": "audio_chunk",
            "sequence": 1,
            "data": "base64audiobytesplaceholder",
        })
        chunk_ack = websocket.receive_json()
        assert chunk_ack["type"] == "chunk_received"
        assert chunk_ack["sequence"] == 1
        assert chunk_ack["status"] == "buffered"
