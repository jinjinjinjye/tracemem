"""The scenario validator: one small broken scenario per issue code, and the pilots pass.

Each case starts from tests/fixtures/minimal.yaml (which has no issues at all)
and breaks exactly one thing, so the validator must report exactly one code.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from support import FIXTURES, MINIMAL, PILOT_IDS, minimal_dict, pilot_path
from tracemem.bench.validate import ISSUE_CODES, Issue, check_file, check_scenario
from tracemem.cli import main
from tracemem.schema import Scenario

# ---------------------------------------------------------------------------
# One edit per case. Each takes the minimal scenario as a dict and breaks one rule.
# ---------------------------------------------------------------------------


def _event(data, turn):
    return next(e for e in data["script"] if e["turn"] == turn)


def _item(data, key):
    return next(i for i in data["items"] if i["key"] == key)


def duplicate_question_id(d):
    d["questions"].append(dict(d["questions"][0]))


def duplicate_item_key(d):
    d["items"].append(dict(_item(d, "model.tagger")))


def turn_in_wrong_session(d):
    d["sessions"][1]["turns"][2]["id"] = "S3-T3"  # third turn of S2 is named as if it were in S3


def turns_out_of_order(d):
    turns = d["sessions"][0]["turns"]
    turns[1]["id"], turns[2]["id"] = "S1-T3", "S1-T2"
    _event(d, "S1-T2")["turn"] = "S1-T3"  # keep the task_open on the same text


def sessions_out_of_order(d):
    d["sessions"][1]["id"] = "S3"
    for turn in d["sessions"][1]["turns"]:
        turn["id"] = turn["id"].replace("S2-", "S3-")
    for event in d["script"]:
        event["turn"] = event["turn"].replace("S2-", "S3-")
    d["questions"][0]["after"] = "S3"


def dates_go_backwards(d):
    d["sessions"][1]["date"] = "2026-01-01"


def event_on_unknown_turn(d):
    _event(d, "S2-T2")["turn"] = "S2-T9"


def accept_names_unknown_turn(d):
    d["script"].append({"turn": "S2-T3", "act": "accept", "item": "model.main", "accepts": "S1-T9"})


def event_on_unknown_item(d):
    _event(d, "S2-T1")["item"] = "model.unknown"


def question_on_unknown_item(d):
    d["questions"][0]["item"] = "model.unknown"


def decide_on_a_task(d):
    d["script"].append({"turn": "S1-T3", "act": "decide", "item": "task.loader", "value": "open"})


def task_progress_without_progress(d):
    del _event(d, "S2-T2")["progress"]


def decide_with_accepts(d):
    _event(d, "S1-T1")["accepts"] = "S1-T2"


def value_not_canonical(d):
    _event(d, "S2-T1")["value"] = "RoBERTa"


def task_values_not_progress(d):
    _item(d, "task.loader")["values"] = {"almost done": []}


def alias_collision(d):
    _item(d, "model.main")["values"]["DistilBERT"].append("BERT-Base")  # spells BERT's alias bert-base


def two_statements_same_item_same_turn(d):
    d["script"].append({"turn": "S2-T1", "act": "restate", "item": "model.main", "value": "DistilBERT"})


def revise_without_decision(d):
    _event(d, "S1-T1")["act"] = "revise"


def restate_different_value(d):
    d["script"].append({"turn": "S2-T3", "act": "restate", "item": "model.main", "value": "BERT"})


def previous_question_with_session(d):
    d["questions"][0]["session"] = "S1"


def as_of_without_session(d):
    d["questions"].append({"id": "asof", "after": "S2", "kind": "as_of", "item": "model.main", "text": "Then?"})


def as_of_about_a_later_session(d):
    d["questions"].append({"id": "asof", "after": "S1", "kind": "as_of", "session": "S2", "item": "model.main",
                           "text": "Then?"})


def question_after_unknown_session(d):
    d["questions"][0]["after"] = "S7"


def confusable_with_itself(d):
    _item(d, "model.main")["confusable_with"] = ["model.main"]


def confusable_with_unknown(d):
    _item(d, "model.main")["confusable_with"] = ["model.unknown"]


def confusable_listed_on_one_side_only(d):
    _item(d, "model.tagger")["confusable_with"] = []


def description_names_a_value(d):
    _item(d, "model.main")["description"] = "we train BERT for the classifier"


def history_question_names_todays_value(d):
    d["questions"][0]["text"] = "What did we train before DistilBERT?"


def non_control_without_trap(d):
    d["category"] = "suggestion_after_decision"


def question_names_its_answer(d):
    d["questions"].append({"id": "leak", "after": "S2", "kind": "current", "item": "model.main",
                           "text": "Are we still on DistilBERT?"})


def question_names_a_stale_value(d):
    d["questions"].append({"id": "leak", "after": "S2", "kind": "current", "item": "model.main",
                           "text": "Did we drop bert-base?"})


def short_session(d):
    d["sessions"][0]["turns"].pop()  # S1-T3 carries no event


def long_session(d):
    d["sessions"][1]["turns"] += [{"id": f"S2-T{i}", "speaker": "Ana", "text": "..."} for i in range(4, 14)]


def confusable_items_share_a_spelling(d):
    _item(d, "model.tagger")["values"]["spaCy"].append("bert-base")


def mention_of_the_current_value(d):
    d["script"].append({"turn": "S1-T3", "act": "mention", "item": "model.main", "value": "BERT"})


def mention_in_a_turn_that_acts_on_the_item(d):
    d["script"].append({"turn": "S2-T1", "act": "mention", "item": "model.main", "value": "DistilBERT"})


CASES = {
    # code: [edits that must produce exactly that code]
    "E-duplicate-id": [duplicate_question_id, duplicate_item_key],
    "E-turn-session": [turn_in_wrong_session],
    "E-order": [turns_out_of_order, sessions_out_of_order],
    "E-date": [dates_go_backwards],
    "E-unknown-turn": [event_on_unknown_turn, accept_names_unknown_turn],
    "E-unknown-item": [event_on_unknown_item, question_on_unknown_item],
    "E-act-kind": [decide_on_a_task],
    "E-fields": [task_progress_without_progress, decide_with_accepts],
    "E-value": [value_not_canonical, task_values_not_progress],
    "E-alias-collision": [alias_collision],
    "E-same-item-turn": [two_statements_same_item_same_turn],
    "E-script": [revise_without_decision, restate_different_value],
    "E-question": [previous_question_with_session, as_of_without_session, as_of_about_a_later_session,
                   question_after_unknown_session],
    "E-confusable": [confusable_with_itself, confusable_with_unknown, confusable_listed_on_one_side_only],
    "W-no-trap": [non_control_without_trap],
    "W-leak": [question_names_its_answer, question_names_a_stale_value, history_question_names_todays_value],
    "W-mention-redundant": [mention_of_the_current_value, mention_in_a_turn_that_acts_on_the_item],
    "W-session-length": [short_session, long_session],
    "W-alias-shared": [confusable_items_share_a_spelling],
    "W-description-leak": [description_names_a_value],
}
# E-schema and E-split-folder need a file on disk; they are tested separately below.
FILE_ONLY = {"E-schema", "E-split-folder"}

PARAMS = [pytest.param(code, edit, id=f"{code}:{edit.__name__}") for code, edits in CASES.items() for edit in edits]


def codes(issues: list[Issue]) -> set[str]:
    return {issue.code for issue in issues}


def test_the_base_fixture_has_no_issues():
    """The starting point is clean, so any code a case reports comes from its one edit."""
    issues, stats = check_file(MINIMAL)
    assert issues == []
    assert stats is not None and stats.current_questions == 4


def test_every_issue_code_has_a_case():
    assert set(CASES) | FILE_ONLY == set(ISSUE_CODES)


@pytest.mark.parametrize("code, edit", PARAMS)
def test_each_broken_scenario_reports_exactly_its_code(code, edit):
    data = minimal_dict()
    edit(data)
    issues, _ = check_scenario(Scenario.model_validate(data))
    assert codes(issues) == {code}, [issue.render() for issue in issues]
    expected_level = "error" if code.startswith("E-") else "warning"
    assert {issue.level for issue in issues} == {expected_level}


def test_errors_stop_before_the_replay_and_warnings_do_not():
    """A scenario with an error gets no trap statistics; one with only warnings still does."""
    data = minimal_dict()
    value_not_canonical(data)
    assert check_scenario(Scenario.model_validate(data))[1] is None
    data = minimal_dict()
    short_session(data)
    assert check_scenario(Scenario.model_validate(data))[1] is not None


def test_schema_error_for_a_misspelt_field():
    issues, stats = check_file(FIXTURES / "broken-misspelt-field.yaml")
    assert codes(issues) == {"E-schema"} and stats is None
    assert issues[0].scenario == "broken-misspelt-field"  # the file name, since the scenario could not be read


def test_schema_error_for_invalid_yaml(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("scenario_id: [unclosed\n", encoding="utf-8")
    assert codes(check_file(path)[0]) == {"E-schema"}


def _write(folder: Path, data: dict, name: str = "scenario.yaml") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_split_field_must_match_its_folder(tmp_path):
    """A file in dev/ that says split: test is an error, and the reverse is fine once they agree."""
    data = minimal_dict()
    data["split"] = "test"
    assert codes(check_file(_write(tmp_path / "dev", data))[0]) == {"E-split-folder"}
    assert check_file(_write(tmp_path / "test", data))[0] == []


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_pilots_validate_without_errors(scenario_id):
    issues, stats = check_file(pilot_path(scenario_id))
    assert [i.render() for i in issues if i.level == "error"] == []
    assert stats is not None and stats.current_questions > 0


def test_pilot_trap_statistics():
    """The trap counts the validator prints, per pilot: (current questions, candidate, mention, confusable)."""
    got = {}
    for scenario_id in PILOT_IDS:
        stats = check_file(pilot_path(scenario_id))[1]
        got[scenario_id] = (stats.current_questions, stats.trap_candidate, stats.trap_mention, stats.trap_confusable)
    assert got == {
        "pilot-01": (11, 1, 2, 3),
        "pilot-02": (8, 3, 0, 0),
        "pilot-03": (7, 1, 0, 3),
        "pilot-04": (12, 1, 0, 0),
        "pilot-05": (8, 2, 3, 0),
    }


# ---------------------------------------------------------------------------
# Redaction: on the test split, print codes and their generic descriptions, never the specific message
# ---------------------------------------------------------------------------


def test_render_redacted_shows_the_code_description_not_the_message():
    issue = Issue("error", "E-value", "s", "'RoBERTa' is not one of ['BERT', 'DistilBERT']")
    assert "RoBERTa" in issue.render()
    redacted = issue.render(redact=True)
    assert "RoBERTa" not in redacted
    assert redacted == f"error: s: E-value: {ISSUE_CODES['E-value']}"


def test_validate_redacts_files_in_a_test_folder(tmp_path, capsys):
    """`tracemem validate` on a file under test/ prints codes and generic text only, and no trap statistics."""
    data = minimal_dict()
    data["split"] = "test"
    value_not_canonical(data)  # message would name 'RoBERTa'
    question_names_its_answer(data)
    path = _write(tmp_path / "test", data)
    assert main(["validate", str(path)]) == 1
    out = capsys.readouterr().out
    assert "E-value" in out and ISSUE_CODES["E-value"] in out
    assert "RoBERTa" not in out
    assert "DistilBERT" not in out
    assert "current questions; traps" not in out


def test_validate_does_not_redact_dev_files_by_default(tmp_path, capsys):
    data = minimal_dict()
    value_not_canonical(data)
    path = _write(tmp_path / "dev", data)
    assert main(["validate", str(path)]) == 1
    assert "RoBERTa" in capsys.readouterr().out


def test_validate_redact_flag(tmp_path, capsys):
    data = minimal_dict()
    value_not_canonical(data)
    path = _write(tmp_path / "dev", data)
    assert main(["validate", "--redact", str(path)]) == 1
    out = capsys.readouterr().out
    assert "E-value" in out and "RoBERTa" not in out


# ---------------------------------------------------------------------------
# Regression tests for validator bugs found while writing this suite (now fixed)
# ---------------------------------------------------------------------------


def test_a_session_with_no_turns_is_reported_not_a_crash():
    """The schema allows `turns: []` and the validator warns about sessions shorter than 3 turns,
    so an empty session should give W-session-length, not an IndexError."""
    data = minimal_dict()
    data["sessions"].append({"id": "S3", "date": "2026-01-10", "turns": []})
    issues, _ = check_scenario(Scenario.model_validate(data))
    assert "W-session-length" in codes(issues)


def test_leak_is_found_when_punctuation_follows_the_value():
    data = minimal_dict()
    data["questions"].append({"id": "leak", "after": "S2", "kind": "current", "item": "model.main",
                              "text": "Is it DistilBERT, or something else?"})
    assert "W-leak" in codes(check_scenario(Scenario.model_validate(data))[0])


def test_a_mention_during_a_dispute_is_not_redundant():
    """In a dispute no value is current, so recalling either side is a real mention: pilot-02 S2-T2
    ("Hmm, I remember IMDB. Let's check the notes before Friday.") must not be warned about."""
    issues, _ = check_file(pilot_path("pilot-02"))
    assert "W-mention-redundant" not in codes(issues)
    assert any(e.turn == "S2-T2" and e.act == "mention" for e in Scenario.model_validate(
        yaml.safe_load(pilot_path("pilot-02").read_text(encoding="utf-8"))).script)
