"""Configuration management for md-drop."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("~/.config/md-drop/config.toml").expanduser()


@dataclass
class VaultConfig:
    path: Path
    strategy: str = "inbox"  # "inbox" or "daily"
    inbox_folder: str = "Inbox"
    daily_folder: str = "Daily"
    daily_captures_heading: str = "## Captures"


@dataclass
class GoogleConfig:
    credentials_file: Path = field(
        default_factory=lambda: Path("~/.config/md-drop/credentials.json").expanduser()
    )
    token_file: Path = field(
        default_factory=lambda: Path("~/.config/md-drop/token.json").expanduser()
    )
    sheet_id: str = ""


@dataclass
class GmailConfig:
    enabled: bool = True
    label: str = "md-drop"
    synced_label: str = "md-drop-synced"


@dataclass
class SyncConfig:
    interval_seconds: int = 300


@dataclass
class Config:
    vault: VaultConfig
    google: GoogleConfig = field(default_factory=GoogleConfig)
    gmail: GmailConfig = field(default_factory=GmailConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load configuration from a TOML file."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    vault_data = data.get("vault", {})
    vault = VaultConfig(
        path=Path(vault_data["path"]).expanduser(),
        strategy=vault_data.get("strategy", "inbox"),
        inbox_folder=vault_data.get("inbox_folder", "Inbox"),
        daily_folder=vault_data.get("daily_folder", "Daily"),
        daily_captures_heading=vault_data.get(
            "daily_captures_heading", "## Captures"
        ),
    )

    google_data = data.get("google", {})
    google = GoogleConfig(
        credentials_file=Path(
            google_data.get("credentials_file", "~/.config/md-drop/credentials.json")
        ).expanduser(),
        token_file=Path(
            google_data.get("token_file", "~/.config/md-drop/token.json")
        ).expanduser(),
        sheet_id=google_data.get("sheet_id", ""),
    )

    gmail_data = data.get("gmail", {})
    gmail = GmailConfig(
        enabled=gmail_data.get("enabled", True),
        label=gmail_data.get("label", "md-drop"),
        synced_label=gmail_data.get("synced_label", "md-drop-synced"),
    )

    sync_data = data.get("sync", {})
    sync = SyncConfig(
        interval_seconds=sync_data.get("interval_seconds", 300),
    )

    return Config(vault=vault, google=google, gmail=gmail, sync=sync)
