# ui/review_panel.py

import discord
from core.db import set, get
from datetime import datetime

class SubmissionReviewPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success, custom_id="submit_approve")
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            message_id = self._get_message_id(interaction)
            print(f"📨 Submission ID: {message_id}")
            if not message_id:
                return await interaction.response.send_message("❌ Could not read submission ID.", ephemeral=True)

            submission = self._find_submission_by_id(message_id)
            print(f"📦 Submission Data: {submission}")
            if not submission:
                return await interaction.response.send_message("❌ Submission not found.", ephemeral=True)

            from core.db import set  # Import here if needed
            set(f"submissions:{submission['user_id']}:{message_id}:status", "approved")

            await self._try_dm(interaction.client, submission["user_id"], "✅ Your Genesis submission has been approved!")
            await interaction.response.send_message("✅ Approved!", ephemeral=True)

            # Editing message view might fail if already edited, so wrap it
            try:
                await interaction.message.edit(view=None)
            except Exception as e:
                print(f"⚠️ Error editing message view: {e}")
        except Exception as e:
            print(f"❌ Unexpected error in approve_button: {e}")


    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger, custom_id="submit_reject")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = self._get_message_id(interaction)
        if not message_id:
            return await interaction.response.send_message("❌ Could not read submission ID.", ephemeral=True)

        submission = self._find_submission_by_id(message_id)
        if not submission:
            return await interaction.response.send_message("❌ Submission not found.", ephemeral=True)

        set(f"submissions:{submission['user_id']}:{message_id}:status", "rejected")

        await self._try_dm(interaction.client, submission["user_id"], "❌ Your Genesis submission was rejected.")
        await interaction.response.send_message("❌ Rejected!", ephemeral=True)
        await interaction.message.edit(view=None)

    def _get_message_id(self, interaction):
        try:
            return interaction.message.embeds[0].footer.text.replace("Submission ID: ", "")
        except Exception:
            return None

    def _find_submission_by_id(self, message_id):
        from core.db import db  # Make sure this is here
        try:
            for key in db.prefix("submissions:"):
                if key.endswith(f":{message_id}"):
                    return db.get(key)
        except Exception as e:
            print(f"❌ Error in _find_submission_by_id: {e}")
        return None



    async def _try_dm(self, client, user_id, message):
        try:
            user = await client.fetch_user(int(user_id))
            await user.send(message)
        except:
            pass
