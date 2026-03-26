"""Tests for configuration loading."""

from pathlib import Path

from md_drop.config import load_config


def test_load_full_config(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[vault]
path = "/tmp/vault"
strategy = "daily"
inbox_folder = "MyInbox"
daily_folder = "Journal"
daily_captures_heading = "## Notes"

[google]
credentials_file = "/tmp/creds.json"
token_file = "/tmp/token.json"
sheet_id = "abc123"

[gmail]
enabled = false
label = "custom-label"
synced_label = "custom-synced"

[sync]
interval_seconds = 60
""")

    cfg = load_config(config_file)
    assert cfg.vault.path == Path("/tmp/vault")
    assert cfg.vault.strategy == "daily"
    assert cfg.vault.inbox_folder == "MyInbox"
    assert cfg.vault.daily_folder == "Journal"
    assert cfg.vault.daily_captures_heading == "## Notes"
    assert cfg.google.sheet_id == "abc123"
    assert cfg.gmail.enabled is False
    assert cfg.gmail.label == "custom-label"
    assert cfg.sync.interval_seconds == 60


def test_load_minimal_config(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[vault]
path = "/tmp/vault"
""")

    cfg = load_config(config_file)
    assert cfg.vault.path == Path("/tmp/vault")
    assert cfg.vault.strategy == "inbox"
    assert cfg.vault.inbox_folder == "Inbox"
    assert cfg.gmail.enabled is True
    assert cfg.gmail.label == "md-drop"
    assert cfg.sync.interval_seconds == 300


def test_load_config_expands_tilde(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[vault]
path = "~/my-vault"

[google]
credentials_file = "~/creds.json"
token_file = "~/token.json"
""")

    cfg = load_config(config_file)
    assert "~" not in str(cfg.vault.path)
    assert "~" not in str(cfg.google.credentials_file)
    assert "~" not in str(cfg.google.token_file)
