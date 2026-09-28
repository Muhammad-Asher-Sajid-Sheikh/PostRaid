import os
import discord
import httpx
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load configuration from environment variables
BOT_TOKEN = os.getenv("POSTRAID_DISCORD_ALERT_BOT", "YOUR_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("POSTRAID_DISCORD_CHANNEL_ID", "123456789012345678"))
USER_ID = int(os.getenv("POSTRAID_DISCORD_USER_ID", "123456789012345678"))


# --- OUTBOUND HELPER ---
async def send_to_channel(content: str) -> bool:
    """Sends text to your private Discord channel."""
    channel = bot.get_channel(CHANNEL_ID) or await bot.fetch_channel(CHANNEL_ID)
    if channel:
        await channel.send(content)
        return True
    return False


# --- INBOUND WEBSOCKET LISTENER ---
@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by the bot itself or other users
    if message.author.bot or message.author.id != USER_ID:
        return

    # Forward the message payload as an HTTP POST request to your FastAPI endpoint
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                "http://127.0.0.1:8000/receive-message",
                json={
                    "author": message.author.name,
                    "content": message.content,
                    "channel_id": str(message.channel.id),
                },
            )
        except Exception as e:
            print(f"Error forwarding message to /receive-message endpoint: {e}")


async def start_bot():
    await bot.start(BOT_TOKEN)