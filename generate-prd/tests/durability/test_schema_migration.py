"""Schema-migration scaffolding tests.

At v1 the migration mechanism is a no-op (only one schema version exists), but the
contract must be in place so v2 ships cleanly — drop a single migration script and
the orchestrator picks it up.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # generate-prd/
SCHEMA = ROOT / "schema" / "state.schema.json"
MIGRATIONS = ROOT / "schema" / "migrations"
ORCHESTRATOR = ROOT / "generate-prd.md"


def test_schema_version_is_one_in_state_schema():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    sv = schema["properties"]["schema_version"]
    assert sv == {"const": 1}, \
        f"State schema's schema_version must be const:1 at v1; got {sv}"


def test_migrations_directory_exists():
    assert MIGRATIONS.is_dir(), "Migrations directory must exist even at v1"


def test_migrations_readme_documents_contract():
    readme = MIGRATIONS / "README.md"
    assert readme.is_file(), "Migrations README must exist"
    text = readme.read_text(encoding="utf-8")
    # Contract beats: naming convention, idempotency, in-place rewrite, exit-code, backups
    assert re.search(r"v<from>-to-v<to>\.py", text), "Naming convention must be documented"
    assert "idempotent" in text.lower(), "Idempotency requirement must be stated"
    assert "in place" in text.lower() or "in-place" in text.lower(), "In-place rewrite must be stated"
    assert "exit code 0" in text.lower(), "Exit-code semantics must be stated"
    assert "backup" in text.lower(), "Backup-before-mutate requirement must be stated"


def test_orchestrator_step_0_checks_schema_version_before_status():
    text = ORCHESTRATOR.read_text(encoding="utf-8")
    # The schema_version check must appear before the status branch in STEP 0
    schema_check_pos = text.find("schema_version")
    status_branch_pos = text.find("branch on `status`")
    assert schema_check_pos != -1, "Orchestrator must reference schema_version in STEP 0"
    assert status_branch_pos != -1, "Orchestrator must have a status branch"
    assert schema_check_pos < status_branch_pos, \
        "schema_version check must precede status branch (corrupt-schema state could otherwise be read as 'completed' etc.)"


def test_orchestrator_documents_migration_script_lookup():
    text = ORCHESTRATOR.read_text(encoding="utf-8")
    assert "migration" in text.lower(), "Migration mechanism must be referenced in orchestrator"
    assert "migrations" in text.lower() or "schema/migrations" in text, \
        "Orchestrator must point to the migrations directory"
    # Must handle both 'older' and 'newer' state scenarios
    assert "<from>" in text and "<current>" in text or \
           re.search(r"schema_version\s*<\s*current", text), \
        "Orchestrator must describe the from/to upgrade case"


def test_no_premature_migration_scripts():
    """At v1 there should be NO migration scripts — just the README contract."""
    scripts = list(MIGRATIONS.glob("v*-to-v*.py"))
    assert not scripts, \
        f"No migration scripts should exist at v1; found: {[s.name for s in scripts]}"
