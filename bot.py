import discord
from discord.ext import commands
from config import DISCORD_TOKEN
import asyncio
from ui.review_panel import SubmissionReviewPanel
from config import REVIEW_CHANNEL_ID

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_ID = 1397306012557377616


@bot.event
async def on_ready():
    bot.add_view(SubmissionReviewPanel())
    print(f"✅ Logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print("✅ Synced slash commands and registered views.")
    print(f"✅ Synced slash commands to guild {GUILD_ID}")
    print(f"🤖 Logged in as {bot.user}")


async def load_extensions():
    await bot.load_extension("cogs.team_commands")
    await bot.load_extension("cogs.admin_commands")
    await bot.load_extension("bounty.bounty_commands")
    await bot.load_extension("cogs.submit_commands")


async def main():
    await load_extensions()
    await bot.start(DISCORD_TOKEN)


@bot.command()
async def testsend(ctx):
    channel = bot.get_channel(REVIEW_CHANNEL_ID)
    await channel.send("✅ Test message from bot")


@bot.command()
async def whoami(ctx):
    from core.db import get_user_team  # import inside to avoid circular issues
    team = get_user_team(str(ctx.author.id))
    if team:
        await ctx.send(f"✅ You are in team **{team['name']}**")
    else:
        await ctx.send("❌ You're not in any team.")


@bot.command()
async def resetteams(ctx):
    from core.db import set
    set("teams", [])
    await ctx.send("✅ DB key 'teams' has been reset to an empty list.")


@bot.command()
async def migrate_teams(ctx):
    from core.db import get, set
    team_dict = get("teams", {})
    if not isinstance(team_dict, dict):
        return await ctx.send("❌ 'teams' is not a dict.")

    new_list = []
    for name, data in team_dict.items():
        if isinstance(data, dict):
            new_list.append({
                "name": name,
                "leader_id": data.get("leader"),
                "members": data.get("members", [])
            })

    set("team_list", new_list)
    await ctx.send(f"✅ Migrated {len(new_list)} teams to 'team_list'.")

asyncio.run(main())

import logging
logging.basicConfig(level=logging.DEBUG)

