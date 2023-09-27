import discord

from config import dev_guild_id

intents = discord.Intents.none()

intents.guilds = True
intents.voice_states = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:
    await tree.sync()
    await tree.sync(guild=discord.Object(dev_guild_id))
