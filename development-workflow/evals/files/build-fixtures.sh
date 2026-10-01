#!/usr/bin/env bash
# Usage: build-fixtures.sh <dest> [--with-resume | --empty | --at-phase4 | --at-phase2-design | --seed-mismatch | --legacy-seed]
# --at-phase4 seeds a bounded-path run at Phase 4: one commit on a feature branch on top of main, all committed.
# --seed-mismatch seeds a phase 2 run whose seed.yaml was edited after the human approved it (seed_approved_hash no longer matches).
# --legacy-seed seeds a phase 2 run created before the Seed approval gate existed (no seed_approved step, no seed_approved_hash).
# Every other seeded run records seed_approved and a matching seed_approved_hash (one seed_approved entry even where a real run would hold two; approval is judged by the hash).
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
