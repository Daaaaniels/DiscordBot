import discord
from core.db import get_teams, save_team, delete_team


class AdminPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(self.KickMemberButton())
        self.add_item(self.UpdatePointsButton())
        self.add_item(self.DeleteTeamButton())

    class KickMemberButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="📤 Kick Member", style=discord.ButtonStyle.red)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(AdminKickMemberModal())

    class UpdatePointsButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="🔢 Update Team Points", style=discord.ButtonStyle.blurple)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(AdminUpdatePointsModal())

    class DeleteTeamButton(discord.ui.Button):
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
        teams = await get_teams()
        team = teams.get(name)

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
            await delete_team(name)
        else:
            await save_team(name, team)
            if role and member_obj:
                await member_obj.remove_roles(role)

        await interaction.response.send_message("✅ Member kicked.", ephemeral=True)


class AdminUpdatePointsModal(discord.ui.Modal, title="Update Total Points for Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    new_points = discord.ui.TextInput(label="New Total Points")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        teams = await get_teams()

        if name not in teams:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        try:
            points = int(self.new_points.value)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)

        teams[name]["points"] = points
        await save_team(name, teams[name])

        await interaction.response.send_message(f"✅ Set `{name}` points to **{points}**.", ephemeral=True)


class AdminDeleteTeamModal(discord.ui.Modal, title="Delete Team"):
    team_name = discord.ui.TextInput(label="Team Name")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        teams = await get_teams()

        if name not in teams:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        role = discord.utils.get(interaction.guild.roles, name=name)
        if role:
            await role.delete()

        await delete_team(name)
        await interaction.response.send_message(f"✅ Team `{name}` deleted.", ephemeral=True)
