from discord.ext import commands
from discord import app_commands, Interaction, Object
from discord.ext import commands
from discord import app_commands, Interaction, Object
from config import GUILD_ID
from ui.team_panel import TeamPanel, send_panel
from ui.embed_builder import build_panel_embed


class TeamCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel", description="Open your private team management panel")
    @app_commands.guilds(Object(id=GUILD_ID))
    async def panel(self, interaction: Interaction):
        embed = await build_panel_embed(interaction.user.id)
        view = await TeamPanel.create(interaction.user.id, interaction.guild)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TeamCommands(bot))
