#!/usr/bin/env bash
# Usage: build-fixtures.sh <dest> [--with-resume | --empty | --at-phase4 | --at-phase2-design | --seed-mismatch | --legacy-seed | --edited-plan | --legacy-presented]
# --at-phase4 seeds a bounded-path run at Phase 4: one commit on a feature branch on top of main, all committed.
# --seed-mismatch seeds a phase 2 run whose seed.yaml was edited after the human approved it (seed_approved_hash no longer matches).
# --legacy-seed seeds a phase 2 run created before the Seed approval gate existed (no seed_approved step, no seed_approved_hash).
# Every other seeded run records seed_approved and a matching seed_approved_hash (one seed_approved entry even where a real run would hold two; approval is judged by the hash).
# --edited-plan seeds a phase 2 run at the plan approval gate: plan.md was edited after it was presented (plan_presented_hash no longer matches; design.md still matches design_presented_hash).
# --legacy-presented seeds a phase 2 run at the spec gate whose design was audited and presented before presented hashes existed (design_audit recorded, no design_presented_hash, no design.presented.md).
# --empty builds a bare greenfield repo (only .gitkeep) instead of the billing-app files.
# Builds a sandbox: <dest>/billing-app (tiny git repo, no remote) and an empty
# <dest>/dev-workflow-runs/. With --with-resume, also seeds one in_progress run
# at phase 2 whose recorded seed_hash no longer matches seed.yaml (stale design).
set -euo pipefail
dest="$1"; with_resume="${2:-}"
if [ "$with_resume" = "--empty" ]; then
  mkdir -p "$dest/new-service" "$dest/dev-workflow-runs"; cd "$dest/new-service"; git init -q -b main
  git config user.email eval@example.com; git config user.name eval
  touch .gitkeep; git add -A; git commit -q -m "Initial commit"; exit 0
fi
repo="$dest/billing-app"
runs="$dest/dev-workflow-runs"
mkdir -p "$repo/src/client" "$repo/src/transport" "$repo/src/export" "$runs"
cd "$repo"
git init -q -b main
git config user.email eval@example.com; git config user.name eval
printf '# billing-app\n\n## Quick start\n\nRun `npm start`. You will recieve a confirmation email.\n' > README.md
printf 'export async function get(url: string) { return fetch(url); }\n' > src/client/http.ts
printf 'export const send = (b: string) => b;\n' > src/transport/send.ts
printf 'export const exportCsv = () => "";\n' > src/export/csv.ts
printf '{"name":"billing-app","version":"1.0.0"}\n' > package.json
git add -A && git commit -q -m "Initial commit"
if [ "$with_resume" = "--with-resume" ]; then
  run="$runs/billing-app/2026-09-28-billing-export"
  mkdir -p "$run"
  printf 'goal: Add scheduled billing export to S3\nconstraints:\n  - no new paid services\nacceptance_criteria:\n  - nightly CSV lands in S3\n' > "$run/seed.yaml"
  old_hash=$(sha256sum "$run/seed.yaml" | cut -d' ' -f1)
  printf '# Design\nNightly cron writes CSV via src/export/csv.ts to S3.\n' > "$run/design.md"
  printf '  - export includes refunds\n' >> "$run/seed.yaml"   # Seed revised after design approved -> design hash now stale
  new_hash=$(sha256sum "$run/seed.yaml" | cut -d' ' -f1)       # the human approved this revised Seed, so only the design is stale
  printf '{"phase":2,"status":"in_progress","steps_completed":["seed_generated","seed_qa: PASS","seed_approved"],"seed_approved_hash":"%s","worktree":null,"design":{"path":"%s/design.md","seed_hash":"%s"},"plan":null}\n' "$new_hash" "$run" "$old_hash" > "$run/state.json"
fi

if [ "$with_resume" = "--at-phase4" ]; then
  cd "$repo"
  printf '{"name":"billing-app","version":"1.0.0","scripts":{"test":"echo 12 passing"}}\n' > package.json
  git add -A && git commit -q --amend --no-edit
  git checkout -q -b dev-workflow/retry-backoff
  printf 'export async function get(url: string, maxAttempts = 3) {\n  let last: unknown;\n  for (let i = 0; i < maxAttempts; i++) {\n    try { return await fetch(url); } catch (e) { last = e; }\n  }\n  throw last;\n}\n' > src/client/http.ts
  git add -A && git commit -q -m "Add retry to http client get"
  run="$runs/billing-app/2026-09-29-retry-backoff"; mkdir -p "$run"
  printf 'goal: Add retry to the HTTP client get\nconstraints:\n  - no new dependencies\nacceptance_criteria:\n  - get retries up to maxAttempts on network error\n' > "$run/seed.yaml"
  printf '# Design\nLoop around fetch in src/client/http.ts with a maxAttempts parameter.\n' > "$run/design.md"
  h=$(sha256sum "$run/seed.yaml" | cut -d' ' -f1)
  printf '{"phase":4,"status":"in_progress","path":"bounded","steps_completed":["seed_generated","seed_qa: PASS","seed_approved","design_approved","implementation_complete"],"seed_approved_hash":"%s","worktree":"%s","design":{"path":"%s/design.md","seed_hash":"%s"},"plan":null}\n' "$h" "$repo" "$run" "$h" > "$run/state.json"
fi

if [ "$with_resume" = "--at-phase2-design" ]; then
  # Phase 2, architectural path: design.md drafted (current with the Seed), not yet presented for approval.
  run="$runs/billing-app/2026-09-30-public-export-api"; mkdir -p "$run"
  printf 'goal: Expose billing exports to customers over a public HTTPS API\nconstraints:\n  - no new paid services\nacceptance_criteria:\n  - a customer can download only their own exports\n' > "$run/seed.yaml"
  cat > "$run/design.md" <<'DESIGN'
# Design: public export download API
- `GET /exports/{exportId}` is a public endpoint on the existing HTTPS server.
- The handler loads the export row by `exportId` taken from the URL and streams the CSV.
- Authentication: callers send an `X-Api-Key` header; keys are stored in the `api_keys` table.
- Export files live in an S3 bucket; the handler builds the object key from `exportId`.
- Errors return the exception message to the caller to ease debugging.
DESIGN
  h=$(sha256sum "$run/seed.yaml" | cut -d' ' -f1)
  printf '{"phase":2,"status":"in_progress","path":"architectural","steps_completed":["seed_generated","seed_qa: PASS","seed_approved","design_drafted"],"seed_approved_hash":"%s","worktree":null,"design":{"path":"%s/design.md","seed_hash":"%s"},"plan":null}\n' "$h" "$run" "$h" > "$run/state.json"
fi

if [ "$with_resume" = "--seed-mismatch" ]; then
  # Phase 2, no design yet: the human approved the Seed, then seed.yaml was edited outside regeneration.
  run="$runs/billing-app/2026-09-30-billing-export"; mkdir -p "$run"
  printf 'goal: Add scheduled billing export to S3\nconstraints:\n  - no new paid services\nacceptance_criteria:\n  - nightly CSV lands in S3\n' > "$run/seed.yaml"
  h=$(sha256sum "$run/seed.yaml" | cut -d' ' -f1)
  printf '  - export includes refunds\n' >> "$run/seed.yaml"
  printf '{"phase":2,"status":"in_progress","steps_completed":["seed_generated","seed_qa: PASS","seed_approved"],"seed_approved_hash":"%s","worktree":null,"design":null,"plan":null}\n' "$h" > "$run/state.json"
fi

if [ "$with_resume" = "--legacy-seed" ]; then
  # Phase 2, no design yet: run created before the Seed approval gate existed.
  run="$runs/billing-app/2026-09-30-billing-export"; mkdir -p "$run"
  printf 'goal: Add scheduled billing export to S3\nconstraints:\n  - no new paid services\nacceptance_criteria:\n  - nightly CSV lands in S3\n' > "$run/seed.yaml"
  printf '{"phase":2,"status":"in_progress","steps_completed":["seed_generated","seed_qa: PASS"],"worktree":null,"design":null,"plan":null}\n' > "$run/state.json"
fi

if [ "$with_resume" = "--edited-plan" ]; then
  # Phase 2, architectural path, plan approval gate: plan.md was presented, then the human edited it.
  run="$runs/billing-app/2026-09-30-csv-export"; mkdir -p "$run"
  printf 'goal: Add a CSV export command\nconstraints:\n  - no new paid services\nacceptance_criteria:\n  - the export command writes a CSV file\n' > "$run/seed.yaml"
  printf '# Design: CSV export\n\n## Executive summary\nAdds an export command that writes a CSV file from src/export/csv.ts.\n\n- `exportCsv` in src/export/csv.ts builds the rows.\n' > "$run/design.md"
  cat > "$run/plan.presented.md" <<'PLAN'
# CSV export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a CSV export command.

**Architecture:** One command calls `exportCsv` in src/export/csv.ts and writes the rows to a file.

**Tech Stack:** TypeScript, Vitest.

**Spec:** design.md in this run directory.

## Executive summary
One task adds the export command and its test. The riskiest part is the file write, which has no atomicity.

## Global Constraints
- No new paid services.

### Task 1: Export command
Files: src/export/csv.ts
- [ ] Write a failing test, then implement.
PLAN
  cp "$run/plan.presented.md" "$run/plan.md"
  printf '\n### Task 2: Scheduler hook\nFiles: src/export/schedule.ts\n- [ ] Call exportCsv nightly.\n' >> "$run/plan.md"
  cp "$run/design.md" "$run/design.presented.md"
  h=$(sha256sum "$run/seed.yaml" | cut -d' ' -f1)
  ph=$(sha256sum "$run/plan.presented.md" | cut -d' ' -f1)
  dh=$(sha256sum "$run/design.presented.md" | cut -d' ' -f1)
  printf '{"phase":2,"status":"in_progress","path":"architectural","steps_completed":["seed_generated","seed_qa: PASS","seed_approved","design_drafted","design_audit","design_approved","plan_drafted","design_audit"],"seed_approved_hash":"%s","design_presented_hash":"%s","plan_presented_hash":"%s","worktree":null,"design":{"path":"%s/design.md","seed_hash":"%s"},"plan":{"path":"%s/plan.md","seed_hash":"%s"}}\n' "$h" "$dh" "$ph" "$run" "$h" "$run" "$h" > "$run/state.json"
fi

if [ "$with_resume" = "--legacy-presented" ]; then
  # Phase 2, architectural path, spec gate: the design was audited and presented before presented hashes existed.
  run="$runs/billing-app/2026-09-30-csv-export"; mkdir -p "$run"
  printf 'goal: Add a CSV export command\nconstraints:\n  - no new paid services\nacceptance_criteria:\n  - the export command writes a CSV file\n' > "$run/seed.yaml"
  printf '# Design: CSV export\n\n- `exportCsv` in src/export/csv.ts builds the rows.\n- The command writes them to a file and reports failures to the caller.\n\n## Assumptions\n- [Certain] src/export/csv.ts exists.\n' > "$run/design.md"
  h=$(sha256sum "$run/seed.yaml" | cut -d' ' -f1)
  printf '{"phase":2,"status":"in_progress","path":"architectural","steps_completed":["seed_generated","seed_qa: PASS","seed_approved","design_drafted","design_audit"],"seed_approved_hash":"%s","worktree":null,"design":{"path":"%s/design.md","seed_hash":"%s"},"plan":null}\n' "$h" "$run" "$h" > "$run/state.json"
fi
