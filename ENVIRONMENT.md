# Environment
This repository uses [dotenv](https://pypi.org/project/python-dotenv/) to configure the bot. This allows all developers
to easily run different instances of the bot without dealing with git conflicts or revealing sensitive information (API keys).

In practice, this just means that you need to create a file called `.env` in the root of the repository.
For example, you would create a text file here:
```
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
```
API_TOKEN=ASJD3KLFaLLsKSADFJ23KLSFD.ASkhjsfd.ASHJKDaADKSLJ_ASDsH12JH90JlpPASM23
```
Below, you can find a description of each variable.

# Variables
### `API_TOKEN`
This is the token that Discord provides on the "Applications" page under the "Bot" tab (right below your bot's username). Be careful not to share the token with anyone.
