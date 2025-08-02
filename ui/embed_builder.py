from core.db import get_teams, get_user_team
import discord


def build_panel_embed(user_id):
    user_team = get_user_team(user_id)  # pull fresh
    if user_team:
        data = get_teams().get(user_team["name"])  # pull fresh team info
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

    return discord.Embed(title="🛠️ Team Management Panel", description=desc, color=discord.Color.blue())
