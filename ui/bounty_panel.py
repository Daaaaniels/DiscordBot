# ui/bounty_panel.py

import discord

def create_bounty_embed(bounty: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"🔥 {bounty['title']}",
        description=bounty['mission'],
        color=discord.Color.gold()
    )
    embed.add_field(name="📍 Location", value=bounty['location'], inline=True)
    embed.add_field(name="💰 Reward", value=bounty['reward'], inline=True)
    embed.set_image(url=bounty['image'])
    embed.set_footer(text="Genesis Bounty Quest")
    return embed
