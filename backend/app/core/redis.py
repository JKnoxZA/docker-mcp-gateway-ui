import json
from datetime import timedelta
from typing import Any, Optional

import redis.asyncio as redis

from app.config.settings import settings


class RedisClient:
    """Redis client wrapper for async operations"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis server"""
        self.redis = redis.from_url(
            settings.REDIS_URL, password=settings.REDIS_PASSWORD, decode_responses=True
        )
        # Test connection
        await self.redis.ping()

    async def disconnect(self):
        """Disconnect from Redis server"""
        if self.redis:
            await self.redis.close()

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration"""
        if not self.redis:
            return False

        serialized_value = json.dumps(value) if not isinstance(value, str) else value
        return await self.redis.set(key, serialized_value, ex=expire)

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        if not self.redis:
            return None

        value = await self.redis.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def delete(self, key: str) -> bool:
        """Delete a key"""
        if not self.redis:
            return False

        return bool(await self.redis.delete(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False

        return bool(await self.redis.exists(key))

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        if not self.redis:
            return False

        return bool(await self.redis.expire(key, seconds))

    # Session management methods
    async def set_session(
        self, session_id: str, user_data: dict, expire_minutes: int = 30
    ):
        """Set user session data"""
        await self.set(f"session:{session_id}", user_data, expire=expire_minutes * 60)

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get user session data"""
        return await self.get(f"session:{session_id}")

    async def delete_session(self, session_id: str):
        """Delete user session"""
        await self.delete(f"session:{session_id}")

    # Build queue methods
    async def push_build_job(self, build_id: str, job_data: dict):
        """Push build job to queue"""
        if not self.redis:
            return False

        await self.redis.lpush(
            "build_queue", json.dumps({"build_id": build_id, **job_data})
        )
        await self.set(f"build:{build_id}", job_data, expire=3600)  # 1 hour

    async def pop_build_job(self) -> Optional[dict]:
        """Pop build job from queue"""
        if not self.redis:
            return None

        job_data = await self.redis.brpop("build_queue", timeout=1)
        if job_data:
            return json.loads(job_data[1])
        return None

    async def get_build_status(self, build_id: str) -> Optional[dict]:
        """Get build status"""
        return await self.get(f"build:{build_id}")

    async def update_build_status(self, build_id: str, status_data: dict):
        """Update build status"""
        await self.set(f"build:{build_id}", status_data, expire=3600)

    # WebSocket connection management
    async def add_websocket_connection(self, room: str, connection_id: str):
        """Add WebSocket connection to room"""
        if not self.redis:
            return False

        await self.redis.sadd(f"ws_connections:{room}", connection_id)

    async def remove_websocket_connection(self, room: str, connection_id: str):
        """Remove WebSocket connection from room"""
        if not self.redis:
            return False

        await self.redis.srem(f"ws_connections:{room}", connection_id)

    async def get_websocket_connections(self, room: str) -> list:
        """Get all WebSocket connections in room"""
        if not self.redis:
            return []

        connections = await self.redis.smembers(f"ws_connections:{room}")
        return list(connections)

    # Event publishing for real-time updates
    async def publish_event(self, channel: str, event_data: dict):
        """Publish event to channel"""
        if not self.redis:
            return False

        await self.redis.publish(channel, json.dumps(event_data))

    async def subscribe_to_channel(self, channel: str):
        """Subscribe to Redis channel"""
        if not self.redis:
            return None

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    # API caching methods
    async def cache_api_response(
        self, endpoint: str, params: str, response_data: Any, ttl: int = 900
    ):
        """Cache API response for 15 minutes by default"""
        cache_key = f"api_cache:{endpoint}:{params}"
        await self.set(cache_key, response_data, expire=ttl)

    async def get_cached_api_response(
        self, endpoint: str, params: str
    ) -> Optional[Any]:
        """Get cached API response"""
        cache_key = f"api_cache:{endpoint}:{params}"
        return await self.get(cache_key)


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency to get Redis client"""
    return redis_client


async def init_redis():
    """Initialize Redis connection"""
    await redis_client.connect()


async def close_redis():
    """Close Redis connection"""
    await redis_client.disconnect()
