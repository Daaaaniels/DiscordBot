from discord.ext import commands
from discord import Embed, Color
from ui.admin_panel import AdminPanel

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="admin_panel")
    @commands.has_permissions(administrator=True)
    async def admin_panel(self, ctx):
        embed = Embed(
            title="🛠️ Admin Tools",
            description="Manage teams with the buttons below.",
            color=Color.red()
        )
        await ctx.send(embed=embed, view=AdminPanel())

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
