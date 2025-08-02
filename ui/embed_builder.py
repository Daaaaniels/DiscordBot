import discord
from core.db import get_user_team


async def build_panel_embed(user_id):
    user_team = await get_user_team(user_id)

    if not user_team:
        desc = "You're not in a team. Use the buttons below to create or join one."
    else:
        leader = f"<@{user_team['leader']}>" if user_team.get(
            "leader") else "Unknown"
        members = ", ".join(
            f"<@{uid}>" for uid in user_team.get("members", [])) or "No members"

        desc = (
            f"**Team:** `{user_team['name']}`\n"
            f"**Points:** {user_team.get('points', 0)}\n"
            f"**Leader:** {leader}\n"
            f"**Members ({len(user_team.get('members', []))}):** {members}"
        )

    return discord.Embed(
        title="🛠️ Team Management Panel",
        description=desc,
        color=discord.Color.blue()
    )
