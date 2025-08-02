import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, REVIEW_CHANNEL_ID
from ui.review_panel import SubmissionReviewPanel
import logging
from core.db import init_db, ensure_default_keys, validate_team_data, clean_malformed_teams

logging.basicConfig(level=logging.DEBUG)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_ID = 1397306012557377616


@bot.event
async def on_ready():
    from core.db import init_db, ensure_default_keys, validate_team_data, get
    from ui.review_panel import SubmissionReviewPanel

    await init_db()
    await ensure_default_keys()
    await validate_team_data()

    # Reattach persistent views from DB
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
    await bot.load_extension("bounty.bounty_commands")
    await bot.load_extension("cogs.submit_commands")


async def main():
    await load_extensions()
    await bot.start(DISCORD_TOKEN)


@bot.command()
async def resetteams(ctx):
    from core.db import set
    await set("teams", "teams", {})
    await ctx.send("✅ DB key 'teams' has been reset to an empty dict.")


@bot.command()
async def migrate_teams(ctx):
    from core.db import get, set
    team_dict = await get("teams", "teams")
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

    await set("team_list", "submissions", new_list)
    await ctx.send(f"✅ Migrated {len(new_list)} teams to 'team_list'.")


@bot.command()
async def whoami(ctx):
    from core.db import get_user_team
    team = await get_user_team(str(ctx.author.id))
    if team:
        await ctx.send(f"✅ You are in team **{team['name']}**")
    else:
        await ctx.send("❌ You're not in any team.")


@bot.command()
async def testsend(ctx):
    channel = bot.get_channel(REVIEW_CHANNEL_ID)
    await channel.send("✅ Test message from bot")


@bot.command()
async def showdb(ctx):
    from core.db import get_teams, get
    teams = await get_teams()
    team_list = await get("team_list", "submissions")

    await ctx.send(f"🧪 teams: `{list(teams.keys())}`\n📋 team_list: `{[t['name'] for t in team_list]}`")


@bot.command()
async def fixdb(ctx):
    from core.db import set
    await set("Genesis Knights", "teams", {
        "leader": str(ctx.author.id),
        "members": [str(ctx.author.id)],
        "points": 0,
        "code": "1234"
    })
    await set("team_list", "submissions", [
        {
            "name": "Genesis Knights",
            "leader_id": str(ctx.author.id),
            "members": [str(ctx.author.id)]
        }
    ])
    await ctx.send("✅ Created one test team and updated team_list.")


@bot.command()
async def wipe_db(ctx):
    from core.db import delete
    await delete("teams", "teams")  # remove bad entry
    await delete("team_list", "submissions")
    await ctx.send("🧼 Database wiped clean.")


@bot.command()
async def fix_ghosts(ctx):
    from core.db import validate_team_data
    await validate_team_data()
    await ctx.send("🧹 Checked and cleaned ghost teams from team_list.")


@bot.command()
async def clean_teams(ctx):
    from core.db import clean_malformed_teams
    await clean_malformed_teams()
    await ctx.send("✅ Cleaned malformed teams.")

# Run bot
asyncio.run(main())
