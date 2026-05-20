"""
Prompt validation harness for generate-prd v1 development.

Loads a prompt file, substitutes provided context variables, sends to Claude,
returns the response for structural assertions in pytest.

Model ID is pinned (dev-tooling exception per CLAUDE.md).
"""

from __future__ import annotations

import os
import pathlib
from typing import Any

import anthropic

MODEL_ID = "claude-opus-4-7"   # dev-tooling pin
MAX_TOKENS = 8192

PROMPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt file by short name (e.g., 'critic-pass' -> 'critic-pass.md')."""
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


def run_prompt(name: str, variables: dict[str, str]) -> str:
    """
    Substitute {{var}} placeholders in the prompt and send to Claude.
    Returns the model's response text.
    """
    template = load_prompt(name)
    for key, value in variables.items():
        template = template.replace(f"{{{{{key}}}}}", value)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": template}],
    )
    return response.content[0].text
