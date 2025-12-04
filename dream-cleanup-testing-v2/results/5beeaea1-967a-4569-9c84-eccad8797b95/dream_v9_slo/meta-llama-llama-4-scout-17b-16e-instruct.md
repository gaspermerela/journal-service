# meta-llama/llama-4-scout-17b-16e-instruct on dream_v9_slo

← [Back to dream_v9_slo](./README.md) | [Back to Index](../README.md)

---

**Status:** REVIEW | **Best Score:** 78/100 (T3)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v9_slo/meta-llama-llama-4-scout-17b-16e-instruct/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T3 (temp=0.5) - 78/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| T1 | 0.0 | 92% | 15 | 42 | 8 | 8 | 5 | **76** | REVIEW |
| T2 | 0.3 | 97% | 15 | 42 | 8 | 8 | 3 | **74** | REVIEW |
| **T3** | 0.5 | 97% | 15 | 44 | 8 | 8 | 3 | **78** | REVIEW |
| T4 | 0.8 | 94% | 14 | 41 | 8 | 8 | 5 | **74** | REVIEW |
| T5 | 1.0 | 98% | 14 | 41 | 8 | 8 | 3 | **72** | REVIEW |
| T6 | 1.5 | 93% | 13 | 40 | 8 | 6 | 5 | **70** | REVIEW |
| T7 | 2.0 | 82% | 11 | 36 | 4 | 4 | 5 | **58** | FAIL |

### Config Analysis

#### T1 (temp=0.0) - 76/100
- **Length:** 4661 chars (92%) - borderline optimal
- **Content:** Very detailed, all C checkpoints preserved
- **Grammar:** G1 fail, many fillers retained ("torej", "a ne", "v bistvu")
- **Readability:** Has paragraphs but verbose
- **Artifacts:** KEEPS "Zdravstveno, da ste pripravljeni" (A2 note)

#### T3 (temp=0.5) - 78/100 WINNER
- **Length:** 4889 chars (97%) - at limit
- **Content:** Excellent detail preservation
- **Grammar:** Similar issues to T1
- **Readability:** Paragraphs present

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P1 (top_p=0.1) - 75/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| **P1** | 0.1 | 94% | 15 | 42 | 8 | 8 | 5 | **75** | REVIEW |
| P2 | 0.3 | 97% | 15 | 42 | 8 | 8 | 3 | **74** | REVIEW |
| P3 | 0.5 | 97% | 15 | 42 | 8 | 8 | 3 | **74** | REVIEW |
| P4 | 0.7 | 97% | 14 | 41 | 8 | 8 | 3 | **72** | REVIEW |
| P5 | 0.9 | 98% | 14 | 41 | 8 | 8 | 3 | **72** | REVIEW |
| P6 | 1.0 | 97% | 14 | 41 | 8 | 6 | 3 | **70** | REVIEW |

---

## Failures Summary (T3 - Best Config)

### Grammar (G) - 10 failures = 15/25
- **G1:** "polnica" NOT fixed to "bolnica"
- **G5:** "stavo" NOT fixed to "stavbo" (multiple occurrences)
- **G9:** "stave" NOT fixed to "stavbe"
- **G20:** "predem" NOT fixed to "pridem"
- **G21:** "obhodnikov" NOT fixed to "hodnikov"
- **G23:** "prubleval" garbled phrase remains
- **G25:** "ta lena vzgor" garbled phrase remains
- **A3:** Excessive fillers retained: "torej", "a ne", "v bistvu", "no"

### Content (C) - 1 failure = 44/45
- **C10:** Cabinet big-doors-vs-small detail - garbled ("omara z večjimi, manjšimi vrati" is confusing)

### Hallucinations (H) - 1 failure = 8/10
- **H1:** "Ali je bistrani?" - garbled phrase from original retained but confusing
- Model preserves too literally, including unclear STT artifacts

### Readability (R) - 2 failures = 8/15
- **R1:** Has paragraph breaks (PASS)
- **R2:** Flow disrupted by excessive fillers
- **R3:** Personal voice preserved (PASS)

### Artifacts (A) - Critical Issues
- **A2 FAIL:** "Zdravstveno, da ste pripravljeni" NOT removed
- **A3 FAIL:** Excessive fillers retained throughout

---

## Key Finding

**Scout preserves content well but fails to clean up the transcription.**

Issues:
1. Retains "Zdravstveno, da ste pripravljeni" artifact
2. Keeps too many filler words
3. Very verbose output (92-98% length)
4. Grammar score penalized by retained errors

Scout seems to interpret the Slovenian prompt too literally ("OHRANI VSAK specifičen detajl") and fails to apply cleanup rules properly.

---

## Production Recommendation

**Scout is NOT recommended for dream_v9_slo prompt.**

- Best score: **78/100** (below PASS threshold of 80)
- Retains artifacts and excessive fillers
- Better suited for prompts that emphasize cleanup over preservation

If used for some reason:
- **Temperature:** 0.5 (T3 config)
- **Post-processing:** Manual removal of "Zdravstveno" and filler words needed
