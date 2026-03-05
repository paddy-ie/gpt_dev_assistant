from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.db.session import get_session
from app.security.jwt import get_jwt_manager
from app.services.run_service import RunService
from app.telemetry import get_telemetry_hub

router = APIRouter(prefix="/ws", tags=["telemetry"])


@router.websocket("/runs/{run_id}")
async def stream_run_events(websocket: WebSocket, run_id: int) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    jwt_manager = get_jwt_manager()
    try:
        payload = jwt_manager.decode_token(token)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    subject = payload.get("sub")
    if subject is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user_id = int(subject)
    with get_session() as session:
        service = RunService(session)
        run = service.get_run(run_id)
        if not run or run.owner_id != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        history = service.list_events(run_id, limit=500)
    await websocket.accept()
    for event in history:
        await websocket.send_json(event.model_dump())
    hub = get_telemetry_hub()
    queue = await hub.subscribe(run_id)
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(run_id, queue)
