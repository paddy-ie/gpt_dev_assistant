import asyncio
import logging
from collections import defaultdict
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)


class TelemetryHub:
    def __init__(self) -> None:
        self._subscribers: dict[int, Set[asyncio.Queue[Dict[str, Any]]]] = defaultdict(set)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def publish(self, run_id: int, payload: Dict[str, Any]) -> None:
        if not self._loop:
            return

        def _dispatch() -> None:
            queues = list(self._subscribers.get(run_id, []))
            if not queues:
                return
            for queue in queues:
                try:
                    queue.put_nowait(payload)
                except asyncio.QueueFull:
                    logger.warning("Telemetry queue full for run %s", run_id)

        self._loop.call_soon_threadsafe(_dispatch)

    async def subscribe(self, run_id: int) -> asyncio.Queue[Dict[str, Any]]:
        if not self._loop:
            self._loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1000)
        self._subscribers[run_id].add(queue)
        return queue

    def unsubscribe(self, run_id: int, queue: asyncio.Queue[Dict[str, Any]]) -> None:
        subscribers = self._subscribers.get(run_id)
        if not subscribers:
            return
        subscribers.discard(queue)
        if not subscribers:
            self._subscribers.pop(run_id, None)


_hub: Optional[TelemetryHub] = None


def get_telemetry_hub() -> TelemetryHub:
    global _hub
    if _hub is None:
        _hub = TelemetryHub()
    return _hub
