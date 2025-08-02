import discord
from ui.embed_builder import build_panel_embed
from core.db import (
    get_teams,
    save_team,
    delete_team,
    get_user_team,
    get,
    db_set,  # ✅ only use this
    remove_user_from_all_teams
)
# --- Public: Send Panel ---


async def send_panel(interaction):
    try:
        print("🧪 Sending team panel...")
        user_id = str(interaction.user.id)

        embed = await build_panel_embed(user_id)
        view = await TeamPanel.create(user_id, interaction.guild)

        print("✅ Built panel view")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        print("✅ Sent panel")
    except Exception as e:
        print(f"❌ Error in send_panel: {e}")


# --- Team Panel View ---


class TeamPanel(discord.ui.View):
    def __init__(self, user_id, user_team):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.user_team = user_team

        if self.user_team:
            self.add_item(self.LeaveTeamButton(self.user_id,self.user_team["name"]))
        else:
            self.add_item(self.CreateTeamButton())
            self.add_item(self.JoinTeamButton())

        self.add_item(self.TeamInfoButtonModal())
        self.add_item(self.LeaderboardButton())

    @classmethod
    async def create(cls, user_id, guild):
        user_team = await get_user_team(str(user_id))
        print(f"📦 TeamPanel initialized with user_team: {user_team}")
        return cls(user_id, user_team)

    class CreateTeamButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="➕ Create Team", style=discord.ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(CreateTeamModal(interaction.user.id))

    class JoinTeamButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="📅 Join Team", style=discord.ButtonStyle.blurple)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(JoinTeamModal(interaction.user.id))

    class LeaveTeamButton(discord.ui.Button):
        def __init__(self, team_name):
            super().__init__(label="👋 Leave Team", style=discord.ButtonStyle.red)
            self.team_name = team_name

        async def callback(self, interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("🚫 You can't leave someone else's team.", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)

            success = await remove_user_from_all_teams(self.user_id)

            if success:
                await interaction.followup.send("✅ You have left your team.", ephemeral=True)
            else:
                await interaction.followup.send("⚠️ You were not found in any team.", ephemeral=True)

            # Rebuild the panel
            from ui.embed_builder import build_panel_embed  # adjust path if needed
            embed = await build_panel_embed(self.user_id)
            view = await TeamPanel.create(self.user_id, interaction.guild)
            await interaction.message.edit(embed=embed, view=view)


    class TeamInfoButtonModal(discord.ui.Button):
        def __init__(self):
            super().__init__(label="📊 Team Info", style=discord.ButtonStyle.gray)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(TeamInfoModal())

    class LeaderboardButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="🏆 Leaderboard", style=discord.ButtonStyle.gray)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            teams = await get_teams()

            if not teams:
                await interaction.followup.send("No teams yet.", ephemeral=True)
                return

            sorted_teams = sorted(
                teams.items(), key=lambda x: x[1].get("points", 0), reverse=True
            )
            text = ""
            for i, (team, data) in enumerate(sorted_teams, start=1):
                text += f"**#{i}** `{team}` — {data.get('points', 0)} points\n"

            embed = discord.Embed(
                title="🏆 Team Leaderboard", description=text, color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


# --- Modals ---


class CreateTeamModal(discord.ui.Modal, title="Create a New Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    team_code = discord.ui.TextInput(
        label="4-digit Join Code (e.g. 1234)", max_length=4)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        code = self.team_code.value.strip()
        user_id = str(interaction.user.id)
        teams = await get_teams()

        if not code.isdigit() or len(code) != 4:
            return await interaction.response.send_message("❌ Code must be a 4-digit number.", ephemeral=True)

        if name in teams:
            return await interaction.response.send_message("❌ Team already exists.", ephemeral=True)

        for data in teams.values():
            if data.get("leader") == user_id:
                return await interaction.response.send_message(
                    "❌ You already created a team.", ephemeral=True
                )

        role = await interaction.guild.create_role(name=name)
        await interaction.user.add_roles(role)

        team_data = {
            "members": [user_id],
            "points": 0,
            "leader": user_id,
            "code": code
        }
        await save_team(name, team_data)

        existing = await get("team_list", "submissions")  # ✅ fix table name
        if not isinstance(existing, list):
            existing = []

        if not any(t["name"] == name for t in existing):
            existing.append({
                "name": name,
                "leader_id": user_id,
                "members": [user_id]
            })
            await db_set("team_list", "submissions", existing)  # ✅ use db_set

        embed = discord.Embed(
            description=f"✅ Team `{name}` created successfully with join code `{code}`!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await send_panel(interaction)


class JoinTeamModal(discord.ui.Modal, title="Join a Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    team_code = discord.ui.TextInput(label="4-digit Join Code")

    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        code = self.team_code.value.strip()
        user_id = str(interaction.user.id)
        teams = await get_teams()

        if name not in teams:
            return await interaction.response.send_message("❌ Team does not exist.", ephemeral=True)

        team = teams[name]

        if team.get("code") != code:
            return await interaction.response.send_message("❌ Incorrect join code.", ephemeral=True)

        for data in teams.values():
            if user_id in data["members"]:
                return await interaction.response.send_message("❌ You're already in a team.", ephemeral=True)

        team["members"].append(user_id)
        await save_team(name, team)

        role = discord.utils.get(interaction.guild.roles, name=name)
        if role:
            await interaction.user.add_roles(role)

        embed = discord.Embed(
            description=f"✅ You joined `{name}`!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await send_panel(interaction)


class TeamInfoModal(discord.ui.Modal, title="Team Info"):
    team_name = discord.ui.TextInput(label="Team Name")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        teams = await get_teams()
        data = teams.get(name)

        if not data:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        member_mentions = []
        for user_id in data["members"]:
            member = interaction.guild.get_member(int(user_id))
            member_mentions.append(
                member.mention if member else f"<@{user_id}> *(left server?)*")

        members_str = "\n".join(member_mentions) or "No members"
        leader_mention = f"<@{data['leader']}>" if data['leader'] else "Unknown"

        show_code = (str(interaction.user.id) ==
                     data["leader"]) or interaction.user.guild_permissions.administrator
        code_info = f"\n**Join Code:** `{data['code']}`" if show_code and data.get(
            "code") else ""

        embed = discord.Embed(
            title=f"📊 Stats for `{name}`",
            description=f"**Leader:** {leader_mention}\n"
                        f"**Points:** {data.get('points', 0)}\n"
                        f"**Members ({len(data['members'])}):**\n{members_str}"
                        f"{code_info}",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
