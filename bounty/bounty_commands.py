# bounty/bounty_commands.py

import discord
from discord.ext import commands, tasks
from discord import app_commands

from bounty.bounty_posting import post_next_bounty
from core.db import get, set, delete


class BountyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_bounty_task.add_exception_type(Exception)
        self.daily_bounty_task.start()

    @app_commands.command(name="post_bounty", description="Manually post the next bounty quest.")
    async def post_bounty(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        success = await post_next_bounty(interaction.channel)
        if success:
            await interaction.followup.send("✅ Bounty posted!")
        else:
            await interaction.followup.send("❌ Failed to post bounty.")

    @app_commands.command(name="start_bounties", description="Start auto-posting bounty every 24h.")
    async def start_bounties(self, interaction: discord.Interaction):
        set("bounty_channel_id", interaction.channel.id)
        await interaction.response.send_message("▶️ Daily bounty posting has been enabled in this channel.", ephemeral=True)

    @app_commands.command(name="stop_bounties", description="Stop auto-posting bounties.")
    async def stop_bounties(self, interaction: discord.Interaction):
        if get("bounty_channel_id"):
            delete("bounty_channel_id")
            await interaction.response.send_message("⏹️ Bounty posting stopped.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ No active bounty posting is configured.", ephemeral=True)

    @tasks.loop(hours=24)
    async def daily_bounty_task(self):
        channel_id = get("bounty_channel_id")
        if not channel_id:
            return

        channel = self.bot.get_channel(int(channel_id))
        if channel:
            await post_next_bounty(channel)
        else:
            print("❌ Could not find the bounty channel.")

    @daily_bounty_task.before_loop
    async def before_bounty_post(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BountyCommands(bot))
