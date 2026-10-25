"""Make an exported n8n workflow safe to publish.

    python tools/sanitize_n8n.py workflow.json clean.json [--keep-host api.anthropic.com ...]

Redacts credential ids and names, webhook ids, pinned (real) test data, static data, instance
ids, URLs on hosts you did not list, Telegram user/chat ids, and anything the scanner would flag.
Never modifies the input file. Prints counts only, never the redacted values.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from scan import RULES

DEFAULT_KEEP_HOSTS = (
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "api.telegram.org",
)
REDACTED = "REDACTED"
_URL = re.compile(r"https?://[^\s\"'<>)]+")
_BOT_PATH = re.compile(r"/bot\d+:[A-Za-z0-9_\-]+")
_ID_IN_TEXT = re.compile(r"(?i)((?:from|chat|user)[._]?id[^\d\-]{0,12})(-?\d{6,})")
_ID_KEY = re.compile(r"(?i)^(?:chat|user|from)_?id$")
_SECRET_RULES = {
    name: pattern
    for name, pattern in RULES.items()
    if name not in {"telegram_numeric_id"}  # handled separately so ids are counted as ids
}


def _clean_string(text: str, keep_hosts: tuple[str, ...], report: dict[str, int]) -> str:
    def url(match: re.Match[str]) -> str:
        host = urlsplit(match.group(0)).hostname or ""
        if host in keep_hosts:
            return match.group(0)
        report["urls"] += 1
        return f"https://{REDACTED.lower()}.invalid"

    text = _URL.sub(url, text)
    text, bot_paths = _BOT_PATH.subn(f"/bot{REDACTED}", text)
    report["secrets"] += bot_paths
    text, ids = _ID_IN_TEXT.subn(lambda m: m.group(1) + REDACTED, text)
    report["telegram_ids"] += ids
    for pattern in _SECRET_RULES.values():
        text, count = pattern.subn(REDACTED, text)
        report["secrets"] += count
    return text


def _walk(node: Any, keep_hosts: tuple[str, ...], report: dict[str, int]) -> Any:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            if key == "credentials" and isinstance(value, dict):
                out[key] = {
                    kind: {"id": REDACTED, "name": REDACTED} for kind in value
                }
                report["credentials"] += len(value)
            elif key == "webhookId":
                report["webhook_ids"] += 1
            elif key in {"pinData", "staticData"}:
                report["pinned_or_static_data"] += 1
            elif _ID_KEY.match(key) and isinstance(value, (int, str)) and str(value).lstrip("-").isdigit():
                out[key] = REDACTED
                report["telegram_ids"] += 1
            else:
                out[key] = _walk(value, keep_hosts, report)
        return out
    if isinstance(node, list):
        return [_walk(item, keep_hosts, report) for item in node]
    if isinstance(node, str):
        return _clean_string(node, keep_hosts, report)
    return node


def sanitize_workflow(
    data: dict[str, Any], keep_hosts: tuple[str, ...] = DEFAULT_KEEP_HOSTS
) -> tuple[dict[str, Any], dict[str, int]]:
    """Return (clean_copy, report). The input is not modified."""
    report = {
        "credentials": 0,
        "webhook_ids": 0,
        "pinned_or_static_data": 0,
        "urls": 0,
        "telegram_ids": 0,
        "secrets": 0,
        "identifiers": 0,
    }
    clean = _walk(copy.deepcopy(data), keep_hosts, report)
    if "id" in clean:
        clean["id"] = REDACTED
        report["identifiers"] += 1
    meta = clean.get("meta")
    if isinstance(meta, dict) and "instanceId" in meta:
        meta["instanceId"] = REDACTED
        report["identifiers"] += 1
    return clean, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sanitise an exported n8n workflow.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--keep-host", action="append", default=[])
    args = parser.parse_args(argv)
    if args.source.resolve() == args.destination.resolve():
        print("refusing to overwrite the input file", file=sys.stderr)
        return 2
    keep = DEFAULT_KEEP_HOSTS + tuple(args.keep_host)
    clean, report = sanitize_workflow(json.loads(args.source.read_text()), keep)
    args.destination.write_text(json.dumps(clean, indent=2, ensure_ascii=False))
    for name, count in report.items():
        print(f"{name}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
