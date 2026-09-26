"""Checks for the decision records in docs/decisions/.

A decision record is a Markdown file named NNNN-slug.md whose YAML front matter
carries its status and its links. Supersession is data, not prose: a record that
replaces another lists it in ``supersedes``, and the replaced record points back
through ``superseded_by``. This module verifies that the links agree, so that a
reader who opens an old decision always learns that it has a successor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

STATUSES = {"proposed", "accepted", "superseded", "rejected"}
REQUIRED = ("id", "title", "status", "date", "decided_by", "supersedes", "superseded_by")
FILENAME = re.compile(r"^(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
SKIP = {"README.md", "0000-template.md"}


@dataclass
class DecisionRecord:
    path: Path
    id: int
    title: str
    status: str
    decided_by: list[str]
    supersedes: list[int] = field(default_factory=list)
    superseded_by: list[int] = field(default_factory=list)


def _front_matter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    data = yaml.safe_load(parts[1])
    return data if isinstance(data, dict) else None


def load_records(folder: Path) -> tuple[list[DecisionRecord], list[str]]:
    """Parse every record in ``folder``; return the records and any parse errors."""
    records: list[DecisionRecord] = []
    errors: list[str] = []
    for path in sorted(folder.glob("*.md")):
        if path.name in SKIP:
            continue
        match = FILENAME.match(path.name)
        if not match:
            errors.append(f"{path.name}: file name must look like 0007-short-slug.md")
            continue
        meta = _front_matter(path.read_text(encoding="utf-8"))
        if meta is None:
            errors.append(f"{path.name}: missing YAML front matter between '---' lines")
            continue
        missing = [key for key in REQUIRED if key not in meta]
        if missing:
            errors.append(f"{path.name}: missing front-matter keys {missing}")
            continue
        if meta["id"] != int(match.group(1)):
            errors.append(f"{path.name}: id {meta['id']} does not match the file number")
            continue
        if meta["status"] not in STATUSES:
            errors.append(f"{path.name}: status {meta['status']!r} is not one of {sorted(STATUSES)}")
            continue
        if not isinstance(meta["date"], date):
            errors.append(f"{path.name}: date must be written as YYYY-MM-DD")
            continue
        lists = {key: meta[key] or [] for key in ("decided_by", "supersedes", "superseded_by")}
        if not all(isinstance(value, list) for value in lists.values()):
            errors.append(f"{path.name}: decided_by, supersedes and superseded_by must be lists")
            continue
        records.append(
            DecisionRecord(
                path=path,
                id=meta["id"],
                title=str(meta["title"]),
                status=meta["status"],
                decided_by=[str(name) for name in lists["decided_by"]],
                supersedes=[int(x) for x in lists["supersedes"]],
                superseded_by=[int(x) for x in lists["superseded_by"]],
            )
        )
    return records, errors


def check_links(records: list[DecisionRecord]) -> list[str]:
    """Return one message per broken rule; an empty list means the records agree."""
    errors: list[str] = []
    by_id: dict[int, DecisionRecord] = {}
    for record in records:
        if record.id in by_id:
            errors.append(f"{record.path.name}: duplicate id {record.id}")
        by_id[record.id] = record

    for record in records:
        name = record.path.name
        if record.status == "accepted" and not record.decided_by:
            errors.append(f"{name}: an accepted record must name who decided it in decided_by")
        if record.status == "superseded" and not record.superseded_by:
            errors.append(f"{name}: status is superseded but superseded_by is empty")
        if record.superseded_by and record.status != "superseded":
            errors.append(f"{name}: superseded_by is set but status is {record.status!r}")
        for old_id in record.supersedes:
            old = by_id.get(old_id)
            if old is None:
                errors.append(f"{name}: supersedes unknown record {old_id}")
            elif record.status == "accepted" and record.id not in old.superseded_by:
                errors.append(
                    f"{name}: supersedes {old_id}, but {old.path.name} does not list "
                    f"{record.id} in superseded_by (links must go both ways)"
                )
        for new_id in record.superseded_by:
            new = by_id.get(new_id)
            if new is None:
                errors.append(f"{name}: superseded_by unknown record {new_id}")
            elif record.id not in new.supersedes:
                errors.append(
                    f"{name}: superseded_by {new_id}, but {new.path.name} does not list "
                    f"{record.id} in supersedes (links must go both ways)"
                )
            elif new.status != "accepted":
                errors.append(f"{name}: superseded by {new_id}, which is {new.status!r}, not accepted")
    return errors


def check_folder(folder: Path) -> list[str]:
    records, errors = load_records(folder)
    return errors + check_links(records)
