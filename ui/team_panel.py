import discord
from core.db import get_teams, save_team, delete_team, get_user_team
from ui.embed_builder import build_panel_embed
from core.db import get
from core.db import remove_user_from_team_list


# --- Public: Send Panel ---


async def send_panel(interaction):
    try:
        print("🧪 Sending team panel...")
        user_id = str(interaction.user.id)

        # Don't get user_team here
        embed = build_panel_embed(user_id)
        view = TeamPanel(user_id)  # Remove second arg

        print("✅ Built panel view")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        print("✅ Sent panel")
    except Exception as e:
        print(f"❌ Error in send_panel: {e}")


# --- Team Panel View ---


class TeamPanel(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.user_team = get_user_team(self.user_id)  # fetch fresh every time
        print(f"📦 TeamPanel initialized with user_team: {self.user_team}")

        if self.user_team:
            self.add_item(self.LeaveTeamButton(self.user_team["name"]))
        else:
            self.add_item(self.CreateTeamButton())
            self.add_item(self.JoinTeamButton())

        self.add_item(self.TeamInfoButtonModal())
        self.add_item(self.LeaderboardButton())

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
            await interaction.response.defer(ephemeral=True)
            user_id = str(interaction.user.id)
            print(
                f"👋 LeaveTeamButton pressed by {user_id} for team '{self.team_name}'")

            teams = get_teams()
            print(f"📦 Loaded teams: {list(teams.keys())}")

            team = teams.get(self.team_name)
            if not team:
                print(f"❌ Team '{self.team_name}' not found.")
            else:
                print(f"🧾 Team data before leave: {team}")

            if not team or user_id not in team["members"]:
                await interaction.followup.send("You're not in this team anymore.", ephemeral=True)
                return

            team["members"].remove(user_id)
            print(f"🗑 Removed {user_id} from team '{self.team_name}'")

            role = discord.utils.get(
                interaction.guild.roles, name=self.team_name)
            if role:
                await interaction.user.remove_roles(role)

            if not team["members"]:
                if role:
                    await role.delete()
                print(f"❌ Team '{self.team_name}' deleted (no members left)")
                delete_team(self.team_name)
            else:
                if team["leader"] == user_id:
                    team["leader"] = team["members"][0]
                print("📤 Saving team:", team_name, team)
                save_team(team_name, team)
                print("📦 All teams after save:", get_teams())

                print(
                    f"✅ Team '{self.team_name}' saved after leader/member update")

            feedback = discord.Embed(
                description=f"✅ You left `{self.team_name}`.", color=discord.Color.blue()
            )
            await interaction.followup.send(embed=feedback, ephemeral=True)

            # Debug panel refresh with delay
            import asyncio
            await asyncio.sleep(0.3)
            await send_panel(interaction)

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
            teams = get_teams()

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
        print("🛠️ on_submit triggered")
        name = self.team_name.value.strip()
        code = self.team_code.value.strip()
        user_id = str(interaction.user.id)
        teams = get_teams()

        if not code.isdigit() or len(code) != 4:
            return await interaction.response.send_message("❌ Code must be a 4-digit number.", ephemeral=True)

        if name in teams:
            return await interaction.response.send_message("❌ Team already exists.", ephemeral=True)

        for data in teams.values():
            if data["leader"] == user_id:
                return await interaction.response.send_message("❌ You already created a team.", ephemeral=True)

        # ✅ Create role
        role = await interaction.guild.create_role(name=name)
        print("✅ Role created and assigned")
        await interaction.user.add_roles(role)

        print("✅ Confirmation sent")

        # ✅ Save to teams (used in leaderboard/panel)
        team_data = {
            "members": [user_id],
            "points": 0,
            "leader": user_id,
            "code": code
        }
        save_team(name, team_data)

        # ✅ Also save to team_list (used in /submit)
        existing = get("team_list", [])
        if not isinstance(existing, list):
            existing = []

        if not any(t["name"] == name for t in existing):
            new_team = {
                "name": name,
                "leader_id": user_id,
                "members": [user_id]
            }
            existing.append(new_team)
            from core.db import set  # make sure this is imported at the top
            set("team_list", existing)

        # ✅ Confirm success to user
        embed = discord.Embed(
            description=f"✅ Team `{name}` created successfully with join code `{code}`!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # ✅ Show updated panel
        await send_panel(interaction)
        print("✅ Panel resent")


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
        teams = get_teams()

        if name not in teams:
            return await interaction.response.send_message("❌ Team does not exist.", ephemeral=True)

        team = teams[name]

        if team.get("code") != code:
            return await interaction.response.send_message("❌ Incorrect join code.", ephemeral=True)

        for data in teams.values():
            if user_id in data["members"]:
                return await interaction.response.send_message("❌ You're already in a team.", ephemeral=True)

        team["members"].append(user_id)
        save_team(name, team)

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
        data = get_teams().get(name)

        if not data:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        member_mentions = []
        for user_id in data["members"]:
            member = interaction.guild.get_member(int(user_id))
            if member:
                member_mentions.append(member.mention)
            else:
                member_mentions.append(f"<@{user_id}> *(left server?)*")

        members_str = "\n".join(member_mentions) or "No members"
        leader_mention = f"<@{data['leader']}>" if data['leader'] else "Unknown"

        show_code = (str(interaction.user.id) ==
                     data["leader"]) or interaction.user.guild_permissions.administrator
        code_info = f"\n**Join Code:** `{data['code']}`" if show_code and data.get(
            "code") else ""

        embed = discord.Embed(
            title=f"📊 Stats for `{name}`",
            description=(
                f"**Leader:** {leader_mention}\n"
                f"**Points:** {data.get('points', 0)}\n"
                f"**Members ({len(data['members'])}):**\n{members_str}"
                f"{code_info}"
            ),
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
