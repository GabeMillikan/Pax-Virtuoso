import discord

intents = discord.Intents.none()

# so that when someone plays a song, we can check what voice channel they're in
intents.voice_states = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
