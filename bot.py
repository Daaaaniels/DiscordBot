import discord
from discord.ext import commands
import asyncio
import logging

from config import DISCORD_TOKEN, REVIEW_CHANNEL_ID
from ui.review_panel import SubmissionReviewPanel
from core.db import (
    init_db,
    get_teams,
    get,
    db_set,
    delete,
    get_user_team,
)

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_ID = 1397306012557377616


@bot.event
async def on_ready():
    await init_db()

    # Reattach persistent views for submissions
    submissions = await get("submissions", "submissions") or {}
    for message_id, data in submissions.items():
        view = SubmissionReviewPanel(
            user_id=data["user_id"],
            team_name=data["team_name"],
            message_id=message_id
        )
        bot.add_view(view)
        print(f"🔁 Reattached view for message ID: {message_id}")

    print(f"✅ Logged in as {bot.user}")
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced slash commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Sync error: {e}")


async def load_extensions():
    await bot.load_extension("cogs.team_commands")
    await bot.load_extension("cogs.admin_commands")
    await bot.load_extension("cogs.submit_commands")
    await bot.load_extension("bounty.bounty_commands")


async def main():
    await load_extensions()
    await bot.start(DISCORD_TOKEN)


# --- Dev Commands (Safe & Updated) ---


@bot.command()
async def resetteams(ctx):
    await db_set("teams", "teams", {})
    await ctx.send("✅ DB key 'teams' has been reset to an empty dict.")


@bot.command()
async def whoami(ctx):
    team = await get_user_team(str(ctx.author.id))
    if team:
        await ctx.send(f"✅ You are in team **{team['name']}**")
    else:
        await ctx.send("❌ You're not in any team.")


@bot.command()
async def testsend(ctx):
    channel = bot.get_channel(REVIEW_CHANNEL_ID)
    if channel:
        await channel.send("✅ Test message from bot")
    else:
        await ctx.send("❌ Review channel not found.")


@bot.command()
async def showdb(ctx):
    teams = await get_teams()
    await ctx.send(f"🧪 teams: `{list(teams.keys())}`")


# --- Run Bot ---
asyncio.run(main())
