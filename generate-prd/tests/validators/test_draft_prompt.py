"""Static structural tests for draft-prd.md."""
from pathlib import Path

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "draft-prd.md").read_text(encoding="utf-8")


def test_required_variables_present():
    for var in ("{{themes}}", "{{template}}"):
        assert var in PROMPT, f"Missing variable: {var}"


def test_all_9_sections_referenced():
    for heading in (
        "Background & Problem", "Target Users", "Goals & Non-Goals", "User Stories",
        "Functional Requirements", "Non-Functional Requirements",
        "Success Metrics", "Risks & Open Questions", "Constraints",
    ):
        assert heading in PROMPT, f"PRD section not referenced: {heading}"


def test_evidence_anchored_sections_identified():
    for heading in ("Background & Problem", "Target Users", "User Stories",
                    "Functional Requirements", "Risks & Open Questions"):
        # Just check the prompt distinguishes these as evidence-anchored;
        # the exact wording is up to the prompt author.
        assert heading in PROMPT
    # Look for some marker of the evidence/judgment distinction
    text = PROMPT.lower()
    assert ("evidence-anchored" in text or "evidence anchored" in text or "from themes" in text
            or "from the themes" in text or "populate" in text), \
        "Prompt must distinguish evidence-anchored sections"


def test_pm_judgment_sections_left_empty_instruction():
    text = PROMPT.lower()
    assert ("pm-judgment" in text or "pm judgment" in text or "leave empty" in text
            or "heading and" in text and "intent" in text or "do not fabricate" in text), \
        "Prompt must instruct that judgment sections stay empty"


def test_citation_format_documented():
    import re
    assert re.search(r"\[T<id>", PROMPT) or re.search(r"\[T\d+", PROMPT), \
        "Citation format must be documented"


def test_no_fabrication_clause():
    text = PROMPT.lower()
    assert "fabricate" in text or "invent" in text or "make up" in text, \
        "Prompt must explicitly forbid fabrication"
