"""scripts/check_public.py keeps personal data and local paths out of the public repository.

The sample strings below are assembled at run time from pieces, so that this
file itself never contains a string the checker would flag.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys

import pytest

from support import REPO

SCRIPT = REPO / "scripts" / "check_public.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_public", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PATTERNS = load_checker().PATTERNS

STUDENT_ID = "".join(["A", "0123456", "Z"])  # a letter, seven digits, a letter
HOME_PATH = "/".join(["", "home", "someone", "project", "notes.txt"])
MAC_PATH = "/".join(["", "Users", "someone", "project"])
WINDOWS_PATH = "\\".join(["C:", "Users", "someone", "project"])
EMAIL = "someone" + "@" + "example" + ".org"
NOREPLY = "12345+someone" + "@" + "users.noreply.github.com"


def test_repository_passes_the_public_check():
    """The script exits 0 on the repository as it is, tests included."""
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "public-content check OK" in result.stdout


@pytest.mark.parametrize("label, sample", [
    ("student-ID-like string", STUDENT_ID),
    ("home-directory path", HOME_PATH),
    ("home-directory path", MAC_PATH),
    ("home-directory path", WINDOWS_PATH),
    ("e-mail address", EMAIL),
])
def test_patterns_catch_samples_written_to_a_file(tmp_path, label, sample):
    path = tmp_path / "draft.md"
    path.write_text(f"Meeting notes.\nSee {sample} for details.\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    assert PATTERNS[label].search(text), f"{label} not caught in {sample!r}"


@pytest.mark.parametrize("harmless", [NOREPLY, "S1-T1", "pilot-01", "A012345Z", "model.sentiment", "q-3fa2b1c0d9e8"])
def test_patterns_leave_ordinary_text_alone(harmless):
    """GitHub no-reply addresses, turn ids and short codes are not flagged."""
    assert not any(pattern.search(f"See {harmless} here.") for pattern in PATTERNS.values())
