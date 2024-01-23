import discord

lingo_roles = {
    "Lingo Noob": {"range": "0-25", "color": discord.Colour.from_rgb(191, 114, 31), "emoji": "<:noobbanner:1199304256071663626>"},
    "Lingo Learner": {"range": "26-50", "color": discord.Colour.dark_blue(), "emoji": "<:learnerbanner:1199304279522025542>"},
    "Lingo Expert": {"range": "51-100", "color": discord.Colour.green(), "emoji": "<:expertbanner:1199304332835819551>"},
    "Lingo Legend": {"range": "101-200", "color": discord.Colour.blue(), "emoji": "<:legendbanner:1199304349550137364>"},
    "Lingo Master": {"range": "201-300", "color": discord.Colour.purple(), "emoji": "<:masterbanner:1199304833585389608>"},
    "Lingo Boss": {"range": "301-400", "color": discord.Colour.red(), "emoji": "<:bossbanner:1199304380101447790>"},
    "Lingo Einstein": {"range": "401-10000", "color": discord.Colour.orange(), "emoji": "<:einsteinbanner:1199304392222965810>"}
}