import asyncio
import aiosqlite

DATABASE = "data.db"


async def wipe_all_team_data():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("DELETE FROM teams")
        await db.execute("DELETE FROM submissions")
        await db.commit()
        print("✅ All team and submission data wiped clean.")

asyncio.run(wipe_all_team_data())
