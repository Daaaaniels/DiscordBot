# core/db.py
import os
import json
import aiosqlite
from typing import Any, Dict

# Use a persistent path via env (e.g., DB_PATH=/data/genesis.db on Railway)
DB_PATH = os.getenv("DB_PATH", "genesis.db")

# --- Internal helpers ---


async def _connect():
    db = await aiosqlite.connect(DB_PATH)
    # Sensible pragmas for a small bot DB
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA synchronous=NORMAL;")
    return db


def _serialize(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _deserialize(payload: str) -> Any:
    return json.loads(payload)

# --- Schema / Init ---


async def init_db():
    async with await _connect() as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS teams (
          name TEXT PRIMARY KEY,
          data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS submissions (
          id   TEXT PRIMARY KEY,
          data TEXT NOT NULL
        );
        """)
        await db.commit()

# --- General-purpose KV over two tables ---


async def get(key: str, table: str):
    column = "name" if table == "teams" else "id"
    async with await _connect() as db:
        cur = await db.execute(f"SELECT data FROM {table} WHERE {column} = ?", (key,))
        row = await cur.fetchone()
        await cur.close()
        return _deserialize(row[0]) if row else None


async def db_set(key: str, table: str, value: Any):
    column = "name" if table == "teams" else "id"
    payload = _serialize(value)
    async with await _connect() as db:
        await db.execute(
            f"INSERT OR REPLACE INTO {table} ({column}, data) VALUES (?, ?)",
            (key, payload),
        )
        await db.commit()


async def delete(key: str, table: str):
    column = "name" if table == "teams" else "id"
    async with await _connect() as db:
        await db.execute(f"DELETE FROM {table} WHERE {column} = ?", (key,))
        await db.commit()

# --- Team-specific helpers ---


async def get_teams() -> Dict[str, dict]:
    async with await _connect() as db:
        cur = await db.execute("SELECT name, data FROM teams")
        rows = await cur.fetchall()
        await cur.close()
        return {name: _deserialize(data) for name, data in rows}


async def save_team(name: str, data: dict):
    await db_set(name, "teams", data)


async def delete_team(name: str):
    await delete(name, "teams")


async def get_user_team(user_id: str | int):
    user_id = str(user_id)
    teams = await get_teams()
    for name, data in teams.items():
        members = [str(m) for m in data.get("members", [])]
        if user_id in members:
            return {"name": name, **data}
    return None


async def remove_user_from_all_teams(user_id: str | int):
    user_id = str(user_id)
    teams = await get_teams()
    changed = False
    for team_name, data in teams.items():
        members = [str(m) for m in data.get("members", [])]
        if user_id in members:
            data["members"] = [m for m in members if str(m) != user_id]
            changed = True
            if not data["members"]:
                await delete_team(team_name)
            else:
                await save_team(team_name, data)
    return changed
