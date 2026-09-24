# Viraj — Personal Life Agent

A CLI agent that tracks tasks, fires reminders, and sends you push notifications.

## Quick start

```bash
# 1. Clone and install
pip install -e .

# 2. Copy and fill in credentials
cp .env.example .env
# edit .env — only NTFY_TOPIC is required

# 3. Run!
agent task list
```

## Commands

### Tasks
```bash
agent task add "Buy groceries" --priority high --due 2026-09-25
agent task list                     # pending tasks (default)
agent task list --filter all        # all tasks
agent task done 1                   # mark task #1 complete
agent task delete 1
```

### Reminders (fires as push notification)
```bash
agent remind add "Dentist appointment" --at "2026-09-25 14:00"
agent remind list
agent remind delete 1
```

### AI assistant (optional — requires Anthropic API key)
```bash
agent ask "What should I focus on today?"
agent ask "Help me prioritize my week"
```

### Daemon (runs scheduled jobs)
```bash
agent start           # blocks; keeps running — use tmux or a systemd service
```

### Manual triggers
```bash
agent brief           # send morning brief right now
agent test-notify     # verify ntfy is wired up
```

## Setup: Notifications via ntfy (free, no account)

1. Install the **ntfy** app on your phone — [iOS](https://apps.apple.com/app/ntfy/id1625396347) or [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy).
2. Pick any unique topic name, e.g. `viraj-yourname`.
3. In the app, tap **+** and subscribe to that topic.
4. Set `NTFY_TOPIC=viraj-yourname` in your `.env`.

That's it — completely free, no account needed.

## Setup: Anthropic API (optional)

Only needed for `agent ask`. Get a key at [console.anthropic.com](https://console.anthropic.com) and paste it into `.env` as `ANTHROPIC_API_KEY`.

## Running the daemon persistently

On macOS/Linux with tmux:
```bash
tmux new-session -d -s agent "agent start"
```

Or create a systemd service to start on boot.

## Data storage

All data lives in `~/.viraj/viraj.db` (SQLite). The only outbound network calls are push notifications to ntfy.sh and (optionally) AI queries to Anthropic.
