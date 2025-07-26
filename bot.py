import discord
from discord.ext import commands
import json
import os

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

# --- Helper: Get User Team ---


def get_user_team(user_id):
    for name, data in teams.items():
        if str(user_id) in data["members"]:
            return name
    return None

# --- Panel View ---


class TeamPanel(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)
        self.user_team = get_user_team(self.user_id)

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
            user_id = str(interaction.user.id)
            team = teams.get(self.team_name)

            if not team or user_id not in team["members"]:
                return await interaction.response.send_message("You're not in this team anymore.", ephemeral=True)

            team["members"].remove(user_id)

            role = discord.utils.get(
                interaction.guild.roles, name=self.team_name)
            if role:
                await interaction.user.remove_roles(role)

            if team["leader"] == user_id:
                team["leader"] = team["members"][0] if team["members"] else None

            if not team["members"]:
                if role:
                    await role.delete()
                del teams[self.team_name]

            with open(TEAM_FILE, "w") as f:
                json.dump(teams, f, indent=4)

            feedback = discord.Embed(
                description=f"✅ You left `{self.team_name}`.", color=discord.Color.blue())
            await interaction.response.send_message(embed=feedback, ephemeral=True)
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
            if not teams:
                return await interaction.response.send_message("No teams yet.", ephemeral=True)

            sorted_teams = sorted(
                teams.items(), key=lambda x: x[1].get("points", 0), reverse=True)
            text = ""
            for i, (team, data) in enumerate(sorted_teams, start=1):
                text += f"**#{i}** `{team}` — {data.get('points', 0)} points\n"

            embed = discord.Embed(title="🏆 Team Leaderboard",
                                  description=text, color=discord.Color.gold())
            await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Embeds ---


def build_panel_embed(user_id):
    user_team = get_user_team(user_id)
    if user_team:
        data = teams[user_team]
        leader = f"<@{data['leader']}>" if data['leader'] else "Unknown"
        description = f"**Team:** `{user_team}`\n**Points:** {data.get('points', 0)}\n**Members:** {len(data['members'])}\n**Leader:** {leader}"
    else:
        description = "You're not in a team. Use the buttons below to create or join one."

    return discord.Embed(title="🛠️ Team Management Panel", description=description, color=discord.Color.blue())

# --- Helper to Send Panel ---


async def send_panel(interaction):
    embed = build_panel_embed(interaction.user.id)
    view = TeamPanel(interaction.user.id)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

# --- Modals ---


class CreateTeamModal(discord.ui.Modal, title="Create a New Team"):
    team_name = discord.ui.TextInput(label="Team Name")

    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        user_id = str(interaction.user.id)

        if name in teams:
            return await interaction.response.send_message("Team already exists.", ephemeral=True)

        for data in teams.values():
            if data["leader"] == user_id:
                return await interaction.response.send_message("You already created a team.", ephemeral=True)

        role = await interaction.guild.create_role(name=name)
        await interaction.user.add_roles(role)

        teams[name] = {"members": [user_id], "points": 0, "leader": user_id}
        with open(TEAM_FILE, "w") as f:
            json.dump(teams, f, indent=4)

        feedback = discord.Embed(
            description=f"✅ Team `{name}` created successfully!", color=discord.Color.green())
        await interaction.response.send_message(embed=feedback, ephemeral=True)
        await send_panel(interaction)


class JoinTeamModal(discord.ui.Modal, title="Join a Team"):
    team_name = discord.ui.TextInput(label="Team Name")

    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        user_id = str(interaction.user.id)

        if name not in teams:
            return await interaction.response.send_message("Team does not exist.", ephemeral=True)

        for data in teams.values():
            if user_id in data["members"]:
                return await interaction.response.send_message("You're already in a team.", ephemeral=True)

        teams[name]["members"].append(user_id)
        role = discord.utils.get(interaction.guild.roles, name=name)
        if role:
            await interaction.user.add_roles(role)

        with open(TEAM_FILE, "w") as f:
            json.dump(teams, f, indent=4)

        feedback = discord.Embed(
            description=f"✅ You joined `{name}`!", color=discord.Color.green())
        await interaction.response.send_message(embed=feedback, ephemeral=True)
        await send_panel(interaction)


class TeamInfoModal(discord.ui.Modal, title="Team Info"):
    team_name = discord.ui.TextInput(label="Team Name")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        data = teams.get(name)
        if not data:
            return await interaction.response.send_message("Team not found.", ephemeral=True)

        embed = discord.Embed(
            title=f"Stats for `{name}`",
            description=f"**Members:** {len(data['members'])}\n**Points:** {data.get('points', 0)}\n**Leader:** <@{data['leader']}>",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Command ---


@bot.command(name="panel")
async def panel(ctx):
    embed = build_panel_embed(ctx.author.id)
    view = TeamPanel(ctx.author.id)
    await ctx.send(embed=embed, view=view)


# --- Admin Panel View ---

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


# --- Admin Modals ---

class AdminKickMemberModal(discord.ui.Modal, title="Kick Member from Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    member_id = discord.ui.TextInput(label="User ID to Kick")

    async def on_submit(self, interaction: discord.Interaction):
        team = teams.get(self.team_name.value.strip())
        if not team:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        member = self.member_id.value.strip()
        if member not in team["members"]:
            return await interaction.response.send_message("❌ Member not in that team.", ephemeral=True)

        team["members"].remove(member)

        if team["leader"] == member:
            team["leader"] = team["members"][0] if team["members"] else None

        if not team["members"]:
            role = discord.utils.get(
                interaction.guild.roles, name=self.team_name.value.strip())
            if role:
                await role.delete()
            del teams[self.team_name.value.strip()]

        else:
            role = discord.utils.get(
                interaction.guild.roles, name=self.team_name.value.strip())
            member_obj = interaction.guild.get_member(int(member))
            if role and member_obj:
                await member_obj.remove_roles(role)

        with open(TEAM_FILE, "w") as f:
            json.dump(teams, f, indent=4)

        await interaction.response.send_message("✅ Member kicked.", ephemeral=True)


class AdminAddPointsModal(discord.ui.Modal, title="Add Points to Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    points = discord.ui.TextInput(label="Points to Add")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        if name not in teams:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        try:
            add = int(self.points.value)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)

        teams[name]["points"] += add
        with open(TEAM_FILE, "w") as f:
            json.dump(teams, f, indent=4)

        await interaction.response.send_message(f"✅ Added {add} points to `{name}`.", ephemeral=True)


class AdminSubtractPointsModal(discord.ui.Modal, title="Subtract Points from Team"):
    team_name = discord.ui.TextInput(label="Team Name")
    points = discord.ui.TextInput(label="Points to Subtract")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        if name not in teams:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        try:
            subtract = int(self.points.value)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)

        teams[name]["points"] = max(0, teams[name]["points"] - subtract)
        with open(TEAM_FILE, "w") as f:
            json.dump(teams, f, indent=4)

        await interaction.response.send_message(f"✅ Subtracted {subtract} points from `{name}`.", ephemeral=True)


class AdminDeleteTeamModal(discord.ui.Modal, title="Delete Team"):
    team_name = discord.ui.TextInput(label="Team Name")

    async def on_submit(self, interaction: discord.Interaction):
        name = self.team_name.value.strip()
        if name not in teams:
            return await interaction.response.send_message("❌ Team not found.", ephemeral=True)

        role = discord.utils.get(interaction.guild.roles, name=name)
        if role:
            await role.delete()

        del teams[name]

        with open(TEAM_FILE, "w") as f:
            json.dump(teams, f, indent=4)

        await interaction.response.send_message(f"✅ Team `{name}` deleted.", ephemeral=True)


# --- Admin Panel Command ---

@bot.command(name="admin_panel")
@commands.has_permissions(administrator=True)
async def admin_panel(ctx):
    embed = discord.Embed(title="🛠️ Admin Tools",
                          description="Manage teams with the buttons below.", color=discord.Color.red())
    await ctx.send(embed=embed, view=AdminPanel())


# --- Run ---
token = os.getenv("DISCORD_TOKEN")
bot.run(token)

