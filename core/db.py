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

    # Optional: fallback check in team_list if needed
    team_list = await get("team_list", "submissions") or []
    for team in team_list:
        if "members" in team and user_id in team["members"]:
            print(f"[⚠️] get_user_team: Found only in `team_list` - {team.get('name')}")
            return {"name": team.get("name"), **team}

    print(f"[⛔] get_user_team: User {user_id} not found in any team.")
    return None



# core/db.py

async def remove_user_from_all_teams(user_id):
    teams = await get_teams()
    team_list = await get("team_list", "submissions") or []

    changed = False

    # Remove from `teams`
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

    # Remove from `team_list`
    new_team_list = []
    for team in team_list:
        if user_id in team.get("members", []):
            team["members"].remove(user_id)
            changed = True
        if team.get("leader_id") != user_id:
            new_team_list.append(team)

    if changed:
        await db_set("team_list", "submissions", new_team_list)
        print("✅ Cleaned user from team_list")

    return changed



async def ensure_default_keys():
    if await get("teams", "teams") is None:
        await db_set("teams", "teams", {})
    if await get("team_list", "submissions") is None:
        await db_set("team_list", "submissions", [])


async def validate_team_data():
    teams = await get_teams()
    team_list = await get("team_list", "submissions") or []

    valid_team_names = set(teams.keys())
    cleaned_list = []

    for team in team_list:
        name = team.get("name")
        if name in valid_team_names:
            cleaned_list.append(team)
        else:
            print(
                f"🧹 Removed ghost team '{name}' from team_list (no longer exists in teams table)")

    if len(cleaned_list) != len(team_list):
        await db_set("team_list", "submissions", cleaned_list)
        print("✅ team_list cleaned and updated.")
    else:
        print("✅ team_list is already clean.")


async def clean_malformed_teams():
    teams = await get_teams()
    cleaned = {}

    for name, data in teams.items():
        if all(key in data for key in ["leader", "members", "code"]):
            cleaned[name] = data
        else:
            print(f"🧹 Removed malformed team: {name} ➤ Missing keys")

    if len(cleaned) != len(teams):
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute("DELETE FROM teams")
            for name, data in cleaned.items():
                await db.execute(
                    "INSERT OR REPLACE INTO teams (name, data) VALUES (?, ?)",
                    (name, repr(data))
                )
            await db.commit()

        print("✅ Malformed teams removed and DB cleaned.")
    else:
        print("✅ No malformed teams found.")
