import copy
import json

from sanitize_n8n import main, sanitize_workflow
from scan import scan_text

SECRET = "sk-ant-" + "Zq9X" * 8
BOT = "123456789" + ":" + "B" * 35
CHAT = "987654" + "321"  # built at runtime so this file does not trip the scanner


def _workflow():
    return {
        "id": "wf-live-17",
        "meta": {"instanceId": "abc123instance"},
        "name": "Assistant",
        "pinData": {"Telegram Trigger": [{"json": {"message": {"text": "my real note"}}}]},
        "staticData": {"global": {"offset": 99}},
        "nodes": [
            {
                "name": "Telegram Trigger",
                "type": "n8n-nodes-base.telegramTrigger",
                "webhookId": "11111111-2222-3333-4444-555555555555",
                "credentials": {"telegramApi": {"id": "7", "name": "Sample bot"}},
                "parameters": {"chatId": int(CHAT)},
            },
            {
                "name": "Allow list",
                "type": "n8n-nodes-base.if",
                "parameters": {"expression": "={{ $json.message.from.id === " + CHAT + " }}"},
            },
            {
                "name": "Ask model",
                "type": "n8n-nodes-base.httpRequest",
                "parameters": {
                    "url": "https://api.anthropic.com/v1/messages",
                    "headers": f"x-api-key: {SECRET}",
                },
            },
            {
                "name": "Notes",
                "type": "n8n-nodes-base.httpRequest",
                "parameters": {
                    "url": "https://my-private-host.duckdns.org/hook?x=1",
                    "tg": f"https://api.telegram.org/bot{BOT}/sendMessage",
                    "owner": "me" + "@gmail.com",
                },
            },
        ],
    }


def test_credentials_webhooks_pinned_and_static_data_are_removed():
    clean, report = sanitize_workflow(_workflow())
    node = clean["nodes"][0]

    assert node["credentials"] == {"telegramApi": {"id": "REDACTED", "name": "REDACTED"}}
    assert "webhookId" not in node
    assert "pinData" not in clean and "staticData" not in clean
    assert clean["id"] == "REDACTED" and clean["meta"]["instanceId"] == "REDACTED"
    assert report["credentials"] == 1 and report["webhook_ids"] == 1
    assert report["pinned_or_static_data"] == 2


def test_telegram_ids_are_redacted_by_key_and_inside_expressions():
    clean, report = sanitize_workflow(_workflow())

    assert clean["nodes"][0]["parameters"]["chatId"] == "REDACTED"
    assert CHAT not in json.dumps(clean)
    assert report["telegram_ids"] == 2


def test_unknown_hosts_redacted_known_hosts_kept():
    clean, report = sanitize_workflow(_workflow())
    dumped = json.dumps(clean)

    assert "https://api.anthropic.com/v1/messages" in dumped
    assert "duckdns" not in dumped
    assert report["urls"] == 1


def test_secrets_bot_tokens_and_emails_do_not_survive():
    clean, report = sanitize_workflow(_workflow())
    dumped = json.dumps(clean, indent=2)

    assert SECRET not in dumped and BOT not in dumped and "gmail" not in dumped
    assert scan_text(dumped) == []
    assert report["secrets"] >= 3


def test_extra_keep_host_is_respected():
    clean, _ = sanitize_workflow(_workflow(), keep_hosts=("my-private-host.duckdns.org",))

    assert "my-private-host.duckdns.org" in json.dumps(clean)


def test_input_is_not_mutated():
    original = _workflow()
    snapshot = copy.deepcopy(original)

    sanitize_workflow(original)

    assert original == snapshot


def test_cli_writes_a_new_file_and_refuses_to_overwrite_the_input(tmp_path, capsys):
    source = tmp_path / "in.json"
    source.write_text(json.dumps(_workflow()))
    destination = tmp_path / "out.json"

    assert main([str(source), str(destination)]) == 0
    assert SECRET not in destination.read_text()
    assert json.loads(source.read_text()) == _workflow()
    assert SECRET not in capsys.readouterr().out
    assert main([str(source), str(source)]) == 2
