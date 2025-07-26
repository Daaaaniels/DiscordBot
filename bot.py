import discord
from discord.ext import commands
import json
import os

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

# --- Buttons ---


class TeamStatsButton(discord.ui.View):
    def __init__(self, team_name):
        super().__init__(timeout=None)
        self.team_name = team_name

    @discord.ui.button(label="📊 Team Stats", style=discord.ButtonStyle.blurple)
    async def show_team_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        team_data = teams.get(self.team_name)
        if not team_data:
            await interaction.response.send_message(f"Team `{self.team_name}` no longer exists.", ephemeral=True)
            return

        member_count = len(team_data["members"])
        points = team_data.get("points", 0)

        embed = discord.Embed(
            title=f"🔢 Stats for `{self.team_name}`",
            description=f"**Members:** {member_count}\n**Points:** {points}",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- !create_team ---


@bot.command(name="create_team")
async def create_team(ctx, *, team_name: str):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    if team_name in teams:
        embed = discord.Embed(
            title="⚠️ Team Exists", description=f"Team `{team_name}` already exists.", color=discord.Color.orange())
        return await ctx.send(embed=embed)

    role = await guild.create_role(name=team_name)
    await ctx.author.add_roles(role)

    teams[team_name] = {"members": [user_id], "points": 0}
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    embed = discord.Embed(title="🎉 Team Created",
                          description=f"You created team `{team_name}` and received the role.", color=discord.Color.green())
    await ctx.send(embed=embed, view=TeamStatsButton(team_name))

# --- !join_team ---


@bot.command(name="join_team")
async def join_team(ctx, *, team_name: str):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    if team_name not in teams:
        embed = discord.Embed(
            title="❌ Team Not Found", description=f"No team named `{team_name}` exists.", color=discord.Color.red())
        return await ctx.send(embed=embed)

    for name, data in teams.items():
        if user_id in data["members"]:
            embed = discord.Embed(title="⚠️ Already in a Team",
                                  description=f"You are already in `{name}`. Leave first.", color=discord.Color.orange())
            return await ctx.send(embed=embed)

    teams[team_name]["members"].append(user_id)
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    role = discord.utils.get(guild.roles, name=team_name)
    if role:
        await ctx.author.add_roles(role)

    embed = discord.Embed(
        title="✅ Joined Team", description=f"You joined `{team_name}` and received the role.", color=discord.Color.green())
    await ctx.send(embed=embed, view=TeamStatsButton(team_name))

# --- !leave_team ---


@bot.command(name="leave_team")
async def leave_team(ctx):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    for team_name, data in list(teams.items()):
        if user_id in data["members"]:
            data["members"].remove(user_id)
            role = discord.utils.get(guild.roles, name=team_name)
            if role:
                await ctx.author.remove_roles(role)
            if not data["members"]:
                if role:
                    await role.delete()
                del teams[team_name]
            with open(TEAM_FILE, "w") as f:
                json.dump(teams, f, indent=4)

            embed = discord.Embed(
                title="👋 Left Team", description=f"You left `{team_name}`.", color=discord.Color.blue())
            return await ctx.send(embed=embed)

    embed = discord.Embed(title="⚠️ Not in Team",
                          description="You are not currently in any team.", color=discord.Color.red())
    await ctx.send(embed=embed)

# --- !team_info ---


@bot.command(name="team_info")
async def team_info(ctx, *, team_name: str = None):
    if not team_name:
        embed = discord.Embed(title="ℹ️ Missing Team Name",
                              description="Use `!team_info <team_name>`.", color=discord.Color.orange())
        return await ctx.send(embed=embed)

    team_data = teams.get(team_name)
    if not team_data:
        embed = discord.Embed(
            title="❌ Team Not Found", description=f"Team `{team_name}` does not exist.", color=discord.Color.red())
        return await ctx.send(embed=embed)

    member_count = len(team_data["members"])
    points = team_data.get("points", 0)

    embed = discord.Embed(
        title=f"🔢 Stats for `{team_name}`",
        description=f"**Members:** {member_count}\n**Points:** {points}",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

# --- Run Bot ---
with open("token.txt") as f:
    token = f.read().strip()

bot.run(token)
