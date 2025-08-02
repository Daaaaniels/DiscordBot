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
    teams = get("teams", {})  # fresh pull every time
    print(f"🔍 get_user_team: Checking teams for user {user_id}...")
    print(f"🧾 Raw teams loaded: {get('teams', {})}")

    for team_name, data in teams.items():
        print(
            f"🧪 Checking team '{team_name}' with members: {data.get('members', [])}")
        if user_id in data.get("members", []):
            print(f"✅ User {user_id} is in team '{team_name}'")
            return {
                "name": team_name,
                "leader_id": data.get("leader"),
                "members": data.get("members", [])
            }
    print(f"🧾 Raw teams loaded: {get('teams', {})}")

    print(f"❌ User {user_id} not found in any team")
    return None



# --- Key-value helpers ---


def get(key, default=None):
    return db.get(key, default)


def set(key, value):
    db[key] = value


def delete(key):
    if key in db:
        del db[key]


def remove_user_from_team_list(user_id, team_name):
    team_list = get("team_list", [])
    if not isinstance(team_list, list):
        return
    updated_list = []
    for team in team_list:
        if team["name"] == team_name:
            if user_id in team["members"]:
                team["members"].remove(user_id)
            if team["leader_id"] == user_id:
                team["leader_id"] = team["members"][0] if team["members"] else None
            if not team["members"]:
                continue  # remove empty team from team_list
        updated_list.append(team)
    set("team_list", updated_list)
