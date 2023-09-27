# Environment

This repository uses [dotenv](https://pypi.org/project/python-dotenv/) to configure the bot. This allows all developers
to easily run different instances of the bot without dealing with git conflicts or revealing sensitive information (API keys).

In practice, this just means that you need to create a file called `.env` in the root of the repository.
For example, you would create a text file here:

```txt
Pax-Virtuoso/
├── abilities/
│   ├── __init__.py
│   └── music.py
├── bot.py
├── main.py
├── README.md
└── .env               <--- HERE
```

then, open the file in a text editor and fill out the required variables in the following format (replacing the example information with your own):

```txt
API_TOKEN=ASJD3KLFaLLsKSADFJ23KLSFD.ASkhjsfd.ASHJKDaADKSLJ_ASDsH12JH90JlpPASM23
```

Below, you can find a description of each variable.

# Variables

### `API_TOKEN`

This is the token that Discord provides on the "Applications" page under the "Bot" tab (right below your bot's username). Be careful not to share the token with anyone.

### `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`

The values passed to `spotipy.SpotifyClientCredentials`, used to access the Spotify API.
You can create your own spotify app on the developer page and get your own values from there.
Alternatively, you can just use the [public SpotDL app's values](https://github.com/spotDL/spotify-downloader/blob/920442e134292e892b762b4fdf7f69aeafc3c972/spotdl/utils/config.py#L252-L253) which works fine.

### `DEV_GUILD_ID`

The Guild ID in which development commands (see: [abilities/development.py](./abilities/development.py)) such as `/view-logs` and `/reboot` are enabled.
