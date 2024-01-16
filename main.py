
import asyncio
from gateway import discord_ws

# Run the connection
asyncio.get_event_loop().run_until_complete(discord_ws.connect())
