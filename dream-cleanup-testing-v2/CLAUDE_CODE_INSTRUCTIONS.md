# Dream Cleanup Testing - Claude Code Instructions

## Overview

You are optimizing Slovenian dream transcription cleanup. This guide explains the **checklist-based scoring system** designed for rapid prompt iteration.

**Key principle:** Score by checking specific checkpoints, not by subjective prose evaluation.

---

## Test Target

**Transcription ID (will change in the future):** `5beeaea1-967a-4569-9c84-eccad8797b95`

All testing uses this single transcription for consistency.

**Raw transcription:** `cache/{transcription_id}/fetched_data.json`
**Scoring criteria:** `criteria/{transcription_id}.md` (gitignored - contains dream content)

---

## Cache Structure

```
cache/{transcription_id}/
├── fetched_data.json                    # Raw transcription + current prompt
└── {prompt_name}/
    └── {model_name}/
        ├── T1.json, T2.json, ... T7.json    # Temperature configs
        ├── P1.json, P2.json, ... P6.json    # Top-p configs
        ├── T3_v2.json, T3_v3.json           # Re-run versions
        └── _summary.json                     # Batch metadata
```

**Example:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v8/llama-3.3-70b-versatile/T1.json`

---

## Parameter Test Grid

### Case 1: Temperature Only (top_p = null)

| Config | Temperature | Expected Behavior |
|--------|-------------|-------------------|
| T1 | 0.0 | Most deterministic |
| T2 | 0.3 | Conservative |
| T3 | 0.5 | Balanced |
| T4 | 0.8 | Slightly creative |
| T5 | 1.0 | Default |
| T6 | 1.5 | More random |
| T7 | 2.0 | Maximum randomness |

### Case 2: Top-p Only (temperature = null)

| Config | Top-p | Expected Behavior |
|--------|-------|-------------------|
| P1 | 0.1 | Very narrow (top 10% tokens) |
| P2 | 0.3 | Narrow sampling |
| P3 | 0.5 | Moderate restriction |
| P4 | 0.7 | Slight restriction |
| P5 | 0.9 | Minimal restriction |
| P6 | 1.0 | Default (no restriction) |

### Case 3: Both Parameters (if needed)

| Config | Temperature | Top-p |
|--------|-------------|-------|
| B1 | 0.3 | 0.9 |
| B2 | 0.5 | 0.5 |
| B3 | 0.5 | 0.9 |
| B4 | 0.8 | 0.5 |

---

## Scoring System (100 Points)

### Point Distribution

| Criterion | Points | What It Measures |
|-----------|--------|------------------|
| **Content** | 45 | Scene details preserved (C1-Cn) |
| **Grammar** | 25 | Spelling/transcription fixes (G1-Gn) |
| **Readability** | 15 | Paragraphs, flow, coherence (R1-R4) |
| **Hallucinations** | 10 | Invented/incorrect content (none = 10) |
| **Length** | 5 | Compression ratio (70-95% optimal) |

**Artifacts (A1-A3):** Pass/fail gate, not scored. Flag if "Hvala" remains.

### Scoring Formulas

#### Content (45 points)

```
Content = 45 × (C_preserved / C_total) - voice_penalty

Where:
- C_preserved = C_total - C_failures
- voice_penalty:
  - Correct (1st person + present tense): 0
  - Minor issues (occasional shifts): -3
  - Major issues (wrong throughout): -7

Minimum: 0
```

#### Grammar (25 points)

```
Grammar = 25 × (G_passed / G_total) - language_penalties

Where:
- G_passed = G_total - G_failures
- language_penalties:
  - G+ (English words present): -3
  - G++ (Russian/Cyrillic present): -5

Minimum: 0
```

#### Readability (15 points)

```
Readability = 15 × (R_score / 4)

Where R_score (0-4) is sum of:
- R1: Paragraph breaks at scene changes (0 or 1)
- R2: Sentences flow logically (0 or 1)
- R3: Personal voice preserved (0 or 1)
- R4: Dream coherence maintained (0 or 1)
```

#### Hallucinations (10 points)

```
Hallucinations = max(0, 10 - (H_count × 2))

Where H_count = number of hallucinated/invented details
- 0 hallucinations: 10 points
- 1 hallucination: 8 points
- 2 hallucinations: 6 points
- 5+ hallucinations: 0 points

Record each hallucination found:
- H1: [what was added/changed]
- H2: [what was added/changed]
```

#### Length (5 points)

```
Based on: cleaned_length / raw_length

| Ratio | Points | Status |
|-------|--------|--------|
| 70-95% | 5 | Optimal |
| 60-69% or 96-100% | 3 | Minor issue |
| 50-59% or 101-110% | 1 | Problematic |
| <50% or >110% | 0 | Severe |
```

#### Artifacts (Pass/Fail Gate)

```
NOT scored, but noted:
- A1: "Hvala" removed? (required - flag if any remain)
- A2: Intro artifacts removed? (optional)
- A3: Fillers reduced? (optional)
```

---

## How to Score

### Step 1: Automated Checks

```
[ ] No "Hvala" in output (A1 - flag if present)
[ ] No English words (and, the, but, with, for)
[ ] No Russian/Cyrillic words
[ ] Length ratio calculated
[ ] First person (jaz/sem) preserved
[ ] Present tense (sedanjik) used
```

### Step 2: Count Grammar Failures (G1-Gn)

- Open criteria file, check each G checkpoint
- Count failures: `G1❌, G5❌, G12❌` = 3 failures
- Note language violations: G+ (English), G++ (Russian)

### Step 3: Count Content Failures (C1-Cn)

- Check each scene's checkpoints against cleaned text
- Count failures: `C3❌, C17❌, C22❌` = 3 failures
- Assess narrative voice (C+): minor or major issues?

### Step 4: Count Hallucinations (H)

- Read cleaned text carefully
- List any invented/changed content not in original
- Record: `H1: added "polna svetlobe" (original was dark)`

### Step 5: Score Readability (R1-R4)

- R1: Are there paragraph breaks? (0 or 1)
- R2: Do sentences flow? (0 or 1)
- R3: Is "jaz" voice preserved? (0 or 1)
- R4: Is dream logic coherent? (0 or 1)

### Step 6: Calculate Total

```
Content:       45 × (passed/total) - voice_penalty = ___
Grammar:       25 × (passed/total) - lang_penalty  = ___
Readability:   15 × (R_score/4)                    = ___
Hallucinations: 10 - (H_count × 2)                 = ___
Length:        [table lookup]                      = ___
─────────────────────────────────────────────────────────
TOTAL:                                             ___/100
```

---

## Thresholds

```
≥90: EXCELLENT - Production ready, minimal issues
≥80: PASS      - Acceptable for production
70-79: REVIEW  - Usable with manual review
60-69: ITERATE - Needs prompt improvements
<60: FAIL      - Not usable
```

---

## Results Format

### Per-Model Results File

Location: `results/{transcription_id}/{prompt_name}/{model}.md`

```markdown
# {model} on {prompt}

**Best:** T1 | Score: 85/100 | Status: PASS

## All Configs

| Config | Params | Len% | G | C | R | H | L | Total | Status |
|--------|--------|------|---|---|---|---|---|-------|--------|
| T1 | t=0.0 | 82% | 21 | 38 | 11 | 10 | 5 | 85 | PASS |
| T2 | t=0.3 | 85% | 19 | 37 | 11 | 10 | 5 | 82 | PASS |

## Failures Summary

### Grammar (G)
- G1: polnica→bolnica (failed in all configs)
- G5: stapo→stavbo (failed in T3, T4)

### Content (C)
- C34: 10m width missing (failed in T2, T3)

### Hallucinations (H)
- T7: H1 "added morning light description"
```

### Main Index File

Location: `results/{transcription_id}/README.md`

```markdown
# Results: {transcription_id}

## Best Result

| Prompt | Model | Config | Score | Status |
|--------|-------|--------|-------|--------|
| dream_v8 | maverick | T5 | 88/100 | PASS |

## Prompt Comparison

| Prompt | Best Model | Config | Score | G | C | R | H | L |
|--------|------------|--------|-------|---|---|---|---|---|
| dream_v8 | maverick | T5 | 88/100 | 21 | 41 | 11 | 10 | 5 |
```

---

## Workflow

### Phase 1: Parameter Optimization

1. **Setup:** Run `fetch_data.py` to get transcription + active prompt
2. **Test Case 1:** `run_cleanups_api.py {model} --prompt {prompt} --case 1`
3. **Score T1-T7:** Use criteria file checklist
4. **Test Case 2:** `run_cleanups_api.py {model} --prompt {prompt} --case 2`
5. **Score P1-P6:** Use criteria file checklist
6. **Compare:** Identify best config (highest score)

### Phase 2: Prompt Optimization

1. **Analyze failures:** Which checkpoints consistently fail?
2. **Identify patterns:** Same G/C checkpoints failing across configs?
3. **Modify prompt:** Address specific issues
4. **WAIT for user to manually insert the new prompt**
5. **Re-test:** Use user instructions on what to re-test

---

## Models to Test

### Tier 1 - Priority

| Model ID | Why Test |
|----------|----------|
| `llama-3.3-70b-versatile` | Baseline, general purpose |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | Best so far |
| `openai/gpt-oss-120b` | Largest, best grammar potential |

### Tier 2 - Secondary

| Model ID | Why Test |
|----------|----------|
| `moonshotai/kimi-k2-instruct` | Strong multilingual |
| `qwen/qwen3-32b` | 100+ languages |

### Skip

- TTS models (playai-*)
- Safety/guard models (llama-guard-*, safeguard-*)
- Tool-use models (compound, compound-mini)

---

## Quick Reference

### Scoring Template

```
Config: T1 | Model: llama-3.3-70b | Prompt: dream_v8

AUTOMATED CHECKS:
[x] No "Hvala" (A1)
[x] No English (G+)
[x] No Russian (G++)
[x] Length: 82%

CRITERIA COUNTS:
G_total: 28 | G_failed: 4 | G_passed: 24
C_total: 44 | C_failed: 4 | C_passed: 40
H_count: 0
R_score: 3/4 (R1 failed - no paragraphs)
Voice: OK (no penalty)
Language: OK (no penalty)

CALCULATION:
Content:       45 × (40/44) - 0 = 40.9
Grammar:       25 × (24/28) - 0 = 21.4
Readability:   15 × (3/4)       = 11.25
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (82% optimal)  = 5
─────────────────────────────────────
TOTAL:                          88.55 → 89/100

STATUS: PASS
```

### Penalty Reference

| Penalty | Points | Applied To |
|---------|--------|------------|
| G+ (English words) | -3 | Grammar |
| G++ (Russian/Cyrillic) | -5 | Grammar |
| Voice minor (occasional shifts) | -3 | Content |
| Voice major (wrong throughout) | -7 | Content |
| Each hallucination | -2 | Hallucinations |
