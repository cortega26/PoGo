import re
from datetime import date
from pathlib import Path


def test_latest_changelog_entry_has_current_date():
    changelog = Path(__file__).resolve().parent.parent / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    match = re.search(r"## \[[^\]]+\] - (\d{4}-\d{2}-\d{2})", text)
    assert match, "No version entry found in CHANGELOG.md"
    entry_date = match.group(1)
    assert entry_date == date.today().isoformat()
