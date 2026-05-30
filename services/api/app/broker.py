"""Redis-backed publish/subscribe broker for mission realtime events.

Mission-room events (manual section 14.2) are fanned out over Redis pub/sub
so they reach every API instance's WebSocket clients (manual section 11:
"Redis ... WebSocket fan-out"). The broker is attached to ``app.state`` so
its client is created on the running event loop and torn down with the app.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger("rescue_net.broker")


def mission_channel(mission_id: Any) -> str:
    return f"mission:{mission_id}"


class Broker:
    """Thin wrapper over a Redis client for mission event fan-out."""

    def __init__(self, redis_url: str | None) -> None:
        self._redis_url = redis_url
        self._client: aioredis.Redis | None = None

    @property
    def enabled(self) -> bool:
        return self._redis_url is not None

    def _client_or_none(self) -> aioredis.Redis | None:
        if not self._redis_url:
            return None
        if self._client is None:
            self._client = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._client

    async def ping(self) -> bool:
        client = self._client_or_none()
        if client is None:
            return False
        try:
            return bool(await client.ping())
        except Exception:  # noqa: BLE001 - readiness probe must not raise
            return False

    async def publish(self, mission_id: Any, event_type: str, data: dict[str, Any]) -> None:
        """Publish a mission event. A no-op (logged) when Redis is unconfigured."""
        client = self._client_or_none()
        event = {"type": event_type, "mission_id": str(mission_id), "data": data}
        if client is None:
            logger.debug("redis not configured; dropping event %s", event_type)
            return
        try:
            await client.publish(mission_channel(mission_id), json.dumps(event, default=str))
        except Exception:  # noqa: BLE001 - publishing must not break the request
            logger.exception("failed to publish mission event %s", event_type)

    async def subscribe(
        self,
        mission_id: Any,
        *,
        on_ready: Callable[[], Awaitable[None]] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield decoded events published to the mission channel.

        ``on_ready`` (if given) is awaited once the subscription is registered
        but before any event is delivered, so callers can avoid a subscribe/
        publish race.
        """
        client = self._client_or_none()
        if client is None:
            return
        channel = mission_channel(mission_id)
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        if on_ready is not None:
            await on_ready()
        try:
            async for message in pubsub.listen():
                if message.get("type") == "message":
                    yield json.loads(message["data"])
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
