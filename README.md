# Viraj — Personal Life Agent

A CLI agent that tracks tasks, fires reminders, and texts you updates via SMS.

## Quick start

```bash
# 1. Clone and install
pip install -e .

# 2. Copy and fill in credentials
cp .env.example .env
# edit .env with your Twilio + Anthropic keys

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

### Reminders (fires as SMS)
```bash
agent remind add "Dentist appointment" --at "2026-09-25 14:00"
agent remind list
agent remind delete 1
```

### AI assistant
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
agent test-sms        # verify Twilio is wired up
```

## Setup: Twilio (SMS)

1. Sign up free at [twilio.com](https://www.twilio.com) — free trial gives ~$15 credit.
2. Get a phone number in the Twilio console.
3. Copy your **Account SID**, **Auth Token**, and phone number into `.env`.

## Setup: Anthropic API

1. Go to [console.anthropic.com](https://console.anthropic.com) → API Keys → Create.
2. Paste the key into `.env` as `ANTHROPIC_API_KEY`.

## Running the daemon persistently

On macOS/Linux with tmux:
```bash
tmux new-session -d -s agent "agent start"
```

Or create a systemd service to start on boot.

## Data storage

All data lives in `~/.viraj/viraj.db` (SQLite). Nothing is sent to the cloud except SMS via Twilio and AI queries to Anthropic.
