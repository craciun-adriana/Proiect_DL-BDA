#!/usr/bin/env python3
"""Append conversation turns to agents/logs/<session_id>.md.

Invoked by Claude Code hooks (see .claude/settings.json); reads the hook JSON from stdin.
  UserPromptSubmit -> logs the user's message
  Stop             -> logs every agent output (text + tool calls) produced since the last user message
"""
import json
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append(session_id, text):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / f"{session_id}.md", "a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n\n")


def user_text(entry):
    """Return the text of a real user message, or None (e.g. tool results)."""
    content = entry.get("message", {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if b.get("type") == "text"]
        return "\n".join(parts) if parts else None
    return None


def agent_outputs(transcript_path):
    entries = []
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not e.get("isSidechain"):
                entries.append(e)
    last_user = -1
    for i, e in enumerate(entries):
        if e.get("type") == "user" and user_text(e) is not None:
            last_user = i
    out = []
    for e in entries[last_user + 1:]:
        if e.get("type") != "assistant":
            continue
        for b in e.get("message", {}).get("content", []):
            if b.get("type") == "text" and b.get("text", "").strip():
                out.append(b["text"])
            elif b.get("type") == "tool_use":
                out.append(f"[tool: {b.get('name')}] {json.dumps(b.get('input'), ensure_ascii=False)}")
    return out


def main():
    data = json.load(sys.stdin)
    sid = data.get("session_id", "unknown")
    event = data.get("hook_event_name")
    if event == "UserPromptSubmit":
        append(sid, f"## USER [{now()}]\n\n{data.get('prompt', '')}")
    elif event == "Stop":
        tp = data.get("transcript_path")
        if tp and Path(tp).exists():
            outs = agent_outputs(tp)
            if outs:
                append(sid, f"## AGENT [{now()}]\n\n" + "\n\n".join(outs))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # never block the session because of logging
        print(f"log_turn.py error: {exc}", file=sys.stderr)
