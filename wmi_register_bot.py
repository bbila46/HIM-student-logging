import discord
from discord.ext import commands
import os
import asyncio
from aiohttp import web

# ---- CONFIGURATION ----
GUILD_ID = 1387102987238768783
ROLE_STUDENT = 1392653369964757154
LOG_CHANNEL_ID = 1392655742430871754
INVITE_LINK = "https://discord.gg/66qx29Tf"

# ---- INTENTS & BOT ----
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
pending_roles = {}

# ---- MODAL ----
class RegistrationModal(discord.ui.Modal, title="🌸 WMI Registration"):
    name = discord.ui.TextInput(label="Full Name", placeholder="e.g. Elira Q.", required=True)
    email = discord.ui.TextInput(label="Email (optional)", placeholder="e.g. elira@example.com", required=False)
    notes = discord.ui.TextInput(label="Notes (optional)", placeholder="Anything you'd like to add?", required=False, style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌸 WMI Registration",
            description="Please confirm your role below to finish registration.",
            color=0xD8BFD8
        )
        embed.add_field(name="Name", value=self.name.value, inline=True)
        embed.add_field(name="Discord", value=interaction.user.mention, inline=True)
        if self.email.value:
            embed.add_field(name="Email", value=self.email.value, inline=True)
        if self.notes.value:
            embed.add_field(name="Notes", value=self.notes.value, inline=False)

        view = RoleSelectionView(
            name=self.name.value,
            email=self.email.value,
            notes=self.notes.value,
            user=interaction.user
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ---- ROLE SELECTION VIEW ----
class RoleSelectionView(discord.ui.View):
    def __init__(self, name, email, notes, user):
        super().__init__(timeout=120)
        self.name = name
        self.email = email
        self.notes = notes
        self.user = user

    @discord.ui.button(label="🎓 MS1 - First Year Student", style=discord.ButtonStyle.primary)
    async def assign_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.user.id)

        pending_roles[self.user.id] = ROLE_STUDENT
        assigned = False

        if member:
            role = guild.get_role(ROLE_STUDENT)
            if role:
                await member.add_roles(role)
                assigned = True

        await interaction.response.send_message(
            f"✅ Registered as **MS1 - First Year Student**.\n📨 [Join server]({INVITE_LINK})\n" +
            ("🎉 Role assigned!" if assigned else "🕓 Role will be given when you join."),
            ephemeral=True
        )

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="📝 New Registration", color=discord.Color.purple())
            embed.add_field(name="Name", value=self.name, inline=True)
            embed.add_field(name="Discord", value=self.user.mention, inline=True)
            if self.email:
                embed.add_field(name="Email", value=self.email, inline=True)
            embed.add_field(name="Role", value="MS1 - First Year Student", inline=True)
            if self.notes:
                embed.add_field(name="Notes", value=self.notes, inline=False)
            await log_channel.send(embed=embed)

        self.stop()

# ---- SLASH COMMAND ----
@bot.tree.command(name="wmi_register", description="Start WMI student registration")
async def wmi_register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegistrationModal())

# ---- ASSIGN ROLE ON JOIN ----
@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return
    role_id = pending_roles.get(member.id)
    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            await member.add_roles(role)
        log = bot.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(f"🎓 {member.mention} joined and was given MS1 role.")
        del pending_roles[member.id]

# ---- ON READY ----
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} command(s) to GUILD {GUILD_ID}")
    except Exception as e:
        print("❌ Sync error:", e)
    print(f"🟣 Logged in as {bot.user}")

# ---- HEALTH CHECK ----
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

# ---- MAIN ----
async def main():
    await bot.login(os.getenv("DISCORD_TOKEN"))
    await start_webserver()
    await bot.connect()

if __name__ == "__main__":
    asyncio.run(main())
