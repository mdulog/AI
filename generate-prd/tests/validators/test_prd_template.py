import pathlib
import re

TEMPLATE_PATH = pathlib.Path(__file__).resolve().parents[2] / "schema" / "prd-template.md"

REQUIRED_SECTIONS = [
    "Background & Problem",
    "Target Users",
    "Goals & Non-Goals",
    "User Stories",
    "Functional Requirements",
    "Non-Functional Requirements",
    "Success Metrics",
    "Risks & Open Questions",
    "Constraints",
]


def template_text():
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def test_template_has_feature_name_placeholder():
    assert "{feature_name}" in template_text()


def test_template_has_all_required_sections():
    text = template_text()
    for section in REQUIRED_SECTIONS:
        assert re.search(rf"^## {re.escape(section)}\s*$", text, re.MULTILINE), \
            f"Missing section: {section}"


def test_each_section_has_italic_intent_line():
    text = template_text()
    # Each section heading must be followed (after blank line) by an italic line
    for section in REQUIRED_SECTIONS:
        pattern = rf"^## {re.escape(section)}\s*\n\s*\n\*[^*\n]+\*"
        assert re.search(pattern, text, re.MULTILINE), \
            f"Section '{section}' missing italic intent line"
