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
bot = commands.Bot(command_prefix='$', intents=intents)

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('my_bot')

# remove default help command
bot.remove_command('help')

# register imported commands with the bot
bot.add_command(game_commands.daily_new_word)
bot.add_command(general_commands.commands)
bot.add_command(general_commands.help_response)
bot.add_command(general_commands.check)
bot.add_command(general_commands.say_hello)
bot.add_command(general_commands.what_is_my_lang)


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


bot.run(TOKEN)
