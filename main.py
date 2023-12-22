import requests
import os
import discord
import pymongo
import logging
from discord.ext import commands
from dotenv import load_dotenv
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

# api endpoints
random_word_url = "https://random-word-api.vercel.app/api?words=1"

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
    print(f"user's discord id: {ctx.author.name} " + user_id)
    existing_user = userCollection.find_one({"id": user_id})


    if existing_user:
        print("user exists in database")
    else:
        # create new user document
        new_user_data = {
            "id":user_id,
            "languages": ["English"],
            "words_learned": {
                "English": []
            },
            "set_lang" : "English"
        }
        # insert new user into users
        result = userCollection.insert_one(new_user_data)
        print(result)

        if result.acknowledged:
            print(f"successfully inserted {ctx.author} added with ID: {result.inserted_id}")
            welcome_message = (
                f"Welcome, {ctx.author.mention}!\n\n"
                f"You are now ready to start learning a new language!\n"
                f"To start learning new words, use `$new`.\n"
                f"The default learning language is set to English. To set your preferred learning language,"
                f"use the `$set` command followed by the language name.\n"
                f"Example: `$set spanish` means you'll start learning new Spanish words.\n"
                f"Use `$help` or `$commands` to view additional commands."
            )
            await ctx.send(welcome_message)
        else:
            print("failed to insert user data")
            logger.error(f"error inserting user data: {ctx.author}")
            await ctx.send(f"Sorry! I couldn't add you to the game, try `$register` command again later.")


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
              f"`$help`: say hello to {bot.user.name}"

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


# check user discord id and name
@bot.command(name="check")
async def check(ctx):
    print(ctx.author.name)
    print(ctx.author.id)
    print(ctx.author.name + " checked")

# figure out how to do the custom decorator function @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# get daily word
@bot.command(name="new")
async def daily_new_word(ctx):
    user_id = str(ctx.author.id)
    existing_user = userCollection.find_one({"id": user_id})

    if existing_user:
        word = get_random_word()

        if word is not None:
            await ctx.send(f"Your new word is: `{word}`")

            # store new word into users collection
            set_lang = existing_user.get("set_lang")
            store_word_users(userCollection, user_id, set_lang, word)

            # store new word into words collection --------------------------------------------------------------------
        else:
            await ctx.send("Failed to fetch a new word. Please try again later.")
    else:
        print(
            f"{ctx.author.name} {ctx.author.id} rolled a new word but they are not registered in the database.")
        await ctx.send(f"{ctx.author.name} is not registered yet! Use the `$register` command to start learning.")


# function to return a randomly generated word using vercel api
def get_random_word():
    try:
        random_word_response = requests.get(url=random_word_url)
        random_word_response.raise_for_status()  # grab http error code
        data = random_word_response.json()[0]  # grab the random word
        print(f"generated word: {data}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching a random word: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None


# function to store new word into words_learned dictionary in users collection
def store_word_users(users_collection, user_id, language, word):
    id_filter = {"id": user_id}

    if language in users_collection.find_one(id_filter).get("words_learned", []):
        print(f"{language} is a valid language that the user set")
        update_query = {"$push": {f"words_learned.{language}": word}}

        # attempt to update user's doc
        result = users_collection.update_one(id_filter, update_query)
        if result.acknowledged:
            print(f"Successfully added the word '{word}' to the user's words_learned in {language}.")
        else:
            print(f"Failed to add the word '{word}' to the user's words_learned in {language}.")


# figure out how to do the custom decorator function @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# users can check their set language, english is default
@bot.command(name="lang")
async def what_is_my_lang(ctx):
    user_id = str(ctx.author.id)
    existing_user = userCollection.find_one({"id": user_id})

    if existing_user:
        set_lang = existing_user.get("set_lang")
        print(f"{ctx.author.name} {ctx.author.id} checked their set language: which is: {set_lang}")
        await ctx.send(f"Your set language is {set_lang}")
    else:
        print(f"{ctx.author.name} {ctx.author.id} checked their set language but they are not registered in the database.")
        await ctx.send(f"{ctx.author.name} is not registered yet! Use the `$register` command to start learning.")


bot.run(TOKEN)
mongoClient.close()
