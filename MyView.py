import discord


class MyView(discord.ui.View):
    def __init__(self, correct_index):
        super().__init__()
        self.correct_index = correct_index

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, custom_id="0", emoji="1️⃣")
    async def button1_callback(self, interaction, button):
        print(f"button 1 clicked (id 0)")
        await interaction.response.send_message("clicked 1")

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, custom_id="1", emoji="2️⃣")
    async def button2_callback(self, interaction, button):
        print(f"button 2 clicked (id 1)")
        await interaction.response.send_message("clicked 2")

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, custom_id="2", emoji="3️⃣")
    async def button3_callback(self, interaction, button):
        print(f"button 3 clicked (id 2)")
        await interaction.response.send_message("clicked 3")