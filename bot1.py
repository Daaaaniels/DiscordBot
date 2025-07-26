import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = 1397306012557377616  # Replace with your real guild ID


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} command(s) to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"✅ Logged in as {bot.user}")


@bot.tree.command(name="panel", description="Open your private team panel")
async def panel(interaction: discord.Interaction):
    await interaction.response.send_message(
        "✅ This is your private team panel!",
        ephemeral=True
    )

# --- Run the bot ---
token = os.getenv("DISCORD_TOKEN")  # Or just replace with token directly
bot.run(token)
