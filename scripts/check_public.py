"""Fail if a tracked file contains personal data or a local path.

Checks every file git tracks (or would track) for:
  * student-ID-like strings (a letter, seven digits, a letter), e.g. matriculation numbers;
  * e-mail addresses, except GitHub's noreply addresses used for authorship;
  * home-directory and Windows user paths;
  * secret-like tokens (common API-key prefixes).
File names are checked as well as contents, and PDF or Office documents may not be
tracked at all (the proposal lists student IDs), unless listed in ALLOWED_DOCUMENTS.

Terms that must never appear publicly but should not be named in a public file
either can be listed, one per line, in the untracked file
.git/info/public-denylist; they are checked too.

Usage: python scripts/check_public.py
"""

import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "student-ID-like string": re.compile(r"(?<![A-Za-z0-9])[A-Za-z]\d{7}[A-Za-z](?![A-Za-z0-9])"),
    "secret-like token": re.compile(r"\b(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|hf_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})\b"),
    "e-mail address": re.compile(r"\b[\w.+-]+@(?!users\.noreply\.github\.com)[\w-]+\.[\w.-]+\b"),
    "home-directory path": re.compile(r"(/home/[\w.-]+|/Users/[\w.-]+|(?i:[a-z]:(\\{1,2}|/)users(\\{1,2}|/)))"),
}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico"}
DOCUMENT_SUFFIXES = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".odt"}
ALLOWED_DOCUMENTS: set[str] = set()  # repository-relative paths of documents the team has approved


def tracked_files(root: Path) -> list[Path]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=root, capture_output=True, text=True, check=True).stdout
    return [root / line for line in out.splitlines() if line]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    patterns = dict(PATTERNS)
    denylist = root / ".git" / "info" / "public-denylist"
    if denylist.exists():
        for term in denylist.read_text(encoding="utf-8").splitlines():
            if term.strip() and not term.startswith("#"):
                patterns[f"local deny-list entry {len(patterns) - len(PATTERNS) + 1}"] = re.compile(re.escape(term.strip()), re.I)
    problems = 0
    for path in tracked_files(root):
        rel = str(path.relative_to(root))
        if path.suffix.lower() in DOCUMENT_SUFFIXES and rel not in ALLOWED_DOCUMENTS:
            print(f"{rel}: document files may not be tracked (add to ALLOWED_DOCUMENTS only after review)")
            problems += 1
            continue
        for label, pattern in patterns.items():
            if pattern.search(rel):
                print(f"{rel}: file name contains a {label}")
                problems += 1
        if path.suffix.lower() in SKIP_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in patterns.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                print(f"{path.relative_to(root)}:{line}: {label}")
                problems += 1
    if problems:
        print(f"{problems} problem(s); public files must not contain personal data or local paths")
        return 1
    print("public-content check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
