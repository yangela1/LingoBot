import asyncio

import discord
import requests
import logging
import random

from discord.ext import commands
from database import userCollection
from database import wordCollection
from MyView import MyView

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a',
                    format='%(asctime)s - %(name)s - ''%(levelname)s - %(message)s')

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

    # check if user has 1 or more lives
    silver, gold, lives = get_lives_and_coins(user_id)

    if lives < 1:
        await ctx.send(f"{ctx.author}, you have no more lives to play right now.")
        return

    question = generate_question()

    word = question["word"]
    correct_index = question["def_options"]["correct_index"]
    corDef = question["def_options"][f"option{correct_index + 1}"]
    # print(f"cordef {corDef}")

    embed, view = interactive_embed(ctx, word, question["def_options"]["option1"], question["def_options"]["option2"],
                                    question["def_options"]["option3"], lives, silver, gold, correct_index)

    print(question)

    message = await ctx.send(embed=embed, view=view)

    view.message = message

    res = await view.wait()  # wait for view to stop by timeout or manually stopping

    if res:
        print("timeout")

    # update words collection with word + def
    store_word_def(wordCollection, word, corDef)

    # update user collection
    if view.correct_or_not:
        print("correct answer guessed, update to db in progress")
        # get + 1 coin
        increment(userCollection, user_id, "coins", 1)

        # increment number of correct guesses + 1
        increment(userCollection, user_id, "correct_guess", 1)

        # store the learnt word
        store_word_users(userCollection, user_id, "English", word)
    elif not view.correct_or_not:
        print("incorrect answer guessed, update to db in progress")
        # decrement heart - 1
        increment(userCollection, user_id, "hearts", -1)

        # increment number of incorrect guesses + 1
        increment(userCollection, user_id, "incorrect_guess", 1)

        # store the incorrect word
        store_wrong_word_user(userCollection, user_id, word)


# function to return a randomly generated word using vercel api
def get_random_words():
    try:
        words = []
        random_word_response = requests.get(url=random_word_url)
        random_word_response.raise_for_status()  # grab http error code
        data = random_word_response.json()  # grab the random words
        print(f"generated words: {data}")
        words.extend(data)

        # Log the generated words
        with open("words.txt", 'a', encoding='utf-8') as file:
            file.write('\n' + ','.join(words) + '\n')
        logger.error(f"generated words: {data}")

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
        # sentences = first_definition.split('.')
        # first_sentence = sentences[0].strip()

        # split the sentence by phrases to only obtain the first phrase
        phrases = first_definition.split(';')
        first_phrase = phrases[0].strip()

        result = first_phrase.lower().rstrip(';.')
        # print(first_definition)
        # print(result)
        # print(f"successfully requested word definition")

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
    id_filter = {"discord_id": user_id}

    # attempt to get user's data
    result = userCollection.find_one(id_filter)

    silver = result.get("coins", None)
    gold = result.get("chal_coins", None)
    lives = result.get("hearts", None)
    return silver, gold, lives


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
            # Log the generated definitions
            with open("words.txt", 'a', encoding='utf-8') as file:
                file.write('\n'.join(definitions) + '\n')

            random.shuffle(definitions)

            correct_index = definitions.index(def_in_question)

            # question structure
            question = {
                "word": word_in_question,
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


# function to show question
def interactive_embed(ctx, word, descr1, descr2, descr3, remaining_lives, silver, gold, correct_index):
    embed = discord.Embed()
    embed.title = f"Guess the meaning of this word"
    embed.description = f"**`{word}`**"
    embed.set_author(name="", icon_url="")
    embed.set_image(url="")
    embed.add_field(name="Options:", value=f"1️⃣ {descr1}\n\n2️⃣ {descr2}\n\n3️⃣ {descr3}", inline=False)
    embed.add_field(name="", value=f"Kiwis: {silver} <:silver:1191744440113569833> {gold} <:gold:1191744402222223432>\n"
                                   f"Remaining lives: {remaining_lives}")
    embed.color = 0xFF5733

    view = MyView(ctx, correct_index)

    return embed, view


@bot.command(name="def")
# function that returns a definition
async def get_word_definition(ctx, *, word):
    # Use the provided word to fetch and print its definition
    definition = get_def(word)

    if definition:
        await ctx.send(f"Definition of `{word}`: {definition}")
    else:
        await ctx.send(f"Unable to retrieve the definition for `{word}`.")


# function that stores word into user collection
def store_word_users(users_collection, user_id, language, word):
    id_filter = {"discord_id": user_id}

    update_query = {
        "$push": {
            f"words_learned.{language}": word
        }
    }

    # attempt to update user's doc
    result = users_collection.update_one(id_filter, update_query)

    if result.modified_count > 0:
        print(f"Successfully added the word '{word}' to the user's words_learned in {language}.")
    else:
        print(f"Failed to add the word '{word}' to the user's words_learned in {language}.")
        logger.error(f"Failed to add the word '{word}' to the user's words_learned in {language}.")


# function that stores word into users collection
def store_wrong_word_user(users_collection, user_id, word):
    id_filter = {"discord_id": user_id}

    update_query = {
        "$push": {
            f"wrong_words": word
        }
    }

    # attempt to update user's doc
    result = users_collection.update_one(id_filter, update_query)

    if result.modified_count > 0:
        print(f"Successfully added the word '{word}' to the user's wrong_words.")
    else:
        print(f"Failed to add the word '{word}' to the user's wrong_words.")
        logger.error(f"Failed to add the word '{word}' to the user's wrong_words.")


# function that stores the word and definition into the Word collection
def store_word_def(words_collection, word, definition, translation=None):
    # check if document with given word exists
    existing_word = words_collection.find_one({"word": word})

    if existing_word is None:
        # attempt to create a new word doc
        new_word_def_data = {
            "word": word,
            "definition": definition,
            "translation": translation
        }

        # insert new word into the collection
        result = words_collection.insert_one(new_word_def_data)
        # print(result)

        if result.acknowledged:
            print(f"successfully inserted {word} into words collection")
        else:
            print("failed to insert word into dictionary")
            logger.error(f"error inserting word data: {word} {definition}")


# function that increments coins, guesses, and hearts for a user
def increment(users_collection, user_id, field, amount):
    id_filter = {"discord_id": user_id}

    # $inc operator in MongoDB is used to increment value of a field
    update_query = {
        "$inc": {
            field: amount
        }
    }

    result = users_collection.update_one(id_filter, update_query)

    if result.modified_count > 0:
        print(f"{field} incremented by {amount} for user {user_id}")
    else:
        print(f"user {user_id} not found, could not increment {field}")
        logger.error(f"error incrementing {field} for user {user_id}")
