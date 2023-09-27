from __future__ import annotations

import asyncio
import io
import subprocess
import sys
from pathlib import Path

from discord import File, Interaction, Object, app_commands

from bot import client, tree
from config import dev_guild_id


@tree.command(
    name="git-pull",
    description="Runs `git pull`.",
    guild=Object(dev_guild_id),
)
async def git_pull(interaction: Interaction) -> None:
    await interaction.response.defer(ephemeral=True)

    git_pull = await asyncio.subprocess.create_subprocess_exec("git", "pull")
    stdout, stderr = await git_pull.communicate()

    if git_pull.returncode not in {0, 1}:
        await interaction.followup.send(
            f"`git pull` failed with return code {git_pull.returncode}",
            files=[
                File(io.BytesIO(stdout), filename="stdout.log"),
                File(io.BytesIO(stderr), filename="stderr.log"),
            ],
        )
        return

    await interaction.followup.send(
        "Success! Consider using `/reboot` to reboot the bot.",
    )


@tree.command(
    description="Shuts down the bot. On production, `cron` should start the bot back up.",
    guild=Object(dev_guild_id),
)
async def shutdown(interaction: Interaction) -> None:
    await interaction.response.send_message("Shutting down.", ephemeral=True)
    await client.close()


@tree.command(
    description="Shuts down and re-starts the bot.",
    guild=Object(dev_guild_id),
)
async def reboot(interaction: Interaction) -> None:
    await interaction.response.send_message("Rebooting.", ephemeral=True)

    try:
        await client.close()
    finally:
        subprocess.Popen(  # noqa
            [sys.executable, "cron/start.py", "force"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


LOG_FILES = [
    Path("cron") / "stdout.log",
    Path("cron") / "stderr.log",
]


@tree.command(
    name="view-logs",
    description="Shuts down and re-starts the bot.",
    guild=Object(dev_guild_id),
)
@app_commands.choices()
async def view_logs(interaction: Interaction, line_count: int | None = None) -> None:
    await interaction.response.defer(ephemeral=True)

    files: list[File] = []

    for log_file in LOG_FILES:
        with log_file.open("rb") as f:
            if line_count is None:
                data = f.read()
            else:
                last_n_lines: list[bytes] = []

                for line in f:
                    last_n_lines.append(line)
                    if len(last_n_lines) > line_count:
                        del last_n_lines[0]

                data = b"".join(last_n_lines)

            files.append(File(io.BytesIO(data), filename=log_file.name))

    await interaction.followup.send(files=files)
