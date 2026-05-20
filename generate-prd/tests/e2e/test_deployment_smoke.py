"""End-to-end deployment smoke test for the generate-prd skill.

This is a STATIC, no-API smoke test. It validates that:

1. The skill ships the expected file set (orchestrator + 6 agents + 7 prompts + schemas + corpus).
2. Frontmatter on the orchestrator and every agent parses and declares the expected fields.
3. The orchestrator references all 6 agent names.
4. Each agent references its corresponding prompt by path.
5. All prompts referenced by any agent or the orchestrator actually exist on disk.
6. PRD template, state schema, transcript-format, and golden-corpus directories are in place.

Live end-to-end behavioral validation (real Anthropic API calls through the orchestrator)
is intentionally deferred — the user opted out of API spend in Phase 1/2. When ready, the
manual flow documented in plan Task 2.8 Step 3 covers it.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # generate-prd/

# ---------- File-shape expectations ----------

EXPECTED_AGENTS = (
    "transcript-normalizer",
    "transcript-distiller",
    "theme-clusterer",
    "prd-drafter",
    "prd-critic",
    "prd-finalizer",
)

EXPECTED_PROMPTS = (
    "normalize-transcript",
    "distill-transcript",
    "cluster-themes",
    "draft-prd",
    "critic-pass",
    "discuss-finding",
    "finalize-prd",
)

AGENT_TO_PROMPT = {
    "transcript-normalizer": "normalize-transcript",
    "transcript-distiller": "distill-transcript",
    "theme-clusterer": "cluster-themes",
    "prd-drafter": "draft-prd",
    "prd-critic": "critic-pass",
    "prd-finalizer": "finalize-prd",
}

AGENT_FRONTMATTER_EXPECTATIONS = {
    "transcript-normalizer": {"model": "sonnet", "tools_must_include": {"Read", "Write", "Bash"}},
    "transcript-distiller":  {"model": "sonnet", "tools_must_include": {"Read"}},
    "theme-clusterer":       {"model": "sonnet", "tools_must_include": {"Read"}},
    "prd-drafter":           {"model": "sonnet", "tools_must_include": {"Read", "Write"}},
    "prd-critic":            {"model": "opus",   "tools_must_include": {"Read"}},
    "prd-finalizer":         {"model": "sonnet", "tools_must_include": {"Read"}},
}


# ---------- Helpers ----------

def _read(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


def _frontmatter(content: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    assert m, "No YAML frontmatter found"
    return yaml.safe_load(m.group(1))


# ---------- Tests ----------

def test_orchestrator_exists_and_has_frontmatter():
    content = _read(ROOT / "generate-prd.md")
    fm = _frontmatter(content)
    assert fm.get("model") == "sonnet"
    assert "Agent" in fm.get("allowed-tools", [])
    assert "Read" in fm.get("allowed-tools", []) and "Write" in fm.get("allowed-tools", [])
    assert "description" in fm and isinstance(fm["description"], str) and len(fm["description"]) > 20


def test_all_six_agents_exist_and_have_valid_frontmatter():
    for agent_name in EXPECTED_AGENTS:
        path = ROOT / "Agents" / f"{agent_name}.md"
        content = _read(path)
        fm = _frontmatter(content)
        expected = AGENT_FRONTMATTER_EXPECTATIONS[agent_name]
        assert fm["name"] == agent_name
        assert fm["model"] == expected["model"], f"{agent_name}: expected model {expected['model']}, got {fm['model']}"
        tools = set(fm["tools"])
        missing = expected["tools_must_include"] - tools
        assert not missing, f"{agent_name}: missing tools {missing}"


def test_orchestrator_references_all_six_agents():
    content = _read(ROOT / "generate-prd.md")
    for agent_name in EXPECTED_AGENTS:
        assert agent_name in content, f"Orchestrator does not reference agent: {agent_name}"


def test_all_seven_prompts_exist():
    for prompt_name in EXPECTED_PROMPTS:
        path = ROOT / "prompts" / f"{prompt_name}.md"
        assert path.is_file(), f"Missing prompt file: {path}"


def test_each_agent_references_its_prompt():
    for agent_name, prompt_name in AGENT_TO_PROMPT.items():
        content = _read(ROOT / "Agents" / f"{agent_name}.md")
        assert f"prompts/{prompt_name}.md" in content, \
            f"{agent_name} does not reference prompts/{prompt_name}.md"


def test_phase_machine_structure_in_orchestrator():
    content = _read(ROOT / "generate-prd.md")
    for step in ("STEP 0", "STEP 1", "STEP 2", "STEP 3", "STEP 4", "STEP 5", "STEP 6"):
        assert step in content, f"Missing {step}"
    for phase in ("5.a", "5.b", "5.c"):
        assert phase in content, f"Missing iteration phase {phase}"
    for cmd in ("/done", "/pause", "/status"):
        assert cmd in content, f"Missing user command {cmd}"


def test_feature_name_prompt_documented_in_step_0():
    content = _read(ROOT / "generate-prd.md")
    assert "feature_name" in content
    assert "kebab-case" in content
    assert re.search(r"\^\[a-z\]\[a-z0-9-\]\*\$", content) or "[a-z][a-z0-9-]" in content, \
        "Orchestrator must document the feature_name validation regex"


def test_context_window_handling_documented():
    content = _read(ROOT / "generate-prd.md")
    assert "70%" in content, "Tier 1 70% compaction threshold must be documented"
    assert "context_carryover" in content or "Tier 2" in content, \
        "Tier 2 clean-restart path must be documented"


def test_stuck_loop_fault_detection_documented():
    content = _read(ROOT / "generate-prd.md")
    assert "stuck_loop" in content or "identical findings 5" in content or "5 iterations in a row" in content, \
        "Stuck-loop fault (5 identical critic passes) must be documented"


def test_state_schema_and_template_present():
    assert (ROOT / "schema" / "state.schema.json").is_file()
    assert (ROOT / "schema" / "prd-template.md").is_file()
    assert (ROOT / "schema" / "transcript-format.md").is_file()


def test_golden_corpus_present():
    corpus = ROOT / "tests" / "golden-corpus"
    assert (corpus / "transcripts").is_dir()
    transcripts = sorted((corpus / "transcripts").glob("T*"))
    assert len(transcripts) == 5, f"Expected 5 golden-corpus transcripts, got {len(transcripts)}"
    assert (corpus / "glossary.md").is_file()
    assert (corpus / "expected" / "themes-summary.md").is_file()
    # Critic fixtures
    for name in ("draft-with-contradiction.md", "draft-with-solution-bias.md",
                 "draft-with-coverage-gap.md"):
        assert (corpus / "critic-fixtures" / name).is_file()


def test_deployment_shape():
    """Simulate the deploy-to-target-project step.

    The plan's deploy command copies:
        generate-prd/generate-prd.md         -> .claude/commands/
        generate-prd/Agents/*.md             -> .claude/agents/

    We don't actually copy here (would mutate the host project's .claude/),
    but we verify the source files exist and are the expected count.
    """
    assert (ROOT / "generate-prd.md").is_file()
    agent_files = sorted((ROOT / "Agents").glob("*.md"))
    assert len(agent_files) == 6, f"Expected 6 agent files, got {len(agent_files)}: {agent_files}"
