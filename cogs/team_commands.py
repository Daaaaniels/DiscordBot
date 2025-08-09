# cogs/team_commands.py
import discord
from discord import app_commands
from discord.ext import commands
import logging

from config import GENESIS_GUILD_ID  # <- use the new name
from ui.team_panel import TeamPanel
from ui.embed_builder import build_panel_embed

log = logging.getLogger(__name__)


class TeamCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Define without guild decorator so we can bind at setup-time
    @app_commands.command(name="panel", description="Open your private team management panel")
    async def panel(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            # Your helpers look async in your snippet; keep awaits.
            embed = await build_panel_embed(interaction.user.id)
            view = await TeamPanel.create(interaction.user.id, interaction.guild)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            log.info("✅ Panel opened for user %s", interaction.user)
        except Exception as e:
            log.exception("❌ Error in /panel: %s", e)

    # Handy health check
    @app_commands.command(name="genesis_status", description="Show Genesis config status")
    async def genesis_status(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"GENESIS_GUILD_ID={GENESIS_GUILD_ID}", ephemeral=True
        )


async def setup(bot: commands.Bot):
    # Add the cog first
    cog = TeamCommands(bot)
    await bot.add_cog(cog)

    tree = bot.tree

    # Remove any previous registrations of these names (global or guild) to avoid conflicts
    for cmd in list(tree.get_commands()):
        if cmd.name in {"panel", "genesis_status"}:
            tree.remove_command(
                cmd.name, type=app_commands.AppCommandType.chat_input)

    # Register to the specific guild if provided; else fall back to global (slow to appear)
    if GENESIS_GUILD_ID:
        guild = discord.Object(id=GENESIS_GUILD_ID)
        tree.add_command(cog.panel, guild=guild)
        tree.add_command(cog.genesis_status, guild=guild)
        synced = await tree.sync(guild=guild)
        print(
            f"✅ team_commands: synced {len(synced)} commands to guild {GENESIS_GUILD_ID}")
    else:
        tree.add_command(cog.panel)
        tree.add_command(cog.genesis_status)
        synced = await tree.sync()
        print(f"✅ team_commands: synced {len(synced)} global commands")
