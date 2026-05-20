"""Static structural tests for finalize-prd.md."""
from pathlib import Path

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "finalize-prd.md").read_text(encoding="utf-8")


def test_required_variables_present():
    for var in ("{{final_draft}}", "{{transcript_index}}"):
        assert var in PROMPT, f"Missing variable: {var}"


def test_three_output_sections_documented():
    for heading in ("## Completeness", "## Citations", "## Recommendations"):
        assert heading in PROMPT, f"Output section not documented: {heading}"


def test_report_only_clause():
    text = PROMPT.lower()
    assert ("never rewrite" in text or "do not rewrite" in text or "only report" in text or
            "report only" in text or "do not modify" in text), \
        "Prompt must specify report-only / no-rewrite contract"


def test_unresolved_citation_handling():
    text = PROMPT.lower()
    assert "resolve" in text or "unresolved" in text or "missing citation" in text or \
           "transcript_index" in text or "not in" in text, \
        "Prompt must address unresolved-citation flagging"


def test_completeness_check_documented():
    text = PROMPT.lower()
    assert ("empty" in text or "intent line" in text or "placeholder" in text or
            "tbd" in text or "blank" in text), \
        "Prompt must specify what counts as incomplete"


def test_no_new_requirements_clause():
    text = PROMPT.lower()
    assert ("not new requirements" in text or "not new findings" in text or
            "no new requirements" in text or "editorial" in text), \
        "Prompt must clarify Recommendations isn't for new requirements"
