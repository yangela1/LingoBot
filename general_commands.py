import logging
import discord
import datetime

from discord.ext import commands
from database import userCollection
from game_commands import get_lives_and_coins
from embeds import stat_embed
from embeds import profile_embed
from embeds import leaderboard_embed
from embeds import role_embed
from PaginationView import PaginationView
from LingoRoles import lingo_roles

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger('my_bot')

# create bot
intents = discord.Intents.all()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix='$', case_insensitive=True, intents=intents, description="LingoBot")

# help
bot.remove_command('help')


@bot.command(name='help')
async def help_response(ctx):
    help_dm = f"How to use LingoBot\n" \
              f"Commands used:\n" \

    try:
        await ctx.author.send(help_dm)
        await ctx.send(f"sent DM to {ctx.author.mention}")
    except discord.errors.HTTPException as e:
        logger.error(f"Error sending DM to {ctx.author}: {e}")


# say hello
@bot.command(name='hello', description="say hello to the bot")
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


# function that returns stats of user
def check_stat(guild_id, user_id):
    # attempt to get user's data
    result = userCollection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})

    existing_user = result["users"].get(str(user_id), {})

    correct_guesses = existing_user.get("correct_guess", None)
    incorrect_guesses = existing_user.get("incorrect_guess", None)
    challenges = existing_user.get("chal_complete", None)

    # total guesses
    total = correct_guesses + incorrect_guesses

    # percentage of correct guesses
    if total == 0:
        percentage = 0
    else:
        percentage = (correct_guesses / total) * 100

    print(f"total = {total}")
    print(f"percentage = {percentage}")

    formatted_percentage = f"{int(percentage)}%"

    return total, formatted_percentage, challenges, correct_guesses


# function that returns number of words learned in each language
def check_words_learned(guild_id, user_id):
    # attempt to get user's data
    result = userCollection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})

    existing_user = result["users"].get(str(user_id), {})

    words_learned = existing_user.get("words_learned")
    word_count = {}

    for language, words in words_learned.items():
        num_words = len(words)
        word_count[language] = num_words
        print(f"{language}: {num_words} words learned")

    return word_count


@bot.command(name="stat", help="Displays user stats")
async def view_stat(ctx):
    try:
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        total, percentage, challenges, correct_guesses = check_stat(guild_id, user_id)
        embed = stat_embed(ctx, total, percentage, challenges, correct_guesses)

        await ctx.send(embed=embed)
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logger.error(error_message)


@bot.command(name="profile", help="Displays user profile")
async def view_profile(ctx):
    try:
        user_id = ctx.author.id
        guild_id = ctx.guild.id
        total, percentage, challenges, correct_guesses = check_stat(guild_id, user_id)
        silver, gold, lives = get_lives_and_coins(guild_id, user_id)
        word_count = check_words_learned(guild_id, user_id)

        # check to see if they have a role
        member = ctx.author
        lingo_role_names = [role.name for role in member.roles if "lingo" in role.name.lower()]

        if lingo_role_names:
            lingo_role_name = lingo_role_names[0]
            emoji_value = lingo_roles.get(lingo_role_name, {}).get("emoji", None)
            embed = profile_embed(ctx, lives, silver, gold, total, percentage, challenges, correct_guesses, word_count, emoji_value)
        else:
            embed = profile_embed(ctx, lives, silver, gold, total, percentage, challenges, correct_guesses, word_count)

        await ctx.send(embed=embed)
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logger.error(error_message)


@bot.command(name="lead", help="Displays the leaderboard based on the number of correct guesses")
async def view_leaderboard(ctx):
    # dictionary of name:num_correct_guesses
    users = {}

    guild_id = ctx.guild.id

    result = userCollection.find_one({"guild_id": guild_id, f"users": {"$exists": True}})

    user_data = result["users"]

    # iterate through all users in collection and add to dictionary
    for user_id, user_data in user_data.items():
        user_name = user_data.get("name")
        num_correct_guesses = user_data.get("correct_guess")

        users[user_name] = num_correct_guesses

    # sort from high to low - based on the second element of each tuple  (item[1])
    sorted_users = dict(sorted(users.items(), key=lambda item: item[1], reverse=True))
    print(f"sorted users: {sorted_users}")

    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    embed = leaderboard_embed(ctx, sorted_users, current_date)
    await ctx.send(embed=embed)


def get_words_learned(guild_id, user_id):
    result = userCollection.find_one({"guild_id": guild_id, f"users.{user_id}": {"$exists": True}})
    existing_user = result["users"].get(str(user_id), {})

    english_words = existing_user.get("words_learned", {}).get("English", [])
    spanish_words = existing_user.get("words_learned", {}).get("Spanish", [])
    modified_spanish_words = [word + " (Spanish)" for word in spanish_words]
    french_words = existing_user.get("words_learned", {}).get("French", [])
    modified_french_words = [word + " (French)" for word in french_words]
    german_words = existing_user.get("words_learned", {}).get("German", [])
    modified_german_words = [word + " (German)" for word in german_words]
    italian_words = existing_user.get("words_learned", {}).get("Italian", [])
    modified_italian_words = [word + " (Italian)" for word in italian_words]
    swedish_words = existing_user.get("words_learned", {}).get("Swedish", [])
    modified_swedish_words = [word + " (Swedish)" for word in swedish_words]

    words_list = []
    for lst in [english_words, modified_spanish_words, modified_french_words, modified_german_words,
                 modified_italian_words, modified_swedish_words]:
        words_list.extend(lst)
    return words_list


@bot.command(name="mywords", help="Displays all the words guessed correctly")
async def view_dictionary(ctx):
    # attempt to get user's data
    guild_id = ctx.guild.id
    user_id = ctx.author.id
    users_words = get_words_learned(guild_id, user_id)

    view = PaginationView(ctx)
    view.data = users_words
    await view.send(ctx)


@bot.command(name="roles")
async def view_roles(ctx):
    embed = role_embed(ctx)
    await ctx.send(embed=embed)


@bot.command(name="lives")
async def get_lives(ctx):
    user_id = ctx.author.id
    guild_id = ctx.guild.id
    try:
        silver, gold, lives = get_lives_and_coins(guild_id, user_id)
        life_message = f"**{ctx.author.name}**, you have {lives} lives remaining."
        await ctx.send(life_message)
    except Exception as e:
        logger.error(f"error occurred: {e}")


