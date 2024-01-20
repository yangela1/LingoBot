import discord
import logging

from discord.ext import commands

import game_commands
import general_commands
from database import userCollection
from database import TOKEN


# create bot
intents = discord.Intents.all()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix='$', case_insensitive=True, intents=intents, description="LingoBot")

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger('my_bot')

# remove default help command
bot.remove_command('help')

# register imported commands with the bot
bot.add_command(game_commands.new_game)
bot.add_command(game_commands.get_word_definition)
bot.add_command(game_commands.gamble_coin)
bot.add_command(game_commands.get_hint)
bot.add_command(game_commands.new_challenge)
bot.add_command(game_commands.buy_life_command)
bot.add_command(game_commands.pass_word_command)
bot.add_command(game_commands.word_of_the_day)

bot.add_command(general_commands.help_response)
bot.add_command(general_commands.check)
bot.add_command(general_commands.say_hello)
bot.add_command(general_commands.view_stat)
bot.add_command(general_commands.view_profile)
bot.add_command(general_commands.view_leaderboard)


# this is called when bot is ready to start being used
@bot.event
async def on_ready():
    print(f'we have logged in as {bot.user.name}')
    print(f'Connected to {len(bot.guilds)} guilds')
    for guild in bot.guilds:
        print(f' - {guild.name} ({guild.id})')


# register user upon using bot command
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # ignore messages from bots

    # check if message starts with bot's command prefix
    if message.content.startswith(bot.command_prefix):

        user_id = message.author.id
        user_name = message.author.name
        user_guild_id = message.guild.id
        user_guild_name = message.guild

        # check if guild exists
        existing_guild = userCollection.find_one({"guild_id": user_guild_id})

        if not existing_guild:
            register_guild(user_guild_id)

        # then check if user exists within the guild
        existing_user = userCollection.find_one({"guild_id": user_guild_id, f"users.{user_id}": {"$exists": True}})

        if not existing_user:
            # if user is not reg, register them to database
            register_user(user_id, user_name, user_guild_id, user_guild_name)

    await bot.process_commands(message)


def register_guild(guild_id):
    userCollection.insert_one({
        "guild_id": guild_id,
        "users": {}
    })
    print(f"successfully inserted guild {guild_id} into database")


def register_user(uid, name, guildid, guildname):
    print(f"user info: {uid} {name} {guildid} {guildname}")

    # create new user document
    new_user_data = {
        "discord_id": uid,
        "name": name,
        "hearts": 3,
        "coins": 0,
        "chal_coins": 0,
        "words_learned": {
            "English": [],
            "Spanish": [],
            "French": [],
            "German": [],
            "Italian": [],
            "Swedish": []
        },
        "wrong_words": [],
        "correct_guess": 0,
        "incorrect_guess": 0,
        "chal_complete": 0

    }
    # insert new user into users
    result = userCollection.update_one({"guild_id": guildid},
                                       {"$set": {f"users.{uid}": new_user_data}}, upsert=True)

    if result.acknowledged:
        print(f"successfully inserted {name} {uid} into guild {guildid}")
    else:
        print("failed to insert user data")
        logger.error(f"error inserting user data: {name} {uid}")


@bot.event
async def on_guild_join(guild):
    # check if guild exists in user collection
    if not userCollection.find_one({"guild_id": guild.id}):
        register_guild(guild.id)
    print(f"Bot joined guild: {guild.name} {guild.id} and added to database")


# list of commands
@bot.command(name='commands')
async def commands(ctx):
    # List all available commands
    command_list = [command.name for command in bot.commands]
    await ctx.send(f"Available commands: {', '.join(command_list)}")


# assign members special roles based on score
@bot.event
async def on_member_update(before, after):
    pass


bot.run(TOKEN)
