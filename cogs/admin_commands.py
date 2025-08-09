# cogs/admin_commands.py

import discord
from discord import app_commands, Interaction, Object
from discord.ext import commands
from config import GENESIS_GUILD_ID
from ui.admin_panel import AdminPanel


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="admin", description="Open the Admin Team Panel")
    @app_commands.guilds(Object(id=GENESIS_GUILD_ID))
    async def admin_panel(self, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("🚫 You need Administrator permissions to use this command.", ephemeral=True)

        view = AdminPanel()
        await interaction.response.send_message("🔧 Admin Panel:", view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
