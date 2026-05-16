# Canonical Normalized Transcript Format (v1)

This document specifies the human-readable, machine-friendly canonical format produced by the transcript **normalizer** stage of the `generate-prd` pipeline. All downstream agents (theme extractors, requirement synthesizers, traceability builders) read these normalized files — never the raw source.

The format is intentionally minimal: a Markdown body of speaker turns plus a YAML front matter header, with timestamps moved to a side-car JSON file so the prose stays clean while temporal fidelity is preserved.

---

## 1. File Location

For every input transcript, the normalizer writes two files:

```
transcripts/.normalized/<original-basename>.md
transcripts/.normalized/<original-basename>.timestamps.json
```

Where `<original-basename>` is the filename of the source transcript with its original extension stripped. Example mapping:

| Source path                                  | Normalized markdown                                | Timestamps side-car                                          |
| -------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------ |
| `transcripts/2026-04-12-kickoff.vtt`         | `transcripts/.normalized/2026-04-12-kickoff.md`    | `transcripts/.normalized/2026-04-12-kickoff.timestamps.json` |
| `transcripts/customer-call-acme.docx`        | `transcripts/.normalized/customer-call-acme.md`    | `transcripts/.normalized/customer-call-acme.timestamps.json` |
| `transcripts/hallway-notes.md`               | `transcripts/.normalized/hallway-notes.md`         | `transcripts/.normalized/hallway-notes.timestamps.json`      |

The `.normalized/` directory is created on demand and is the **only** location writers may emit normalized transcripts to. The directory is leading-dot-prefixed to keep it visually grouped at the top of `transcripts/` and to signal "tool-managed — do not hand-edit."

---

## 2. Front Matter (YAML)

Every normalized `.md` file begins with a YAML front matter block delimited by `---` fences. Fields appear in the order listed below.

| Field             | Type                                        | Required | Description                                                                                                                                                                                  |
| ----------------- | ------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `transcript_id`   | string (e.g. `T01`, `T02`, ...)             | yes      | Stable short ID assigned by the orchestrator. Used in traceability tables and citation anchors. Must be unique within a run.                                                                  |
| `source_format`   | enum: `vtt` \| `srt` \| `docx` \| `markdown` \| `notes` | yes      | The detected format of the source file. `notes` is the catch-all for free-form plain text / hand-written notes with no formal structure.                                                     |
| `source_path`     | string (relative path)                      | yes      | Path to the original source file, **relative to the project root**. Used by the auditor to re-open the raw input if a turn is disputed.                                                      |
| `normalized_at`   | string (ISO 8601 UTC)                       | yes      | Timestamp the normalizer wrote this file. Format: `YYYY-MM-DDTHH:MM:SSZ`. Drives idempotency checks — re-runs compare this against source-file mtime.                                        |
| `speakers`        | list of strings                             | yes      | **Reserved for v2.** In v1 this field MUST be present and MUST be an empty list (`[]`). v2 will populate it with canonical speaker names after a dedicated speaker-disambiguation pass.       |
| `glossary_applied`| boolean                                     | yes      | `true` if a `glossary.md` was found and term substitutions were applied during normalization; `false` otherwise. Audited to explain why two transcripts use different terminology for the same concept. |

### v1 → v2 forward-compatibility note

`speakers` is declared in v1 specifically so consumers can rely on the field's **presence** without version-sniffing. v1 readers MUST treat an empty list as "speaker identity is whatever appears inline in the body turns." v2 will add a `version: 2` discriminator before populating the list, so v1 readers will continue to see `[]` on v1 files indefinitely.

### Example front matter

```yaml
---
transcript_id: T03
source_format: vtt
source_path: transcripts/2026-04-12-kickoff.vtt
normalized_at: 2026-05-15T14:22:08Z
speakers: []
glossary_applied: true
---
```

---

## 3. Body Structure

The body is a sequence of **speaker turns**. The rules are:

1. **One turn per blank-line-separated block.** Turns are separated by exactly one blank line. No other Markdown constructs (headings, lists, horizontal rules, code fences) appear in the body of a v1 file.
2. **Exact turn format:** `**<speaker>**: <utterance>`
   - The speaker name is wrapped in `**` bold-markdown delimiters.
   - A single space follows the closing `**`, then a literal `:`, then a single space, then the utterance.
3. **Speaker names** are taken verbatim from the source. If the source used `SPEAKER_01` the normalized file uses `SPEAKER_01`; if it used `Alice` it uses `Alice`. v1 does NOT attempt to merge or canonicalize identities — that is v2's job.
4. **Multi-line utterances are allowed.** A single turn may span multiple lines as long as the block contains no blank lines internally. Continuation lines are not re-prefixed with the speaker name; they appear flush-left under the opening line.
5. **No timestamps inline.** All temporal metadata lives in the side-car (§ 4). The body MUST NOT contain `[HH:MM:SS]`, VTT cues, or similar.
6. **Turn ordering is preserved.** Turn N in the body corresponds to turn N (0-based) in the side-car.

### Example body (3 turns, 1 multi-line)

```markdown
**Alice**: Thanks everyone for joining. I want to spend the first ten minutes on the customer onboarding flow before we get into pricing.

**Bob**: Quick context for folks who weren't on last week's call —
we shipped the email-verification step but it's regressing the activation rate
by about four percent week over week. That's the headline issue today.

**Carol**: Do we have segmentation on which cohorts are dropping off?
```

---

## 4. Timestamp Side-car File

The side-car file `<original-basename>.timestamps.json` lives next to the normalized markdown and preserves the original temporal data extracted from the source.

### Schema

A single JSON object whose keys are **stringified 0-based turn indexes** (`"0"`, `"1"`, `"2"`, …) and whose values are either:

- a **string** in `HH:MM:SS` 24-hour format representing the turn's start time as it appeared in the source, OR
- `null` if the source did not carry a timestamp for that turn (e.g., `notes` or `markdown` inputs).

Keys are stringified integers (JSON object keys must be strings); they are stored in ascending order for human readability but consumers MUST NOT rely on key ordering — parse and sort numerically.

### Format choices and rationale

- **`HH:MM:SS`, not full ISO 8601.** Source transcripts almost universally carry only relative-to-recording offsets, not wall-clock timestamps. `HH:MM:SS` matches what VTT/SRT actually contain.
- **Millisecond precision is discarded.** VTT cues like `00:01:23.456 --> 00:01:27.890` are truncated to `00:01:23`. Sub-second precision is never load-bearing for PRD synthesis and noise-pollutes diffs.
- **Side-car instead of inline.** Keeps the Markdown body diff-friendly when only timestamps change (e.g., re-running normalization with a new clock offset) and lets downstream agents that don't care about timing skip the JSON entirely.

### Example side-car

```json
{
  "0": "00:00:12",
  "1": "00:00:34",
  "2": "00:01:48"
}
```

---

## 5. Worked Example: VTT → Normalized

This section shows a complete end-to-end transformation of a 3-turn VTT input.

### 5.1 Source: `transcripts/2026-04-12-kickoff.vtt`

```
WEBVTT

00:00:12.000 --> 00:00:33.500
<v Alice>Thanks everyone for joining. I want to spend the first ten minutes on the customer onboarding flow before we get into pricing.

00:00:34.000 --> 00:01:47.200
<v Bob>Quick context for folks who weren't on last week's call —
we shipped the email-verification step but it's regressing the activation rate
by about four percent week over week. That's the headline issue today.

00:01:48.000 --> 00:01:54.000
<v Carol>Do we have segmentation on which cohorts are dropping off?
```

### 5.2 Output: `transcripts/.normalized/2026-04-12-kickoff.md`

```markdown
---
transcript_id: T03
source_format: vtt
source_path: transcripts/2026-04-12-kickoff.vtt
normalized_at: 2026-05-15T14:22:08Z
speakers: []
glossary_applied: true
---

**Alice**: Thanks everyone for joining. I want to spend the first ten minutes on the customer onboarding flow before we get into pricing.

**Bob**: Quick context for folks who weren't on last week's call —
we shipped the email-verification step but it's regressing the activation rate
by about four percent week over week. That's the headline issue today.

**Carol**: Do we have segmentation on which cohorts are dropping off?
```

### 5.3 Output: `transcripts/.normalized/2026-04-12-kickoff.timestamps.json`

```json
{
  "0": "00:00:12",
  "1": "00:00:34",
  "2": "00:01:48"
}
```

### 5.4 What changed in the transformation

- `WEBVTT` header dropped — format is now indicated by `source_format: vtt` in front matter.
- Cue timing lines (`00:00:12.000 --> 00:00:33.500`) extracted to the side-car, truncated to second precision, and indexed by 0-based turn number.
- `<v Speaker>` VTT voice tags rewritten to `**Speaker**:` Markdown bold-prefix form.
- Bob's multi-line utterance preserved verbatim, no per-line speaker prefix added.
- `glossary_applied: true` indicates the normalizer found a project `glossary.md` and ran term substitution; with no glossary present this would be `false`.
- `speakers: []` because v1 does not perform speaker canonicalization.

---

## 6. Out of Scope for v1

The following are deliberately deferred to v2 and MUST NOT appear in v1 normalized files:

- Canonical speaker identity resolution (`speakers:` stays empty).
- Confidence scores per turn.
- Diarization or speaker-change probabilities.
- Sentiment, intent, or topic annotations.
- Cross-transcript reference links.

Any of these emerging in v1 output is a normalizer bug, not a format extension.
