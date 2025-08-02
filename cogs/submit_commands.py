# cogs/submit_commands.py

import discord
from discord import app_commands
from discord.ext import commands
from core.db import set
from datetime import datetime
from ui.review_panel import SubmissionReviewPanel
from config import REVIEW_CHANNEL_ID
from core.db import get
from ui.embed_builder import build_panel_embed
from core.db import get_user_team

GUILD_ID = 1397306012557377616  # Replace with your server's ID


class SubmitCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="submit", description="Submit your Genesis Rank Point screenshot.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def submit(self, interaction: discord.Interaction, attachment: discord.Attachment):
        print("🚀 /submit triggered")
        user_id = str(interaction.user.id)
        print("⏳ calling get_user_team()")
        team = get_user_team(user_id)

        print("✅ got team:", team)
        print(f"👤 User: {user_id}, Team: {team}")
        if not team:
            await interaction.response.send_message("❌ You are not in a team.", ephemeral=True)
            return

        if team["leader_id"] != user_id:
            await interaction.response.send_message("🚫 Only the team leader can submit rank points.", ephemeral=True)
            return

        if not attachment.content_type.startswith("image/"):
            await interaction.response.send_message("❌ Please attach an image (screenshot).", ephemeral=True)
            return

        print("📸 Attachment is valid")
        timestamp = datetime.utcnow().isoformat()
        message_id = str(interaction.id)
        team_name = team["name"]

        submission_data = {
            "user_id": user_id,
            "message_id": message_id,
            "image_url": attachment.url,
            "timestamp": timestamp,
            "status": "pending",
            "team_name": team_name  # ✅ FIXED comma + key
        }

        print("💾 Saving submission to DB")
        set(f"submissions:{user_id}:{message_id}", submission_data)

        print("✅ Responding to user")
        await interaction.response.send_message(
            "✅ Submission received! Your screenshot has been saved for review.",
            ephemeral=True
        )

        print("📤 Building and sending review message")
        review_channel = interaction.client.get_channel(REVIEW_CHANNEL_ID)
        if review_channel:
            # ✅ FIXED - no overwriting
            view = SubmissionReviewPanel(
                user_id=user_id, team_name=team_name, message_id=message_id)
            embed = discord.Embed(
                title="📥 New Rank Point Submission",
                description=f"Submitted by <@{user_id}> from team **{team_name}**",
                color=discord.Color.blurple(),
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=attachment.url)
            embed.set_footer(text=f"Submission ID: {message_id}")

            print(f"📺 Channel: {review_channel}")
            await review_channel.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(SubmitCommands(bot))
