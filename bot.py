import os
import sys
import asyncio
import logging
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, REVIEW_CHANNEL_ID, GENESIS_GUILD_ID
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
log = logging.getLogger("genesis.bot")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
# Enable only if you truly need to read message content
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    # Init DB (async)
    await init_db()

    # Reattach persistent views for previously-sent submission messages
    submissions = await get("submissions", "submissions") or {}
    for message_id, data in submissions.items():
        try:
            view = SubmissionReviewPanel(
                user_id=data["user_id"],
                team_name=data["team_name"],
                message_id=message_id
            )
            bot.add_view(view)
            log.info("🔁 Reattached view for message ID: %s", message_id)
        except Exception as e:
            log.exception("Failed to reattach view for %s: %s", message_id, e)

    log.info("✅ Logged in as %s (id=%s)", bot.user, bot.user.id)

    # Slash command sync: prefer fast guild-only sync if GENESIS_GUILD_ID is set
    try:
        if GENESIS_GUILD_ID:
            await bot.tree.sync(guild=discord.Object(id=GENESIS_GUILD_ID))
            log.info("✅ Synced slash commands to guild %s", GENESIS_GUILD_ID)
        else:
            await bot.tree.sync()
            log.info("✅ Synced global slash commands")
    except Exception as e:
        log.exception("❌ Slash command sync error: %s", e)


async def load_extensions():
    """Load cogs/extensions with clear logging."""
    extensions = [
        "cogs.team_commands",
        "cogs.admin_commands",
        "cogs.submit_commands",
        "bounty.bounty_commands",
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            log.info("🔌 Loaded extension: %s", ext)
        except Exception as e:
            log.exception("❌ Failed to load %s: %s", ext, e)


async def main():
    # Fail fast if token is missing
    if not DISCORD_TOKEN:
        sys.stderr.write(
            "[FATAL] DISCORD_TOKEN is not set. "
            "On Railway: add it under Variables. Locally: put it in .env.\n"
        )
        sys.exit(1)

    await load_extensions()
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        log.info("Shutting down…")
    finally:
        await bot.close()

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
    if REVIEW_CHANNEL_ID is None:
        return await ctx.send("❌ REVIEW_CHANNEL_ID is not configured.")
    channel = bot.get_channel(REVIEW_CHANNEL_ID) or await bot.fetch_channel(REVIEW_CHANNEL_ID)
    if channel:
        await channel.send("✅ Test message from bot")
        await ctx.send("✅ Sent a test message to the review channel.")
    else:
        await ctx.send("❌ Review channel not found.")


@bot.command()
async def showdb(ctx):
    teams = await get_teams()
    await ctx.send(f"🧪 teams: `{list(teams.keys())}`")


@bot.command()
@commands.is_owner()
async def sync(ctx):
    if not GENESIS_GUILD_ID:
        return await ctx.send("GENESIS_GUILD_ID not set")
    guild = discord.Object(id=GENESIS_GUILD_ID)
    try:
        bot.tree.clear_commands(guild=None)  # clear accidental global regs
    except Exception:
        pass
    synced = await bot.tree.sync(guild=guild)
    await ctx.send(f"Synced {len(synced)} commands to {GENESIS_GUILD_ID}.")


# --- Run Bot ---
if __name__ == "__main__":
    asyncio.run(main())
