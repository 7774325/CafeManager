import json
from channels.generic.websocket import AsyncWebsocketConsumer

class KaraokeStaffConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.outlet_id = self.scope['url_route']['kwargs']['outlet_id']
        self.room_group_name = f'staff_alerts_{self.outlet_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """When the ordering station sends JSON, send it to the monitor."""
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "order_alert_event",
                "data": data
            }
        )

    async def order_alert_event(self, event):
        """Sends data to the browser monitor."""
        await self.send(text_data=json.dumps(event['data']))