import discord
from core.db import get_teams


async def build_panel_embed(user_id):
    teams = await get_teams()
    user_team = None
    team_name = None

    # Find user's team
    for name, data in teams.items():
        if user_id in data.get("members", []):
            user_team = data
            team_name = name
            break

    if not user_team:
        desc = "You're not in a team. Use the buttons below to create or join one."
    else:
        leader = f"<@{user_team['leader']}>" if user_team.get(
            "leader") else "Unknown"
        members = ", ".join(
            f"<@{uid}>" for uid in user_team.get("members", [])) or "No members"

        desc = (
            f"**Team:** `{team_name}`\n"
            f"**Points:** {user_team.get('points', 0)}\n"
            f"**Leader:** {leader}\n"
            f"**Members ({len(user_team.get('members', []))}):** {members}"
        )

    return discord.Embed(
        title="🛠️ Team Management Panel",
        description=desc,
        color=discord.Color.blue()
    )
