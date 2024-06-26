import re
import os
import datetime

import discord
import requests
import logging
import random

from discord.ext import commands

from database import userCollection
from database import wordCollection
from database import wordOfTheDayCollection
from embeds import interactive_embed
from embeds import wotd_embed
from embeds import image_embed
from GameConstants import GameConstants
from LingoRoles import lingo_roles

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a',
                    format='%(asctime)s - %(name)s - ''%(levelname)s - %(message)s')

logger = logging.getLogger('my_bot')

# api endpoints
random_word_url = "https://random-word-api.vercel.app/api?words=3"
words_api_url = "https://wordsapiv1.p.rapidapi.com/words/"
translate_url = "https://google-translate113.p.rapidapi.com/api/v1/translator/"
pexels_url = "https://api.pexels.com/v1/search"

# create bot
intents = discord.Intents.all()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix='$', intents=intents)

# global variables
current_word = None
current_view = None
current_translated_word = None
game_starter = None

hard_languages = {
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Swedish": "sv"
}

# headers
words_headers = {
    "X-RapidAPI-Key": os.getenv("X_RAPIDAPIKEY"),
    "X-RapidAPI-Host": os.getenv("X_RAPIDHOST_WORDS")
}

translate_headers = {
    "X-RapidAPI-Key": os.getenv("X_RAPIDAPIKEY"),
    "X-RapidAPI-Host": os.getenv("X_RAPIDHOST_TRANSLATE"),
    "content-type": "application/x-www-form-urlencoded",
}

pexel_headers = {
    "Authorization": os.getenv("PEXELS_KEY")
}


# play the game
@bot.command(name="play")
async def new_game(ctx):
    # check if a game is already in session
    global current_view, game_starter
    game_starter = ctx.author.id

    if current_view and not current_view.stopped:
        await ctx.send("A game is already in process. Finish the current game.")
        return

    user_id = ctx.author.id
    guild_id = ctx.guild.id

    # check if user has 1 or more lives
    silver, gold, lives = get_lives_and_coins(guild_id, user_id)

    if lives < 1:
        await ctx.send(f"**{ctx.author}**, you have no more lives to play right now.")
        return

    question = generate_question()
    word = question["word"]  # current game word

    global current_word
    current_word = word  # set global word

    correct_index = question["def_options"]["correct_index"]
    corDef = question["def_options"][f"option{correct_index + 1}"]
    # print(f"cordef {corDef}")

    embed, view = interactive_embed(ctx, word, question["def_options"]["option1"], question["def_options"]["option2"],
                                    question["def_options"]["option3"], lives, silver, gold, correct_index,
                                    False)
    print(question)

    current_view = view  # set global view

    message = await ctx.send(embed=embed, view=view)
    view.message = message
    res = await view.wait()  # wait for view to stop by timeout or manually stopping
    print(view.requiz)
    if res:
        print("timeout")
        view.correct_or_not = 'N'  # set to incorrect

    # update words collection with word + def
    store_word_def(wordCollection, word, corDef)

    # update user collection
    if view.correct_or_not == 'Y':
        print("correct answer guessed, update to db in progress".upper())
        # get + silvers
        increment(userCollection, guild_id, user_id, "coins", GameConstants.PLAY_W_SILVER)

        # increment number of correct guesses + 1
        increment(userCollection, guild_id, user_id, "correct_guess", 1)

        # store the learnt word
        store_word_users(userCollection, guild_id, user_id, "English", word)
    elif view.correct_or_not == 'N':
        print("incorrect answer guessed, update to db in progress".upper())
        # decrement heart - 1
        increment(userCollection, guild_id, user_id, "hearts", -1)

        # increment number of incorrect guesses + 1
        increment(userCollection, guild_id, user_id, "incorrect_guess", 1)

        # store the incorrect word
        store_wrong_word_user(userCollection, guild_id, user_id, word)
    elif view.correct_or_not == 'P':
        print("passed word")
        print(view.correct_or_not)

    # update lingo role
    await update_role_based_on_score(ctx, guild_id, user_id)


@bot.command(name="chal")
async def new_challenge(ctx):
    # check if a game is already in session
    global current_view, game_starter
    game_starter = ctx.author.id

    if current_view and not current_view.stopped:
        await ctx.send("A game is already in process. Finish the current game.")
        return

    user_id = ctx.author.id
    guild_id = ctx.guild.id

    # check if user has 1 or more lives
    silver, gold, lives = get_lives_and_coins(guild_id, user_id)

    if lives < 1:
        await ctx.send(f"**{ctx.author}**, you have no more lives to play right now.")
        return

    question = generate_question()

    # grab a random language to translate the word into
    language, code = get_random_language()

    word = question["word"]  # current game word

    # put the word through translate api
    translation = translate_word(word, "en", code)
    # print(f"translated word `{word}` is `{translation}`")

    global current_word
    current_word = word  # set global word
    print(f"word: {word}")

    global current_translated_word
    current_translated_word = translation  # set global translated word

    correct_index = question["def_options"]["correct_index"]
    corDef = question["def_options"][f"option{correct_index + 1}"]
    # print(f"cordef {corDef}")

    print(f"langueage: {language}")
    embed, view = interactive_embed(ctx, current_word, question["def_options"]["option1"],
                                    question["def_options"]["option2"], question["def_options"]["option3"],
                                    lives, silver, gold, correct_index, True, language=language,
                                    translation=current_translated_word)
    print(question)

    current_view = view  # set global view

    message = await ctx.send(embed=embed, view=view)
    view.message = message
    res = await view.wait()  # wait for view to stop by timeout or manually stopping

    if res:
        print("timeout")
        view.correct_or_not = 'N'

    # update words collection with word + def + translation
    store_word_def(wordCollection, word, corDef, language, translation)

    # update user collection
    if view.correct_or_not == 'Y':
        print("correct answer guessed, update to db in progress".upper())
        # get + silvers
        increment(userCollection, guild_id, user_id, "coins", GameConstants.CHAL_W_SILVER)

        # get + gold
        increment(userCollection, guild_id, user_id, "chal_coins", GameConstants.CHAL_W_GOLD)

        # increment number of correct guesses + 1
        increment(userCollection, guild_id, user_id, "correct_guess", 1)

        # increment number of challenge complete + 1
        increment(userCollection, guild_id, user_id, "chal_complete", 1)

        # store the learnt word
        store_word_users(userCollection, guild_id, user_id, language, translation)
    elif view.correct_or_not == 'N':
        print("incorrect answer guessed, update to db in progress".upper())
        # decrement heart - 1
        increment(userCollection, guild_id, user_id, "hearts", -1)

        # increment number of incorrect guesses + 1
        increment(userCollection, guild_id, user_id, "incorrect_guess", 1)

        # store the incorrect word
        store_wrong_word_user(userCollection, guild_id, user_id, translation)
    elif view.correct_or_not == 'P':
        print("passed challenge")

    # update lingo role
    await update_role_based_on_score(ctx, guild_id, user_id)


# function that chooses a random hard mode language
def get_random_language():
    result = random.choice(list(hard_languages.items()))
    key, value = result
    # print(f"random language: {key} {value}")
    return key, value


# function that returns the code to use in Google Translate api
def get_code(language):
    api_url = translate_url + "support-languages"
    try:
        response = requests.get(url=api_url, headers=translate_headers)
        response.raise_for_status()
        data = response.json()
        target_code = None
        lowercase_language = language.lower()
        for entry in data:
            if lowercase_language in entry["language"].lower():
                target_code = entry["code"]
                break

        if target_code is not None:
            print(f"the code for {language} is: {target_code}")
        else:
            print(f"could not find target code for {language}")
            logger.error(f"could not find target code for {language}")

        return target_code
    except Exception as e:
        print(f"An error occurred while fetching target code for {language}")
        logger.error(f"An error occurred while fetching target code for {language} {e}")
        return None


# function that returns the translated word
def translate_word(word, source_code, target_code):
    api_url = f"{translate_url}text"

    payload = {
        "from": source_code,
        "to": target_code,
        "text": word
    }

    try:
        response = requests.post(url=api_url, data=payload, headers=translate_headers)
        response.raise_for_status()
        data = response.json()
        # print(data)
        translation = data["trans"]
        # print(f"translation of {word} is {translation}")
        return translation.lower()
    except Exception as e:
        print(f"An error occurred while translating the word '{word}' into code '{target_code}'")
        logger.error(f"An error occurred while translating the word {word}, code {target_code} {e}")
        return None


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
    api_url = f"{words_api_url}{word}/definitions"

    try:
        definition_response = requests.get(url=api_url, headers=words_headers)
        definition_response.raise_for_status()  # grab http error code
        data = definition_response.json()

        # access definitions
        meanings = data["definitions"]

        first_definition = meanings[0]["definition"]
        # print(first_definition)
        return first_definition
    except requests.exceptions.RequestException as e:
        # print("unable to request word def")
        logger.error(f"Definition request exception: {e} \nError: Unable to fetch definition for '{word}'")
        return None
    except (IndexError, KeyError) as e:
        # Handle JSON parsing errors or missing data
        # print("unable to request word def")
        logging.error(f"JSON Parsing Error: {e} \nError: No definition found for '{word}'")
        return None
    except Exception as e:
        # Handle other unexpected errors
        # print("unable to request word def")
        logging.error(f"An unexpected error occurred: {e} \nError: An unexpected error occurred for '{word}'")
        return None


# function that gets the synonym of the word
def get_syn():
    global current_word

    api_url = f"{words_api_url}{current_word}/synonyms"

    try:
        response = requests.get(url=api_url, headers=words_headers)
        response.raise_for_status()  # grab http error code
        data = response.json()["synonyms"]

        synonym = random.choice(data)
        return synonym
    except Exception as e:
        # Handle other unexpected errors
        print("unable to request word synonym")
        logging.error(f"An unexpected error occurred: {e} Synonym for {current_word} cannot be fetched.")
        return None


@bot.command(name="hint")
async def get_hint(ctx):
    print(f"{ctx.author.name} used a hint command")
    global current_view, game_starter

    # check if a game is in progress
    if current_word is None or current_view is None or current_view.stopped:
        await ctx.send("You need to start a game first. Use `$play` or `$chal`.")
        return

    # check if user running command is the same user who started the game
    if ctx.author.id != game_starter:
        await ctx.send("You can only use hints if you started the game.")
        return

    # check if it is a requiz
    if current_view.requiz is True:
        await ctx.send("You cannot use a hint in a re-quiz.")
        return

    # check if user has enough coins
    is_challenge = current_view.challenge

    user_id = ctx.author.id
    guild_id = ctx.guild.id
    silver, gold, lives = get_lives_and_coins(guild_id, user_id)

    if is_challenge and silver < GameConstants.CHAL_HINT_SILVERCOST:
        await ctx.send(
            f"You do not have enough coins. A challenge hint costs {GameConstants.CHAL_HINT_SILVERCOST} <:silver:1191744440113569833>.")
        return
    elif not is_challenge and silver < GameConstants.PLAY_HINT_SILVERCOST:
        await ctx.send(
            f"You do not have enough coins. A play hint costs {GameConstants.PLAY_HINT_SILVERCOST} <:silver:1191744440113569833>.")
        return

    # determine which word to display based on game mode
    word_to_display = current_translated_word if current_view.challenge else current_word

    # provide user with a hint
    synonym = get_syn()
    if synonym:
        await ctx.send(f"Hint: A synonym for `{word_to_display}` in English is `{synonym}`.\n"
                       f"**{ctx.author.name}** -{GameConstants.CHAL_HINT_SILVERCOST if current_view.challenge else GameConstants.PLAY_HINT_SILVERCOST} "
                       f"<:silver:1191744440113569833>")
        if is_challenge:
            increment(userCollection, guild_id, user_id, "coins", -GameConstants.CHAL_HINT_SILVERCOST)
        else:
            increment(userCollection, guild_id, user_id, "coins", -GameConstants.PLAY_HINT_SILVERCOST)
    else:
        await ctx.send(f"Sorry! Kiwi is unable to provide a hint at this time.")


# function that returns user's lives and coins
def get_lives_and_coins(guild_id, user_id):
    # attempt to get user's data
    result = userCollection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})

    user_data = result["users"].get(str(user_id), {})
    # print(f"user data {user_data}")
    silver = user_data.get("coins", None)
    gold = user_data.get("chal_coins", None)
    lives = user_data.get("hearts", None)
    return silver, gold, lives


# function to create questions
def generate_question(word=None, definition=None):
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

        if word is not None and definition is not None:
            word_in_question = word
            def_in_question = definition

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


@bot.command(name="def")
# function that returns a definition
async def get_word_definition(ctx, *, args: str = ""):
    error_message = "Invalid input. Use `$def <word>` to get the definition."
    # Check if the user provided any arguments
    if not args.strip():
        await ctx.send(error_message)
        return

    words = args.split()

    if len(words) != 1:
        await ctx.send(error_message)
        return

    # Use the provided word to fetch and print its definition
    word = words[0]

    # Check if the word contains only alphabetical characters using reg expressions
    if not re.match("^[a-zA-Z]+$", word):
        await ctx.send(error_message)
        return

    definition, language, english_word = get_def_first_check_database(word)

    if definition:
        await ctx.send(f"Definition of `{word}`: {definition}")
    else:
        await ctx.send(f"Kiwi is confused and was unable to retrieve the definition for `{word}`.")


def get_def_first_check_database(word):
    # first check if the word definition is stored in the database before fetching
    existing_word = wordCollection.find_one({"$or": [{"word": word}, {"translation": word}]})

    if existing_word:
        definition = existing_word.get("definition")
        language = existing_word.get("language", None)
        english_word = existing_word.get("word")
        print(f"found in db. the definition of {word} is {definition}")
    else:
        definition = get_def(word)
        language = None
        english_word = word
    if definition:
        print(f"Definition of `{word}`: {definition}")
    else:
        print(f"Kiwi is confused and was unable to retrieve the definition for `{word}`.")

    return definition, language, english_word

@bot.command(name="gamble")
async def gamble_coin(ctx, *, input_str: str = ""):
    kiwi_message = f"Invalid input. Use `$gamble <positive number>` to start gambling."

    # Check if input_str is empty or consists only of whitespace
    if not input_str.strip():
        await ctx.send(kiwi_message)
        return

    # Split the input string into words
    words = input_str.split()

    # Check if there are more than one word in the input
    if len(words) > 1:
        await ctx.send(kiwi_message)
        return

    # check to see if input has only digits
    if not words[0].isdigit():
        await ctx.send(kiwi_message)
        return

    amount = int(words[0])

    user_id = ctx.author.id
    guild_id = ctx.guild.id
    # get silvers from db
    silver, gold, lives = get_lives_and_coins(guild_id, user_id)

    # they want to gamble more than they have
    if amount > silver:
        await ctx.send(f"You only have {silver} <:silver:1191744440113569833> to gamble.")
        return

    # they aren't gambling anything
    if amount == 0:
        await ctx.send(kiwi_message)
        return

    try:
        # generate random number between 0 to 2 times the input amount
        random_int = random.randint(0, amount * 2)
        result = random_int - amount
        print(f"random int = {random_int}, result = {result}")

        # make changes to database with resulting number
        increment(userCollection, guild_id, user_id, "coins", result)

        # get silvers from db
        silver, gold, lives = get_lives_and_coins(guild_id, user_id)

        string = f"You have {silver} <:silver:1191744440113569833>."

        if result > 0:
            await ctx.send(f"Congrats! You won +{result} <:silver:1191744440113569833>.\n{string}")
        elif result == 0:
            await ctx.send(f"You did not win or lose any <:silver:1191744440113569833>.\n{string}")
        else:
            await ctx.send(f"Bad luck! You lost -{abs(result)} <:silver:1191744440113569833>.\n{string}")
    except ValueError as ve:
        print(f"Invalid input: {ve}")
        await ctx.send(kiwi_message)
    except Exception as e:
        print(f"Error updating database: {e}")
        await ctx.send("Sorry, slots machine broke. Try again!")


# function that stores word into user collection
def store_word_users(users_collection, guild_id, user_id, language, word):
    # attempt to get user's data
    result = users_collection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})

    existing_user = result["users"].get(str(user_id), {})

    if existing_user:
        # check if word already exists in database
        words_learned = existing_user.get("words_learned", {}).get("English", [])

        if word not in words_learned:
            # word doesn't exist in user's dictionary, add it

            update_query = {
                "$push": {
                    f"users.{user_id}.words_learned.{language}": word
                }
            }

            # attempt to update user's doc
            result = users_collection.update_one(result, update_query)

            if result.modified_count > 0:
                print(f"Successfully added the word '{word}' to the user's words_learned in {language}.")
            else:
                print(f"Failed to add the word '{word}' to the user's words_learned in {language}.")
                logger.error(f"Failed to add the word '{word}' to the user's words_learned in {language}.")
        else:
            print(f"word already exists in user's dictionary, word: {word}")
    else:
        print(f"user {user_id} not found")
        logger.error(f"user {user_id} not found while trying to store word in user's dictionary")


# function that stores word into users collection
def store_wrong_word_user(users_collection, guild_id, user_id, word):
    guild_query = users_collection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})

    existing_user = guild_query["users"].get(str(user_id), {})

    if existing_user:
        # check if word already exists in database
        wrong_words = existing_user.get("wrong_words", [])

        if word not in wrong_words:
            # word doesn't exist in user's dictionary, add it

            update_query = {
                "$push": {
                    f"users.{user_id}.wrong_words": word
                }
            }

            # attempt to update user's doc
            result = users_collection.update_one(guild_query, update_query)

            if result.modified_count > 0:
                print(f"Successfully added the word '{word}' to the user's wrong_words.")
            else:
                print(f"Failed to add the word '{word}' to the user's wrong_words.")
                logger.error(f"Failed to add the word '{word}' to the user's wrong_words.")


# function that stores the word and definition into the Word collection
def store_word_def(words_collection, word, definition, language=None, translation=None):
    # check if document with given word exists
    existing_word = words_collection.find_one({"word": word})

    if existing_word is None:
        # attempt to create a new word doc
        new_word_def_data = {
            "word": word,
            "definition": definition,
        }

        if translation is not None:
            new_word_def_data["translation"] = translation
            new_word_def_data["language"] = language

        # insert new word into the collection
        result = words_collection.insert_one(new_word_def_data)
        # print(result)

        if result.acknowledged:
            print(f"successfully inserted {word} into words collection")
        else:
            print("failed to insert word into dictionary")
            logger.error(f"error inserting word data: {word} {definition}")


# function that increments coins, guesses, and hearts for a user
def increment(users_collection, guild_id, user_id, field, amount):
    result = users_collection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})

    if field == "hearts":
        update_query = {
            "$inc": {
                f"users.{user_id}.{field}": amount,
            },
            "$set": {
                f"users.{user_id}.last_reset_time": datetime.datetime.utcnow()
            }
        }
        print("\tupdated last reset time")
    else:
        # $inc operator in MongoDB is used to increment value of a field
        update_query = {
            "$inc": {
                f"users.{user_id}.{field}": amount
            }
        }

    try:
        result = users_collection.update_one(result, update_query)

        if result.matched_count == 0:
            print(f"user {user_id} not found, could not increment {field}")
            logger.error(f"Error incrementing {field} for user {user_id}")
            raise ValueError(f"User {user_id} not found")

        print(f"\t{field} incremented by {amount} for user {user_id}")
    except Exception as e:
        print(f"Error updating database: {e}")
        logger.error(f"Error updating database: {e}")
        raise


@bot.command(name="buylife")
async def buy_life_command(ctx):
    user_id = ctx.author.id
    guild_id = ctx.guild.id

    # get gold and lives from database
    silver, gold, lives = get_lives_and_coins(guild_id, user_id)

    if lives >= GameConstants.MAX_LIVES:
        await ctx.send("You have max lives already. Purchase cancelled.")
        return

    if gold < GameConstants.HEART_GOLDCOST:
        await ctx.send(f"You do not have enough gold. "
                       f"A life costs {GameConstants.HEART_GOLDCOST} <:gold:1191744402222223432>. Purchase cancelled.")
        return

    print(f"user bought heart")
    # decrement gold
    increment(userCollection, guild_id, user_id, "chal_coins", -GameConstants.HEART_GOLDCOST)

    # increment life
    increment(userCollection, guild_id, user_id, "hearts", 1)

    await ctx.send(f"Purchase successful!\n"
                   f"**{ctx.author.name}** -{GameConstants.HEART_GOLDCOST} <:gold:1191744402222223432>, "
                   f"+1 life")


@bot.command(name="pass")
async def pass_word_command(ctx):
    user_id = ctx.author.id
    guild_id = ctx.guild.id

    print(f"{ctx.author.name} used a pass")
    global current_view, game_starter

    # check if a game is in progress
    if current_word is None or current_view is None or current_view.stopped:
        await ctx.send("You need to start a game first. Use `$play` or `$chal`.")
        return

    # check if user running command is the same user who started the game
    if ctx.author.id != game_starter:
        await ctx.send("You can only use a pass if you started the game.")
        return

    # check if requiz
    if current_view.requiz is True:
        await ctx.send("You cannot pass during a re-quiz.")
        return

    # get gold and lives from database
    silver, gold, lives = get_lives_and_coins(guild_id, user_id)

    if silver >= 3:
        increment(userCollection, guild_id, user_id, "coins", -GameConstants.PASS_SILVERCOST)

        # stop the current view
        current_view.correct_or_not = 'P'
        current_view.stop()

        # send message
        await ctx.send(f"Current word passed. Starting a new game...\n"
                       f"**{ctx.author.name}** -{GameConstants.PASS_SILVERCOST} <:silver:1191744440113569833>")

        if current_view.challenge:
            await new_challenge(ctx)
        else:
            await new_game(ctx)
    else:
        await ctx.send(f"You do not have enough silver to use a pass. A pass costs {GameConstants.PASS_SILVERCOST}"
                       f"<:silver:1191744440113569833>.")


# function that returns a new word and definition
def generate_word_of_the_day():
    try:
        words = get_random_words()

        if not words:
            raise ValueError("No words retrieved.")

        definition = None
        i = 0
        while not definition and i < len(words):
            word = words[i]
            definition = get_def(word)
            i += 1

        if definition:
            print(f"{word}: {definition}")
            # Log the generated definitions
            with open("words.txt", 'a', encoding='utf-8') as file:
                file.write('\n'.join(definition) + '\n')
            return word, definition
        else:
            print("No definition found.")
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# function that stores the WOD in the wod database
def store_word_of_the_day(word, definition, date):
    try:
        # update the WOD in the database
        existing_entry = wordOfTheDayCollection.find_one()
        print(f"existing entry: {existing_entry}")

        if existing_entry:
            # grab the word
            existing_word = existing_entry["word"]
            # update the existing entry
            wordOfTheDayCollection.update_one(
                {"word": existing_word},
                {"$set": {"word": word, "definition": definition, "date": date}}
            )
            print(f"updated wod in database {word}")
        else:
            # insert new entry
            word_data = {
                "word": word,
                "definition": definition,
                "date": date
            }

            print(word_data)
            wordOfTheDayCollection.insert_one(word_data)
    except Exception as e:
        print(f"error updating word of the day collection {e}")
        logger.error(f"error inserting word of the day: {word}")


# function that grabs a new word, stores it into the WOD collection and word collection
def update_word_of_the_day(current_date, guild_id, user_id):
    word, definition = generate_word_of_the_day()

    # store the word into WOD collection
    store_word_of_the_day(word, definition, current_date)

    # store the word into word collection
    store_word_def(wordCollection, word, definition)

    # store the word into user's learned_words
    store_word_users(userCollection, guild_id, user_id, "English", word)

    print(f"new word of the day! '{word}'")

    return word, definition


@bot.command(name="wotd")
async def word_of_the_day(ctx):
    user_id = ctx.author.id
    guild_id = ctx.guild.id

    # get current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # check if a day has passed before generating new wod
    existing_wod = wordOfTheDayCollection.find_one()

    if existing_wod:
        stored_date_str = existing_wod["date"]
        stored_word = existing_wod["word"]
        stored_def = existing_wod["definition"]

        # check if one or more days has passed
        if stored_date_str != current_date:
            word, definition = update_word_of_the_day(current_date, guild_id, user_id)
            image_url, url, photographer = get_image(word)
            print(f"{image_url} {photographer}")
            embed = wotd_embed(ctx, word, definition, current_date, image_url, url, photographer)

            await ctx.send(embed=embed)
        else:
            print(f"a day has not passed since last entry for WOD")

            # store the current WOD into user's learned words
            store_word_users(userCollection, guild_id, user_id, "English", stored_word)

            image_url, url, photographer = get_image(stored_word)
            print(f"{image_url} {photographer}")
            embed = wotd_embed(ctx, stored_word, stored_def, stored_date_str, image_url, url, photographer)
            await ctx.send(embed=embed)
    else:
        print("no existing wod entry found. generating new entry")
        word, definition = update_word_of_the_day(current_date, guild_id, user_id)
        image_url, url, photographer = get_image(word)
        print(f"{image_url} {photographer}")
        embed = wotd_embed(ctx, word, definition, current_date, image_url, url, photographer)
        await ctx.send(embed=embed)


# function that retrieves an image for a word
def get_image(word):
    params = {
        "query": word,
        "orientation": "square",
        "size": "medium"
    }
    try:
        response = requests.get(url=pexels_url, headers=pexel_headers, params=params)
        response.raise_for_status()  # grab http error code
        data = response.json()
        # print(data)
        photos_list = data["photos"]
        random_index = random.randint(0, len(photos_list) - 1)
        image_url = data["photos"][0]["src"]["medium"]
        url = data["photos"][0]["url"]
        # print(url)
        photographer = data["photos"][0]["photographer"]
        return image_url, url, photographer
    except Exception as e:
        print(f"error retrieving an image, error {e}")
        logger.error(f"error retrieving an image for word '{word}', error {e}")
        return None, None, None


@bot.command(name="img")
async def image_def(ctx, *, args: str = ""):
    error_message = "Invalid input. Use `$img <word>` to get a photo representation of the word."

    # Check if the user provided any arguments
    if not args.strip():
        await ctx.send(error_message)
        return

    words = args.split()

    if len(words) != 1:
        await ctx.send(error_message)
        return

    # Use the provided word to fetch and print its definition
    word = words[0]

    # Check if the word contains only alphabetical characters using reg expressions
    if not re.match("^[a-zA-Z]+$", word):
        await ctx.send(error_message)
        return

    try:
        image_url, url, photographer = get_image(word)
        if url is not None and photographer is not None and image_url is not None:
            embed = image_embed(word, image_url, url, photographer)
            await ctx.send(embed=embed)
        else:
            raise ValueError("Image URL or photographer is None")
    except Exception as e:
        print(f"error retrieving image for '{word}' {e}")
        logger.error(f"error retrieving image for '{word}' {e}")
        await ctx.send("Sorry! Kiwi was unable to retrieve a photo for that word.")


def get_correct_guesses(guild_id, user_id):
    # attempt to get user's data
    result = userCollection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})

    existing_user = result["users"].get(str(user_id), {})

    correct_guesses = existing_user.get("correct_guess", None)
    return correct_guesses


# function that updates the role based on the score
async def update_role_based_on_score(ctx, guild_id, user_id):
    member = ctx.author

    # get score from database
    score = get_correct_guesses(guild_id, user_id)

    for role_name, properties in lingo_roles.items():
        score_range = properties["range"]
        lower_bound, upper_bound = map(int, score_range.split('-'))

        if int(lower_bound) <= score <= int(upper_bound):
            role = discord.utils.get(member.guild.roles, name=role_name)

            if role:
                roles_to_remove = [r for r in member.roles if r.name in lingo_roles.keys()]

                # check if the role is not already in the member's roles
                if role not in member.roles:
                    await member.remove_roles(*roles_to_remove)
                    await member.add_roles(role)
                    # print(f"updated role for {member.name} based on score: {role_name}")

                    # tell user
                    await ctx.send(f"Congratulations {member.mention}! Your role has been updated to `{role_name}` 🎉\n"
                                   f"`$profile` to see your new role badge\n"
                                   f"`$roles` to find out how to get certain roles")
                else:
                    print(f"{member.name} already has the role {role_name}")
            else:
                print(f"role {role_name} not found, cannnot update role")
                logger.error(f"role {role_name} not found, cannnot update role")
            break


# command that translates a given word to english based on given source language
@bot.command(name="trl")
async def get_translation(ctx, *, args: str = ""):
    ip = "Invalid input."
    error_input_message = ("Use `$trl <word> <source language>` to get the English translation.\n"
                           "e.g. `$trl merci french`")

    # Check if the user provided any arguments
    if not args.strip():
        await ctx.send(f"{ip} {error_input_message}")
        return

    words = args.split()

    # Check if the user provided only one argument
    if len(words) == 1:
        await ctx.send(f"{ip} {error_input_message}")
        return

    # Check if the word contains any digits or special characters
    special_characters = set(")(*&^%$#@!")
    if any(word.isnumeric() or any(char in special_characters for char in word) for word in words):
        await ctx.send(f"{ip} {error_input_message}")
        return

    source_language = words[-1]
    source_words = words[0:-1]  # a list

    word_to_translate = " ".join(source_words)
    print(word_to_translate)

    error_message = (f"Sorry! Kiwi could not translate `{word_to_translate}` from `{source_language.capitalize()}` "
                     f"to English.")

    # grab source language code
    code = get_code(source_language)

    if code:
        # first check if the word definition is stored in the database before fetching
        existing_word = wordCollection.find_one({source_language.capitalize(): word_to_translate})

        if existing_word:
            english_translation = existing_word.get("word")
            print(f"found in db. the english translation of {word_to_translate} is {english_translation}")
        else:
            english_translation = translate_word(word_to_translate, code, "en")
            print(f"not found in db. translated word to english is: {english_translation}")
        await ctx.send(
            f"`{word_to_translate}` in {source_language.capitalize()} is `{english_translation}` in English.")
    else:
        await ctx.send(f"{error_message}\n{error_input_message}")


# function to reset lives
def reset_lives(guild_id, user_id):
    last_reset_time, lives = get_last_reset_time_and_hearts(guild_id, user_id)
    now = datetime.datetime.utcnow()
    time_diff = (now - last_reset_time).total_seconds()

    print(f"time diff: {time_diff} seconds")

    # reset one life every 6 hours
    if time_diff >= (GameConstants.RESET_HEARTS_SECONDS * 3):
        amount_to_refill = min(3, GameConstants.MAX_LIVES - lives)
    elif time_diff >= (GameConstants.RESET_HEARTS_SECONDS * 2):
        amount_to_refill = min(2, GameConstants.MAX_LIVES - lives)
    elif time_diff >= GameConstants.RESET_HEARTS_SECONDS:
        amount_to_refill = 1
    else:
        amount_to_refill = 0

    if amount_to_refill > 0:
        increment(userCollection, guild_id, user_id, "hearts", amount_to_refill)


def get_last_reset_time_and_hearts(guild_id, user_id):
    try:
        result = userCollection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})
        user_data = result["users"].get(str(user_id), {})
        last_reset_time = user_data.get("last_reset_time", None)
        lives = user_data.get("hearts", None)
        print(f"last reset time: {last_reset_time}")
        print(f"hearts: {lives}")
        return last_reset_time, lives
    except Exception as e:
        print(f"couldn't find last_reset_time {e}")


@bot.command(name="requiz")
# requiz
async def get_requiz_question(ctx):
    # check if a game is already in session
    global current_view, game_starter
    game_starter = ctx.author.id

    if current_view and not current_view.stopped:
        await ctx.send("A game is already in process. Finish the current game.")
        return

    user_id = ctx.author.id
    guild_id = ctx.guild.id

    # check if user has 1 or more lives
    silver, gold, lives = get_lives_and_coins(guild_id, user_id)

    if lives < 1:
        await ctx.send(f"**{ctx.author}**, you have no more lives to play right now.")
        return

    # grab random wrong word and definition then put it into the question generator
    wrong_word = get_wrong_words(ctx.guild.id, ctx.author.id)
    if not wrong_word:
        await ctx.send(f"**{ctx.author}**, you have not guessed any words incorrectly. Try another game mode! (`$play` or `$chal`)")
        return

    definition, language, english_word = get_def_first_check_database(wrong_word)

    question = generate_question(wrong_word, definition)

    word = question["word"]  # current game word

    which_langauge = "English"
    word_to_store = word

    # see if the requiz word is a challenge word or not
    if language:
        which_langauge = language
        word_to_store = wrong_word
        print(f"current translated word: {current_translated_word}")

    correct_index = question["def_options"]["correct_index"]
    corDef = question["def_options"][f"option{correct_index + 1}"]
    # print(f"cordef {corDef}")

    embed, view = interactive_embed(ctx, word, question["def_options"]["option1"], question["def_options"]["option2"],
                                    question["def_options"]["option3"], lives, silver, gold, correct_index,
                                    challenge=False, requiz=True)
    print(question)

    current_view = view  # set global view

    message = await ctx.send(embed=embed, view=view)
    view.message = message
    res = await view.wait()  # wait for view to stop by timeout or manually stopping

    if res:
        print("timeout")
        view.correct_or_not = 'N'  # set to incorrect

    # update user collection
    if view.correct_or_not == 'Y':
        print("correct answer guessed, update to db in progress".upper())
        # get + silvers
        increment(userCollection, guild_id, user_id, "coins", GameConstants.PLAY_W_SILVER)

        # increment number of correct guesses + 1
        increment(userCollection, guild_id, user_id, "correct_guess", 1)

        # store the learnt word
        store_word_users(userCollection, guild_id, user_id, which_langauge, word_to_store)

        # remove word from wrong_words
        remove_word_from_wrong_words(guild_id, user_id, wrong_word)
    elif view.correct_or_not == 'N':
        print("incorrect answer guessed, update to db in progress".upper())
        # decrement heart - 1
        increment(userCollection, guild_id, user_id, "hearts", -1)

        # increment number of incorrect guesses + 1
        increment(userCollection, guild_id, user_id, "incorrect_guess", 1)

    # update lingo role
    await update_role_based_on_score(ctx, guild_id, user_id)


def get_wrong_words(guild_id, user_id):
    try:
        result = userCollection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})
        user_data = result["users"].get(str(user_id), {})
        wrong_words = user_data.get("wrong_words", {})
        random_word = random.choice(wrong_words)
        print(f"random word: {random_word}")
        return random_word
    except Exception as e:
        print(f"couldn't return a random word from user's wrong_words {e}")


def remove_word_from_wrong_words(guild_id, user_id, word):
    try:
        userCollection.update_one(
            {"guild_id": guild_id},
            {"$pull": {f"users.{user_id}.wrong_words": word}}
        )
    except Exception as e:
        print(f"couldn't return a random word from user's wrong_words {e}")
