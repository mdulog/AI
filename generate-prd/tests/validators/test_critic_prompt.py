"""Static structural tests for critic-pass.md.

The critic prompt is the heart of the discovery loop. These tests verify the prompt
DOCUMENTS the contract (all 7 finding types, output format, no-closure clause).
Behavioral tests against the live model are deferred to Phase 4 manual tuning.
"""
import re
from pathlib import Path

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "critic-pass.md").read_text(encoding="utf-8")

ALL_SEVEN_TYPES = (
    "CONTRADICTION", "COVERAGE_GAP", "UNSUPPORTED_ASSUMPTION", "SOLUTION_BIAS",
    "GOAL_METRIC_MISMATCH", "PERSONA_STORY_MISMATCH", "EVIDENCE_THIN",
)


def test_required_variables_present():
    for var in ("{{transcripts}}", "{{themes}}", "{{qa_history}}", "{{current_draft}}"):
        assert var in PROMPT, f"Missing variable: {var}"


def test_all_seven_finding_types_named():
    for t in ALL_SEVEN_TYPES:
        assert t in PROMPT, f"Finding type not documented: {t}"


def test_finding_heading_format_specified():
    assert "### Finding" in PROMPT, "Finding heading format must be documented"
    assert re.search(r"### Finding \d", PROMPT) or "### Finding N" in PROMPT, \
        "Finding heading pattern must be illustrated"


def test_recommended_starting_point_line_specified():
    assert "Recommended starting point" in PROMPT, \
        "Recommended-starting-point line must be specified"


def test_no_findings_output_specified():
    text = PROMPT.lower()
    assert "no significant findings" in text or "no findings" in text, \
        "Zero-findings output must be specified"


def test_closure_signals_explicitly_forbidden():
    text = PROMPT.lower()
    forbidden_phrases_referenced = sum(p in text for p in (
        "we're done", "looks complete", "consider finalizing",
        "ready to finalize", "no more findings", "/done",
    ))
    assert forbidden_phrases_referenced >= 3, \
        f"Prompt must explicitly forbid at least 3 closure phrases; found {forbidden_phrases_referenced}"


def test_read_only_clause():
    text = PROMPT.lower()
    assert "read-only" in text or "read only" in text or "do not rewrite" in text, \
        "Prompt must specify read-only / no-rewrite contract"


def test_no_ranking_clause():
    text = PROMPT.lower()
    assert ("low priority" in text or "skip" in text or "rank" in text or
            "every finding" in text), \
        "Prompt must address the no-rank-as-skippable rule"


def test_planted_fixtures_exist():
    fixtures_dir = Path(__file__).resolve().parents[1] / "golden-corpus" / "critic-fixtures"
    for name in ("draft-with-contradiction.md", "draft-with-solution-bias.md",
                 "draft-with-coverage-gap.md"):
        assert (fixtures_dir / name).is_file(), f"Missing planted fixture: {name}"
