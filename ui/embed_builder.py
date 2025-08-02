from discord import Embed, Color
from core.db import get_user_team


def build_panel_embed(user_id):
    team = get_user_team(user_id)

    if team:
        leader = f"<@{team['leader_id']}>" if team.get(
            "leader_id") else "Unknown"
        members = ", ".join(
            f"<@{uid}>" for uid in team.get("members", [])) or "No members"
        desc = (
            f"**Team:** `{team['name']}`\n"
            f"**Points:** {team.get('points', 0)}\n"
            f"**Leader:** {leader}\n"
            f"**Members ({len(team['members'])}):** {members}"
        )
    else:
        desc = "You're not in a team. Use the buttons below to create or join one."

    return Embed(title="🛠️ Team Management Panel", description=desc, color=Color.blue())
