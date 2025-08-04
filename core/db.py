import aiosqlite
import ast
from typing import Any

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
    column = "name" if table == "teams" else "id"
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(f"SELECT data FROM {table} WHERE {column} = ?", (key,))
        row = await cursor.fetchone()
        return ast.literal_eval(row[0]) if row else None


async def db_set(key: str, table: str, value: Any):
    column = "name" if table == "teams" else "id"
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            f"INSERT OR REPLACE INTO {table} ({column}, data) VALUES (?, ?)",
            (key, repr(value))
        )
        await db.commit()


async def delete(key, table):
    column = "name" if table == "teams" else "id"
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(f"DELETE FROM {table} WHERE {column} = ?", (key,))
        await db.commit()

# --- Team-Specific Helpers ---


async def get_teams():
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute("SELECT name, data FROM teams")
        rows = await cursor.fetchall()
        return {name: ast.literal_eval(data) for name, data in rows}


async def save_team(name, data):
    await db_set(name, "teams", data)


async def delete_team(name):
    await delete(name, "teams")


async def get_user_team(user_id):
    teams = await get_teams()
    for name, data in teams.items():
        if user_id in data.get("members", []):
            print(f"[✅] get_user_team: Found in `teams` - {name}")
            return {"name": name, **data}

    print(f"[⛔] get_user_team: User {user_id} not found in any team.")
    return None


async def remove_user_from_all_teams(user_id):
    teams = await get_teams()
    changed = False

    for team_name, data in teams.items():
        if user_id in data.get("members", []):
            data["members"].remove(user_id)
            changed = True

            if not data["members"]:
                await delete(team_name, "teams")
                print(f"🧹 Deleted empty team: {team_name}")
            else:
                await save_team(team_name, data)
                print(f"✅ Removed user {user_id} from team {team_name}")

    return changed
