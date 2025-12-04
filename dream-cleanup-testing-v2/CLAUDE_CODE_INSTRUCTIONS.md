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

## Scoring System

### Criteria File Structure

Each transcription has a criteria file: `criteria/{transcription_id}.md`

**DO NOT COMMIT** - Contains actual dream content for scoring reference.

The criteria file defines:
- **G1-G28** - Grammar checkpoints (specific spelling errors to fix)
- **C1-C44** - Content checkpoints (specific details to preserve)
- **A1-A3** - Artifact checkpoints ("Hvala", intro, fillers)
- **R1-R4** - Readability checkpoints (paragraphs, flow, voice)

### How to Score

**Step 1: Run automated checks**
```
[ ] No "Hvala" in output
[ ] No English words (and, the, but, with)
[ ] No Russian/Cyrillic words
[ ] Length ratio 70-95%
[ ] First person (jaz/sem) preserved
[ ] Present tense (sedanjik) used
```

**Step 2: Check Grammar (G1-G28)**
- Open criteria file, check each G checkpoint against cleaned text
- Count failures: `G1❌, G5❌` = 2 failures
- Score: `10 - (failures × 0.5)` (minimum 0)
- Language violations (G+, G++) = -2 each

**Step 3: Check Content (C1-C44)**
- Check each scene's checkpoints against cleaned text
- Count failures: `C3❌, C17❌, C22❌` = 3 failures
- Score: `10 - (failures × 0.25)` (minimum 0)
- Meta-check violations (C+, C++, C+++) = -2 each

**Step 4: Check Artifacts (A1-A3)**
- A1: All "Hvala" removed? (-0.5 per remaining)
- A2: "Zdravstveno..." removed? (no penalty if kept)
- A3: Fillers reduced? (-1 if excessive)

**Step 5: Check Readability (R1-R4)**
- R1: Paragraph breaks at scene changes?
- R2: Sentences flow logically?
- R3: Personal "jaz" voice preserved?
- R4: Dream logic maintained?
- Score: 10 (excellent) → 5 (wall of text) → 0 (unreadable)

### Scoring Formula

```
Grammar:     10 - (G_failures × 0.5) - (G+/G++ × 2)
Content:     10 - (C_failures × 0.25) - (C+/++/+++ × 2)
Artifacts:   10 - (A1_remaining × 0.5) - (A3_penalty)
Readability: Subjective 0-10 based on R1-R4

TOTAL: G + C + A + R (max 40)
```

---

## Results Format

### Per-Model Results File

Location: `results/{transcription_id}/{prompt_name}/{model}.md`

```markdown
# {model} on {prompt}

**Best:** T1 | Score: 36/40

## All Configs

| Config | Params | Len% | G | C | A | R | Total | Failed |
|--------|--------|------|---|---|---|---|-------|--------|
| T1 | t=0.0 | 82% | 8 | 9 | 10 | 9 | 36 | G1, G5 |
| T2 | t=0.3 | 85% | 7 | 9 | 10 | 9 | 35 | G1, G5, G12 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Key Findings

- G1 (polnica→bolnica) not fixed in any config
- T6+ severely over-summarizes (<60% ratio)
```

### Main Index File

Location: `results/{transcription_id}/README.md`

```markdown
# Results: {transcription_id}

## Best Result

| Prompt | Model | Config | Score |
|--------|-------|--------|-------|
| dream_v8 | maverick | T5 | 38/40 |

## Prompt Comparison

| Prompt | Best Model | Best Config | Score | Key Failures |
|--------|------------|-------------|-------|--------------|
| dream_v8 | maverick | T5 | 38/40 | G1 |
| dream_v7 | llama-3.3 | T1 | 36/40 | G1, G5, C3 |
```

---

## Workflow

### Phase 1: Parameter Optimization

1. **Setup:** Run `fetch_data.py` to get transcription + active prompt
2. **Test Case 1:** `run_cleanups_api.py {model} --prompt {prompt} --case 1` for models specified by the user.
3. **Score T1-T7:** Use criteria file checklist
4. **Test Case 2:** `run_cleanups_api.py {model} --prompt {prompt} --case 2` for models specified by the user.
5. **Score P1-P6:** Use criteria file checklist
6. **Compare:** Identify best config (highest score) and compare models

### Phase 2: Prompt Optimization

1. **Analyze failures:** Which checkpoints consistently fail?
2. **Identify patterns:** Same G checkpoints failing across configs?
3. **Modify prompt:** Address specific issues
4. **WAIT for user to manually insert the new prompt**
5. **Re-test:** Use user instructions on what to re-test

---

## Models to Test

### Tier 1 - Priority

| Model ID | Why Test |
|----------|----------|
| `llama-3.3-70b-versatile` | Baseline, general purpose |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | Best so far (38/40) |
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

## Database Operations

### Fetch Transcription + Prompt

```python
# Use fetch_data.py - saves to cache/{transcription_id}/fetched_data.json
python fetch_data.py
```

---

## Quick Reference

### Automated Checks (before scoring)

```bash
# Check for Hvala
grep -i "hvala" cleaned_text

# Check for English
grep -iE "\b(and|the|but|with|for|building)\b" cleaned_text

# Check length ratio
echo "scale=2; cleaned_len / 5051 * 100" | bc
```

### Scoring Template

```
Config: T1 | Model: llama-3.3-70b | Prompt: dream_v8

AUTOMATED:
[x] No "Hvala"
[x] No English
[x] No Russian
[x] Length: 82%
[x] First person
[x] Present tense

SCORES:
Grammar (G1-G28):    8/10  | Failed: G1, G5
Content (C1-C44):    9/10  | Failed: C3
Artifacts (A1-A3):   10/10 | Failed: -
Readability (R1-R4): 9/10  | Failed: -
─────────────────────────────
TOTAL:               36/40
```

