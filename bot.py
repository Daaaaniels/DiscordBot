import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TEAM_FILE = "teams.json"
teams = {}

if os.path.exists(TEAM_FILE):
    with open(TEAM_FILE, "r") as f:
        teams = json.load(f)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")


@bot.command()
async def create_team(ctx, *, team_name: str):
    guild = ctx.guild
    author_id = str(ctx.author.id)

    if team_name in teams:
        await ctx.send(f"⚠️ Team `{team_name}` already exists.")
        return

    role = await guild.create_role(name=team_name)
    await ctx.author.add_roles(role)

    teams[team_name] = {
        "members": [author_id],
        "points": 0
    }

    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    await ctx.send(f"🎉 Team `{team_name}` created and role assigned to you!")


@bot.command()
async def join_team(ctx, *, team_name: str):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    if team_name not in teams:
        await ctx.send(f"❌ Team `{team_name}` does not exist.")
        return

    for name, data in teams.items():
        if user_id in data["members"]:
            await ctx.send(f"⚠️ You are already in team `{name}`.")
            return

    teams[team_name]["members"].append(user_id)
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    role = discord.utils.get(guild.roles, name=team_name)
    if role:
        await ctx.author.add_roles(role)

    await ctx.send(f"✅ You joined team `{team_name}`!")


@bot.command()
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

            await ctx.send(f"👋 You left team `{team_name}`.")
            return

    await ctx.send("⚠️ You are not in any team.")

with open("token.txt") as f:
    token = f.read().strip()

bot.run(token)
