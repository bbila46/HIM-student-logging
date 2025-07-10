import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import app_commands
from dotenv import load_dotenv
import os
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# IDs
SWM_GUILD_ID = 1387102987238768783
LOG_CHANNEL_ID = 1392655742430871754
WIM_INVITE_LINK = "https://discord.gg/66qx29Tf"
STUDENT_ROLE_ID = 1392653369964757154
PROFESSOR_ROLE_ID = 1392654292648722494

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =========================
# View & Button Classes
# =========================

class RoleSelectView(View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user
        self.add_item(StudentButton(user))
        self.add_item(ProfessorButton(user))

class StudentButton(Button):
    def __init__(self, user):
        super().__init__(label="🎓 Student", style=discord.ButtonStyle.primary, custom_id="student_button")
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        await handle_application(interaction, self.user, "Student", STUDENT_ROLE_ID)

class ProfessorButton(Button):
    def __init__(self, user):
        super().__init__(label="👩‍🏫 Professor", style=discord.ButtonStyle.secondary, custom_id="professor_button")
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        await handle_application(interaction, self.user, "Professor", PROFESSOR_ROLE_ID)

# =========================
# Handle Application Logic
# =========================

async def handle_application(interaction, user, role_name, role_id):
    guild = interaction.guild
    role = guild.get_role(role_id)

    if not role:
        await interaction.response.send_message("❌ Role not found.", ephemeral=True)
        return

    if role in user.roles:
        await interaction.response.send_message(f"You already have the **{role_name}** role.", ephemeral=True)
        return

    try:
        await user.add_roles(role, reason="WMI Registration")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to assign role: {e}", ephemeral=True)
        return

    try:
        await user.send(
            f"✅ You have registered as a **{role_name}** for Wisteria Medical Institute!\n"
            f"Here is your invite link: {WIM_INVITE_LINK}"
        )
    except:
        await interaction.followup.send("⚠️ Role assigned, but I couldn’t DM you the invite.", ephemeral=True)

    await interaction.response.send_message(f"✅ Registered as **{role_name}**! Check DMs.", ephemeral=True)

    # Log
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="📨 WMI Application Submitted",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Username", value=user.display_name, inline=True)
        embed.add_field(name="Discord", value=str(user), inline=True)
        embed.add_field(name="Role", value=role_name, inline=True)
        embed.add_field(name="Date", value=str(datetime.datetime.utcnow().date()), inline=True)
        await log_channel.send(embed=embed)

# =========================
# Slash Command /WMI-register
# =========================

@tree.command(name="WMI-register", description="Start the WMI Registration process")
@app_commands.checks.has_permissions(administrator=True)
async def register_command(interaction: discord.Interaction):
    if interaction.guild.id != SWM_GUILD_ID:
        await interaction.response.send_message("❌ This command is only allowed in SWM.", ephemeral=True)
        return

    user = interaction.user

    embed = discord.Embed(
        title="📋 Wisteria Medical Institute Registration",
        description="Click one of the buttons below to select your role.",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="👤 Display Name", value=user.display_name, inline=True)
    embed.add_field(name="🆔 Discord", value=str(user), inline=True)
    embed.add_field(name="📅 Date", value=str(datetime.datetime.utcnow().date()), inline=True)
    embed.set_footer(text="WMI Registration Panel")

    view = RoleSelectView(user)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# =========================
# Sync + Ready
# =========================

@bot.event
async def on_ready():
    try:
        await tree.sync(guild=discord.Object(id=SWM_GUILD_ID))
        print(f"✅ Synced slash commands to guild {SWM_GUILD_ID}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"✅ Bot is online as {bot.user}")

# =========================
# Web Server for Render
# =========================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"WIM Registration Bot is running.")

def run_webserver():
    server = HTTPServer(('0.0.0.0', 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_webserver, daemon=True).start()

# =========================
# Run Bot
# =========================

bot.run(TOKEN)
