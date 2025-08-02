# bounty/bounty_posting.py

from bounty.bounty_data import BOUNTIES
from ui.bounty_panel import create_bounty_embed
from core.db import get, set


async def post_next_bounty(channel):
    try:
        index = int(get("last_bounty_index", 0))
        bounty = BOUNTIES[index]

        embed = create_bounty_embed(bounty)
        await channel.send(embed=embed)

        # Update index for next bounty
        next_index = (index + 1) % len(BOUNTIES)
        set("last_bounty_index", next_index)
        set("active_bounty", bounty)
        return True
    except Exception as e:
        print(f"[Bounty Error] Failed to post bounty: {e}")
        return False
