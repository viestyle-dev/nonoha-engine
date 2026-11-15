"""WebSocket host for nonoha_core.inspection.

One WebSocket per (client, graph): text frames carry JSON control operations
and notifications, binary frames carry samples. The core inspector decides
what to send and when (credits, budgets, pauses); this module only moves
messages. Outgoing messages go through a per-connection queue drained by one
sender task, so the inspector's ``send`` never blocks the event loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from nonoha_core.inspection import Inspector, InspectorFull, Limits

logger = logging.getLogger(__name__)

CLOSE_DISABLED = 4403
CLOSE_NO_GRAPH = 4404
CLOSE_TOO_MANY = 4429


def _json_default(value: Any):
    try:
        import numpy as np

        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    except ImportError:  # pragma: no cover
        pass
    return str(value)


class InspectorHost:
    def __init__(self, node_flow, enabled: bool, plugins: list[dict] | None = None, limits: Limits | None = None):
        self.enabled = enabled
        self._node_flow = node_flow
        self.inspector = (
            Inspector(resolve_graph=node_flow.get_graph, limits=limits, plugins=plugins or [])
            if enabled
            else None
        )

    async def handle(self, websocket: WebSocket, graph_name: str) -> None:
        await websocket.accept()
        if self.inspector is None:
            await websocket.close(code=CLOSE_DISABLED)
            return
        if self._node_flow.get_graph(graph_name) is None:
            await websocket.close(code=CLOSE_NO_GRAPH)
            return

        outbox: asyncio.Queue = asyncio.Queue()
        try:
            session = self.inspector.open_session(graph_name, outbox.put_nowait)
        except InspectorFull:
            await websocket.close(code=CLOSE_TOO_MANY)
            return

        sender = asyncio.create_task(self._drain(websocket, outbox))
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                text = message.get("text")
                if text is None:
                    continue  # binary from the client is not part of the protocol
                try:
                    op = json.loads(text)
                except ValueError:
                    outbox.put_nowait({"t": "error", "code": "bad_json", "message": "control frames must be JSON"})
                    continue
                if isinstance(op, dict):
                    self.inspector.handle(session, op)
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            self.inspector.close_session(session)
            sender.cancel()

    @staticmethod
    async def _drain(websocket: WebSocket, outbox: asyncio.Queue) -> None:
        try:
            while True:
                message = await outbox.get()
                if isinstance(message, (bytes, bytearray)):
                    await websocket.send_bytes(bytes(message))
                else:
                    await websocket.send_text(json.dumps(message, separators=(",", ":"), default=_json_default))
        except asyncio.CancelledError:
            pass
        except Exception as e:  # connection gone; the receive loop ends the session
            logger.debug("inspector sender stopped: %s", e)
