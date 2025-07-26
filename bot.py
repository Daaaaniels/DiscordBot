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

# --- !create_team ---


@bot.command(name="create_team")
async def create_team(ctx, *, team_name: str):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    if team_name in teams:
        embed = discord.Embed(
            title="⚠️ Team Exists",
            description=f"Team `{team_name}` already exists.",
            color=discord.Color.orange()
        )
        return await ctx.send(embed=embed)

    role = await guild.create_role(name=team_name)
    await ctx.author.add_roles(role)

    teams[team_name] = {"members": [user_id], "points": 0}
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    embed = discord.Embed(
        title="🎉 Team Created",
        description=f"You created team `{team_name}` and received the role.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# --- !join_team ---


@bot.command(name="join_team")
async def join_team(ctx, *, team_name: str):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    if team_name not in teams:
        embed = discord.Embed(
            title="❌ Team Not Found",
            description=f"No team named `{team_name}` exists.",
            color=discord.Color.red()
        )
        return await ctx.send(embed=embed)

    for name, data in teams.items():
        if user_id in data["members"]:
            embed = discord.Embed(
                title="⚠️ Already in a Team",
                description=f"You are already in `{name}`. Leave first.",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

    teams[team_name]["members"].append(user_id)
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    role = discord.utils.get(guild.roles, name=team_name)
    if role:
        await ctx.author.add_roles(role)

    embed = discord.Embed(
        title="✅ Joined Team",
        description=f"You joined `{team_name}` and received the role.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

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
                title="👋 Left Team",
                description=f"You left `{team_name}`.",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)

    embed = discord.Embed(
        title="⚠️ Not in Team",
        description="You are not currently in any team.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# --- Run ---
with open("token.txt") as f:
    token = f.read().strip()

bot.run(token)
