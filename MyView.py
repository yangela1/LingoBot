import discord
from GameConstants import GameConstants


class MyView(discord.ui.View):
    def __init__(self, ctx, correct_index, challenge=False, current_word=None, current_translated_word=None):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.correct_index = correct_index
        self.buttons_disabled = False
        self.button_emojis = {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
        }
        self.correct_or_not = None
        self.stopped = False
        self.challenge = challenge
        self.current_word = current_word
        self.current_translated_word = current_translated_word
        self.chal_message = f"`{self.current_translated_word}` in English is `{self.current_word}`.\n"

    # function that handles button clicks
    async def handle_button_click(self, interaction, button, button_id):
        # print(f"button {button_id} clicked (index {button.custom_id})")
        # the correct button id: 1, 2, or 3
        correct_button = self.correct_index + 1

        # grab the correct emoji corresp to the button id
        button_emoji = self.button_emojis.get(correct_button, "❓")

        # check if clicked button is correct or not based on the index
        if int(button.custom_id) == self.correct_index:
            # print("correct button clicked")
            self.disable_buttons()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"Correct!\n"
                                            f"{self.chal_message if self.challenge else ''}"
                                            f"**{self.ctx.author.name}** +{GameConstants.CHAL_W_SILVER if self.challenge else GameConstants.PLAY_W_SILVER} "
                                            f"<:silver:1191744440113569833>"
                                            f"{', +' + str(GameConstants.CHAL_W_GOLD) + ' <:gold:1191744402222223432>' if self.challenge else ''}")
            self.correct_or_not = "Y"
            self.stop()
        else:
            print("wrong button clicked")
            self.disable_buttons()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"Incorrect :( the correct answer is {button_emoji}\n"
                                            f"{self.chal_message if self.challenge else ''}" 
                                            f"**{self.ctx.author.name}** -1 heart")
            self.correct_or_not = "N"
            self.stop()

    # function that triggers after timeout
    async def on_timeout(self):
        correct_button = self.correct_index + 1
        button_emoji = self.button_emojis.get(correct_button, "❓")
        await self.ctx.send(f"Timeout! {self.ctx.author.mention}\n"
                            f"The correct answer is {button_emoji}\n"
                            f"{self.chal_message if self.challenge else ''}"
                            f"**{self.ctx.author.name}** -1 heart")

        self.disable_buttons()
        await self.message.edit(view=self)
        self.stop()

    def stop(self):
        self.stopped = True
        super().stop()

    # function to disable buttons
    def disable_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
                child.style = discord.ButtonStyle.gray

    # function that checks whether the user who is interacting with it is not anyone else
    async def interaction_check(self, interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Hey! It's not your turn to guess.", ephemeral=True)
            return False
        else:
            return True

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, custom_id="0", emoji="1️⃣")
    async def button1_callback(self, interaction, button):
        await self.handle_button_click(interaction, button, 1)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, custom_id="1", emoji="2️⃣")
    async def button2_callback(self, interaction, button):
        await self.handle_button_click(interaction, button, 2)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, custom_id="2", emoji="3️⃣")
    async def button3_callback(self, interaction, button):
        await self.handle_button_click(interaction, button, 3)

