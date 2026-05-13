#!/usr/bin/env python3
"""
Smoke-test grader for the generate-knowledge-base policy change.

Compares two output trees (baseline vs new) artifact-by-artifact and reports
regression risk via an LLM judge running on Claude Opus 4.7.

Usage:
    python scripts/smoke_grade.py --baseline ./kb-baseline/docs --new ./kb-new/docs

Requires:
    - ANTHROPIC_API_KEY in the environment
    - pip install anthropic pydantic

Exit codes:
    0  no regressions detected
    1  at least one artifact regressed (or other failure)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel


# JUDGE_MODEL is pinned to a specific version because the Anthropic SDK does
# not resolve generic aliases like "opus" — it requires an exact model ID.
# This is a documented dev-tooling exception to the project's no-pin policy
# (see CLAUDE.md § Model and Effort Policy). Orchestrator and agent
# frontmatter must continue to use generic aliases.
JUDGE_MODEL = "claude-opus-4-7"
MAX_TOKENS = 4096
EXIT_REGRESSION = 1

ADR_DIR = "architecture/decisions"

ARTIFACTS: list[dict[str, str]] = [
    {
        "path": "architecture/overview.md",
        "rubric": (
            "Identifies architectural layers, references real files/components, "
            "ends with `## Assumptions`, no generic placeholders."
        ),
    },
    {
        "path": "architecture/components.md",
        "rubric": (
            "Lists concrete components/services with descriptions; cites code; "
            "ends with `## Assumptions`."
        ),
    },
    {
        "path": "architecture/integrations.md",
        "rubric": (
            "Identifies external dependencies and integration points; "
            "ends with `## Assumptions`."
        ),
    },
    {
        "path": "conventions/coding.md",
        "rubric": (
            "Captures stable repeatable rules with concrete examples; "
            "distinguishes required vs observed."
        ),
    },
    {
        "path": "conventions/testing.md",
        "rubric": "Captures stable testing patterns with concrete examples.",
    },
    {
        "path": "conventions/naming.md",
        "rubric": "Captures naming conventions with concrete examples.",
    },
    {
        "path": "specs/00-overview.md",
        "rubric": "Covers product behavior and feature areas; ends with `## Assumptions`.",
    },
]

ADR_RUBRIC = (
    "Set of MADR-format ADRs (3-5 expected). Each ADR cites code evidence and "
    "has the MADR sections (Context and Problem Statement, Considered Options, "
    "Decision Outcome, Consequences). Compare significance and grounding in "
    "aggregate across the set."
)

SYSTEM_PROMPT = (
    "You are grading documentation quality for a regression check. Two "
    "versions of an artifact are produced under different model+effort "
    "policies for a documentation-generation skill. Detect regressions in "
    "the NEW version vs BASELINE.\n\n"
    "Verdict guidance:\n"
    "- 'regress' — NEW is materially worse on the rubric (missing sections, "
    "less specific evidence, vaguer language, fewer real symbols, lost detail).\n"
    "- 'improvement' — NEW is materially better on the rubric.\n"
    "- 'pass' — no meaningful difference; acceptable variance from non-determinism.\n\n"
    "Improvements are fine; regressions are the failure. Be willing to call "
    "'pass' when differences are stylistic or equivalent. Reserve 'regress' "
    "for substantive losses — not minor wording changes. Cite specific "
    "differences (section names, missing facts) in the rationale."
)


class Verdict(BaseModel):
    verdict: Literal["pass", "regress", "improvement"]
    confidence: Literal["low", "medium", "high"]
    rationale: str


def grade_pair(
    client: anthropic.Anthropic,
    artifact: str,
    rubric: str,
    baseline: str,
    new: str,
) -> Verdict | None:
    """Send a baseline-vs-new pair to the judge. Returns None on refusal."""
    user_content = (
        f"ARTIFACT: {artifact}\n"
        f"RUBRIC: {rubric}\n\n"
        f"BASELINE:\n---\n{baseline}\n---\n\n"
        f"NEW:\n---\n{new}\n---"
    )
    response = client.messages.parse(
        model=JUDGE_MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        output_format=Verdict,
    )
    return response.parsed_output


def grade_single_artifact(
    client: anthropic.Anthropic,
    baseline_root: Path,
    new_root: Path,
    artifact_path: str,
    rubric: str,
) -> dict:
    """Grade one fixed-path artifact. Returns a result row for printing."""
    baseline_file = baseline_root / artifact_path
    new_file = new_root / artifact_path
    if not baseline_file.exists() or not new_file.exists():
        which = "baseline" if not baseline_file.exists() else "new"
        return {
            "artifact": artifact_path,
            "verdict": "skip",
            "confidence": "-",
            "rationale": f"Missing in {which}",
        }

    verdict = grade_pair(
        client,
        artifact_path,
        rubric,
        baseline_file.read_text(),
        new_file.read_text(),
    )
    if verdict is None:
        return {
            "artifact": artifact_path,
            "verdict": "skip",
            "confidence": "-",
            "rationale": "Judge could not produce a structured verdict (refusal or parse failure)",
        }
    return {
        "artifact": artifact_path,
        "verdict": verdict.verdict,
        "confidence": verdict.confidence,
        "rationale": verdict.rationale,
    }


def grade_adrs(
    client: anthropic.Anthropic, baseline_root: Path, new_root: Path
) -> dict | None:
    """Grade ADRs as a concatenated set. ADR count varies; we judge in aggregate."""
    baseline_dir = baseline_root / ADR_DIR
    new_dir = new_root / ADR_DIR
    baseline_files = sorted(baseline_dir.glob("*.md")) if baseline_dir.exists() else []
    new_files = sorted(new_dir.glob("*.md")) if new_dir.exists() else []
    if not baseline_files or not new_files:
        return None

    baseline_text = "\n\n---\n\n".join(p.read_text() for p in baseline_files)
    new_text = "\n\n---\n\n".join(p.read_text() for p in new_files)
    label = f"ADRs ({len(baseline_files)} -> {len(new_files)})"

    verdict = grade_pair(client, label, ADR_RUBRIC, baseline_text, new_text)
    if verdict is None:
        return {
            "artifact": label,
            "verdict": "skip",
            "confidence": "-",
            "rationale": "Judge could not produce a structured verdict",
        }
    return {
        "artifact": label,
        "verdict": verdict.verdict,
        "confidence": verdict.confidence,
        "rationale": verdict.rationale,
    }


def print_result(row: dict) -> None:
    glyph = {
        "pass": "PASS",
        "regress": "REGRESS",
        "improvement": "IMPROVE",
        "skip": "SKIP",
    }.get(row["verdict"], "?")
    print(f"[{glyph:>8}] {row['artifact']:<45} (confidence: {row['confidence']})")
    if row.get("rationale"):
        print(f"           {row['rationale']}")
    print()


def print_summary(results: list[dict]) -> None:
    counts: dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("=" * 60)
    print("Summary:")
    for verdict in ("pass", "improvement", "regress", "skip"):
        if verdict in counts:
            print(f"  {verdict}: {counts[verdict]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grade baseline vs new docs trees for regression risk.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Path to baseline docs/ tree (output under the OLD policy)",
    )
    parser.add_argument(
        "--new",
        type=Path,
        required=True,
        help="Path to new docs/ tree (output under the NEW policy)",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: ANTHROPIC_API_KEY environment variable not set")
    if not args.baseline.is_dir():
        sys.exit(f"ERROR: --baseline is not a directory: {args.baseline}")
    if not args.new.is_dir():
        sys.exit(f"ERROR: --new is not a directory: {args.new}")

    client = anthropic.Anthropic()
    results: list[dict] = []

    print(f"Grading with judge model: {JUDGE_MODEL}")
    print(f"Baseline: {args.baseline}")
    print(f"New:      {args.new}\n")

    for artifact in ARTIFACTS:
        result = grade_single_artifact(
            client, args.baseline, args.new, artifact["path"], artifact["rubric"]
        )
        results.append(result)
        print_result(result)

    adr_result = grade_adrs(client, args.baseline, args.new)
    if adr_result is not None:
        results.append(adr_result)
        print_result(adr_result)

    print_summary(results)
    if any(r["verdict"] == "regress" for r in results):
        sys.exit(EXIT_REGRESSION)


if __name__ == "__main__":
    main()
