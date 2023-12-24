import logging
import discord

from discord.ext import commands
from database import userCollection

# Configure the logger
logging.basicConfig(level=logging.ERROR, filename='bot_errors.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('my_bot')

# create bot
intents = discord.Intents.all()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix='$', intents=intents)


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


