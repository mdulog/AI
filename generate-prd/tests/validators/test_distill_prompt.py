"""Static structural tests for distill-transcript.md."""
import re
from pathlib import Path

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "distill-transcript.md").read_text(encoding="utf-8")


def test_required_variables_present():
    for var in ("{{transcript_id}}", "{{normalized_transcript}}"):
        assert var in PROMPT, f"Missing variable: {var}"


def test_all_five_sections_documented():
    for heading in ("## Problems", "## Jobs to be done", "## Pains",
                    "## Personas", "## Customer-proposed solutions"):
        assert heading in PROMPT, f"Output section not documented: {heading}"


def test_citation_format_documented():
    # Either an example like [T01:00:01:23] or the pattern description
    assert re.search(r"\[T<id>", PROMPT) or re.search(r"\[T\d+", PROMPT), \
        "Citation format must be documented"


def test_disfluency_clause_present():
    text = PROMPT.lower()
    assert "disfluenc" in text or "paraphras" in text, \
        "Must instruct to paraphrase, not quote disfluencies"


def test_anti_solution_clause_present():
    # The clause should explicitly tell the model not to invent solutions
    text = PROMPT.lower()
    has_no_solution_clause = any(
        phrase in text for phrase in (
            "do not propose", "do not suggest", "do not recommend",
            "do not invent", "must not propose", "never propose",
        )
    )
    assert has_no_solution_clause, "Anti-solution clause missing"
    # And the "customer-proposed solutions" section must be the ONLY place solution-like content goes
    assert "customer-proposed solutions" in text


def test_speaker_label_caveat():
    text = PROMPT.lower()
    assert "hint" in text or "not ground truth" in text or "may be mis" in text, \
        "Prompt must caveat speaker labels (e.g., 'hints, not ground truth')"
