"""Verify every `Agent(...)` dispatch in the orchestrator is preceded by a checkpoint write.

The continuous-state design (spec § 2.2) requires write-ahead state: the orchestrator
must persist `prd/.state.json` BEFORE invoking the LLM, so a mid-call crash leaves
a recoverable record. This test parses the orchestrator markdown and confirms the
pattern is documented at every Agent dispatch site.
"""
import re
from pathlib import Path

ORCHESTRATOR = Path(__file__).resolve().parents[2] / "generate-prd.md"


def test_every_agent_invocation_is_preceded_by_checkpoint_annotation():
    text = ORCHESTRATOR.read_text(encoding="utf-8")
    misses = []
    for m in re.finditer(r"\bAgent\s*\(", text):
        prefix = text[max(0, m.start() - 400):m.start()]
        has_marker = "Checkpoint:" in prefix or "checkpoint write" in prefix.lower()
        if not has_marker:
            line = text[:m.start()].count("\n") + 1
            misses.append(f"  line ~{line}: no checkpoint annotation in 400 chars before Agent(")
    assert not misses, "Agent dispatches missing checkpoint-before-call annotation:\n" + "\n".join(misses)


def test_continuous_checkpoint_principle_documented():
    """The 'write before LLM call' invariant must be stated as a principle, not just per-step."""
    text = ORCHESTRATOR.read_text(encoding="utf-8")
    assert "Checkpoint discipline" in text or "checkpoint discipline" in text or \
           "write-ahead" in text.lower(), \
        "Orchestrator must state the checkpoint discipline as a named invariant"
    assert "BEFORE every Agent" in text or "BEFORE the dispatch" in text or \
           "before every Agent invocation" in text.lower(), \
        "Orchestrator must explicitly say writes happen BEFORE the agent call"


def test_agent_dispatch_count_matches_expected_phases():
    """7 dispatches expected: normalize, distill, cluster, draft(initial), critic, draft(refine), finalize."""
    text = ORCHESTRATOR.read_text(encoding="utf-8")
    dispatches = re.findall(r"Dispatch `Agent\(\{ subagent_type: \"([^\"]+)\"", text)
    expected = [
        "transcript-normalizer",
        "transcript-distiller",
        "theme-clusterer",
        "prd-drafter",   # initial
        "prd-critic",
        "prd-drafter",   # refine
        "prd-finalizer",
    ]
    assert dispatches == expected, f"Dispatch sequence mismatch.\nGot:      {dispatches}\nExpected: {expected}"
