import discord

intents = discord.Intents.none()

intents.guilds = True
intents.voice_states = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready() -> None:
    await tree.sync()
