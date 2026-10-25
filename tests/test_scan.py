import json

import pytest
from scan import Finding, main, scan_text, scan_tree

# Secrets are assembled at runtime so this file does not trip the scanner it tests.
ANTHROPIC = "sk-ant-" + "a1B2" * 8
GOOGLE = "AIza" + "x" * 35
TELEGRAM = "123456789" + ":" + "A" * 35
PEM = "-----BEGIN " + "RSA PRIVATE KEY-----"


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        (f"key = {ANTHROPIC}", "anthropic_key"),
        (f'"k": "{GOOGLE}"', "google_api_key"),
        (f"url /bot{TELEGRAM}/send", "telegram_bot_token"),
        (PEM, "private_key"),
        ("mail me at jane.doe" + "@gmail.com", "email_address"),
        ("call +243 " + "812 345 678", "phone_number"),
        ('"chatId": ' + "987654321", "telegram_numeric_id"),
        ("API_KEY=" + "q" * 24, "generic_secret_assignment"),
    ],
)
def test_each_rule_fires(text, rule):
    assert (1, rule) in scan_text(text)


def test_secret_inside_a_json_string_is_found():
    text = json.dumps({"nodes": [{"parameters": {"headers": f"Bearer {ANTHROPIC}"}}]}, indent=2)

    assert any(rule == "anthropic_key" for _, rule in scan_text(text))


def test_placeholder_email_and_plain_numbers_are_not_flagged():
    assert scan_text("write to someone@example.com in 2026 with 12345 items") == []


def test_finding_never_contains_the_secret(tmp_path):
    (tmp_path / "a.txt").write_text(f"token: {ANTHROPIC}\n")

    findings = scan_tree(tmp_path)

    assert findings
    assert ANTHROPIC not in repr(findings)


def test_line_numbers_and_relative_paths(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "n.txt").write_text(f"ok\nok\nkey {GOOGLE}\n")

    assert scan_tree(tmp_path) == [Finding("sub/n.txt", 3, "google_api_key")]


def test_allowlist_suppresses_one_rule_for_one_path_only(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("contact bob" + "@corp.org")
    (tmp_path / "b.md").write_text("contact bob" + "@corp.org")

    findings = scan_tree(tmp_path, {"docs/*.md": ["email_address"]})

    assert [f.path for f in findings] == ["b.md"]


def test_binary_oversized_and_skipped_dirs_are_ignored(tmp_path):
    (tmp_path / "bin.dat").write_bytes(b"\x00\x01" + ANTHROPIC.encode())
    (tmp_path / "big.txt").write_text(ANTHROPIC + "\n" + "x" * 1_100_000)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text(ANTHROPIC)

    assert scan_tree(tmp_path) == []


def test_cli_exit_codes_and_output_hides_matches(tmp_path, capsys):
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "a.txt").write_text("nothing here")
    dirty = tmp_path / "dirty"
    dirty.mkdir()
    (dirty / "a.txt").write_text(ANTHROPIC)

    assert main([str(clean)]) == 0
    assert main([str(dirty)]) == 1
    captured = capsys.readouterr()
    assert "a.txt:1 anthropic_key" in captured.out
    assert ANTHROPIC not in captured.out + captured.err
