"""WebSocket host for nonoha_core.inspection.

One WebSocket per (client, graph): text frames carry JSON control operations
and notifications, binary frames carry samples. The core inspector decides
what to send and when (credits, budgets, pauses); this module only moves
messages. Outgoing messages go through a per-connection outbox drained by one
sender task, so the inspector's ``send`` never blocks the event loop.

The outbox follows the inspector's rule that the latest value wins: a
pending activity or status message is replaced by a newer one instead of
queued behind it. Samples are bounded by the inspector's credits, and
replies by what the client sends; past ``OUTBOX_LIMIT`` messages the client
is taken to have stopped reading and its session ends.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from nonoha_core.inspection import Inspector, InspectorFull, Limits

logger = logging.getLogger(__name__)

CLOSE_DISABLED = 4403
CLOSE_NO_GRAPH = 4404
CLOSE_TOO_MANY = 4429

OUTBOX_LIMIT = 256
_REPLACED = ("activity", "status")  # kinds where only the newest pending one is sent


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


class OutboxFull(Exception):
    """The client stopped reading."""


class Outbox:
    """Messages for one client, in order, sent by one task (``drain``)."""

    __slots__ = ("_websocket", "_items", "_latest", "_ready", "_limit")

    def __init__(self, websocket: WebSocket, limit: int = OUTBOX_LIMIT):
        self._websocket = websocket
        self._items: deque[Any] = deque()
        self._latest: dict[str, dict] = {}
        self._ready = asyncio.Event()
        self._limit = limit

    def put(self, message: Any) -> None:
        """The inspector's ``send``: never blocks; ``OutboxFull`` when the
        client has stopped reading (the inspector then closes the session)."""
        if type(message) is dict:
            kind = message.get("t")
            if kind in _REPLACED:
                pending = kind in self._latest
                self._latest[kind] = message
                if pending:
                    return  # its place in the order is kept; the newest is sent
                message = kind  # a marker for the newest message of this kind
        if len(self._items) >= self._limit:
            self._items.clear()
            self._latest.clear()
            raise OutboxFull(f"more than {self._limit} messages waiting: the client is not reading")
        self._items.append(message)
        self._ready.set()

    async def drain(self) -> None:
        websocket = self._websocket
        items = self._items
        try:
            while True:
                if not items:
                    self._ready.clear()
                    await self._ready.wait()
                    continue
                item = items.popleft()
                if type(item) is str:
                    item = self._latest.pop(item)
                if type(item) is dict:
                    await websocket.send_text(json.dumps(item, separators=(",", ":"), default=_json_default))
                else:
                    await websocket.send_bytes(item)  # a sample frame (bytearray)
        except asyncio.CancelledError:
            pass
        except Exception as e:  # connection gone; the receive loop ends the session
            logger.debug("inspector sender stopped: %s", e)


class InspectorHost:
    def __init__(self, node_flow, enabled: bool, plugins: list[dict] | None = None, limits: Limits | None = None):
        self._node_flow = node_flow
        self.inspector = (
            Inspector(resolve_graph=node_flow.get_graph, limits=limits, plugins=plugins or [])
            if enabled
            else None
        )

    async def handle(self, websocket: WebSocket, graph_name: str) -> None:
        await websocket.accept()
        inspector = self.inspector
        if inspector is None:
            await websocket.close(code=CLOSE_DISABLED)
            return
        if self._node_flow.get_graph(graph_name) is None:
            await websocket.close(code=CLOSE_NO_GRAPH)
            return

        outbox = Outbox(websocket)
        try:
            session = inspector.open_session(graph_name, outbox.put)
        except InspectorFull:
            await websocket.close(code=CLOSE_TOO_MANY)
            return

        sender = asyncio.create_task(outbox.drain())
        try:
            while not session.closed:
                try:
                    message = await websocket.receive()
                except (WebSocketDisconnect, RuntimeError):
                    break  # the connection is gone
                if message.get("type") == "websocket.disconnect":
                    break
                text = message.get("text")
                if text is None:
                    continue  # binary from the client is not part of the protocol
                try:
                    op = json.loads(text)
                except ValueError:
                    try:
                        outbox.put({"t": "error", "code": "bad_json", "message": "control frames must be JSON"})
                    except OutboxFull:
                        break
                    continue
                if isinstance(op, dict):
                    try:
                        inspector.handle(session, op)
                    except Exception:
                        logger.exception("inspector operation failed; closing session")
                        break
                # A "close" operation, or an outbox that overflowed, closes
                # the session: the loop ends and so does the connection
        finally:
            inspector.close_session(session)
            sender.cancel()
            try:
                await websocket.close()
            except Exception:
                pass  # already closed by the client
