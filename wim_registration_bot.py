# wim_registration_bot.py

import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import app_commands
from dotenv import load_dotenv
import os
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load environment variables from the .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration (provided IDs and invite link)
SWM_GUILD_ID = 1387102987238768783
LOG_CHANNEL_ID = 1392655742430871754
WIM_INVITE_LINK = "https://discord.gg/66qx29Tf"
STUDENT_ROLE_ID = 1392653369964757154
PROFESSOR_ROLE_ID = 1392654292648722494

# Set up bot intents; ensure members intent is enabled
intents = discord.Intents.default()
intents.members = True

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------------
# Discord UI: Buttons and View
# ------------------------------

class RoleSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StudentButton())
        self.add_item(ProfessorButton())

class StudentButton(Button):
    def __init__(self):
        super().__init__(
            label="🎓 Student", 
            style=discord.ButtonStyle.primary,
            custom_id="student_button"
        )

    async def callback(self, interaction: discord.Interaction):
        await handle_application(interaction, "Student", STUDENT_ROLE_ID)

class ProfessorButton(Button):
    def __init__(self):
        super().__init__(
            label="👩‍🏫 Professor", 
            style=discord.ButtonStyle.secondary,
            custom_id="professor_button"
        )

    async def callback(self, interaction: discord.Interaction):
        await handle_application(interaction, "Professor", PROFESSOR_ROLE_ID)

# ------------------------------
# Application Handling Function
# ------------------------------

async def handle_application(interaction: discord.Interaction, role_name: str, role_id: int):
    # Ensure this command is used in the correct server
    if interaction.guild.id != SWM_GUILD_ID:
        await interaction.response.send_message("This interaction is not valid in this server.", ephemeral=True)
        return

    member = interaction.user
    guild = interaction.guild
    role = guild.get_role(role_id)
    if role is None:
        await interaction.response.send_message("Role not found on the server.", ephemeral=True)
        return

    if role in member.roles:
        await interaction.response.send_message(f"You already have the **{role_name}** role.", ephemeral=True)
        return

    try:
        await member.add_roles(role, reason="WIM Registration Application")
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to assign roles.", ephemeral=True)
        return
    except Exception as e:
        await interaction.response.send_message(f"Error assigning role: {e}", ephemeral=True)
        return

    # Send the invite link via DM
    try:
        await member.send(
            f"✅ You have registered as a **{role_name}** for Wisteria Medical Institute!\n"
            f"Here is your invite link to WIM:\n{WIM_INVITE_LINK}\n\nWelcome!"
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "Could not send you a DM, but your role was assigned. Please check your server invites.",
            ephemeral=True
        )

    await interaction.response.send_message(f"✅ Registered as **{role_name}**! Check your DMs for the invite.", ephemeral=True)

    # Log the application in the designated log channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="📨 New WIM Application",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Name", value=member.display_name, inline=True)
        embed.add_field(name="Discord Tag", value=str(member), inline=True)
        embed.add_field(name="Role Selected", value=role_name, inline=True)
        embed.add_field(name="Date", value=str(datetime.datetime.utcnow().date()), inline=True)
        embed.set_footer(text="WIM Registration System")
        await log_channel.send(embed=embed)

# ------------------------------
# Slash Command: /register
# ------------------------------

@bot.tree.command(name="register", description="Post the WIM Registration buttons")
async def register_command(interaction: discord.Interaction):
    if interaction.guild.id != SWM_GUILD_ID:
        await interaction.response.send_message("This command can only be used in the SWM server.", ephemeral=True)
        return
    view = RoleSelectView()
    await interaction.response.send_message(
        "**📣 Wisteria Medical Institute Registration is now open!**\n"
        "Click your role below to apply and get your invite to WIM:",
        view=view
    )

# ------------------------------
# Bot Startup: on_ready and Slash Command Sync
# ------------------------------

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"⚠️ Failed to sync commands: {e}")
    print(f"✅ Bot is online as {bot.user} (ID: {bot.user.id})")

# ------------------------------
# Minimal Web Server for Render (Port 10000)
# ------------------------------

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"WIM Registration Bot is running")

def run_webserver():
    server = HTTPServer(('0.0.0.0', 10000), Handler)
    server.serve_forever()

# Start the web server in a background thread
threading.Thread(target=run_webserver, daemon=True).start()

# ------------------------------
# Run the Bot
# ------------------------------

bot.run(TOKEN)
