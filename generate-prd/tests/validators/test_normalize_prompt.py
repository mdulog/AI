"""Static structural tests for normalize-transcript.md.

These check that the prompt FILE documents the right contract.
Behavioral (live-API) validation is deferred — see plan for context.
"""
import re
from pathlib import Path

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "normalize-transcript.md").read_text(encoding="utf-8")


def test_prompt_declares_required_variables():
    for var in ("{{source_format}}", "{{transcript_id}}", "{{raw_text}}"):
        assert var in PROMPT, f"Missing variable placeholder: {var}"


def test_prompt_specifies_yaml_frontmatter_keys():
    for key in ("transcript_id", "source_format", "source_path", "normalized_at",
                "speakers", "glossary_applied"):
        assert key in PROMPT, f"Front-matter key not documented: {key}"


def test_prompt_specifies_speaker_block_format():
    # The prompt should show or describe the **<speaker>**: <utterance> pattern
    assert re.search(r"\*\*[^*]*\*\*:", PROMPT) or "**<speaker>**" in PROMPT, \
        "Prompt must document the **speaker**: <utterance> body format"


def test_prompt_has_donot_clauses():
    text = PROMPT.lower()
    assert "paraphrase" in text, "Must explicitly forbid paraphrasing"
    assert "commentary" in text or "explanat" in text, "Must forbid commentary"


def test_prompt_documents_glossary_is_preprocessed():
    # Glossary application is deterministic preprocessing, NOT this prompt's job
    text = PROMPT.lower()
    assert "glossary" in text, "Prompt must mention glossary handling (to clarify it's preprocessed)"
