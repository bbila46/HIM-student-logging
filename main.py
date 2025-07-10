import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import asyncio
from aiohttp import web

# Setup intents
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants
ROLE_STUDENT = 1392653369964757154
ROLE_PROFESSOR = 1392654292648722494
LOG_CHANNEL_ID = 1392655742430871754
GUILD_ID = 1387102987238768783
INVITE_LINK = "https://discord.gg/66qx29Tf"

# Temporary storage for role assignments (user_id -> role_id)
pending_roles = {}

# ---- Modal ----
class RegistrationModal(discord.ui.Modal, title="🏫 WMI Registration"):

    username = discord.ui.TextInput(
        label="Your Full Name",
        placeholder="e.g. Dr. Elira Q.",
        required=True,
        style=discord.TextStyle.short
    )

    notes = discord.ui.TextInput(
        label="Optional Notes",
        placeholder="Anything you'd like to add...",
        required=False,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Wisteria Medical Institute Registration",
            description="Choose your role below to complete registration:",
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

# ---- Role Selector ----
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
    async def professor_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, ROLE_PROFESSOR, "👩‍🏫 Faculty Professor")

    async def assign_role(self, interaction, role_id, role_label):
        guild = interaction.guild
        member = guild.get_member(self.discord_user.id)

        # Save the chosen role for later (when they join the main server)
        pending_roles[self.discord_user.id] = role_id

        assigned_now = False
        if member and member.guild.id == GUILD_ID:
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)
                assigned_now = True

        message = (
            f"✅ You are now registered as **{role_label}**.\n"
            f"📨 Please click [this link]({INVITE_LINK}) to join the **main WMI server**.\n"
        )
        if assigned_now:
            message += "🎉 Your role was automatically assigned!"
        else:
            message += "🕓 Your role will be assigned once you join."

        await interaction.response.send_message(message, ephemeral=True)

        # Log to the log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title=f"📝 New Registration - {role_label}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            log_embed.add_field(name="Full Name", value=self.full_name, inline=True)
            log_embed.add_field(name="Discord", value=self.discord_user.mention, inline=True)
            log_embed.add_field(name="Role Chosen", value=role_label, inline=True)
            if self.notes:
                log_embed.add_field(name="Notes", value=self.notes, inline=False)
            log_embed.set_footer(text=f"Registered on {discord.utils.format_dt(discord.utils.utcnow(), style='F')}")
            await log_channel.send(embed=log_embed)

        self.stop()

# ---- Slash Command ----
@bot.tree.command(name="wmi_register", description="Register for Wisteria Medical Institute")
async def wmi_register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegistrationModal())

# ---- Auto Role on Join ----
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
        print(f"✅ Assigned {role.name} to {member.name} in main server")

        # Notify in log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"🎓 {member.mention} has joined and was assigned the role **{role.name}** automatically."
            )

    del pending_roles[member.id]

# ---- On Ready ----
@bot.event
async def on_ready():
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced slash commands to WMI Guild ({GUILD_ID})")
    except Exception as e:
        print("❌ Error syncing:", e)
    print(f"🟣 Logged in as {bot.user}")

# ---- Render Web Server Port ----
async def handle(request):
    return web.Response(text="WMI Registration Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.environ.get("PORT", 8000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server listening on port {port}")

# ---- Launch ----
async def main():
    await bot.login(os.getenv("DISCORD_TOKEN"))
    await start_webserver()
    await bot.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔻 Bot stopped")
