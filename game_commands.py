import discord
import requests
import logging

from discord.ext import commands
from database import userCollection

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('my_bot')

# api endpoints
random_word_url = "https://random-word-api.vercel.app/api?words=1"
definition_url = "https://api.dictionaryapi.dev/api/v2/entries/en/"

# create bot
intents = discord.Intents.all()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix='$', intents=intents)


# figure out how to do the custom decorator function @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# get daily word
@bot.command(name="new")
async def daily_new_word(ctx):
    user_id = str(ctx.author.id)
    existing_user = userCollection.find_one({"id": user_id})

    if existing_user:
        word = get_random_word()  # get random word

        if word is not None:
            word_def = get_def(word)  # get definition for the word

            # check if word_def is not None before sending the message
            if word_def is not None:
                await ctx.send(f"Your new word is:`{word}`\n"
                               f"`{word_def}`")

                # store new word into users collection
                set_lang = existing_user.get("set_lang")
                store_word_users(userCollection, user_id, set_lang, word)

                # store new word into words collection ---------------------------------------------------
            else:
                await ctx.send("Failed to fetch a new word. Please try again later.")
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


# function to get the definition of the word using dictionary api
def get_def(word):
    word_url = definition_url + word

    try:
        definition_response = requests.get(url=word_url)
        definition_response.raise_for_status()  # grab http error code
        data = definition_response.json()

        # access definitions
        meanings = data[0]["meanings"]
        first_part_of_speech = meanings[0]["partOfSpeech"]
        first_definition = meanings[0]["definitions"][0]["definition"].lower().rstrip('.')

        result = (f"{first_part_of_speech}\n"
                  f"{first_definition}")
        print(f"successfully requested word definition")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Definition request exception: {e} \nError: Unable to fetch definition for '{word}'")
        return None
    except (IndexError, KeyError) as e:
        # Handle JSON parsing errors or missing data
        logging.error(f"JSON Parsing Error: {e} \nError: No definition found for '{word}'")
        return None
    except Exception as e:
        # Handle other unexpected errors
        logging.error(f"An unexpected error occurred: {e} \nError: An unexpected error occurred for '{word}'")
        return None
