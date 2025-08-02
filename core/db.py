import aiosqlite
import ast

DATABASE = "data.db"


async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS teams (
          name TEXT PRIMARY KEY,
          data TEXT
        );
        CREATE TABLE IF NOT EXISTS submissions (
          id TEXT PRIMARY KEY,
          data TEXT
        );
        """)
        await db.commit()


# --- General-Purpose Functions ---


async def get(key, table):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(f"SELECT data FROM {table} WHERE name = ?", (key,))
        row = await cursor.fetchone()
        return ast.literal_eval(row[0]) if row else None


async def set(key, table, value):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            f"INSERT OR REPLACE INTO {table} (name, data) VALUES (?, ?)",
            (key, repr(value))
        )
        await db.commit()


async def delete(key, table):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(f"DELETE FROM {table} WHERE name = ?", (key,))
        await db.commit()


# --- Team-Specific Helpers ---


async def get_teams():
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute("SELECT name, data FROM teams")
        rows = await cursor.fetchall()
        return {name: ast.literal_eval(data) for name, data in rows}


async def save_team(name, data):
    await set(name, "teams", data)


async def delete_team(name):
    await delete(name, "teams")


async def get_user_team(user_id):
    teams = await get_teams()
    for team_name, data in teams.items():
        if user_id in data.get("members", []):
            return {"name": team_name, **data}
    return None


async def remove_user_from_team_list(user_id):
    team_list = await get("team_list", "submissions") or []
    updated_list = []

    for team in team_list:
        if "members" in team and user_id in team["members"]:
            team["members"].remove(user_id)
        if team.get("leader_id") != user_id:
            updated_list.append(team)

    await set("team_list", "submissions", updated_list)
    
async def ensure_default_keys():
    if await get("teams", "teams") is None:
        await set("teams", "teams", {})
    if await get("team_list", "submissions") is None:
        await set("team_list", "submissions", [])
