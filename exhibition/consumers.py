import json
from typing import Any

from channels.generic.websocket import AsyncWebsocketConsumer


class CapacityConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        if self.scope["user"].is_anonymous:
            print("کاربر ناشناس سعی در اتصال به WebSocket داشت")
            await self.close()
            return

        self.group_name = "capacity_updates"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"کاربر {self.scope['user'].username} به گروه capacity_updates متصل شد")

    async def disconnect(self, close_code: int) -> None:
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"کاربر {self.scope['user'].username} از WebSocket قطع شد (کد: {close_code})")

    async def capacity_update(self, event: dict[str, Any]) -> None:
        print(f"پیام capacity_update به کاربر {self.scope['user'].username} ارسال می‌شود: {event}")
        await self.send(text_data=json.dumps(event))