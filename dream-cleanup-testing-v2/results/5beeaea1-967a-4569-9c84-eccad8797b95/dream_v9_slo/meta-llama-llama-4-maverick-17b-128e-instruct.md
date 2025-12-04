# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v9_slo

← [Back to dream_v9_slo](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS | **Best Score:** 81/100 (P3)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v9_slo/meta-llama-llama-4-maverick-17b-128e-instruct/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T3 (temp=0.5) - 78/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| T1 | 0.0 | 76% | 17 | 40 | 8 | 10 | 5 | **78** | REVIEW |
| T2 | 0.3 | 75% | 17 | 40 | 8 | 10 | 5 | **78** | REVIEW |
| **T3** | 0.5 | 75% | 17 | 41 | 8 | 10 | 5 | **78** | REVIEW |
| T4 | 0.8 | 73% | 16 | 39 | 8 | 10 | 5 | **76** | REVIEW |
| T5 | 1.0 | 74% | 15 | 38 | 8 | 10 | 5 | **74** | REVIEW |
| T6 | 1.5 | 42% | 12 | 28 | 8 | 8 | 0 | **54** | FAIL |
| T7 | 2.0 | 61% | 10 | 32 | 4 | 6 | 3 | **53** | FAIL |

### Config Analysis

#### T1 (temp=0.0) - 78/100
- **Length:** 3838 chars (76%) - optimal
- **Content:** Good preservation, all details present
- **Grammar:** G1 fail (polnica), G2 fail (pretličju), cleaner than llama
- **Readability:** No paragraph breaks
- **Artifacts:** Clean

#### T3 (temp=0.5) - 78/100
- **Length:** 3781 chars (75%) - optimal
- **Content:** Preserves 10m width (C34)
- **Grammar:** G1 fail, some garbled phrases cleaned
- **Readability:** No paragraphs

#### T6, T7 - FAIL
- Severe length issues (42%, 61%)
- Significant content loss
- High temperature causes degradation

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P3 (top_p=0.5) - 81/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 77% | 17 | 40 | 8 | 10 | 5 | **78** | REVIEW |
| P2 | 0.3 | 76% | 17 | 40 | 8 | 10 | 5 | **78** | REVIEW |
| **P3** | 0.5 | 86% | 17 | 43 | 8 | 10 | 5 | **81** | PASS |
| P4 | 0.7 | 54% | 14 | 32 | 8 | 10 | 1 | **63** | ITERATE |
| P5 | 0.9 | 76% | 15 | 39 | 8 | 10 | 5 | **75** | REVIEW |
| P6 | 1.0 | 45% | 12 | 28 | 8 | 8 | 0 | **54** | FAIL |

### Config Analysis

#### P3 (top_p=0.5) - 81/100 WINNER
- **Length:** 4352 chars (86%) - optimal
- **Content:** Excellent detail preservation
- **Grammar:** G1 fail, but cleaner overall
- **Readability:** Better flow, no paragraphs
- **Key:** Preserves C34 (10m width detail)

#### P4, P6 - Length Issues
- P4 under-generates (54%)
- P6 severely under-generates (45%)
- Unstable behavior at higher top_p

---

## Failures Summary (P3 - Best Config)

### Grammar (G) - 8 failures = 17/25
- **G1:** "polnica" NOT fixed to "bolnica"
- **G2:** "pretličju" NOT fixed to "pritličju"
- **G20:** "predem" NOT fixed to "pridem"
- **G21:** "obhodnikov" NOT fixed to "hodnikov"
- **G23:** "prublev čimprej" garbled phrase - simplified but not properly fixed
- **G24:** "nadelujem" appears as "Nadaljujem" - partially fixed
- **G25:** "ko hori ta ljena vzgor" → "ko hodita gor" - fixed but lost detail
- **G27:** "nadreval" → not present (content simplified)

### Content (C) - 2 failures = 43/45
- **C30:** "hodnik levo-desno" at landing - MISSING
  - Original: "je bil tudi hodnik, levo-desno"
  - P3: Says "ker čez ta del je piso tudi" - loses left-right corridor detail
- **C26:** "napol tek" (half-running) - MISSING or simplified

### Hallucinations (H) - 0 failures = 10/10
- None detected in P3

### Readability (R) - 2 failures = 8/15
- **R1:** No paragraph breaks - output is single block of text
- **R2:** Sentence flow good (pass)

---

## Key Finding

**P3 (top_p=0.5) achieves best score but still no paragraphs.**

Maverick strengths:
- Cleaner grammar overall than other models
- Preserves specific details like 10m width
- Stable at lower temperatures

Weaknesses:
- No paragraph breaks in any config
- Unstable at high top_p values (P4-P6)

---

## Production Recommendation

**Maverick now PASSES with score 81/100.**

If used:
- **Top-p:** 0.5 (P3 config)
- **Temperature:** null
- **Expected Score:** 81/100
- **Post-processing:** Manual paragraph insertion needed
