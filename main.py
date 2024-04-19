import json

import discord
import discord.utils
from discord.ext import tasks, commands
from colorama import Fore
import platform
import asyncio

import config
import presets
from presets import print
import requests


intents = discord.Intents.all()
intents.typing = True
intents.presences = True
intents.members = True
intents.guilds = True


@tasks.loop(seconds=30)
async def status_loop():
    await client.wait_until_ready()

    api_url = 'https://api.api-ninjas.com/v1/facts?limit=1'
    response = requests.get(api_url, headers={'X-Api-Key': config.NINJAS_API_KEY})
    text = ""
    if response.status_code == requests.codes.ok and response.text and response.text[0] and response.text[0]:
        text = json.loads(response.text)[0]["fact"]
    else:
        print("Error:", response.status_code, response.text)

    await client.change_presence(status=discord.Status.idle,
                                 activity=discord.Activity(type=discord.ActivityType.watching,
                                                           name=f"🧐 {text} "))
    await asyncio.sleep(10)
    memberCount = 0
    for guild in client.guilds:
        memberCount += guild.member_count
    await client.change_presence(status=discord.Status.dnd,
                                 activity=discord.Activity(type=discord.ActivityType.listening,
                                                           name=f"{memberCount} people! 😀", ))
    await asyncio.sleep(10)


class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('.'), intents=discord.Intents().all())
        self.cogsList = ["cogs.schedule"]

    async def setup_hook(self):
        for ext in self.cogsList:
            await self.load_extension(ext)

    async def on_ready(self):
        print(" Logged in as " + Fore.YELLOW + self.user.name)
        print(" Bot ID " + Fore.YELLOW + str(self.user.id))
        print(" Discord Version " + Fore.YELLOW + discord.__version__)
        print(" Python version " + Fore.YELLOW + platform.python_version())
        print(" Syncing slash commands...")
        synced = await self.tree.sync()
        print(" Slash commands synced " + Fore.YELLOW + str(len(synced)) + " Commands")
        print(" Initializing status loop....")
        if not status_loop.is_running():
            status_loop.start()


client = Client()
client.run(presets.token)
