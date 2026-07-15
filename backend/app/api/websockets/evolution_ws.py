"""
WebSocket for real-time evolution streaming.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class EvolutionWebSocketManager:
    """
    Manages WebSocket connections for real-time evolution updates.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.engine = None  # will be set

    def set_engine(self, engine):
        self.engine = engine

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected, total {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        # Broadcast to all connections
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"WebSocket send failed: {e}")
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def handle_client(self, websocket: WebSocket):
        """
        Handle client lifecycle: receives commands, streams evolution.
        """
        await self.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                except Exception:
                    msg = {"type": data}

                msg_type = msg.get("type", "")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "start":
                    problem = msg.get("problem", "Solve a complex reasoning problem and evolve.")
                    # Start engine stream in background
                    if self.engine:
                        asyncio.create_task(self._stream_evolution(websocket, problem))
                    else:
                        await websocket.send_json({"type": "error", "message": "Engine not initialized"})

                elif msg_type == "stop":
                    if self.engine:
                        result = self.engine.stop()
                        await websocket.send_json({"type": "stopped", "data": result})
                    else:
                        await websocket.send_json({"type": "error", "message": "No engine"})

                elif msg_type == "get_state":
                    if self.engine:
                        state = self.engine.get_current_state()
                        await websocket.send_json({"type": "state", "data": state})

                elif msg_type == "resume":
                    if self.engine:
                        res = self.engine.resume()
                        await websocket.send_json({"type": "resumed", "data": res})

        except WebSocketDisconnect:
            self.disconnect(websocket)
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.disconnect(websocket)

    async def _stream_evolution(self, websocket: WebSocket, problem: str):
        if not self.engine:
            return
        try:
            async for result in self.engine.run_forever(problem):
                # Send to requesting client
                await websocket.send_json({"type": "generation", "data": result})
                # Also broadcast to others
                await self.broadcast({"type": "generation_broadcast", "data": {"generation": result.get("generation"), "fitness": result.get("evolution", {}).get("winner_eval", {}).get("fitness", 0)}})
                if self.engine.should_stop:
                    break
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass


# Global singleton
manager = EvolutionWebSocketManager()


def get_ws_manager() -> EvolutionWebSocketManager:
    return manager
