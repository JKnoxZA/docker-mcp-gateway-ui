import json
import logging
import uuid
from typing import Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        # Connection subscriptions (connection_id -> set of channels)
        self.subscriptions: Dict[str, Set[str]] = {}
        # Channel subscribers (channel -> set of connection_ids)
        self.channel_subscribers: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str = None) -> str:
        """Accept a new WebSocket connection"""
        if connection_id is None:
            connection_id = str(uuid.uuid4())

        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()

        logger.info(f"WebSocket connection {connection_id} established")
        return connection_id

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            # Remove from all channels
            if connection_id in self.subscriptions:
                for channel in self.subscriptions[connection_id]:
                    if channel in self.channel_subscribers:
                        self.channel_subscribers[channel].discard(connection_id)
                        if not self.channel_subscribers[channel]:
                            del self.channel_subscribers[channel]

            # Remove connection
            del self.active_connections[connection_id]
            del self.subscriptions[connection_id]

            logger.info(f"WebSocket connection {connection_id} disconnected")

    async def subscribe_to_channel(self, connection_id: str, channel: str):
        """Subscribe a connection to a channel"""
        if connection_id not in self.active_connections:
            return False

        # Add to connection subscriptions
        self.subscriptions[connection_id].add(channel)

        # Add to channel subscribers
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        self.channel_subscribers[channel].add(connection_id)

        # Also subscribe in Redis for persistence
        await redis_client.add_websocket_connection(channel, connection_id)

        logger.info(f"Connection {connection_id} subscribed to channel {channel}")
        return True

    async def unsubscribe_from_channel(self, connection_id: str, channel: str):
        """Unsubscribe a connection from a channel"""
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].discard(channel)

        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(connection_id)
            if not self.channel_subscribers[channel]:
                del self.channel_subscribers[channel]

        # Remove from Redis
        await redis_client.remove_websocket_connection(channel, connection_id)

        logger.info(f"Connection {connection_id} unsubscribed from channel {channel}")

    async def send_personal_message(self, connection_id: str, message: dict):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
                return False
        return False

    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast a message to all subscribers of a channel"""
        if channel not in self.channel_subscribers:
            return 0

        sent_count = 0
        disconnected_connections = []

        for connection_id in self.channel_subscribers[channel].copy():
            if connection_id in self.active_connections:
                try:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_text(json.dumps(message))
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)

        return sent_count

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all active connections"""
        sent_count = 0
        disconnected_connections = []

        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
                sent_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected_connections.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.disconnect(connection_id)

        return sent_count

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)

    def get_channel_subscriber_count(self, channel: str) -> int:
        """Get number of subscribers for a channel"""
        return len(self.channel_subscribers.get(channel, set()))

    def get_connection_channels(self, connection_id: str) -> List[str]:
        """Get all channels a connection is subscribed to"""
        return list(self.subscriptions.get(connection_id, set()))

    async def handle_message(self, connection_id: str, message: dict):
        """Handle incoming WebSocket message"""
        try:
            message_type = message.get("type")

            if message_type == "subscribe":
                channel = message.get("channel")
                if channel:
                    await self.subscribe_to_channel(connection_id, channel)
                    await self.send_personal_message(
                        connection_id,
                        {
                            "type": "subscription_confirmed",
                            "channel": channel,
                            "timestamp": str(uuid.uuid4()),
                        },
                    )

            elif message_type == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    await self.unsubscribe_from_channel(connection_id, channel)
                    await self.send_personal_message(
                        connection_id,
                        {
                            "type": "unsubscription_confirmed",
                            "channel": channel,
                            "timestamp": str(uuid.uuid4()),
                        },
                    )

            elif message_type == "ping":
                await self.send_personal_message(
                    connection_id,
                    {
                        "type": "pong",
                        "timestamp": str(uuid.uuid4()),
                    },
                )

            elif message_type == "get_status":
                await self.send_personal_message(
                    connection_id,
                    {
                        "type": "status",
                        "connection_id": connection_id,
                        "subscribed_channels": self.get_connection_channels(connection_id),
                        "total_connections": self.get_connection_count(),
                        "timestamp": str(uuid.uuid4()),
                    },
                )

        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self.send_personal_message(
                connection_id,
                {
                    "type": "error",
                    "message": "Invalid message format",
                    "timestamp": str(uuid.uuid4()),
                },
            )


class WebSocketManager:
    """High-level WebSocket manager with Redis integration"""

    def __init__(self):
        self.connection_manager = ConnectionManager()

    async def start_redis_subscriber(self):
        """Start Redis subscriber for cross-process event distribution"""
        try:
            # Subscribe to all event channels
            channels = [
                "build_events",
                "container_events",
                "system_events",
                "health_alerts",
            ]

            for channel in channels:
                pubsub = await redis_client.subscribe_to_channel(channel)
                if pubsub:
                    # Start background task to handle messages
                    import asyncio
                    asyncio.create_task(self._handle_redis_messages(pubsub, channel))

            logger.info("Redis WebSocket subscriber started")

        except Exception as e:
            logger.error(f"Failed to start Redis subscriber: {e}")

    async def _handle_redis_messages(self, pubsub, channel: str):
        """Handle messages from Redis pub/sub"""
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        await self.connection_manager.broadcast_to_channel(
                            channel, event_data
                        )
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")

        except Exception as e:
            logger.error(f"Error in Redis message handler for {channel}: {e}")

    async def connect(self, websocket: WebSocket) -> str:
        """Connect a new WebSocket client"""
        return await self.connection_manager.connect(websocket)

    def disconnect(self, connection_id: str):
        """Disconnect a WebSocket client"""
        self.connection_manager.disconnect(connection_id)

    async def handle_websocket_communication(self, websocket: WebSocket, connection_id: str):
        """Handle WebSocket communication lifecycle"""
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle the message
                await self.connection_manager.handle_message(connection_id, message)

        except WebSocketDisconnect:
            self.disconnect(connection_id)
        except json.JSONDecodeError:
            await self.connection_manager.send_personal_message(
                connection_id,
                {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": str(uuid.uuid4()),
                },
            )
        except Exception as e:
            logger.error(f"Error in WebSocket communication: {e}")
            self.disconnect(connection_id)

    async def publish_event(self, channel: str, event_data: dict):
        """Publish an event to a channel"""
        # Broadcast to local connections
        await self.connection_manager.broadcast_to_channel(channel, event_data)

        # Publish to Redis for cross-process distribution
        await redis_client.publish_event(channel, event_data)

    def get_stats(self) -> dict:
        """Get WebSocket connection statistics"""
        return {
            "total_connections": self.connection_manager.get_connection_count(),
            "channels": {
                channel: self.connection_manager.get_channel_subscriber_count(channel)
                for channel in self.connection_manager.channel_subscribers.keys()
            },
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """Dependency to get WebSocket manager"""
    return websocket_manager