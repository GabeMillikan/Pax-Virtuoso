from discord import Interaction, app_commands

from bot import tree


@tree.command(description="Plays a song")
@app_commands.describe(name="The name of the song.")
async def play(interaction: Interaction, name: str) -> None:
    """
    TODO: Implement & document this command
    """
    await interaction.response.send_message(
        f"Hello {interaction.user.mention}! Now playing: {name}"
    )
