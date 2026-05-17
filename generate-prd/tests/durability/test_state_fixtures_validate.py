"""Schema-validates every state fixture under state-fixtures/.

The resume-from-X tests (in_progress, paused, faulted) are manual playbooks because
they require driving the actual orchestrator. But the JSON fixtures they feed are
ordinary state documents — they MUST validate against state.schema.json or the
orchestrator's resume code path can't read them. This test catches the simpler
failure mode (broken fixture) without needing a live run.
"""
import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "state.schema.json"
FIXTURES_DIR = Path(__file__).resolve().parent / "state-fixtures"

EXPECTED_FIXTURES = (
    "in-progress-mid-loop.json",
    "paused-after-iteration-3.json",
    "faulted-stuck-loop.json",
)


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_all_expected_fixtures_exist():
    for name in EXPECTED_FIXTURES:
        assert (FIXTURES_DIR / name).is_file(), f"Missing fixture: {name}"


@pytest.mark.parametrize("fixture_name", EXPECTED_FIXTURES)
def test_fixture_validates_against_state_schema(fixture_name: str):
    schema = _load_schema()
    state = json.loads((FIXTURES_DIR / fixture_name).read_text(encoding="utf-8"))
    jsonschema.validate(state, schema)


def test_in_progress_fixture_models_mid_loop_state():
    state = json.loads((FIXTURES_DIR / "in-progress-mid-loop.json").read_text())
    assert state["status"] == "in_progress"
    assert state["iteration_count"] >= 5, "Mid-loop fixture should have non-trivial iteration count"
    assert state["qa_turn_count"] > 0, "Mid-loop fixture must have qa_history"
    assert state["fault"] is None, "in_progress state must have null fault"


def test_paused_fixture_models_clean_pause():
    state = json.loads((FIXTURES_DIR / "paused-after-iteration-3.json").read_text())
    assert state["status"] == "paused"
    assert state["fault"] is None, "paused (non-fault) state must have null fault"
    # The qa_history's last entry should reflect the /pause command
    last_turn = state["qa_history"][-1]
    assert last_turn.get("command") == "/pause", \
        "Paused fixture's last qa_history entry should be the /pause command"


def test_faulted_fixture_carries_diagnostic():
    state = json.loads((FIXTURES_DIR / "faulted-stuck-loop.json").read_text())
    assert state["status"] == "faulted"
    assert state["fault"] is not None, "faulted state must have a fault payload"
    fault = state["fault"]
    assert fault["type"] == "stuck_loop"
    assert "diagnostic" in fault and len(fault["diagnostic"]) > 20, \
        "Diagnostic must be present and non-trivial — the PM reads this on resume"
    # Verify the fixture actually contains 5 identical hashes at the tail
    critic_hashes = [
        entry["output_hash"]
        for entry in state["qa_history"]
        if entry.get("kind") == "critic_pass"
    ]
    tail_5 = critic_hashes[-5:]
    assert len(set(tail_5)) == 1, \
        f"Fault fixture should have 5 identical critic hashes at the tail; got {tail_5}"


def test_resume_playbooks_documented():
    """Each fixture should be paired with a manual playbook."""
    playbooks_dir = FIXTURES_DIR.parent
    expected_playbooks = (
        "test_resume_in_progress.md",
        "test_resume_paused.md",
        "test_resume_faulted.md",
    )
    for name in expected_playbooks:
        path = playbooks_dir / name
        assert path.is_file(), f"Missing playbook: {path}"
        text = path.read_text(encoding="utf-8")
        assert "Setup" in text and "Run" in text and ("Expected" in text or "Pass criteria" in text), \
            f"Playbook {name} missing expected sections"
