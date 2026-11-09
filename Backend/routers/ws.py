from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from db.database import SessionLocal, Scan
from services.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/scans/{scan_id}")
async def scan_progress_ws(websocket: WebSocket, scan_id: int):
    await manager.connect(scan_id, websocket)
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan:
            await websocket.send_json({"type": "status", "status": scan.status.value})
        while True:
            # Keep the connection alive. The server pushes all useful events.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(scan_id, websocket)
    finally:
        db.close()
