import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import asyncio
from aiohttp import web

# Bot setup
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants
ROLE_STUDENT = 1392653369964757154
LOG_CHANNEL_ID = 1392655742430871754
GUILD_ID = 1387102987238768783
INVITE_LINK = "https://discord.gg/66qx29Tf"

# Store users who haven't joined yet
pending_roles = {}

# ------------------- MODAL FORM ------------------- #
class RegistrationModal(discord.ui.Modal, title="🌸 WMI Registration - Step 1"):

    username = discord.ui.TextInput(
        label="Your Full Name",
        placeholder="e.g. Elira Q.",
        required=True,
        style=discord.TextStyle.short
    )

    email = discord.ui.TextInput(
        label="Email Address (optional)",
        placeholder="e.g. elira@example.com",
        required=False,
        style=discord.TextStyle.short
    )

    notes = discord.ui.TextInput(
        label="Optional Notes",
        placeholder="Anything you’d like to share with us?",
        required=False,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌸 Wisteria Medical Institute Registration",
            description="Please choose your role below to complete your registration.",
            color=0xD8BFD8  # Wisteria / light purple
        )
        embed.add_field(name="Full Name", value=self.username.value, inline=True)
        embed.add_field(name="Discord", value=interaction.user.mention, inline=True)
        embed.add_field(name="Date", value=discord.utils.format_dt(discord.utils.utcnow(), style='F'), inline=False)

        if self.email.value:
            embed.add_field(name="Email", value=self.email.value, inline=True)
        if self.notes.value:
            embed.add_field(name="Notes", value=self.notes.value, inline=False)

        view = RoleSelectionView(
            full_name=self.username.value,
            email=self.email.value,
            discord_user=interaction.user,
            notes=self.notes.value
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ------------------- ROLE SELECTION ------------------- #
class RoleSelectionView(discord.ui.View):
    def __init__(self, full_name, email, discord_user, notes):
        super().__init__(timeout=120)
        self.full_name = full_name
        self.email = email
        self.discord_user = discord_user
        self.notes = notes

    @discord.ui.button(label="🎓 MS1 - First Year Student", style=discord.ButtonStyle.primary)
    async def student_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.discord_user.id)

        # Save pending role if member not in guild yet
        pending_roles[self.discord_user.id] = ROLE_STUDENT
        assigned_now = False

        if member and member.guild.id == GUILD_ID:
            role = member.guild.get_role(ROLE_STUDENT)
            if role:
                await member.add_roles(role)
                assigned_now = True

        msg = (
            f"✅ You are now registered as **🎓 MS1 - First Year Student**.\n"
            f"📨 Please [join our Discord server]({INVITE_LINK}).\n"
        )
        msg += "🎉 Your role has been assigned!" if assigned_now else "🕓 Your role will be given once you join."

        await interaction.response.send_message(msg, ephemeral=True)

        # Log the registration
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📝 New MS1 Registration",
                color=discord.Color.purple(),
                timestamp=discord.utils.utcnow()
            )
            log_embed.add_field(name="Full Name", value=self.full_name, inline=True)
            log_embed.add_field(name="Discord", value=self.discord_user.mention, inline=True)
            if self.email:
                log_embed.add_field(name="Email", value=self.email, inline=True)
            log_embed.add_field(name="Role", value="🎓 MS1 - First Year Student", inline=True)
            if self.notes:
                log_embed.add_field(name="Notes", value=self.notes, inline=False)
            log_embed.set_footer(text="Wisteria Medical Institute AutoLogger")
            await log_channel.send(embed=log_embed)

        self.stop()

# ------------------- SLASH COMMAND ------------------- #
@bot.tree.command(name="wmi_register", description="Start the WMI student registration process.")
async def wmi_register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegistrationModal())

# ------------------- MEMBER JOIN DETECTOR ------------------- #
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return

    role_id = pending_roles.get(member.id)
    if not role_id:
        return

    role = member.guild.get_role(role_id)
    if role:
        await member.add_roles(role)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"🎓 {member.mention} has joined and was auto-assigned the **MS1** role.")
        del pending_roles[member.id]

# ------------------- STARTUP SYNC & HEALTH ------------------- #
@bot.event
async def on_ready():
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced commands to guild {GUILD_ID}")
    except Exception as e:
        print("❌ Sync failed:", e)
    print(f"🟣 Logged in as {bot.user}")

# Web server for Koyeb/Render health check
async def handle(request):
    return web.Response(text="WMI Bot is alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.environ.get("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server running on port {port}")

# ------------------- MAIN ENTRY ------------------- #
async def main():
    await bot.login(os.getenv("DISCORD_TOKEN"))
    await start_webserver()
    await bot.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔻 Bot stopped.")
