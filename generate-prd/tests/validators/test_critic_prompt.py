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


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "golden-corpus" / "critic-fixtures"

ALL_PLANTED_FIXTURES = (
    ("draft-with-contradiction.md",        "CONTRADICTION"),
    ("draft-with-coverage-gap.md",         "COVERAGE_GAP"),
    ("draft-with-solution-bias.md",        "SOLUTION_BIAS"),
    ("draft-with-unsupported-assumption.md", "UNSUPPORTED_ASSUMPTION"),
    ("draft-with-goal-metric-mismatch.md", "GOAL_METRIC_MISMATCH"),
    ("draft-with-persona-story-mismatch.md", "PERSONA_STORY_MISMATCH"),
    ("draft-with-evidence-thin-section.md", "EVIDENCE_THIN"),
)


def test_planted_fixtures_exist():
    for filename, _expected_finding in ALL_PLANTED_FIXTURES:
        assert (FIXTURES_DIR / filename).is_file(), f"Missing planted fixture: {filename}"
    # Every named finding type has a fixture
    fixture_findings = {finding for _name, finding in ALL_PLANTED_FIXTURES}
    assert fixture_findings == set(ALL_SEVEN_TYPES), \
        f"Fixture set must cover all 7 finding types; missing: {set(ALL_SEVEN_TYPES) - fixture_findings}"


def test_each_planted_fixture_declares_its_expected_finding_in_comment_header():
    """Every fixture must start with an HTML comment naming its expected finding type.

    This is durable documentation: the next engineer (or live tuner) reads the
    fixture and knows exactly which critic finding it's designed to trigger.
    """
    for filename, expected_finding in ALL_PLANTED_FIXTURES:
        text = (FIXTURES_DIR / filename).read_text(encoding="utf-8")
        assert text.lstrip().startswith("<!--"), \
            f"{filename}: must open with an HTML comment header"
        header_end = text.find("-->")
        assert header_end > 0
        header = text[:header_end]
        assert f"Expected critic finding: {expected_finding}" in header, \
            f"{filename}: header must declare 'Expected critic finding: {expected_finding}'"


def test_unsupported_assumption_fixture_contains_evidence_free_claim():
    """The fixture must contain a specific claim with no golden-corpus support."""
    text = (FIXTURES_DIR / "draft-with-unsupported-assumption.md").read_text()
    assert "Salesforce" in text, "UNSUPPORTED_ASSUMPTION fixture must reference Salesforce"
    # And the golden-corpus transcripts must NOT mention Salesforce (else it'd be supported)
    corpus_dir = Path(__file__).resolve().parents[1] / "golden-corpus" / "transcripts"
    for transcript in corpus_dir.glob("*"):
        assert "Salesforce" not in transcript.read_text(encoding="utf-8"), \
            f"{transcript.name} mentions Salesforce — UNSUPPORTED_ASSUMPTION fixture is no longer evidence-free"


def test_goal_metric_mismatch_fixture_has_filled_goal_and_empty_metrics():
    text = (FIXTURES_DIR / "draft-with-goal-metric-mismatch.md").read_text()
    # Goals must have content
    goals_section = re.search(r"## Goals & Non-Goals\n(.*?)(?=\n## )", text, re.DOTALL)
    assert goals_section, "Fixture must have a Goals section"
    goals_body = goals_section.group(1)
    assert "50%" in goals_body or "Reduce" in goals_body, "Goals must contain a measurable target"
    # Metrics must be empty (heading + intent line only)
    metrics_section = re.search(r"## Success Metrics\n\*[^*]+\*\n(.*?)(?=\n## )", text, re.DOTALL)
    assert metrics_section, "Fixture must have a Success Metrics section"
    metrics_body = metrics_section.group(1).strip()
    assert metrics_body == "", \
        f"Success Metrics body must be empty for GOAL_METRIC_MISMATCH; got: {metrics_body!r}"


def test_persona_story_mismatch_fixture_declares_one_persona_and_alien_story():
    text = (FIXTURES_DIR / "draft-with-persona-story-mismatch.md").read_text()
    # Target Users declares "SMB ops manager"
    assert "SMB ops manager" in text
    # User Stories include an "enterprise IT admin" story (alien to the declared persona)
    assert "enterprise IT admin" in text or "enterprise IT" in text


def test_evidence_thin_fixture_has_one_citation_with_overweighted_claim():
    text = (FIXTURES_DIR / "draft-with-evidence-thin-section.md").read_text()
    assert "Primary risk" in text or "primary risk" in text or "biggest blocker" in text, \
        "EVIDENCE_THIN fixture must over-weight the claim"
    risks_section = re.search(r"## Risks & Open Questions\n(.*?)(?=\n## )", text, re.DOTALL)
    assert risks_section
    risks_body = risks_section.group(1)
    # The compliance claim should cite T03 exactly once
    t03_citations = re.findall(r"\[T03[:\]]", risks_body)
    assert len(t03_citations) == 1, \
        f"EVIDENCE_THIN fixture should have exactly one T03 citation for the over-weighted claim; got {len(t03_citations)}"


def test_clean_baseline_fixture_exists_and_has_metrics_and_no_solution_bias():
    text = (FIXTURES_DIR / "draft-very-clean.md").read_text()
    # Must have populated Success Metrics
    metrics_section = re.search(r"## Success Metrics\n\*[^*]+\*\n(.*?)(?=\n## )", text, re.DOTALL)
    assert metrics_section and len(metrics_section.group(1).strip()) > 50, \
        "Clean fixture must have a populated Success Metrics section"
    # Must NOT contain obvious solution-bias keywords in Functional Requirements
    func_section = re.search(r"## Functional Requirements\n(.*?)(?=\n## )", text, re.DOTALL)
    assert func_section
    func_body = func_section.group(1).lower()
    for bias_keyword in ("rest api", "endpoint", "react component", "redis", "/onboarding/"):
        assert bias_keyword not in func_body, \
            f"Clean fixture's Functional Requirements should not contain '{bias_keyword}'"


def test_finding_type_definitions_are_distinct():
    """The critic prompt's per-type definitions must use enough distinct vocabulary
    that the model can confidently label a finding as exactly one of the seven.

    We can't check semantic distinctness from here, but we can check that each
    finding type's definition row contains a keyword that doesn't appear in any
    other type's row. This catches the most common authoring failure mode:
    accidentally giving two types overlapping definitions.
    """
    # Extract the | TYPE | definition | rows from the prompt's finding-types table
    type_def_rows = re.findall(r"\|\s*`([A-Z_]+)`\s*\|\s*([^|]+?)\s*\|", PROMPT)
    type_defs = {t: d for t, d in type_def_rows if t in ALL_SEVEN_TYPES}
    assert len(type_defs) == 7, f"Expected 7 finding-type definition rows; found {len(type_defs)}"
    # Each definition must contain ≥1 distinct content word not present in any other
    for t, definition in type_defs.items():
        words = {w.lower() for w in re.findall(r"\b[a-z]{4,}\b", definition.lower())}
        others_words: set[str] = set()
        for other_t, other_def in type_defs.items():
            if other_t == t:
                continue
            others_words |= {w.lower() for w in re.findall(r"\b[a-z]{4,}\b", other_def.lower())}
        distinct = words - others_words
        assert distinct, \
            f"Finding type {t}'s definition has no distinct content word vs the others; vocabulary collapse"
