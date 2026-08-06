"""Tests for JIRA CSV loading."""
from pathlib import Path

from gitdoctor.jira_client import load_ticket_keys_from_csv


def test_load_csv_keys(tmp_path: Path):
    csv_file = tmp_path / "tickets.csv"
    csv_file.write_text("key,summary\nMON-1,One\nMON-2,Two\n")
    keys = load_ticket_keys_from_csv(csv_file)
    assert keys == ["MON-1", "MON-2"]
