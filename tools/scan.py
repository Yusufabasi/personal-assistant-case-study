"""Scan a folder for secrets and personal data before publishing it.

    python tools/scan.py PATH [--allow .scan-allow.json]

Prints `path:line rule` and exits 1 if anything is found. It never prints the matched text,
so its own output is safe to paste into a chat or an issue.

The allowlist maps a path pattern to the rule names to ignore for that path only:
    {"docs/*.md": ["email_address"]}
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_BYTES = 1_000_000
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}

RULES: dict[str, re.Pattern[str]] = {
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    "openai_style_key": re.compile(r"\bsk-[A-Za-z0-9]{32,}"),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    # No leading \b: in "/bot123...:AAA..." the "t" and the first digit are both word characters.
    "telegram_bot_token": re.compile(r"(?<!\d)\d{8,10}:[A-Za-z0-9_\-]{35}(?![A-Za-z0-9_\-])"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    "email_address": re.compile(
        r"\b[A-Za-z0-9._%+\-]+@(?!example\.(?:com|org|net)\b)[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    ),
    "phone_number": re.compile(r"(?<![\d\w])\+\d{1,3}[ \-]?\d{2,3}[ \-]?\d{3}[ \-]?\d{3,4}(?!\d)"),
    "telegram_numeric_id": re.compile(
        r"""(?i)["']?(?:chat|user|from)_?id["']?\s*[:=]\s*["']?-?\d{6,}"""
    ),
    "generic_secret_assignment": re.compile(
        r"""(?i)(?:api[_\-]?key|secret|token|password)["']?\s*[:=]\s*["']?[A-Za-z0-9_\-/+=]{16,}"""
    ),
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str


def _is_binary(chunk: bytes) -> bool:
    return b"\x00" in chunk


def _allowed(rel: str, rule: str, allowlist: dict[str, list[str]]) -> bool:
    return any(fnmatch.fnmatch(rel, pat) and rule in rules for pat, rules in allowlist.items())


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return (line, rule) for every rule that matches, once per line and rule."""
    hits: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in RULES.items():
            if pattern.search(line):
                hits.append((number, rule))
    return hits


def scan_tree(root: Path, allowlist: dict[str, list[str]] | None = None) -> list[Finding]:
    allowlist = allowlist or {}
    findings: list[Finding] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or SKIP_DIRS.intersection(path.relative_to(root).parts):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            raw = path.read_bytes()
        except OSError:
            continue
        if _is_binary(raw[:8192]):
            continue
        rel = path.relative_to(root).as_posix()
        for line, rule in scan_text(raw.decode("utf-8", errors="ignore")):
            if not _allowed(rel, rule, allowlist):
                findings.append(Finding(rel, line, rule))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a folder for secrets and personal data.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--allow", type=Path, help="JSON allowlist: {path_glob: [rule, ...]}")
    args = parser.parse_args(argv)
    allowlist = json.loads(args.allow.read_text()) if args.allow else {}
    findings = scan_tree(args.path, allowlist)
    for finding in findings:
        print(f"{finding.path}:{finding.line} {finding.rule}")
    print(f"{len(findings)} finding(s)", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
