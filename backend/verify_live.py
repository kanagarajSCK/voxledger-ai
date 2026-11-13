"""
Verification script for VoxLedger AI Phase 2 Foundation & Core Ledger Engine.
Tests live backend REST endpoints, ledger calculations, and WebSocket voice stream gateway.
"""
import sys
import threading
import time
import httpx
import uvicorn
import websockets
import asyncio
from decimal import Decimal

sys.path.insert(0, ".")
from app.main import app


async def test_websocket(port: int):
    uri = f"ws://127.0.0.1:{port}/api/v1/ws/voice"
    async with websockets.connect(uri) as ws:
        ack = await ws.recv()
        assert "connection_ack" in ack

        await ws.send('{"type": "ping"}')
        pong = await ws.recv()
        assert "pong" in pong

        await ws.send('{"type": "stream_init", "language": "hi-IN", "sample_rate": 16000}')
        ready = await ws.recv()
        assert "stream_ready" in ready


def main():
    port = 8899
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(2)

    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5.0) as client:
            # 1. Health check
            r_health = client.get("/api/v1/health")
            assert r_health.status_code == 200
            print("1. Health Endpoint -> VERIFIED")

            # 2. Customer creation
            c_res = client.post(
                "/api/v1/customers",
                json={"name": "Live Test Kirana", "phone": "+919999000001", "address": "Market #4"},
            )
            assert c_res.status_code == 201
            cust = c_res.json()
            cid = cust["id"]
            print(f"2. Customer Creation -> VERIFIED ({cust['name']} / ID: {cid})")

            # 3. Credit transaction
            tx1 = client.post(
                "/api/v1/transactions",
                json={"customer_id": cid, "amount": 1000.00, "type": "CREDIT", "description": "Wheat 25kg"},
            )
            assert tx1.status_code == 201
            print("3. Credit Transaction -> VERIFIED (INR 1000.00 Credit Added)")

            # 4. Payment transaction
            tx2 = client.post(
                "/api/v1/transactions",
                json={"customer_id": cid, "amount": 350.00, "type": "PAYMENT", "description": "Cash Received"},
            )
            assert tx2.status_code == 201
            print("4. Payment Transaction -> VERIFIED (INR 350.00 Payment Recorded)")

            # 5. Customer Balance Verification (1000 - 350 = 650)
            c_updated = client.get(f"/api/v1/customers/{cid}")
            assert c_updated.status_code == 200
            assert c_updated.json()["outstanding_balance"] == "650.00"
            assert c_updated.json()["total_credit"] == "1000.00"
            assert c_updated.json()["total_payment"] == "350.00"
            print("5. Balance Calculation -> VERIFIED (Outstanding Balance: INR 650.00)")

            # 6. Dashboard Summary Verification
            d_res = client.get("/api/v1/dashboard/summary")
            assert d_res.status_code == 200
            dash = d_res.json()
            assert dash["total_customers"] >= 1
            assert Decimal(dash["total_outstanding_credit"]) >= Decimal("650.00")
            print(f"6. Dashboard Summary -> VERIFIED (Total Customers: {dash['total_customers']}, Outstanding: INR {dash['total_outstanding_credit']})")

        # 7. WebSocket Voice Streaming Test
        asyncio.run(test_websocket(port))
        print("7. WebSocket Voice Stream Gateway -> VERIFIED")

        print("\nALL PHASE 2 BACKEND LIVE INTEGRATIONS VERIFIED AND OPERATIONAL!")

    finally:
        server.should_exit = True
        t.join(timeout=2)


if __name__ == "__main__":
    main()
