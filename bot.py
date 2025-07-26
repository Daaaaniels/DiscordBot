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


@bot.event
async def on_message(message):
    print(f"[DEBUG] Heard message: {message.content}")
    await bot.process_commands(message)

# --- Buttons ---


class TeamStatsButton(discord.ui.View):
    def __init__(self, team_name):
        super().__init__(timeout=None)
        self.team_name = team_name

    @discord.ui.button(label="📊 Team Stats", style=discord.ButtonStyle.blurple)
    async def show_team_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        team_data = teams.get(self.team_name)
        if not team_data:
            await interaction.response.send_message(f"Team `{self.team_name}` no longer exists.", ephemeral=True)
            return

        member_count = len(team_data["members"])
        points = team_data.get("points", 0)
        leader_id = team_data.get("leader", "Unknown")

        embed = discord.Embed(
            title=f"🔢 Stats for `{self.team_name}`",
            description=f"**Members:** {member_count}\n**Points:** {points}\n**Leader:** <@{leader_id}>",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- !create_team ---


@bot.command(name="create_team")
async def create_team(ctx, *, team_name: str):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    if team_name in teams:
        embed = discord.Embed(
            title="⚠️ Team Exists", description=f"Team `{team_name}` already exists.", color=discord.Color.orange())
        return await ctx.send(embed=embed)

    role = await guild.create_role(name=team_name)
    await ctx.author.add_roles(role)

    teams[team_name] = {"members": [user_id], "points": 0, "leader": user_id}
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    embed = discord.Embed(title="🎉 Team Created",
                          description=f"You created team `{team_name}` and received the role. You are the team leader.",
                          color=discord.Color.green())
    await ctx.send(embed=embed, view=TeamStatsButton(team_name))

# --- !join_team ---


@bot.command(name="join_team")
async def join_team(ctx, *, team_name: str):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    if team_name not in teams:
        embed = discord.Embed(title="❌ Team Not Found", description=f"No team named `{team_name}` exists.",
                              color=discord.Color.red())
        return await ctx.send(embed=embed)

    for name, data in teams.items():
        if user_id in data["members"]:
            embed = discord.Embed(title="⚠️ Already in a Team",
                                  description=f"You are already in `{name}`. Leave first.", color=discord.Color.orange())
            return await ctx.send(embed=embed)

    teams[team_name]["members"].append(user_id)
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    role = discord.utils.get(guild.roles, name=team_name)
    if role:
        await ctx.author.add_roles(role)

    embed = discord.Embed(
        title="✅ Joined Team", description=f"You joined `{team_name}` and received the role.", color=discord.Color.green())
    await ctx.send(embed=embed, view=TeamStatsButton(team_name))

# --- !leave_team ---


@bot.command(name="leave_team")
async def leave_team(ctx):
    user_id = str(ctx.author.id)
    guild = ctx.guild

    for team_name, data in list(teams.items()):
        if user_id in data["members"]:
            data["members"].remove(user_id)
            role = discord.utils.get(guild.roles, name=team_name)

            if user_id == data.get("leader"):
                if data["members"]:
                    data["leader"] = data["members"][0]  # new leader
                    new_leader = f"<@{data['leader']}>"
                else:
                    data["leader"] = None
                    new_leader = "None"
            else:
                new_leader = f"<@{data['leader']}>"

            if role:
                await ctx.author.remove_roles(role)
            if not data["members"]:
                if role:
                    await role.delete()
                del teams[team_name]

            with open(TEAM_FILE, "w") as f:
                json.dump(teams, f, indent=4)

            embed = discord.Embed(
                title="👋 Left Team", description=f"You left `{team_name}`.\nNew Leader: {new_leader}",
                color=discord.Color.blue())
            return await ctx.send(embed=embed)

    embed = discord.Embed(title="⚠️ Not in Team",
                          description="You are not currently in any team.", color=discord.Color.red())
    await ctx.send(embed=embed)

# --- !kick_member ---


@bot.command(name="kick_member")
async def kick_member(ctx, member: discord.Member):
    user_id = str(ctx.author.id)
    target_id = str(member.id)
    guild = ctx.guild

    for team_name, data in teams.items():
        if user_id == data.get("leader"):
            if target_id in data["members"]:
                if target_id == user_id:
                    embed = discord.Embed(title="❌ Cannot Kick Self",
                                          description="You cannot kick yourself from your own team.",
                                          color=discord.Color.red())
                    return await ctx.send(embed=embed)

                data["members"].remove(target_id)
                role = discord.utils.get(guild.roles, name=team_name)
                if role:
                    await member.remove_roles(role)

                with open(TEAM_FILE, "w") as f:
                    json.dump(teams, f, indent=4)

                embed = discord.Embed(
                    title="👢 Member Kicked",
                    description=f"<@{target_id}> has been removed from `{team_name}`.",
                    color=discord.Color.orange()
                )
                return await ctx.send(embed=embed)

            else:
                embed = discord.Embed(title="⚠️ Not a Member",
                                      description=f"{member.mention} is not in your team.",
                                      color=discord.Color.red())
                return await ctx.send(embed=embed)

    embed = discord.Embed(title="🚫 Not a Leader",
                          description="Only the team leader can use this command.",
                          color=discord.Color.red())
    await ctx.send(embed=embed)

# --- !team_info ---


@bot.command(name="team_info")
async def team_info(ctx, *, team_name: str = None):
    if not team_name:
        embed = discord.Embed(title="ℹ️ Missing Team Name",
                              description="Use `!team_info <team_name>`.", color=discord.Color.orange())
        return await ctx.send(embed=embed)

    team_data = teams.get(team_name)
    if not team_data:
        embed = discord.Embed(
            title="❌ Team Not Found", description=f"Team `{team_name}` does not exist.", color=discord.Color.red())
        return await ctx.send(embed=embed)

    member_count = len(team_data["members"])
    points = team_data.get("points", 0)
    leader_id = team_data.get("leader", "Unknown")

    embed = discord.Embed(
        title=f"🔢 Stats for `{team_name}`",
        description=f"**Members:** {member_count}\n**Points:** {points}\n**Leader:** <@{leader_id}>",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

# --- !leaderboard ---


@bot.command(name="leaderboard")
async def leaderboard(ctx):
    if not teams:
        embed = discord.Embed(
            title="📉 Leaderboard",
            description="No teams found yet.",
            color=discord.Color.dark_gray()
        )
        return await ctx.send(embed=embed)

    sorted_teams = sorted(
        teams.items(), key=lambda x: x[1].get("points", 0), reverse=True)

    leaderboard_text = ""
    for index, (team_name, data) in enumerate(sorted_teams, start=1):
        points = data.get("points", 0)
        leaderboard_text += f"**#{index}** — `{team_name}`: {points} points\n"

    embed = discord.Embed(
        title="🏆 Team Leaderboard",
        description=leaderboard_text,
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

# --- Admin: Kick Member ---


@bot.command(name="admin_kick")
@has_permissions(administrator=True)
async def admin_kick(ctx, team_name: str, member: discord.Member):
    user_id = str(member.id)

    if team_name not in teams or user_id not in teams[team_name]["members"]:
        return await ctx.send(embed=discord.Embed(
            title="❌ Error",
            description=f"{member.mention} is not in team `{team_name}`.",
            color=discord.Color.red()
        ))

    teams[team_name]["members"].remove(user_id)
    role = discord.utils.get(ctx.guild.roles, name=team_name)
    if role:
        await member.remove_roles(role)

    await ctx.send(embed=discord.Embed(
        title="👢 Kicked",
        description=f"{member.mention} was removed from `{team_name}`.",
        color=discord.Color.orange()
    ))

    # Delete team if no members remain
    if not teams[team_name]["members"]:
        if role:
            await role.delete()
        del teams[team_name]

    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)


# --- Admin: Add Points ---
@bot.command(name="admin_add_points")
@has_permissions(administrator=True)
async def admin_add_points(ctx, team_name: str, amount: int):
    if team_name not in teams:
        return await ctx.send(embed=discord.Embed(
            title="❌ Error",
            description=f"Team `{team_name}` not found.",
            color=discord.Color.red()
        ))

    teams[team_name]["points"] += amount
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    await ctx.send(embed=discord.Embed(
        title="➕ Points Assigned",
        description=f"Added `{amount}` points to `{team_name}`.",
        color=discord.Color.green()
    ))


# --- Admin: Remove Points ---
@bot.command(name="admin_remove_points")
@has_permissions(administrator=True)
async def admin_remove_points(ctx, team_name: str, amount: int):
    if team_name not in teams:
        return await ctx.send(embed=discord.Embed(
            title="❌ Error",
            description=f"Team `{team_name}` not found.",
            color=discord.Color.red()
        ))

    teams[team_name]["points"] = max(0, teams[team_name]["points"] - amount)
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    await ctx.send(embed=discord.Embed(
        title="➖ Points Reduced",
        description=f"Removed `{amount}` points from `{team_name}`.",
        color=discord.Color.orange()
    ))


# --- Admin: Delete Team ---
@bot.command(name="admin_delete_team")
@has_permissions(administrator=True)
async def admin_delete_team(ctx, *, team_name: str):
    if team_name not in teams:
        return await ctx.send(embed=discord.Embed(
            title="❌ Error",
            description=f"Team `{team_name}` not found.",
            color=discord.Color.red()
        ))

    role = discord.utils.get(ctx.guild.roles, name=team_name)
    if role:
        await role.delete()

    del teams[team_name]
    with open(TEAM_FILE, "w") as f:
        json.dump(teams, f, indent=4)

    await ctx.send(embed=discord.Embed(
        title="🗑️ Team Deleted",
        description=f"Team `{team_name}` has been deleted.",
        color=discord.Color.red()
    ))


# --- Handle Missing Permissions Error ---
@admin_kick.error
@admin_add_points.error
@admin_remove_points.error
@admin_delete_team.error
async def admin_permission_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.send(embed=discord.Embed(
            title="🚫 No Permission",
            description="You must be an **Administrator** to use this command.",
            color=discord.Color.red()
        ))


# --- Run Bot ---
with open("token.txt") as f:
    token = f.read().strip()

bot.run(token)
