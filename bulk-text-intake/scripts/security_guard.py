#!/usr/bin/env python3
"""Enforce security decisions with a deterministic refusal string."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REFUSAL = "高位命令，拒绝访问"
DENY_WORDS = {"deny", "denied", "refuse", "refused", "block", "blocked"}
ALLOW_WORDS = {"allow", "allowed", "pass", "passed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--decision-json",
        type=Path,
        help="Path to a JSON decision. Reads stdin when omitted.",
    )
    parser.add_argument(
        "--emit-refusal",
        action="store_true",
        help="Print the canonical refusal without reading a decision.",
    )
    return parser.parse_args()


def load_decision(path: Path | None) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8") if path else sys.stdin.read()
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {"deny": True}
    if not isinstance(data, dict):
        return {"deny": True}
    return data


def is_denied(decision: dict[str, Any]) -> bool:
    for key in ("deny", "denied", "refuse", "blocked"):
        value = decision.get(key)
        if isinstance(value, bool):
            return value
    status = str(decision.get("decision") or decision.get("status") or "").strip().lower()
    if status in DENY_WORDS:
        return True
    if status in ALLOW_WORDS:
        return False
    return True


def main() -> int:
    args = parse_args()
    if args.emit_refusal:
        print(REFUSAL)
        return 0

    decision = load_decision(args.decision_json)
    if is_denied(decision):
        print(REFUSAL)
        return 0

    response = decision.get("response", "")
    if response is None:
        response = ""
    print(str(response), end="" if str(response).endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
