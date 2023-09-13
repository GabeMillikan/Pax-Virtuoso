from discord import Interaction

from bot import client, tree


@tree.command(description="Get the bot's ping time to Discord")
async def ping(interaction: Interaction) -> None:
    await interaction.response.send_message(
        f"Pong! My ping time to Discord is {client.latency * 1000:.0f} milliseconds."
    )
