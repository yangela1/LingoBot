import requests
import os
import discord
import pymongo
from discord.app_commands import commands
from dotenv import load_dotenv
from User import User # import user class

intents = discord.Intents.all()
intents.members = True
intents.messages = True

client = discord.Client(intents=intents)

# load env variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Check if the token was loaded successfully
if not TOKEN:
    print("Error: Discord token not found in .env file")
else:
    print("Discord token loaded successfully")

# this is called when bot is ready to start being used
@client.event
async def on_ready():
    print(f"we have logged in as {client.user}!)")


# when bot receives a message, the on_message() event is called
@client.event
async def on_message(message):
    prefix = '$'
    hello_message = "hello"
    help_message = "help"

    if message.author == client.user:
        return # ignore message sent by bot itself

    if message.content.lower() == prefix + hello_message:
        await say_hello(message)

    if message.content.lower() == prefix + help_message:
        await give_help(message)


async def say_hello(message):
    await message.channel.send(f'Hello, {message.author.mention}!')

async def give_help(message):
    help_dm = f'Commands to type:/n' \
              f'$hello: say hello!'
    help_chat = f'DM sent!'

    await message.channel.send(help_chat)
    # send user dm --------------------------------------------------------------------------------------------


client.run(TOKEN)


