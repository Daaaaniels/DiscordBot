# ui/review_panel.py

import discord
from core.db import db_set, get
from datetime import datetime


class SubmissionReviewPanel(discord.ui.View):
    def __init__(self, user_id, team_name, message_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.team_name = team_name
        self.message_id = message_id

        self.add_item(self.ApproveButton(user_id, team_name, message_id))
        self.add_item(self.RejectButton(user_id, message_id))

    class ApproveButton(discord.ui.Button):
        def __init__(self, user_id, team_name, message_id):
            super().__init__(label="✅ Approve", style=discord.ButtonStyle.green, custom_id="approve_submission")
            self.user_id = user_id
            self.team_name = team_name
            self.message_id = message_id

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(
                ApproveModal(self.user_id, self.team_name, self.message_id)
            )


    class RejectButton(discord.ui.Button):
        def __init__(self, user_id, message_id):
            super().__init__(label="❌ Reject", style=discord.ButtonStyle.danger, custom_id="reject_submission")
            self.user_id = user_id
            self.message_id = message_id

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(
                RejectModal(self.user_id, self.message_id)
            )




class ApproveModal(discord.ui.Modal, title="Approve Submission"):
    points = discord.ui.TextInput(label="New Total Points", required=True)

    def __init__(self, user_id, team_name, message_id):
        super().__init__()
        self.user_id = user_id
        self.team_name = team_name
        self.message_id = message_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            teams = get("teams", {})
            team = teams.get(self.team_name)

            if not team:
                return await interaction.followup.send("❌ Team not found.", ephemeral=True)

            try:
                new_points = int(self.points.value)
            except ValueError:
                return await interaction.followup.send("❌ Invalid point value.", ephemeral=True)

            team["points"] = new_points
            teams[self.team_name] = team
            db_set("teams", teams)
            db_set(f"submissions:{self.user_id}:{self.message_id}:status", "approved")

            await try_dm(
                interaction.client,
                self.user_id,
                f"✅ Your submission has been approved!\n🏆 `{self.team_name}` now has **{new_points}** points!"
            )

            await interaction.followup.send("✅ Submission approved and points updated!", ephemeral=True)
            await interaction.message.edit(view=None)

        except Exception as e:
            print(f"❌ ApproveModal error: {e}")
            await interaction.followup.send("❌ Something went wrong during approval.", ephemeral=True)


class RejectModal(discord.ui.Modal, title="Reject Submission"):
    reason = discord.ui.TextInput(
        label="Reason for rejection",
        style=discord.TextStyle.paragraph,
        required=True,
        placeholder="Explain why the submission was rejected..."
    )

    def __init__(self, user_id, message_id):
        super().__init__()
        self.user_id = user_id
        self.message_id = message_id
        print(
            f"📝 RejectModal created for user {user_id}, message {message_id}")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            db_set(f"submissions:{self.user_id}:{self.message_id}:status", "rejected")

            await try_dm(
                interaction.client,
                self.user_id,
                f"❌ Your submission was rejected.\n📄 Reason: {self.reason.value}"
            )

            await interaction.followup.send("❌ Submission rejected.", ephemeral=True)
            await interaction.message.edit(view=None)

        except Exception as e:
            print(f"❌ RejectModal error: {e}")
            await interaction.followup.send("❌ Something went wrong during rejection.", ephemeral=True)


# --- DM Utility ---


async def try_dm(client, user_id, message):
    try:
        user = await client.fetch_user(int(user_id))
        await user.send(message)
    except:
        pass
