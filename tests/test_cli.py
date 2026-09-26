"""The `tracemem` command: validate, replay, run, report, systems, and the test-split guard."""

from __future__ import annotations

import json

import pytest
import yaml

from support import DEV, PILOT_IDS, REPO, pilot_path, raw_yaml
from tracemem import cli
from tracemem.bench.load import load_scenario, scenario_paths
from tracemem.bench.replay import replay
from tracemem.cli import main

DEV_FILES = scenario_paths(DEV)


@pytest.fixture
def at_repo_root(monkeypatch):
    monkeypatch.chdir(REPO)


def test_validate_default_folder(at_repo_root, capsys):
    """With no arguments, validate checks benchmark/scenarios/dev and succeeds."""
    assert main(["validate"]) == 0
    out = capsys.readouterr().out
    assert f"{len(DEV_FILES)} scenario files, 0 errors" in out
    assert "pilot-01: 11 current questions" in out


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_replay_prints_operations_and_expected_answers(at_repo_root, capsys, scenario_id):
    assert main(["replay", str(pilot_path(scenario_id).relative_to(REPO))]) == 0
    out = capsys.readouterr().out
    assert out.startswith(f"# {scenario_id}:")
    assert "| question | kind | expected |" in out


def test_replay_shows_the_pilot_01_suggestion_and_revision(at_repo_root, capsys):
    main(["replay", str(pilot_path("pilot-01"))])
    out = capsys.readouterr().out
    assert "S2-T3   ADD as proposed    model.sentiment = DistilBERT" in out
    assert "| model.sentiment@S2 | current | BERT |" in out


def test_systems_lists_the_registry(capsys):
    assert main(["systems"]) == 0
    out = capsys.readouterr().out
    for name in ("oracle", "always-oldest", "latest-candidate", "latest-mention", "always-conflict", "always-none",
                 "pipeline-gold"):
        assert name in out


def test_run_then_report(at_repo_root, tmp_path, capsys):
    """run writes a run folder whose metrics say the oracle is perfect; report reads it back."""
    out_dir = tmp_path / "runs"
    assert main(["run", "--system", "oracle", "--out", str(out_dir)]) == 0
    (folder,) = list(out_dir.iterdir())
    assert folder.name.endswith("-oracle-dev-end_to_end")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["system"] == "oracle" and manifest["split"] == "dev" and manifest["uses_gold_labels"] is True
    assert set(manifest["scenarios"]) == {load_scenario(p).scenario_id for p in DEV_FILES} >= set(PILOT_IDS)
    metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["current_accuracy"]["all"]["value"] == 1.0
    questions = sum(len(replay(load_scenario(p)).questions) for p in DEV_FILES)  # 52 with the five pilots alone
    assert metrics["outcome_counts"] == {"correct": questions}
    assert len((folder / "answers.jsonl").read_text(encoding="utf-8").splitlines()) == questions
    assert "uses gold labels" in capsys.readouterr().out

    assert main(["report", str(folder), "--resamples", "50"]) == 0
    report = capsys.readouterr().out
    assert "| current_accuracy | all | 1.000" in report
    assert "oracle (uses gold labels)" in report

    assert main(["report", str(folder), "--resamples", "50", "--weighting", "episode"]) == 0
    assert "Weighting: episode" in capsys.readouterr().out


def test_report_compares_two_runs(at_repo_root, tmp_path, capsys):
    out_dir = tmp_path / "runs"
    main(["run", "--system", "oracle", "--out", str(out_dir)])
    main(["run", "--system", "latest-candidate", "--out", str(out_dir)])
    capsys.readouterr()
    folders = sorted(out_dir.iterdir(), key=lambda p: "oracle" not in p.name)
    assert main(["report", *map(str, folders), "--resamples", "50", "--no-stratify"]) == 0
    assert "Paired differences against oracle" in capsys.readouterr().out


def test_run_rejects_an_unknown_system(at_repo_root, tmp_path, capsys):
    assert main(["run", "--system", "nonexistent", "--out", str(tmp_path)]) == 2
    assert "unknown system" in capsys.readouterr().out


def test_run_refuses_gold_candidates_for_a_system_that_cannot_take_them(at_repo_root, tmp_path, capsys):
    assert main(["run", "--system", "oracle", "--condition", "gold_candidates", "--out", str(tmp_path)]) == 2
    assert "cannot run" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_run_records_the_weighting(at_repo_root, tmp_path):
    assert main(["run", "--system", "always-oldest", "--weighting", "episode", "--out", str(tmp_path)]) == 0
    (folder,) = list(tmp_path.iterdir())
    metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["weighting"] == "episode"


# -- the test-split guard -------------------------------------------------------------------------


@pytest.fixture
def test_split_root(tmp_path):
    """A scenario root with one pilot copied into test/ (split changed to test), outside the repository."""
    data = raw_yaml(pilot_path("pilot-01"))
    data["split"] = "test"
    (tmp_path / "scenarios" / "test").mkdir(parents=True)
    (tmp_path / "scenarios" / "test" / "copy.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return tmp_path / "scenarios"


def fake_git(status: str, tag: str | None):
    def _git(*args):
        if args[:1] == ("status",):
            return status
        if args[:1] == ("describe",):
            return tag
        return "0" * 40
    return _git


def run_test_split(root, out, *extra):
    return main(["run", "--system", "oracle", "--split", "test", "--root", str(root), "--out", str(out), *extra])


def test_test_split_is_refused_without_a_freeze_tag(test_split_root, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_git", fake_git(status="", tag=None))
    assert run_test_split(test_split_root, tmp_path / "runs") == 2
    out = capsys.readouterr().out
    assert "refusing to run on the test split" in out and "freeze" in out
    assert not (tmp_path / "runs").exists()
    assert not (tmp_path / "results").exists()


def test_test_split_is_refused_with_uncommitted_changes_even_with_a_tag(test_split_root, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_git", fake_git(status=" M src/tracemem/schema.py", tag="freeze-1"))
    assert run_test_split(test_split_root, tmp_path / "runs", "--i-know-this-is-the-test-split") == 2
    assert "uncommitted changes" in capsys.readouterr().out
    assert not (tmp_path / "runs").exists()


def test_test_split_runs_with_a_freeze_tag_and_is_logged(test_split_root, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_git", fake_git(status="", tag="freeze-1"))
    assert run_test_split(test_split_root, tmp_path / "runs") == 0
    (entry,) = (tmp_path / "results" / "test-runs.jsonl").read_text(encoding="utf-8").splitlines()
    logged = json.loads(entry)
    assert logged["freeze"] == "freeze-1" and logged["system"] == "oracle"


def test_test_split_override_flag_without_a_tag(test_split_root, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_git", fake_git(status="", tag=None))
    assert run_test_split(test_split_root, tmp_path / "runs", "--i-know-this-is-the-test-split") == 0
    logged = json.loads((tmp_path / "results" / "test-runs.jsonl").read_text(encoding="utf-8"))
    assert logged["freeze"] == "override: no freeze tag"
