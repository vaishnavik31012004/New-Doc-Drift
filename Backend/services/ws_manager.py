"""
Keeps track of WebSocket clients subscribed to a given scan_id and lets
background tasks push live agent-progress events to them.
"""
import asyncio
import json
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket


class ScanWebSocketManager:
    def __init__(self):
        self._connections: Dict[int, List[WebSocket]] = defaultdict(list)
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, scan_id: int, ws: WebSocket):
        await ws.accept()
        self._connections[scan_id].append(ws)

    def disconnect(self, scan_id: int, ws: WebSocket):
        if ws in self._connections[scan_id]:
            self._connections[scan_id].remove(ws)

    async def _broadcast(self, scan_id: int, payload: dict):
        dead = []
        for ws in self._connections.get(scan_id, []):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(scan_id, ws)

    def broadcast_threadsafe(self, scan_id: int, payload: dict):
        """Safe to call from a background thread (not the event loop)."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast(scan_id, payload), self._loop)


manager = ScanWebSocketManager()
