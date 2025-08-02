import discord
from core.db import get_teams, get_user_team


async def build_panel_embed(user_id):
    user_team = await get_user_team(user_id)
    if user_team:
        teams = await get_teams()
        data = teams.get(user_team["name"])
        if not data:
            return discord.Embed(
                title="🛠️ Team Management Panel",
                description="You're not in a team. Use the buttons below to create or join one.",
                color=discord.Color.blue()
            )

        leader = f"<@{data['leader']}>" if data.get("leader") else "Unknown"
        members = ", ".join(
            f"<@{uid}>" for uid in data.get("members", [])) or "No members"

        desc = (
            f"**Team:** `{user_team['name']}`\n"
            f"**Points:** {data.get('points', 0)}\n"
            f"**Leader:** {leader}\n"
            f"**Members ({len(data.get('members', []))}):** {members}"
        )
    else:
        desc = "You're not in a team. Use the buttons below to create or join one."

    return discord.Embed(
        title="🛠️ Team Management Panel",
        description=desc,
        color=discord.Color.blue()
    )
