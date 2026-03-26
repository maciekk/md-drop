"""Shared Note dataclass used across sources and writer."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Note:
    timestamp: datetime
    title: str
    body: str
    source: str  # "web" or "email"
    source_id: str = ""  # Sheet row index or Gmail message ID, for marking as synced
