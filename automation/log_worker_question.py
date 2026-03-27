#!/usr/bin/env python3
"""Append a worker question to worker_questions.yaml for routing."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = ROOT / "automation" / "worker_questions.yaml"


def load_questions() -> dict:
    if not QUESTIONS_PATH.exists():
        return {"version": 1, "questions": []}
    data = yaml.safe_load(QUESTIONS_PATH.read_text()) or {"version": 1, "questions": []}
    if "questions" not in data:
        data["questions"] = []
    return data


def save_questions(payload: dict) -> None:
    QUESTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUESTIONS_PATH.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Record ask_parent question")
    parser.add_argument("task_id", help="Background task id from create_task")
    parser.add_argument("question", help="Question text from worker")
    parser.add_argument("--owner", default="worker", help="Who logged the question")
    args = parser.parse_args()

    state = load_questions()
    state.setdefault("questions", [])
    state["questions"].append(
        {
            "task_id": args.task_id,
            "question": args.question,
            "status": "open",
            "owner": args.owner,
            "created_at": dt.datetime.now(dt.UTC).isoformat(),
        }
    )
    save_questions(state)
    print(f"Recorded question for {args.task_id}")


if __name__ == "__main__":
    main()
