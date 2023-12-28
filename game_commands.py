import asyncio

import discord
import requests
import logging
import random

from discord.ui import Button, View
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

    question = generate_question()
    correct_index = question["def_options"]["correct_index"]

    lives, coins = get_lives_and_coins(user_id)

    embed, view = interactive_embed(question["word"], question["def_options"]["option1"], question["def_options"]["option2"],
                              question["def_options"]["option3"], lives, coins)

    print(question)

    await ctx.send(embed=embed, view=view)


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

        first_definition = meanings[0]["definitions"][0]["definition"]

        # split the definitions by sentences
        sentences = first_definition.split('.')
        first_sentence = sentences[0].strip()

        # split the sentence by phrases to only obtain the first phrase
        phrases = first_sentence.split(';')
        first_phrase = phrases[0].strip()

        result = first_phrase.lower().rstrip(';.')
        # print(first_definition)
        # print(result)
        print(f"successfully requested word definition")
        return result

    except requests.exceptions.RequestException as e:
        print("unable to request word def")
        logger.error(f"Definition request exception: {e} \nError: Unable to fetch definition for '{word}'")
        return None
    except (IndexError, KeyError) as e:
        # Handle JSON parsing errors or missing data
        print("unable to request word def")
        logging.error(f"JSON Parsing Error: {e} \nError: No definition found for '{word}'")
        return None
    except Exception as e:
        # Handle other unexpected errors
        print("unable to request word def")
        logging.error(f"An unexpected error occurred: {e} \nError: An unexpected error occurred for '{word}'")
        return None


# function that returns user's lives and coins
def get_lives_and_coins(user_id):
    user = userCollection.find_one({"discord_id": user_id})

    lives = user.get("hearts", None)
    coins = user.get("coins", None)
    return lives, coins


# function to create questions
def generate_question():
    max_attempts = 5
    attempt = 0

    while attempt < max_attempts:
        word_bank = get_random_words()  # grab 3 random words
        word_in_question = word_bank[0]
        word_for_def1 = word_bank[1]
        word_for_def2 = word_bank[2]

        def_in_question = get_def(word_in_question)  # grab definition of those words
        other_def1 = get_def(word_for_def1)
        other_def2 = get_def(word_for_def2)

        definitions = [def_in_question, other_def1, other_def2]

        if all(definition is not None for definition in definitions):
            random.shuffle(definitions)

            correct_index = definitions.index(def_in_question)

            # question structure
            question = {
                "word" : word_in_question,
                "def_options": {
                    "option1": definitions[0],
                    "option2": definitions[1],
                    "option3": definitions[2],
                    "correct_index": correct_index
                }
            }

            return question
        attempt += 1

    # else exceeded maximum attempts without finding valid defs
    print("could not generate question")
    logger.error("Could not generate question")
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
    coins = 2
    embed = interactive_embed(question, descr1, descr2, descr3, lives, coins)

    # send embed with buttons
    await ctx.send(embed=embed)


# function to show question
def interactive_embed(word, descr1, descr2, descr3, remaining_lives, coin_avail):
    embed = discord.Embed()
    embed.title = f"Guess the meaning of this word"
    embed.description = f"**`{word}`**"
    embed.set_author(name="", icon_url="") # SET AUTHOR TO THE PERSON WHO TRIGGERED COMMAND
    embed.set_footer(text=f"LingoCoins: {coin_avail}   Remaining Lives: {remaining_lives}", icon_url="")
    embed.set_image(url="")
    embed.add_field(name="Options:", value=f"1️⃣ {descr1}\n\n2️⃣ {descr2}\n\n3️⃣ {descr3}", inline=False)
    embed.color = 0xFF5733

    # create a view and add a button
    view = discord.ui.View()
    button1 = discord.ui.Button(style=discord.ButtonStyle.secondary, emoji="1️⃣", custom_id="0")
    button2 = discord.ui.Button(style=discord.ButtonStyle.secondary, emoji="2️⃣", custom_id="1")
    button3 = discord.ui.Button(style=discord.ButtonStyle.secondary, emoji="3️⃣", custom_id="2")
    view.add_item(button1)
    view.add_item(button2)
    view.add_item(button3)

    return embed, view

@bot.command()
async def button(ctx):
    button = Button(label="click me", style=discord.ButtonStyle.green)

    async def button_callback(interaction):
        await interaction.response.send_message("hi!")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send("hi", view=view)





