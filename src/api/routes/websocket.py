"""WebSocket routes for real-time content generation progress."""

import asyncio
import json
from typing import Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.models.content import ContentRequest, ContentStatus


router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize connection manager."""
        # content_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, content_id: str) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            content_id: Content ID to subscribe to
        """
        await websocket.accept()
        if content_id not in self.active_connections:
            self.active_connections[content_id] = []
        self.active_connections[content_id].append(websocket)
        logger.debug(f"WebSocket connected for content_id: {content_id}")

    def disconnect(self, websocket: WebSocket, content_id: str) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            content_id: Content ID the connection was subscribed to
        """
        if content_id in self.active_connections:
            if websocket in self.active_connections[content_id]:
                self.active_connections[content_id].remove(websocket)
            if not self.active_connections[content_id]:
                del self.active_connections[content_id]
        logger.debug(f"WebSocket disconnected for content_id: {content_id}")

    async def send_progress(self, content_id: str, data: dict[str, Any]) -> None:
        """Send progress update to all connections for a content_id.

        Args:
            content_id: Content ID
            data: Progress data to send
        """
        if content_id not in self.active_connections:
            return

        message = json.dumps(data, default=str)
        disconnected = []

        for connection in self.active_connections[content_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn, content_id)

    async def broadcast_all(self, data: dict[str, Any]) -> None:
        """Broadcast message to all connected clients.

        Args:
            data: Data to broadcast
        """
        message = json.dumps(data, default=str)
        for content_id in list(self.active_connections.keys()):
            for connection in self.active_connections[content_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass


# Global connection manager
manager = ConnectionManager()


class ProgressTracker:
    """Tracks and broadcasts content generation progress."""

    PHASES = [
        ("research", "researching", "Gathering information about the topic..."),
        ("planning", "planning", "Creating content outline..."),
        ("writing", "writing", "Writing the initial draft..."),
        ("editing", "editing", "Polishing and improving content..."),
        ("finalize", "completed", "Content generation complete!"),
    ]

    def __init__(self, content_id: str, topic: str):
        """Initialize progress tracker.

        Args:
            content_id: Content ID
            topic: Content topic
        """
        self.content_id = content_id
        self.topic = topic
        self.current_phase_idx = -1
        self.started_at = datetime.utcnow()
        self.phase_timings: dict[str, float] = {}

    async def start(self) -> None:
        """Start tracking and send initial message."""
        await manager.send_progress(
            self.content_id,
            {
                "type": "started",
                "content_id": self.content_id,
                "topic": self.topic,
                "status": "pending",
                "progress": 0,
                "message": "Starting content generation...",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def update_phase(self, phase: str, status: str | None = None) -> None:
        """Update current phase and broadcast progress.

        Args:
            phase: Phase name
            status: Optional status override
        """
        # Find phase index
        for idx, (phase_name, phase_status, phase_message) in enumerate(self.PHASES):
            if phase_name == phase:
                self.current_phase_idx = idx
                progress = int((idx + 1) / len(self.PHASES) * 100)

                await manager.send_progress(
                    self.content_id,
                    {
                        "type": "progress",
                        "content_id": self.content_id,
                        "phase": phase,
                        "status": status or phase_status,
                        "progress": progress,
                        "message": phase_message,
                        "phases_completed": idx,
                        "total_phases": len(self.PHASES),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                break

    async def complete(self, content: str | None = None) -> None:
        """Mark generation as complete.

        Args:
            content: Generated content (optional preview)
        """
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()

        await manager.send_progress(
            self.content_id,
            {
                "type": "completed",
                "content_id": self.content_id,
                "status": "completed",
                "progress": 100,
                "message": "Content generation complete!",
                "processing_time_seconds": elapsed,
                "content_preview": content[:500] if content else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def error(self, error_message: str, phase: str | None = None) -> None:
        """Report an error.

        Args:
            error_message: Error description
            phase: Phase where error occurred
        """
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()

        await manager.send_progress(
            self.content_id,
            {
                "type": "error",
                "content_id": self.content_id,
                "status": "failed",
                "progress": int((self.current_phase_idx + 1) / len(self.PHASES) * 100),
                "message": f"Error: {error_message}",
                "error": error_message,
                "failed_phase": phase,
                "processing_time_seconds": elapsed,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


# Registry for progress trackers
_progress_trackers: dict[str, ProgressTracker] = {}


def get_progress_tracker(content_id: str, topic: str | None = None) -> ProgressTracker:
    """Get or create a progress tracker for a content ID.

    Args:
        content_id: Content ID
        topic: Content topic (required for new trackers)

    Returns:
        ProgressTracker instance
    """
    if content_id not in _progress_trackers:
        if topic is None:
            topic = "Unknown topic"
        _progress_trackers[content_id] = ProgressTracker(content_id, topic)
    return _progress_trackers[content_id]


def remove_progress_tracker(content_id: str) -> None:
    """Remove a progress tracker.

    Args:
        content_id: Content ID
    """
    if content_id in _progress_trackers:
        del _progress_trackers[content_id]


@router.websocket("/ws/content/{content_id}")
async def websocket_content_progress(websocket: WebSocket, content_id: str):
    """WebSocket endpoint for real-time content generation progress.

    Clients connect to receive updates about a specific content generation job.

    Message types:
    - started: Generation has started
    - progress: Phase update with progress percentage
    - completed: Generation finished successfully
    - error: An error occurred

    Args:
        websocket: WebSocket connection
        content_id: Content ID to subscribe to
    """
    await manager.connect(websocket, content_id)

    try:
        # Send initial connection confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "content_id": content_id,
                    "message": "Connected to content generation progress stream",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

        # Keep connection open and handle incoming messages
        while True:
            try:
                # Wait for messages (ping/pong, or client commands)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,  # 30 second timeout for keepalive
                )

                # Handle client messages
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_text(
                            json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                        )
                    elif message.get("type") == "status":
                        # Client requesting current status
                        tracker = _progress_trackers.get(content_id)
                        if tracker:
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "status",
                                        "content_id": content_id,
                                        "phase_idx": tracker.current_phase_idx,
                                        "timestamp": datetime.utcnow().isoformat(),
                                    }
                                )
                            )
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_text(
                        json.dumps({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
                    )
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.debug(f"WebSocket client disconnected: {content_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {content_id}: {e}")
    finally:
        manager.disconnect(websocket, content_id)


@router.websocket("/ws/broadcast")
async def websocket_broadcast(websocket: WebSocket):
    """WebSocket endpoint for receiving all content generation updates.

    Useful for admin dashboards or monitoring tools.

    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()

    # Use a special "broadcast" channel
    broadcast_id = "__broadcast__"
    if broadcast_id not in manager.active_connections:
        manager.active_connections[broadcast_id] = []
    manager.active_connections[broadcast_id].append(websocket)

    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "message": "Connected to broadcast stream",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_text(
                    json.dumps({"type": "ping", "timestamp": datetime.utcnow().isoformat()})
                )

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, broadcast_id)
