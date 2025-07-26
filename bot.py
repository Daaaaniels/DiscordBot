import discord
from discord.ext import commands
import json
import os
from discord.ext.commands import has_permissions, MissingPermissions

# --- Setup ---
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
TEAM_FILE = "teams.json"

# --- Load or initialize team data ---
if os.path.exists(TEAM_FILE):
    with open(TEAM_FILE, "r") as f:
        teams = json.load(f)
else:
    teams = {}

# --- Bot ready ---


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_message(message):
    print(f"[DEBUG] Heard message: {message.content}")
    await bot.process_commands(message)

# --- Panel Buttons ---


class TeamPanel(discord.ui.View):
    def __init__(self, user_id, in_team):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.in_team = in_team

        if self.in_team:
            self.add_item(LeaveTeamButton())
            self.add_item(TeamInfoButton())
        else:
            self.add_item(CreateTeamButton())
            self.add_item(JoinTeamButton())

        self.add_item(LeaderboardButton())


class CreateTeamButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🆕 Create Team", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Use `!create_team <name>` to create a team.", ephemeral=True)


class JoinTeamButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔗 Join Team", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Use `!join_team <name>` to join a team.", ephemeral=True)


class LeaveTeamButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Leave Team", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Use `!leave_team` to leave your team.", ephemeral=True)


class TeamInfoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="📊 Team Info", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Use `!team_info <team_name>` to view your team info.", ephemeral=True)


class LeaderboardButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🏆 Leaderboard", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Use `!leaderboard` to view top teams.", ephemeral=True)

# --- !panel ---


@bot.command(name="panel")
async def panel(ctx):
    user_id = str(ctx.author.id)
    in_team = any(user_id in team["members"] for team in teams.values())

    embed = discord.Embed(
        title="🏁 Team Panel",
        description="Use the buttons below to manage your team.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TeamPanel(user_id, in_team))

# --- Run Bot ---
with open("token.txt") as f:
    token = f.read().strip()

bot.run(token)
