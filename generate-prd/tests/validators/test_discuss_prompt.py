"""Static structural tests for discuss-finding.md."""
from pathlib import Path

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "discuss-finding.md").read_text(encoding="utf-8")


def test_required_variables_present():
    for var in ("{{finding}}", "{{relevant_section}}", "{{relevant_themes}}", "{{prior_qa}}"):
        assert var in PROMPT, f"Missing variable: {var}"


def test_one_question_constraint_documented():
    text = PROMPT.lower()
    assert ("one question" in text or "exactly one" in text or "single question" in text), \
        "Prompt must constrain output to a single question"


def test_non_leading_constraint():
    text = PROMPT.lower()
    assert ("non-leading" in text or "non leading" in text or "open-ended" in text or
            "open ended" in text or "not a yes/no" in text or "not a yes or no" in text), \
        "Prompt must require non-leading / open-ended phrasing"


def test_no_preamble_constraint():
    text = PROMPT.lower()
    assert "preamble" in text or "no explanation" in text or "plain text" in text, \
        "Prompt must forbid preamble / explanation around the question"


def test_implementation_topics_forbidden():
    text = PROMPT.lower()
    # The prompt should list forbidden topics — API, database, UI, etc.
    forbidden_topic_mentions = sum(t in text for t in (
        "api", "database", "ui", "button", "dashboard", "implementation", "how would you build",
    ))
    assert forbidden_topic_mentions >= 3, \
        f"Prompt must explicitly forbid implementation topics; found {forbidden_topic_mentions} mentions"


def test_what_why_not_how_documented():
    text = PROMPT.lower()
    assert ("what and why" in text or "not how" in text or "what, not how" in text or
            "underlying" in text), \
        "Prompt must orient discussion to WHAT/WHY, not HOW"
