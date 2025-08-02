try:
    from replit import db as replit_db
    _ = replit_db.get("test_key", "test_default")
    db = replit_db
    print("✅ Using Replit DB")
except Exception:
    class FakeDB:
        def __init__(self):
            self._data = {}

        def get(self, key, default=None):
            return self._data.get(key, default)

        def __setitem__(self, key, value):
            self._data[key] = value

        def __getitem__(self, key):
            return self._data[key]

        def __delitem__(self, key):
            if key in self._data:
                del self._data[key]

        def __contains__(self, key):
            return key in self._data

        def prefix(self, start):
            return [k for k in self._data if k.startswith(start)]

    db = FakeDB()
    print("✅ Using Fake local DB")

# --- Team Management ---


def get_teams():
    return dict(db.get("teams") or {})


def save_team(name, data):
    teams = get_teams()
    teams[name] = data
    db["teams"] = teams


def delete_team(name):
    teams = get_teams()
    if name in teams:
        del teams[name]
        db["teams"] = teams


def get_user_team(user_id):
    user_id = str(user_id)
    teams = get("team_list", [])

    if not isinstance(teams, list):
        print("⚠️ DB 'team_list' is not a list — resetting to empty list")
        return None

    for team in teams:
        if isinstance(team, dict) and user_id in team.get("members", []):
            return {
                "name": team.get("name", "Unknown"),
                "leader_id": team.get("leader_id"),
                "members": team.get("members", [])
            }
    return None


# --- Key-value helpers ---


def get(key, default=None):
    return db.get(key, default)


def set(key, value):
    db[key] = value


def delete(key):
    if key in db:
        del db[key]
