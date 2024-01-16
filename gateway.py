import os
import json
import asyncio
import websockets
import requests
from dotenv import load_dotenv

load_dotenv("bot.env")


class DiscordWebSocket:
    """Creates a WebSocket for Discord's gateway"""

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE = 3
    VOICE_STATE = 4
    VOICE_PING = 5
    RESUME = 6
    RECONNECT = 7
    REQUEST_MEMBERS = 8
    INVALIDATE_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11
    GUILD_SYNC = 12

    HEARTBEAT_PAYLOAD = '{"op": 1, "d": null}'

    def __init__(self, token, gateway, heartbeat_interval):
        self.token = token
        self.gateway = gateway
        self.heartbeat_interval = heartbeat_interval
        self.websocket = None

    async def send_heartbeat(self):
        """Sends a heartbeat every 41250ms to keep the service running"""
        while True:
            await asyncio.sleep(self.heartbeat_interval / 1000)
            await self.websocket.send(self.HEARTBEAT_PAYLOAD)

    async def send_payload(self, data):
        """Sends a identify payload to the gateway"""
        await self.websocket.send(data)

    async def send_message(self, channel_id, message):
        endpoint = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        data = {
            "content": message
        }
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }

        response = requests.post(endpoint, json=data, headers=headers)

        if response.status_code == 200:
            print("Message sent")
        else:
            print(f"Failed. Code Returned: {response.status_code}, Response: {response.text}")

    async def connect(self):
        async with websockets.connect(self.gateway) as self.websocket:
            heartbeat_task = asyncio.create_task(self.send_heartbeat())
            data = json.dumps({
                "op": self.IDENTIFY,
                "d": {
                    "token": self.token,
                    "properties": {
                        '$os': 'linux',
                        '$browser': 'disco',
                        '$device': 'disco'
                    },
                    "intents": 7
                }
            })
            payload_task = asyncio.create_task(self.send_payload(data))
            try:
                while True:
                    result = await self.websocket.recv()
                    payload = json.loads(result)

                    if payload.get("op") != self.HEARTBEAT:
                        print("Received '%s' " % payload)
                        with open('received_reply.json', 'w') as json_file:
                            json.dump(payload, json_file, indent=4)
                            json_file.write('\n')
                    target_channel_id = os.getenv("TESTING_CHANNEL")
                    message = "Testing"
                    await self.send_message(target_channel_id, message)
            except Exception as e:
                print(f"Error {e}")
            finally:
                if self.websocket and not self.websocket.closed:
                    await self.websocket.close()

                if 'heartbeat_task' in locals() and not heartbeat_task.done:
                    heartbeat_task.cancel()


discord_bot_token = os.getenv("DISCORD_TOKEN")
discord_gateway = "wss://gateway.discord.gg/?v=10&encoding=json"
heartbeat_interval = 41250
discord_ws = DiscordWebSocket(discord_bot_token, discord_gateway, heartbeat_interval
                              )
