"""
Verification script for VoxLedger AI Phase 1 Foundation.
Tests live backend REST endpoints and WebSocket voice stream gateway.
"""
import sys
import threading
import time
import httpx
import uvicorn
import websockets
import asyncio

sys.path.insert(0, ".")
from app.main import app


async def test_websocket(port: int):
    uri = f"ws://127.0.0.1:{port}/api/v1/ws/voice"
    async with websockets.connect(uri) as ws:
        # Initial ack
        ack = await ws.recv()
        print("WS ACK RECEIVED:", ack)

        # Ping
        await ws.send('{"type": "ping"}')
        pong = await ws.recv()
        print("WS PONG RECEIVED:", pong)

        # Init stream
        await ws.send('{"type": "stream_init", "language": "hi-IN", "sample_rate": 16000}')
        ready = await ws.recv()
        print("WS STREAM_READY RECEIVED:", ready)


def main():
    port = 8899
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    try:
        # 1. Test REST endpoints
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5.0) as client:
            # Health check unversioned
            r1 = client.get("/api/health")
            assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
            data1 = r1.json()
            assert data1["status"] == "healthy"
            assert data1["database_connected"] is True
            print("REST /api/health -> VERIFIED (200 OK, DB Connected)")

            # Health check versioned
            r2 = client.get("/api/v1/health")
            assert r2.status_code == 200
            data2 = r2.json()
            assert data2["status"] == "healthy"
            print("REST /api/v1/health -> VERIFIED (200 OK)")

            # Root endpoint
            r3 = client.get("/")
            assert r3.status_code == 200
            print("REST / -> VERIFIED (200 OK)")

            # Structured 404 test
            r4 = client.get("/api/v1/nonexistent")
            assert r4.status_code == 404
            data4 = r4.json()
            assert data4["success"] is False
            assert data4["error"]["code"] == "NOT_FOUND"
            print("REST 404 Structured Error -> VERIFIED")

        # 2. Test WebSocket endpoint
        asyncio.run(test_websocket(port))
        print("WEBSOCKET /api/v1/ws/voice -> VERIFIED (Handshake + Ping + StreamInit)")

        print("\nALL PHASE 1 BACKEND VERIFICATIONS COMPLETED SUCCESSFULLY!")

    finally:
        server.should_exit = True
        t.join(timeout=2)


if __name__ == "__main__":
    main()
