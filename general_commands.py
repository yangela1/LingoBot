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
def check_stat(user_id):
    id_filter = {"discord_id": user_id}

    # attempt to get user's data
    result = userCollection.find_one(id_filter)

    correct_guesses = result.get("correct_guess", None)
    incorrect_guesses = result.get("incorrect_guess", None)
    challenges = result.get("chal_complete", None)

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

    return total, formatted_percentage, challenges


@bot.command(name="stat")
async def view_stat(ctx):
    user_id = ctx.author.id
    total, percentage, challenges = check_stat(user_id)
    embed = stat_embed(ctx, total, percentage, challenges)

    await ctx.send(embed=embed)


# function that returns the embed for stats
def stat_embed(ctx, total, percentage, challenges):
    embed = discord.Embed()
    embed.title = f"Stats"
    embed.description = f""
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.add_field(name="Total guesses:", value=total, inline=False)
    embed.add_field(name="Percentage of correct guesses:", value=percentage, inline=False)
    embed.add_field(name="Challenges complete:", value=challenges, inline=False)
    embed.color = 0x800080

    return embed

