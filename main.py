import requests
import os
import discord
import pymongo
from discord.ext import commands
from dotenv import load_dotenv
from User import User # import user class

intents = discord.Intents.all()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='$', intents=intents)

# load env variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Check if the token was loaded successfully
if not TOKEN:
    print("Error: Discord token not found in .env file")
else:
    print("Discord token loaded successfully")

# global vars
BOT_NAME = "language_bot"

# this is called when bot is ready to start being used
@bot.event
async def on_ready():
    print(f'we have logged in as {bot.user.name}')

# when bot receives a message, the on_message() event is called
@bot.command(name='hello')
async def say_hello(ctx):
    response = f'Hello, {ctx.author.mention}!'
    print('said hello')
    await ctx.send(response)

bot.run(TOKEN)


