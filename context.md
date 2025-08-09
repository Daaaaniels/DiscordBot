1. Project Name
   Genesis Discord Bot / Genesis Server Tools

2. Purpose
   Short description of what the project does, who it’s for, and its main features.
   Example:

A modular Discord bot for managing Genesis game servers in Last Island of Survival.
Handles team creation, ranking, Genesis Core tracking, and seasonal competitions.

3. Tech Stack
   Language: Python 3.x

Libraries:

discord.py (version …)

aiosqlite for database

Any other important ones

Database: SQLite (async)

Hosting: (local / Replit / VPS / etc.)

4. Folder Structure
   project/
   │
   ├── bot.py # Main entry point
   ├── core/ # Core logic & utilities
   │ ├── db.py # Database functions
   │ ├── utils.py # Helper utilities
   │
   ├── cogs/ # Feature modules
   │ ├── team_commands.py # Slash/text team commands
   │ ├── admin_commands.py # Admin tools
   │
   ├── ui/ # UI elements (embeds, views, modals)
   │ ├── panel.py # Team panel
   │ ├── admin_panel.py # Admin panel
   │
   ├── bounty/ # Bounty quest features
   │
   └── requirements.txt

5. Key Features
   Team creation & join codes (4-digit)

Rank points & Genesis Core tracking

Submission review & approval system

Seasonal leaderboard with reset

Integration with in-game Genesis currency system

6. Data Flow
   Briefly explain how data moves through the system.
   Example:

Player submits proof → Bot sends to review queue → Admin approves → Bot updates DB → Leaderboard refreshes.

7. Special Rules / Notes
   No PvP talents due to balancing concerns.

Persistent Core counts across wipes.

Rate: 300 Genesis Fragments = 1 Core.

Seasons time-based, prize for Top 1 team.
