from discord.ext import commands
from discord import app_commands, Interaction, Object
import logging

from config import GUILD_ID
from ui.team_panel import TeamPanel
from ui.embed_builder import build_panel_embed

log = logging.getLogger(__name__)


class TeamCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel", description="Open your private team management panel")
    @app_commands.guilds(Object(id=GUILD_ID))
    async def panel(self, interaction: Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            embed = await build_panel_embed(interaction.user.id)
            view = await TeamPanel.create(interaction.user.id, interaction.guild)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            log.info(f"✅ Panel opened for user {interaction.user}")
        except Exception as e:
            log.error(f"❌ Error in /panel: {e}")



async def setup(bot):
    await bot.add_cog(TeamCommands(bot))
