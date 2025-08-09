import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from core.db import db_set, get_user_team
from ui.review_panel import SubmissionReviewPanel
from config import REVIEW_CHANNEL_ID, GENESIS_GUILD_ID

import logging
log = logging.getLogger(__name__)

GUILD_ID = 1397306012557377616


class SubmitCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="submit", description="Submit your Genesis Rank Point screenshot.")
    @app_commands.guilds(discord.Object(id=GENESIS_GUILD_ID))
    async def submit(self, interaction: discord.Interaction, attachment: discord.Attachment):
        log.info("🚀 /submit triggered")
        user_id = str(interaction.user.id)

        log.info("⏳ calling get_user_team()")
        team = await get_user_team(user_id)
        log.info(f"✅ got team: {team}")

        if not team:
            await interaction.response.send_message("❌ You are not in a team.", ephemeral=True)
            return

        if team["leader"] != user_id:
            await interaction.response.send_message("🚫 Only the team leader can submit rank points.", ephemeral=True)
            return

        if not attachment.content_type or not attachment.content_type.startswith("image/"):
            await interaction.response.send_message("❌ Please attach an image (screenshot).", ephemeral=True)
            return

        log.info("📸 Attachment is valid")
        team_name = team["name"]

        await interaction.response.send_message(
            "✅ Submission received! Your screenshot has been saved for review.",
            ephemeral=True
        )

        review_channel = interaction.client.get_channel(REVIEW_CHANNEL_ID)
        if not review_channel:
            log.error("❌ Review channel not found.")
            return

        log.info("📤 Sending embed...")
        embed = discord.Embed(
            title="📥 New Rank Point Submission",
            description=f"Submitted by <@{user_id}> from team **{team_name}**",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_image(url=attachment.url)

        # Step 1: Send embed (no view)
        message = await review_channel.send(embed=embed)

        # Step 2: Store submission in DB
        await db_set(str(message.id), "submissions", {
            "user_id": user_id,
            "team_name": team_name,
            "status": "pending"
        })

        # Step 3: Attach persistent review view
        view = SubmissionReviewPanel(user_id, team_name, message.id)
        await message.edit(view=view)

        log.info(f"✅ Submission saved and view attached: msg_id={message.id}")


async def setup(bot):
    await bot.add_cog(SubmitCommands(bot))
