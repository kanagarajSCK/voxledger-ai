import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("voxledger.websocket")


class ConnectionManager:
    def __init__(self):
        # Active connections mapped by client id or session id
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}. Active: {len(self.active_connections)}")

    def disconnect(self, client_id: str) -> None:
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}. Active: {len(self.active_connections)}")

    async def send_json(self, client_id: str, message: dict) -> bool:
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
        return False

    async def broadcast(self, message: dict) -> None:
        for client_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                self.disconnect(client_id)


manager = ConnectionManager()
