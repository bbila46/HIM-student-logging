import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Role IDs
ROLE_STUDENT = 1392653369964757154
ROLE_PROFESSOR = 1392654292648722494

# Log channel ID
LOG_CHANNEL_ID = 1392655742430871754

# Invite link
INVITE_LINK = "https://discord.gg/66qx29Tf"

class RegistrationModal(discord.ui.Modal, title="🏫 WMI Registration"):

    username = discord.ui.TextInput(
        label="Your Full Name",
        placeholder="e.g. Dr. Elira Q.",
        required=True,
        style=discord.TextStyle.short
    )

    notes = discord.ui.TextInput(
        label="Optional Notes",
        placeholder="Any additional info you'd like to add...",
        required=False,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Wisteria Medical Institute Registration",
            description="Please select your role below to complete registration:",
            color=0xD8BFD8  # Light purple
        )
        embed.add_field(name="Full Name", value=self.username.value, inline=True)
        embed.add_field(name="Discord", value=interaction.user.mention, inline=True)
        embed.add_field(name="Date", value=discord.utils.format_dt(discord.utils.utcnow(), style='F'), inline=False)
        if self.notes.value:
            embed.add_field(name="Notes", value=self.notes.value, inline=False)

        view = RoleSelectionView(
            full_name=self.username.value,
            discord_user=interaction.user,
            notes=self.notes.value
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class RoleSelectionView(discord.ui.View):
    def __init__(self, full_name, discord_user, notes):
        super().__init__(timeout=120)
        self.full_name = full_name
        self.discord_user = discord_user
        self.notes = notes

    @discord.ui.button(label="🎓 MS1 - First Year Student", style=discord.ButtonStyle.primary)
    async def student_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, ROLE_STUDENT, "🎓 MS1 - First Year Student")

    @discord.ui.button(label="👩‍🏫 Faculty Professor", style=discord.ButtonStyle.secondary)
    async def faculty_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, ROLE_PROFESSOR, "👩‍🏫 Faculty Professor")

    async def assign_role(self, interaction, role_id, role_label):
        guild = interaction.guild
        member = guild.get_member(self.discord_user.id)

        if not member:
            await interaction.response.send_message("Could not find the member in this server.", ephemeral=True)
            return

        # Assign the role
        role = guild.get_role(role_id)
        if role:
            await member.add_roles(role)

        # Send confirmation and invite
        await interaction.response.send_message(
            f"✅ You have been registered as **{role_label}**.\n"
            f"Join our main server here: {INVITE_LINK}",
            ephemeral=True
        )

        # Log to channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title=f"📝 New Registration - {role_label}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            log_embed.add_field(name="Name", value=self.full_name, inline=True)
            log_embed.add_field(name="Discord", value=self.discord_user.mention, inline=True)
            log_embed.add_field(name="Role", value=role_label, inline=True)
            if self.notes:
                log_embed.add_field(name="Notes", value=self.notes, inline=False)
            log_embed.set_footer(text=f"Registered on {discord.utils.format_dt(discord.utils.utcnow(), style='F')}")
            await log_channel.send(embed=log_embed)

        self.stop()


@bot.tree.command(name="wmi_register", description="Register to Wisteria Medical Institute")
async def register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegistrationModal())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ Please set DISCORD_TOKEN environment variable.")
    else:
        bot.run(TOKEN)
