import json
import pathlib
import jsonschema
import pytest

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[2] / "schema" / "state.schema.json"
FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def load_fixture(name: str):
    with open(FIXTURES / name) as f:
        return json.load(f)


def test_minimal_valid_state_passes():
    jsonschema.validate(load_fixture("state-valid-minimal.json"), load_schema())


def test_mid_run_valid_state_passes():
    jsonschema.validate(load_fixture("state-valid-mid-run.json"), load_schema())


def test_invalid_status_fails():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(load_fixture("state-invalid-bad-status.json"), load_schema())
