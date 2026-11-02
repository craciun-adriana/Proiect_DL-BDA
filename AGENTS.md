# AGENTS.md

Instructions for AI agents working in this repository.

## Session logging (required)

Every agent session must have its own log file under `agents/logs/`, named `<session_id>.md`.
For each session the log must contain, appended in order:

1. **The user's message** — every prompt, verbatim.
2. **Every output from the agent** — all text replies and tool calls made in response.

### How it is done

Logging is automated by `agents/log_turn.py`, wired up as Claude Code hooks in `.claude/settings.json`:

- `UserPromptSubmit` → appends the user's message to the session log.
- `Stop` (end of each turn) → appends all agent outputs from that turn.

The log file is created automatically on the first message of a session.

### If hooks are not available

If your agent runtime does not run the hooks, you must log manually: after **each turn**, run

```
echo '{"session_id":"<id>","hook_event_name":"UserPromptSubmit","prompt":"<user message>"}' | python agents/log_turn.py
```

for the user message, and append your own outputs to `agents/logs/<id>.md` in the format used by the script
(`## USER [timestamp]` / `## AGENT [timestamp]` headings). Never skip a turn and never edit or delete earlier entries.
