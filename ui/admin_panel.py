import discord
from core.db import get_teams, save_team, delete_team


class AdminPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(self.KickMemberModal())
        self.add_item(self.AddPointsModal())
        self.add_item(self.SubtractPointsModal())
        self.add_item(self.DeleteTeamModal())

    class KickMemberModal(discord.ui.Button):
        def __init__(self):
            super().__init__(label="📤 Kick Member", style=discord.ButtonStyle.red)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(AdminKickMemberModal())

    class AddPointsModal(discord.ui.Button):
        def __init__(self):
            super().__init__(label="➕ Add Points", style=discord.ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(AdminAddPointsModal())

    class SubtractPointsModal(discord.ui.Button):
        def __init__(self):
            super().__init__(label="➖ Subtract Points", style=discord.ButtonStyle.blurple)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(AdminSubtractPointsModal())

    class DeleteTeamModal(discord.ui.Button):
        def __init__(self):
            super().__init__(label="🗑️ Delete Team", style=discord.ButtonStyle.gray)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(AdminDeleteTeamModal())

# --- Modals ---


class AdminKickMemberModal(discord.ui.Modal, title="Kick Member from Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    member_id = discord.ui.TextInput(label="User ID to Kick")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        member = self.member_id.value.strip()
        team = get_teams().get(name)

        if not team:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        if member not in team["members"]:
            return await interaction.response.send_message("❌ Member not in that team.", ephemeral=True)

        team["members"].remove(member)

        if team["leader"] == member:
            team["leader"] = team["members"][0] if team["members"] else None

        role = discord.utils.get(interaction.guild.roles, name=name)
        member_obj = interaction.guild.get_member(int(member))

        if not team["members"]:
            if role:
                await role.delete()
            delete_team(name)
        else:
            save_team(name, team)
            if role and member_obj:
                await member_obj.remove_roles(role)

        await interaction.response.send_message("✅ Member kicked.", ephemeral=True)


class AdminAddPointsModal(discord.ui.Modal, title="Add Points to Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    points = discord.ui.TextInput(label="Points to Add")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        teams = get_teams()

        if name not in teams:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        try:
            amount = int(self.points.value)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)

        teams[name]["points"] += amount
        save_team(name, teams[name])

        await interaction.response.send_message(f"✅ Added {amount} points to `{name}`.", ephemeral=True)


class AdminSubtractPointsModal(discord.ui.Modal, title="Subtract Points from Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    points = discord.ui.TextInput(label="Points to Subtract")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        teams = get_teams()

        if name not in teams:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        try:
            amount = int(self.points.value)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)

        teams[name]["points"] = max(0, teams[name]["points"] - amount)
        save_team(name, teams[name])

        await interaction.response.send_message(f"✅ Subtracted {amount} points from `{name}`.", ephemeral=True)


class AdminDeleteTeamModal(discord.ui.Modal, title="Delete Team"):
    team_name = discord.ui.TextInput(label="Team Name")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        if name not in get_teams():
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        role = discord.utils.get(interaction.guild.roles, name=name)
        if role:
            await role.delete()

        delete_team(name)
        await interaction.response.send_message(f"✅ Team `{name}` deleted.", ephemeral=True)
