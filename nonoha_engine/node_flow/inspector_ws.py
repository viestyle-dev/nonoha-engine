"""WebSocket host for nonoha_core.inspection.

One WebSocket per (client, graph): text frames carry JSON control operations
and notifications, binary frames carry samples. The core inspector decides
what to send and when (credits, budgets, pauses); this module only moves
messages. Outgoing messages go through a per-connection outbox drained by one
sender task, so the inspector's ``send`` never blocks the event loop.

The outbox follows the inspector's rule that the latest value wins: a
pending status message is replaced by a newer one, and a pending activity
message absorbs the newer one's rows (rows are changes only, so none may be
dropped). Samples are bounded by the inspector's credits, and replies by
what the client sends; past ``OUTBOX_LIMIT`` messages the client is taken to
have stopped reading and its session ends.

When the inspector ends a session (a client that stopped reading or
acknowledging), the outbox closes the connection, which ends the receive
loop as well.
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
CLOSE_ENDED = 4408  # the engine ended the session: the client stopped reading or acknowledging
CLOSE_TOO_MANY = 4429

OUTBOX_LIMIT = 256


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

    __slots__ = ("_websocket", "_items", "_latest", "_ready", "_limit", "_close_code")

    def __init__(self, websocket: WebSocket, limit: int = OUTBOX_LIMIT):
        self._websocket = websocket
        self._items: deque[Any] = deque()
        self._latest: dict[str, dict] = {}
        self._ready = asyncio.Event()
        self._limit = limit
        self._close_code: int | None = None

    def put(self, message: Any) -> None:
        """The inspector's ``send``: never blocks; ``OutboxFull`` when the
        client has stopped reading (the inspector then ends the session)."""
        if self._close_code is not None:
            return  # closing: nothing more goes out
        kind = message.get("t") if type(message) is dict else None
        if kind == "activity" or kind == "status":
            pending = self._latest.get(kind)
            self._latest[kind] = message if pending is None or kind == "status" else _merged_rows(pending, message)
            if pending is not None:
                return  # the pending one keeps its place in the order and goes out as the newest
            message = kind  # a marker for the pending message of this kind
        if len(self._items) >= self._limit:
            self._items.clear()
            self._latest.clear()
            raise OutboxFull(f"more than {self._limit} messages waiting: the client is not reading")
        self._items.append(message)
        self._ready.set()

    def close(self, code: int = CLOSE_ENDED) -> None:
        """The session ended (the inspector's ``on_close``): drop what waits
        and close the connection, which ends the host's receive loop."""
        if self._close_code is None:
            self._close_code = code
            self._items.clear()
            self._latest.clear()
            self._ready.set()

    async def drain(self) -> None:
        websocket = self._websocket
        items = self._items
        try:
            while True:
                if self._close_code is not None and not items:
                    await websocket.close(code=self._close_code)
                    return
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


def _merged_rows(pending: dict, newer: dict) -> dict:
    """Activity rows are changes only: the newer message with the pending
    rows it does not replace (the newest row per port). Only a client that
    reads slower than the rounds come gets here."""
    rows = {row[0]: row for row in pending["p"]}
    for row in newer["p"]:
        rows[row[0]] = row
    return {**newer, "p": list(rows.values())}


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
            session = inspector.open_session(graph_name, outbox.put, outbox.close)
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
                    op = None
                if type(op) is dict:
                    inspector.handle(session, op)
                else:
                    inspector.reject(session, "bad_json", "control frames must be JSON objects")
                # A "close" operation ends the session, and so the loop. A
                # session the inspector ends (a client that stopped reading
                # or acknowledging) is closed by the outbox, which ends the
                # receive above.
        finally:
            inspector.close_session(session)
            sender.cancel()
            try:
                await websocket.close()
            except Exception:
                pass  # already closed
