import discord
from discord import app_commands
from discord.ext import commands
import logging

from config import GENESIS_GUILD_ID  # <- use this
from ui.team_panel import TeamPanel
from ui.embed_builder import build_panel_embed

log = logging.getLogger(__name__)


class TeamCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="panel", description="Open your private team management panel")
    async def panel(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            embed = await build_panel_embed(interaction.user.id)
            view = await TeamPanel.create(interaction.user.id, interaction.guild)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            log.info("✅ Panel opened for %s", interaction.user)
        except Exception:
            log.exception("❌ Error in /panel")

    @app_commands.command(name="genesis_status", description="Debug Genesis config")
    async def genesis_status(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"GENESIS_GUILD_ID={GENESIS_GUILD_ID}", ephemeral=True
        )


async def setup(bot: commands.Bot):
    cog = TeamCommands(bot)
    await bot.add_cog(cog)
    tree = bot.tree

    # Avoid duplicates/old registrations
    for cmd in list(tree.get_commands()):
        if cmd.name in {"panel", "genesis_status"}:
            tree.remove_command(
                cmd.name, type=app_commands.AppCommandType.chat_input)

    if GENESIS_GUILD_ID:
        guild = discord.Object(id=GENESIS_GUILD_ID)
        tree.add_command(cog.panel, guild=guild)
        tree.add_command(cog.genesis_status, guild=guild)
        await tree.sync(guild=guild)
        print(f"✅ team_commands: synced to guild {GENESIS_GUILD_ID}")
    else:
        tree.add_command(cog.panel)
        tree.add_command(cog.genesis_status)
        await tree.sync()
        print("✅ team_commands: synced globally (may take up to ~1h)")
