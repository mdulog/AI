# State-schema migration mechanism

The orchestrator's STEP 0 reads `schema_version` from `prd/.state.json` BEFORE branching on `status`. If the file's version is less than the current schema's version, the orchestrator runs the migration script(s) located in this directory.

## Contract

- One script per **single-step** upgrade: `v<from>-to-v<to>.py` (no skipping versions).
- The orchestrator chains them: e.g., a v1 state under a v3 skill runs `v1-to-v2.py` then `v2-to-v3.py`.
- Each script is invoked as `python3 v<from>-to-v<to>.py path/to/state.json` — it rewrites the file in place to the target schema. **Exit code 0 = success; anything else = halt.**
- Scripts MUST be idempotent (running twice on already-migrated state is a no-op or a clear failure).
- Scripts MUST NOT delete or rename fields without a backup copy under `prd/.archive/migration-backups/<timestamp>-pre-v<from>-to-v<to>.json`.

## Why this scaffolding exists at v1

The skill ships with v1 state and v1 schema, so today the migration check is a no-op — `schema_version == 1` matches the schema's `1` and the orchestrator continues. The contract is documented now so that when v2 ships, the only thing that needs to happen is dropping `v1-to-v2.py` into this directory; the orchestrator's STEP 0 already knows to look here.

## File layout

```
generate-prd/schema/
  state.schema.json          # The current (v1) schema
  migrations/
    README.md                # This file
    v1-to-v2.py              # NOT YET — will be added when v2 schema ships
    v2-to-v3.py              # NOT YET — added when v3 ships
```

## What v1 → v2 might look like (hypothetical)

The most likely v2 change is enabling persona/speaker tracking (currently a reserved-but-empty `speakers:` field in normalized transcript front matter, and not in the state schema at all). A v1-to-v2 script would:

1. Add an empty `persona_map: {}` field to state.
2. Re-write `qa_history` entries to include a `speaker_id: null` field where missing.
3. Bump `schema_version` to `2`.
4. Write the backup as above.

This is illustrative — the actual v2 spec will dictate the migration.

## What this directory must NOT contain

- A `v0-to-v1.py` script. There is no v0; v1 is the floor.
- Skip-version scripts like `v1-to-v3.py`. Chain single-step scripts instead.
- Anything that mutates `prd/<feature_name>.md`. Migrations touch state only; the PRD draft is content the PM owns.
