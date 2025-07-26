import discord
from discord.ext import commands
import json
import os
from discord.ext.commands import has_permissions, MissingPermissions

# --- Setup ---
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
TEAM_FILE = "teams.json"

# --- Load or initialize team data ---
if os.path.exists(TEAM_FILE):
    with open(TEAM_FILE, "r") as f:
        teams = json.load(f)
else:
    teams = {}

# --- Bot ready ---


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# --- Modals ---


class CreateTeamModal(discord.ui.Modal, title="Create a New Team"):
    team_name = discord.ui.TextInput(
        label="Team Name", placeholder="Enter a unique team name")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        user_id = str(interaction.user.id)

        # Check if user already leads a team
        for team, data in teams.items():
            if data.get("leader") == user_id:
                return await interaction.response.send_message("❌ You already created a team.", ephemeral=True)

        if name in teams:
            return await interaction.response.send_message("❌ Team already exists.", ephemeral=True)

        role = await interaction.guild.create_role(name=name)
        await interaction.user.add_roles(role)

        teams[name] = {"members": [user_id], "points": 0, "leader": user_id}
        with open(TEAM_FILE, "w") as f:
            json.dump(teams, f, indent=4)

        await interaction.response.send_message(f"✅ Team `{name}` created and you are the leader!", ephemeral=True)


class JoinTeamModal(discord.ui.Modal, title="Join a Team"):
    team_name = discord.ui.TextInput(
        label="Team Name", placeholder="Enter existing team name")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        user_id = str(interaction.user.id)

        if name not in teams:
            return await interaction.response.send_message("❌ Team does not exist.", ephemeral=True)

        for t, d in teams.items():
            if user_id in d["members"]:
                return await interaction.response.send_message("❌ You are already in a team.", ephemeral=True)

        teams[name]["members"].append(user_id)
        with open(TEAM_FILE, "w") as f:
            json.dump(teams, f, indent=4)

        role = discord.utils.get(interaction.guild.roles, name=name)
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message(f"✅ You joined `{name}`!", ephemeral=True)


class TeamInfoModal(discord.ui.Modal, title="Team Information"):
    team_name = discord.ui.TextInput(
        label="Team Name", placeholder="Enter the team name")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        team_data = teams.get(name)

        if not team_data:
            return await interaction.response.send_message(f"❌ Team `{name}` does not exist.", ephemeral=True)

        member_count = len(team_data["members"])
        points = team_data.get("points", 0)
        leader_id = team_data.get("leader", "Unknown")

        embed = discord.Embed(
            title=f"🔢 Stats for `{name}`",
            description=f"**Members:** {member_count}\n**Points:** {points}\n**Leader:** <@{leader_id}>",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Panel View ---


class TeamPanel(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.user_team = None
        for name, data in teams.items():
            if str(user_id) in data["members"]:
                self.user_team = name
                break

        if self.user_team:
            self.add_item(self.LeaveTeamButton(self.user_team))
        else:
            self.add_item(self.CreateTeamButton())
            self.add_item(self.JoinTeamButton())

        self.add_item(self.TeamInfoButtonModal())
        self.add_item(self.LeaderboardButton())

    class CreateTeamButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="➕ Create Team", style=discord.ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(CreateTeamModal())

    class JoinTeamButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="📥 Join Team", style=discord.ButtonStyle.blurple)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(JoinTeamModal())

    class LeaveTeamButton(discord.ui.Button):
        def __init__(self, team_name):
            super().__init__(label="👋 Leave Team", style=discord.ButtonStyle.red)
            self.team_name = team_name

        async def callback(self, interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            team = teams.get(self.team_name)

            if not team or user_id not in team["members"]:
                return await interaction.response.send_message("⚠️ You're not in this team anymore.", ephemeral=True)

            # Remove member
            team["members"].remove(user_id)

            # Remove role
            role = discord.utils.get(
                interaction.guild.roles, name=self.team_name)
            if role:
                await interaction.user.remove_roles(role)

            # Leader logic
            if team.get("leader") == user_id:
                if team["members"]:
                    team["leader"] = team["members"][0]
                else:
                    team["leader"] = None

            # If team is empty, delete it and the role
            if not team["members"]:
                if role:
                    await role.delete()
                del teams[self.team_name]

            with open(TEAM_FILE, "w") as f:
                json.dump(teams, f, indent=4)

            await interaction.response.send_message(f"✅ You left `{self.team_name}`.", ephemeral=True)

    class TeamInfoButtonModal(discord.ui.Button):
        def __init__(self):
            super().__init__(label="📊 Team Info", style=discord.ButtonStyle.gray)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(TeamInfoModal())

    class LeaderboardButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="🏆 Leaderboard", style=discord.ButtonStyle.gray)

        async def callback(self, interaction: discord.Interaction):
            if not teams:
                return await interaction.response.send_message("📉 No teams yet.", ephemeral=True)

            sorted_teams = sorted(
                teams.items(), key=lambda x: x[1].get("points", 0), reverse=True)
            leaderboard_text = ""
            for i, (team, data) in enumerate(sorted_teams, start=1):
                leaderboard_text += f"**#{i}** `{team}` — {data.get('points', 0)} points\n"

            embed = discord.Embed(
                title="🏆 Team Leaderboard", description=leaderboard_text, color=discord.Color.gold())
            await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Panel Command ---


@bot.command(name="panel")
async def panel(ctx):
    view = TeamPanel(ctx.author.id)
    await ctx.send("🛠️ Team Management Panel:", view=view)

# --- Run Bot ---
with open("token.txt") as f:
    token = f.read().strip()

bot.run(token)
