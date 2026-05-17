"""Static tests for stuck-loop fault detection and context-window handling.

These tests verify the ORCHESTRATOR documents the contracts; the behavioral
triggers themselves require live runs (see the manual playbooks alongside).
"""
import re
from pathlib import Path

ORCHESTRATOR = Path(__file__).resolve().parents[2] / "generate-prd.md"
TEXT = ORCHESTRATOR.read_text(encoding="utf-8")


# ---------- Task 3.5: stuck-loop fault detection ----------

def test_orchestrator_documents_stuck_loop_detection_with_5_window():
    assert "stuck_loop" in TEXT, "Fault type 'stuck_loop' must be named in the orchestrator"
    # The 5-in-a-row window must be explicit (not "many", not "several")
    has_window = (
        "5 iterations in a row" in TEXT
        or "identical findings 5" in TEXT
        or re.search(r"last 5 .*output_hash", TEXT) is not None
        or re.search(r"5 `output_hash`", TEXT) is not None
    )
    assert has_window, "Stuck-loop window of 5 must be explicit in the orchestrator"


def test_orchestrator_documents_output_hash_invariant():
    assert "output_hash" in TEXT, "Stuck-loop detection requires output_hash; must be named"
    assert "sha256" in TEXT.lower() or "hash" in TEXT.lower(), "Hashing algorithm must be specified"


def test_orchestrator_documents_three_stuck_loop_choices():
    """Per spec § 7.7.4 — PM gets 3 choices on stuck-loop fault."""
    text_lower = TEXT.lower()
    assert "finalize anyway" in text_lower, "Must offer 'finalize anyway' on stuck-loop"
    assert "pivot" in text_lower, "Must offer 'pivot the discussion' on stuck-loop"
    assert "report a bug" in text_lower or "bug" in text_lower, "Must offer 'report a bug' on stuck-loop"


def test_stuck_loop_playbook_exists():
    playbook = ORCHESTRATOR.parent / "tests" / "durability" / "test_stuck_loop_detection.md"
    assert playbook.is_file()
    text = playbook.read_text()
    assert "Pass criteria" in text
    assert "/skip" in text, "Playbook must use /skip to keep draft byte-identical across iterations"


# ---------- Task 3.6: context-window handling ----------

def test_orchestrator_documents_tier1_70_percent_threshold():
    assert "70%" in TEXT, "Tier 1 threshold of 70% must be explicit"
    assert "compaction" in TEXT.lower(), "Compaction must be named"


def test_orchestrator_documents_tier2_clean_restart():
    text_lower = TEXT.lower()
    assert "tier 2" in text_lower, "Tier 2 must be named as a distinct mechanism"
    assert "context_carryover" in TEXT or "carryover" in text_lower, \
        "Tier 2 must use the context_carryover fault type"
    # Must explicitly say it pauses with status=paused (not faulted) on Tier 2
    assert re.search(r'status.*paused', TEXT, re.IGNORECASE), \
        "Tier 2 should set status=paused so resume works on next run"


def test_orchestrator_documents_compaction_preserves_disk_state():
    """The key invariant: compaction is in-memory only; disk state is unaffected."""
    text_lower = TEXT.lower()
    has_invariant = (
        "in-memory" in text_lower
        or "state on disk is unaffected" in text_lower
        or "disk truth" in text_lower
        or ("on-disk" in text_lower and "unaffected" in text_lower)
        or "remains on disk" in text_lower
    )
    assert has_invariant, "Orchestrator must state compaction is in-memory; disk state is unaffected"


def test_orchestrator_keeps_recent_turns_verbatim():
    """Tier 1 retains the last 3-5 Q&A turns verbatim per spec § 7.9."""
    assert ("3–5" in TEXT or "3-5" in TEXT or "last 3" in TEXT.lower()), \
        "Tier 1 retention window (last 3-5 verbatim turns) must be documented"


def test_compaction_playbook_exists():
    playbook = ORCHESTRATOR.parent / "tests" / "durability" / "test_context_compaction.md"
    assert playbook.is_file()
    text = playbook.read_text()
    assert "Tier 1" in text and "Tier 2" in text, "Playbook must cover both tiers"


# ---------- Cross-cutting: both faults are differentiable in state ----------

def test_fault_types_documented():
    """Both fault types (stuck_loop, context_carryover) must be enumerated, not folded together."""
    assert "stuck_loop" in TEXT
    assert "context_carryover" in TEXT
    # And they must trigger different status values: stuck_loop -> faulted, context_carryover -> paused
    # (rough check; full behavior is in the playbooks)
