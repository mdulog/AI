"""Static structural tests for cluster-themes.md."""
import re
from pathlib import Path

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "cluster-themes.md").read_text(encoding="utf-8")


def test_distillations_variable_present():
    assert "{{distillations}}" in PROMPT


def test_theme_block_format_documented():
    # Look for the "## Theme:" header pattern in instructions or examples
    assert "## Theme:" in PROMPT, "Theme h2 format must be documented"


def test_frequency_line_documented():
    assert re.search(r"Frequency:\s*N?/5", PROMPT) or "Frequency: N/5" in PROMPT or "Frequency:" in PROMPT, \
        "Frequency: N/5 line format must be documented"


def test_contradictions_block_documented():
    assert "Contradictions:" in PROMPT or "contradiction" in PROMPT.lower(), \
        "Contradictions block must be documented"


def test_low_frequency_outlier_handling():
    text = PROMPT.lower()
    assert "1/5" in text or "low-frequency" in text or "outlier" in text or "single transcript" in text, \
        "Must instruct on low-frequency / outlier theme handling"


def test_cross_transcript_citation_documented():
    # Cross-transcript citations should reference [T<id>:...] pattern
    assert re.search(r"\[T<id>", PROMPT) or re.search(r"\[T\d+", PROMPT), \
        "Citation format must be documented"
