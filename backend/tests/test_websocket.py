import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from app.main import app
from app.core.websocket_manager import WebSocketManager

client = TestClient(app)


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager for testing"""
    with patch('app.api.websocket.routes.get_websocket_manager') as mock_get_manager:
        mock_manager = AsyncMock(spec=WebSocketManager)
        mock_get_manager.return_value = mock_manager
        yield mock_manager


class TestWebSocketEndpoints:
    """Test WebSocket endpoints"""

    def test_websocket_stats_endpoint(self, mock_websocket_manager):
        """Test WebSocket stats endpoint"""
        mock_stats = {
            "total_connections": 5,
            "channels": {
                "build_events": 2,
                "container_events": 3
            }
        }
        mock_websocket_manager.get_stats.return_value = mock_stats

        response = client.get("/api/ws/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_connections"] == 5
        assert "channels" in data

    def test_broadcast_message_endpoint(self, mock_websocket_manager):
        """Test broadcast message endpoint"""
        mock_websocket_manager.publish_event.return_value = 3

        response = client.post(
            "/api/ws/broadcast",
            params={"channel": "test_channel"},
            json={"type": "test", "message": "Hello World"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["recipients"] == 3
        assert data["channel"] == "test_channel"


class TestWebSocketConnectionManager:
    """Test WebSocket connection manager functionality"""

    @pytest.mark.asyncio
    async def test_connection_manager_connect(self):
        """Test WebSocket connection"""
        from app.core.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        connection_id = await manager.connect(mock_websocket, "test-id")

        assert connection_id == "test-id"
        assert "test-id" in manager.active_connections
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_manager_disconnect(self):
        """Test WebSocket disconnection"""
        from app.core.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        # First connect
        await manager.connect(mock_websocket, "test-id")

        # Then disconnect
        manager.disconnect("test-id")

        assert "test-id" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_connection_manager_subscribe(self):
        """Test channel subscription"""
        from app.core.websocket_manager import ConnectionManager
        from app.core.redis import redis_client

        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        with patch.object(redis_client, 'add_websocket_connection') as mock_redis:
            await manager.connect(mock_websocket, "test-id")
            success = await manager.subscribe_to_channel("test-id", "test-channel")

            assert success is True
            assert "test-channel" in manager.subscriptions["test-id"]
            assert "test-id" in manager.channel_subscribers["test-channel"]
            mock_redis.assert_called_once_with("test-channel", "test-id")

    @pytest.mark.asyncio
    async def test_connection_manager_send_message(self):
        """Test sending message to connection"""
        from app.core.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, "test-id")

        message = {"type": "test", "data": "hello"}
        success = await manager.send_personal_message("test-id", message)

        assert success is True
        mock_websocket.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self):
        """Test broadcasting to channel"""
        from app.core.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()

        # Connect two clients to same channel
        await manager.connect(mock_websocket1, "test-id-1")
        await manager.connect(mock_websocket2, "test-id-2")
        await manager.subscribe_to_channel("test-id-1", "test-channel")
        await manager.subscribe_to_channel("test-id-2", "test-channel")

        message = {"type": "broadcast", "data": "hello all"}
        sent_count = await manager.broadcast_to_channel("test-channel", message)

        assert sent_count == 2
        mock_websocket1.send_text.assert_called_once_with(json.dumps(message))
        mock_websocket2.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_connection_manager_handle_subscribe_message(self):
        """Test handling subscribe message"""
        from app.core.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, "test-id")

        subscribe_message = {
            "type": "subscribe",
            "channel": "test-channel"
        }

        with patch.object(manager, 'subscribe_to_channel') as mock_subscribe:
            with patch.object(manager, 'send_personal_message') as mock_send:
                await manager.handle_message("test-id", subscribe_message)

                mock_subscribe.assert_called_once_with("test-id", "test-channel")
                mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_manager_handle_ping_message(self):
        """Test handling ping message"""
        from app.core.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, "test-id")

        ping_message = {"type": "ping"}

        with patch.object(manager, 'send_personal_message') as mock_send:
            await manager.handle_message("test-id", ping_message)

            # Should send pong response
            args, kwargs = mock_send.call_args
            assert args[0] == "test-id"
            assert args[1]["type"] == "pong"


class TestWebSocketManager:
    """Test high-level WebSocket manager"""

    @pytest.mark.asyncio
    async def test_websocket_manager_initialization(self):
        """Test WebSocket manager initialization"""
        from app.core.websocket_manager import WebSocketManager

        manager = WebSocketManager()

        assert manager.connection_manager is not None

    @pytest.mark.asyncio
    async def test_websocket_manager_publish_event(self):
        """Test event publishing"""
        from app.core.websocket_manager import WebSocketManager
        from app.core.redis import redis_client

        manager = WebSocketManager()

        with patch.object(manager.connection_manager, 'broadcast_to_channel') as mock_broadcast:
            with patch.object(redis_client, 'publish_event') as mock_redis_publish:
                event_data = {"type": "test_event", "data": "test"}

                await manager.publish_event("test_channel", event_data)

                mock_broadcast.assert_called_once_with("test_channel", event_data)
                mock_redis_publish.assert_called_once_with("test_channel", event_data)

    def test_websocket_manager_get_stats(self):
        """Test getting WebSocket stats"""
        from app.core.websocket_manager import WebSocketManager

        manager = WebSocketManager()
        manager.connection_manager.active_connections = {"id1": None, "id2": None}
        manager.connection_manager.channel_subscribers = {
            "channel1": {"id1"},
            "channel2": {"id1", "id2"}
        }

        stats = manager.get_stats()

        assert stats["total_connections"] == 2
        assert stats["channels"]["channel1"] == 1
        assert stats["channels"]["channel2"] == 2


class TestWebSocketErrorHandling:
    """Test WebSocket error handling"""

    @pytest.mark.asyncio
    async def test_connection_manager_send_message_error(self):
        """Test handling send message error"""
        from app.core.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.send_text.side_effect = Exception("Connection lost")

        await manager.connect(mock_websocket, "test-id")

        message = {"type": "test", "data": "hello"}
        success = await manager.send_personal_message("test-id", message)

        # Should return False and remove the connection
        assert success is False
        assert "test-id" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_connection_manager_invalid_message(self):
        """Test handling invalid message format"""
        from app.core.websocket_manager import ConnectionManager

        manager = ConnectionManager()
        mock_websocket = AsyncMock()

        await manager.connect(mock_websocket, "test-id")

        # Send invalid message (missing type)
        invalid_message = {"data": "test"}

        with patch.object(manager, 'send_personal_message') as mock_send:
            await manager.handle_message("test-id", invalid_message)

            # Should not process the message but won't crash
            mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_websocket_integration():
    """Integration test for WebSocket functionality"""
    # This would be a more complex test that actually establishes WebSocket connections
    # and tests the full flow. For now, we'll keep it simple.
    pass