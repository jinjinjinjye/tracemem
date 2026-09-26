"""The decision-record checker (decisions.py, run in CI by scripts/check_decisions.py).

Each test builds a small docs/decisions-like folder in a temporary directory and
breaks one rule, so the checker must report it.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from support import REPO
from tracemem.decisions import check_folder, load_records


def record(folder, name: str, *, id: int, status: str = "accepted", decided_by="[team]", supersedes="[]",
           superseded_by="[]", date: str = "2026-09-26") -> None:
    """Write one decision record with the given front matter."""
    (folder / name).write_text(
        "---\n"
        f"id: {id}\n"
        f"title: Record {id}\n"
        f"status: {status}\n"
        f"date: {date}\n"
        f"decided_by: {decided_by}\n"
        f"supersedes: {supersedes}\n"
        f"superseded_by: {superseded_by}\n"
        "---\n\n"
        f"# {id:04d}. Record {id}\n",
        encoding="utf-8",
    )


@pytest.fixture
def valid(tmp_path):
    """Record 1 was replaced by record 2 (links both ways); record 3 is a proposal; README and template are skipped."""
    record(tmp_path, "0001-first-choice.md", id=1, status="superseded", superseded_by="[2]")
    record(tmp_path, "0002-second-choice.md", id=2, supersedes="[1]")
    record(tmp_path, "0003-open-question.md", id=3, status="proposed", decided_by="[]")
    (tmp_path / "README.md").write_text("# Decision records\n", encoding="utf-8")
    (tmp_path / "0000-template.md").write_text("---\nid: 0\nstatus: whatever\n---\n", encoding="utf-8")
    return tmp_path


def test_a_valid_folder_passes(valid):
    assert check_folder(valid) == []
    records, errors = load_records(valid)
    assert [r.id for r in records] == [1, 2, 3] and errors == []
    assert records[1].supersedes == [1] and records[0].superseded_by == [2]


def test_one_way_link_from_the_new_record_is_rejected(valid):
    """Record 2 says it replaces 1, but 1 does not say it was replaced."""
    record(valid, "0001-first-choice.md", id=1, status="accepted")
    errors = check_folder(valid)
    assert any("0002-second-choice.md" in e and "both ways" in e for e in errors), errors


def test_one_way_link_from_the_old_record_is_rejected(valid):
    """Record 1 says 2 replaced it, but 2 does not list 1 in supersedes."""
    record(valid, "0002-second-choice.md", id=2)
    errors = check_folder(valid)
    assert any("0001-first-choice.md" in e and "both ways" in e for e in errors), errors


def test_superseded_record_without_a_successor_is_rejected(valid):
    record(valid, "0003-open-question.md", id=3, status="superseded", decided_by="[]")
    errors = check_folder(valid)
    assert any("0003" in e and "superseded_by is empty" in e for e in errors), errors


def test_accepted_record_without_decided_by_is_rejected(valid):
    record(valid, "0002-second-choice.md", id=2, supersedes="[1]", decided_by="[]")
    errors = check_folder(valid)
    assert any("0002" in e and "decided_by" in e for e in errors), errors


def test_duplicate_id_is_rejected(valid):
    record(valid, "0003-same-number-again.md", id=3, status="proposed", decided_by="[]")
    errors = check_folder(valid)
    assert any("duplicate id 3" in e for e in errors), errors


@pytest.mark.parametrize("name", ["3-too-short.md", "0004_Under_Score.md", "0004-Capital.md", "0004.md"])
def test_bad_filename_is_rejected(valid, name):
    record(valid, name, id=4, status="proposed", decided_by="[]")
    errors = check_folder(valid)
    assert any(name in e and "file name" in e for e in errors), errors


@pytest.mark.parametrize("change, message", [
    (dict(status="decided"), "status"),
    (dict(date="'next week'"), "date"),
    (dict(decided_by="team"), "must be lists"),
])
def test_malformed_front_matter_is_rejected(valid, change, message):
    record(valid, "0004-malformed.md", id=4, **change)
    errors = check_folder(valid)
    assert any("0004-malformed.md" in e and message in e for e in errors), errors


def test_id_must_match_the_file_number(valid):
    record(valid, "0004-wrong-number.md", id=5, status="proposed", decided_by="[]")
    assert any("does not match the file number" in e for e in check_folder(valid))


def test_missing_front_matter_is_rejected(valid):
    (valid / "0004-no-front-matter.md").write_text("# Just a heading\n", encoding="utf-8")
    assert any("front matter" in e for e in check_folder(valid))


def test_the_repository_decision_records_pass():
    assert check_folder(REPO / "docs" / "decisions") == []


def test_the_ci_script_exit_codes(valid, tmp_path_factory):
    """scripts/check_decisions.py exits 0 on a valid folder and 1 on a broken one."""
    script = REPO / "scripts" / "check_decisions.py"
    ok = subprocess.run([sys.executable, str(script), str(valid)], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    broken = tmp_path_factory.mktemp("broken")
    record(broken, "0001-lonely.md", id=1, status="superseded")
    bad = subprocess.run([sys.executable, str(script), str(broken)], capture_output=True, text=True)
    assert bad.returncode == 1 and "error:" in bad.stdout
