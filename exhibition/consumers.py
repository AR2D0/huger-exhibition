import json
from typing import Any

from channels.generic.websocket import AsyncWebsocketConsumer


class CapacityConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.group_name = "capacity_updates"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:  # noqa: ARG002
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def capacity_update(self, event: dict[str, Any]) -> None:
        await self.send(text_data=json.dumps(event))

