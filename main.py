import requests
import os
import discord
import pymongo
import logging
from discord.ext import commands
from dotenv import load_dotenv
from User import User # import user class
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# load env variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
USER = os.getenv("MONGO_USER")
PASSWORD = os.getenv("MONGO_PASSWORD")
HOST = os.getenv("MONGO_HOST")
DATABASE = os.getenv("DATABASE")
uri = f"mongodb+srv://{USER}:{PASSWORD}@{HOST}/{DATABASE}?retryWrites=true&w=majority"

# Create a new client and connect to the server
mongoClient = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    mongoClient.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = mongoClient[DATABASE]

# access collection user
userCollection = db["users"]

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('my_bot')

intents = discord.Intents.all()
intents.members = True
intents.messages = True

# create bot
bot = commands.Bot(command_prefix='$', intents=intents)

# Check if the token was loaded successfully
if not TOKEN:
    print("Error: Discord token not found in .env file")
else:
    print("Discord token loaded successfully")


# this is called when bot is ready to start being used
@bot.event
async def on_ready():
    print(f'we have logged in as {bot.user.name}')


# register user to database
@bot.command(name="register")
async def register(ctx):
    user_id = str(ctx.author.id)
    print("user's discord id:" + user_id)
    existing_user = userCollection.find_one({"id": user_id})

    if existing_user:
        print("user exists in database")
    else:
        # create new user document
        new_user_data = {
            "id":user_id,
            "languages": [],
            "words_learned": {}
        }
        # insert new user into users
        result = userCollection.insert_one(new_user_data)
        print(result)

        if result.acknowledged:
            print(f"successfully inserted {ctx.author} added with ID: {result.inserted_id}")
        else:
            print("failed to insert user data")
            logger.error(f"error inserting user data: {ctx.author}")


# list of commands
@bot.command(name='commands')
async def commands(ctx):
    # List all available commands
    command_list = [command.name for command in bot.commands]
    await ctx.send(f"Available commands: {', '.join(command_list)}")


# help
bot.remove_command('help')


@bot.command(name='help')
async def help_response(ctx):
    help_dm = f"How to use {bot.user.name}\n" \
              f"Commands used:\n" \
              f"$help: say hello to {bot.user.name}"

    try:
        await ctx.author.send(help_dm)
        await ctx.send(f"sent DM to {ctx.author.mention}")
    except discord.errors.HTTPException as e:
        logger.error(f"Error sending DM to {ctx.author}: {e}")


# say hello
@bot.command(name='hello')
async def say_hello(ctx):
    response = f'Hello, {ctx.author.mention}!'
    print('said hello')
    await ctx.send(response)


@bot.command(name="check")
async def check(ctx):
    print(ctx.author.name)
    print(ctx.author.id)
    print(ctx.author.name + " checked")


# get daily word
@bot.command(name="daily")
async def daily_new_word(ctx):
    pass

bot.run(TOKEN)
mongoClient.close()
