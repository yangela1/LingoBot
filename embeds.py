import discord
from MyView import MyView


# function to show question
def interactive_embed(ctx, word, descr1, descr2, descr3, remaining_lives, silver, gold, correct_index, challenge,
                      language=None, translation=None):
    embed = discord.Embed()
    if language:
        embed.title = f"Guess the meaning of this word"
        embed.description = f"**`{translation}`** _({language})_"
        embed.color = 0xd13636
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

    view = MyView(ctx, correct_index, challenge, word, translation)

    return embed, view


# function that returns the embed for stats
def stat_embed(ctx, total, percentage, challenges):
    embed = discord.Embed()
    embed.title = f"Stats"
    embed.description = f""
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.add_field(name="\u200B", value=f"**Total plays**: {total}\n"
                                         f"**Correct guesses**: {percentage}\n"
                                         f"**Challenges complete**: {challenges}", inline=False)
    embed.color = 0x800080

    return embed


# function that returns the embed for user profile
def profile_embed(ctx, lives, silver, gold, total, percentage, challenges, languages):
    embed = discord.Embed()
    embed.title = f""
    embed.description = ""
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.add_field(name="\u200B", value=f"**Lives**: {lives}", inline=False)
    embed.add_field(name="Kiwis:", value=f"**{silver}** <:silver:1191744440113569833>  "
                                         f"**{gold}** <:gold:1191744402222223432>", inline=False)
    embed.add_field(name="\u200B", value=f"**Total plays**: {total}\n"
                                         f"**Correct guesses**: {percentage}\n"
                                         f"**Challenges complete**: {challenges}", inline=False)
    embed.color = 0x77DD77

    # show language and word count if > 0
    embed.add_field(name="\u200B", value="", inline=False)

    field_value = ""
    for language, num_words in languages.items():
        field_value += f"{language}: {num_words}\n"

    embed.add_field(name="Words per Language Mastery:\n", value=field_value, inline=False)

    return embed


# function that returns the embed for hints
def hint_embed(word_in_question, synonym):
    embed = discord.Embed()
    embed.title = f"The synonym for `{word_in_question} is `{synonym}`"
    embed.color = 0xffbe24
