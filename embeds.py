import discord
from MyView import MyView
from LingoRoles import lingo_roles


# function to show question
def interactive_embed(ctx, word, descr1, descr2, descr3, remaining_lives, silver, gold, correct_index, challenge,
                      language=None, translation=None):
    stuck_message = f"stuck? use a $hint or $pass the word"
    embed = discord.Embed()
    if language:
        embed.title = f"Guess the meaning of this word"
        embed.description = f"**`{translation}`** _({language})_"
        embed.color = discord.Color.dark_green()
    else:
        embed.title = "Guess the meaning of this word"
        embed.description = f"**`{word}`**"
        embed.color = 0xfffd78
    embed.set_author(name="", icon_url="")
    embed.set_image(url="")
    embed.add_field(name="Options:", value=f"1️⃣ {descr1}\n\n2️⃣ {descr2}\n\n3️⃣ {descr3}", inline=False)
    embed.add_field(name="", value=f"Kiwis: {silver} <:silver:1191744440113569833>"
    # f" {gold} <:gold:1191744402222223432>"
                                   f"\nLives: {remaining_lives}")
    embed.set_footer(text=stuck_message)

    view = MyView(ctx, correct_index, challenge, word, translation)

    return embed, view


# function that returns the embed for stats
def stat_embed(ctx, total, percentage, challenges, correct_guesses):
    embed = discord.Embed()
    embed.title = f"Stats"
    embed.description = f""
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.add_field(name="\u200B", value=f"**Total plays**: {total}\n"
                                         f"**Guess accuracy**: {percentage}\n"
                                         f"**Score(correct guesses)**: {correct_guesses}\n"          
                                         f"**Challenges complete**: {challenges}", inline=False)
    embed.color = 0x800080

    return embed


# function that returns the embed for user profile
def profile_embed(ctx, lives, silver, gold, total, percentage, challenges, correct_guesses, languages):
    embed = discord.Embed()
    embed.title = f""
    embed.description = ""
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.add_field(name="\u200B", value=f"**Lives**: {lives}", inline=False)
    embed.add_field(name="Kiwis:", value=f"**{silver}** <:silver:1191744440113569833>  "
                                         f"**{gold}** <:gold:1191744402222223432>", inline=False)
    embed.add_field(name="\u200B", value=f"**Total plays**: {total}\n"
                                         f"**Guess accuracy**: {percentage}\n"
                                         f"**Score(correct guesses)**: {correct_guesses}\n"  
                                         f"**Challenges complete**: {challenges}", inline=False)
    embed.color = 0x77DD77

    # show language and word count if > 0
    embed.add_field(name="\u200B", value="", inline=False)

    field_value = ""
    for language, num_words in languages.items():
        field_value += f"{language}: {num_words}\n"

    embed.add_field(name="Words per Language Mastery:\n", value=field_value, inline=False)

    return embed


# function that returns the embed for leaderboard
def leaderboard_embed(ctx, users_guesses, current_time):
    embed = discord.Embed()
    embed.title = f"🏆 Leaderboard 🏆"
    embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar.url)
    embed.add_field(name='\u0020', value="")

    # enumerate over each item in dict starting at 1
    for rank, (user, guesses) in enumerate(users_guesses.items(), start=1):
        if rank == 1:
            medal = "🥇"
        elif rank == 2:
            medal = "🥈"
        elif rank == 3:
            medal = "🥉"
        else:
            medal = ""

        # bold the current user's rank on the leaderboard
        if user == ctx.author.name:
            user_text = f"**{user}**"
        else:
            user_text = user

        embed.add_field(name="", value=f"#{rank} {medal} {user_text} Score: {guesses} ", inline=False)
    embed.color = discord.Color.gold()

    embed.add_field(name='\u0020', value="")

    footer_text = f"Leaderboard updated at {current_time}."
    embed.set_footer(text=footer_text)
    return embed


# function that returns the embed for WOTD
def wotd_embed(ctx, word, definition, current_date, image_url=None, url=None, photographer=None):
    footer_text = "Learn a new word every day with $wotd!"
    embed = discord.Embed()
    embed.title = f"📚 Word of the day ({current_date}) ✨"
    embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar.url)
    embed.add_field(name='\u0020', value="")
    embed.add_field(name=f"`{word}`: {definition}", value="", inline=False)
    if image_url is not None:
        embed.set_image(url=image_url)
    if photographer is not None and url is not None:
        creds = f"Photo was taken by {photographer} on Pexels"
        footer_content = f"{creds}\n{url}\n{footer_text}"
    else:
        footer_content = footer_text
    embed.color = discord.Color.blurple()
    embed.set_footer(text=footer_content)
    return embed


# function that returns the embed for WOTD
def image_embed(word, image_url, url, photographer):
    embed = discord.Embed()
    embed.title = word
    embed.set_image(url=image_url)
    embed.set_footer(text=f"Photo was taken by {photographer} on Pexels\n{url}")
    embed.color = discord.Color.greyple()
    return embed


def dictionary_embed(ctx, data, current_page, total_pages):
    embed = discord.Embed()
    embed.title = f"🧠 {ctx.author.name}'s word bank 🧠"
    embed.description = ("Use `$def <word>` to get the definition, <word> must be in English.\n"
                         "Use `$trl <word(s)> <source language>` to get the English translation.\n\n"
                         "Here's a list of words you've mastered so far:")
    embed.add_field(name='\u0020', value="")
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

    for item in data:
        embed.add_field(name=item, value="", inline=False)

    embed.color = discord.Color.purple()

    embed.set_footer(text=f"Page {current_page} / {total_pages}")

    return embed


# create an embed that shows user what all the roles are and how they can earn it
def role_embed(ctx):
    embed = discord.Embed()
    embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar.url)
    embed.title = f"LingoBot Role Ladder 🧗"
    embed.description = (f"Each role grants you special badges displayed on your profile.\n"
                         f"Keep playing `$play`, `$chal` to earn points and climb the ranks!")

    embed.color = discord.Color.og_blurple()

    embed.add_field(name='\u0020', value="")
    for index, (role_name, properties) in enumerate(reversed(lingo_roles.items())):
        score_range = properties["range"]
        lower_bound, upper_bound = map(int, score_range.split('-'))
        if index == 0:
            medal_emoji = "🥇"
        elif index == 1:
            medal_emoji = "🥈"
        elif index == 2:
            medal_emoji = "🥉"
        elif index == 3 or index == 4:
            medal_emoji = "🌟"
        else:
            medal_emoji = "⭐"

        embed.add_field(name=f"{medal_emoji} {role_name}",
                        value=f"Score: {lower_bound}-{upper_bound}" if index != 0 else
                        f"Score: {lower_bound}+", inline=False)

    embed.set_footer(text="Check your score using $stat or $profile\n"
                          "Check the leaderboard in your server using $lead")
    return embed
