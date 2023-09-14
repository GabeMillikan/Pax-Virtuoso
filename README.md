# Pax-Virtuoso
This is an open-source ([MIT licensed](./LICENSE)) Discord bot that plays music. It's a sister to [Pax-Academia](https://github.com/Arborym/Pax-Academia) and is primarily developed for the [Homework Help Discord server](https://discord.gg/homework), but it will work great in your server too!

## Contributing
Anyone and everyone is more than welcome to contribute! Read [CONTRIBUTING.md](./CONTRIBUTING.md) to get started.

## Installation
1. Install dependencies with `pip`
    ```sh
    pip install -r requirements.txt
    ```
    or with [pip-tools](https://pypi.org/project/pip-tools/)
    ```sh
    pip install pip-tools
    pip-sync
    ```
2. Create and fill out `.env` (see [ENVIRONMENT.md](./ENVIRONMENT.md) for more details)
3. [Add the bot to your server.](https://discordpy.readthedocs.io/en/stable/discord.html#inviting-your-bot) Note that this bot requires the following permissions:
    - Read Messages/View Channels
    - Embed Links
    - Use Slash Commands
    - Connect
    - Speak
    - Use Voice Activity
    - Use External Sounds

    You can use this link to invite the bot (replace `{CLIENT_ID}` with its id):\
    `https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=35186556290048&scope=bot`
4. Run the bot
    ```sh
    python main.py
    ```
5. Listen to some tunes 🎶 (see [Usage](#Usage))

## Usage
TODO: list out all the commands and how to use them
