import discord
import requests
import logging
import random

from discord.ext import commands
from database import userCollection

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a', format='%(asctime)s - %(name)s - '
                                                                                         '%(levelname)s - %(message)s')
logger = logging.getLogger('my_bot')

# api endpoints
random_word_url = "https://random-word-api.vercel.app/api?words=3"
definition_url = "https://api.dictionaryapi.dev/api/v2/entries/en/"

# create bot
intents = discord.Intents.all()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix='$', intents=intents)


# play the game
@bot.command(name="play")
async def new_game(ctx):
    user_id = ctx.author.id

    get_random_words()  # get random word


# function to return a randomly generated word using vercel api
def get_random_words():
    try:
        words = []
        random_word_response = requests.get(url=random_word_url)
        random_word_response.raise_for_status()  # grab http error code
        data = random_word_response.json()  # grab the random words
        print(f"generated words: {data}")
        words.extend(data)
        return words
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching random words: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None


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


# function to store new word into words_learned dictionary in users collection !!!!!!!!!!!!!!!!!!!!!!!!CHANGE THIS AFTER I IMPLEMENT GAME LOGIC
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


@bot.command(name="test")
async def testing(ctx):
    question = "hindered"
    descr1 = "xasdasdasdasdas"
    descr2 = "fasdjaskdjkajsd"
    descr3 = "asldjaksdjasd"
    lives = 3
    embed = interactive_embed(question, descr1, descr2, descr3, lives)

    # send embed with buttons
    await ctx.send(embed=embed)


# function to show question
def interactive_embed(word, descr1, descr2, descr3, remaining_lives):
    embed = discord.Embed()
    embed.title = f"Guess the meaning of this word"
    embed.description = f"**`{word}`**"
    embed.set_author(name="", icon_url="")
    embed.set_footer(text=f"Remaining Lives: {remaining_lives}", icon_url="")
    embed.set_image(url="")
    embed.add_field(name="Options:", value=f"1️⃣ {descr1}\n2️⃣ {descr2}\n3️⃣ {descr3}", inline=False)
    embed.color = 0xFF5733

    return embed
