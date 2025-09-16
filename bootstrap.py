import discord

from cogs.music import MusicCog
from discord import app_commands
from discord.ext import commands

global TOKEN

try:
    with open('key.txt', 'r') as f:
        TOKEN = f.read().strip()
except:
    print('Key not found')

GUILD_ID = discord.Object(id=325753627224440833)
intents = discord.Intents.all()

class DiscordBot(commands.Bot):
    def __init__(self, *, intents, guild_id, **options):
        super().__init__(intents=intents, **options)

        self.guild_id = guild_id

    async def on_ready(self):
        print('Logged in as {0.user}'.format(self))

    async def setup_hook(self):
        await self.add_cog(MusicCog(self, guild_id=self.guild_id))

        await self.sync_commands()
    
    async def sync_commands(self):
        try:
            synced = await self.tree.sync(guild=GUILD_ID)
            print("Commands synced!: ", synced)
        except:
            print("Error syncing commands!")
    

bot = DiscordBot(intents=intents, guild_id=GUILD_ID, command_prefix='!')

bot.run(TOKEN)

 

