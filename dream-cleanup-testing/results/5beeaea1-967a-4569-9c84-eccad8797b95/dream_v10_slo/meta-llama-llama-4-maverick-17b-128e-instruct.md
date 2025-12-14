# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v10_slo

← [Back to dream_v10_slo](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS | **Best Score:** 82/100 (P2)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v10_slo/meta-llama-llama-4-maverick-17b-128e-instruct/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T2/T4 (temp=0.3/0.8) - 80/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| T1 | 0.0 | 50% | 23 | 28 | 11 | 10 | 0 | **72** | REVIEW |
| **T2** | 0.3 | 73% | 21 | 36 | 15 | 10 | 5 | **80** | PASS |
| T3 | 0.5 | 53% | 22 | 29 | 11 | 10 | 1 | **73** | REVIEW |
| **T4** | 0.8 | 73% | 21 | 36 | 15 | 10 | 5 | **80** | PASS |
| T5 | 1.0 | 60% | 21 | 32 | 11 | 10 | 3 | **77** | REVIEW |
| T6 | 1.5 | 53% | 21 | 29 | 11 | 10 | 1 | **72** | REVIEW |
| T7 | 2.0 | 55% | 21 | 30 | 11 | 10 | 1 | **73** | REVIEW |

### Config Analysis

#### T1 (temp=0.0) - 72/100 (POOR)
- **Length:** 2510 chars (50%) - SEVERE over-processing
- **Issue:** Too aggressive with Slovenian prompt at temp=0
- **Compare:** 78% with English prompt (dream_v10)

#### T2/T4 - 80/100 (BEST Temperature)
- **Length:** ~73% - good range
- **More stable** than T1

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P2 (top_p=0.3) - 82/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 68% | 21 | 35 | 11 | 10 | 3 | **80** | PASS |
| **P2** | 0.3 | 81% | 21 | 38 | 15 | 10 | 5 | **82** | PASS |
| P3 | 0.5 | 76% | 21 | 37 | 15 | 10 | 5 | **81** | PASS |
| P4 | 0.7 | 52% | 22 | 28 | 11 | 10 | 1 | **72** | REVIEW |
| P5 | 0.9 | 78% | 21 | 37 | 15 | 10 | 5 | **81** | PASS |
| P6 | 1.0 | 79% | 21 | 38 | 15 | 10 | 5 | **82** | PASS |

---

## CASE 3: Both Parameters

| Config | Temp | top_p | Len% | Total | Status |
|--------|------|-------|------|-------|--------|
| B1 | 0.3 | 0.9 | 75% | **79** | REVIEW |
| B2 | 0.5 | 0.5 | 77% | **80** | PASS |
| B3 | 0.5 | 0.9 | 73% | **78** | REVIEW |
| B4 | 0.8 | 0.5 | 68% | **77** | REVIEW |

---

## Failures Summary (T1 - Baseline Config)

### Grammar (G) - 2 failures = 23/25

- **G21:** "obhodnikov" remains (should be "hodnikov")
- **G26:** "špricali" past tense (should be "špricam" present)

### Content (C) - 16 failures = 28/45 (due to 50% length)

**LOST/SIMPLIFIED:**
- **C10:** Cabinet description - heavily simplified
- **C21:** "zelo globoko pod" depth - not emphasized
- **C22:** Stair variations - present but simplified
- **C23:** Flat areas + corridors mixed - LOST
- **C26:** "napol tek" movement - LOST
- **C29:** Others unhappy with stairs - LOST
- **C30:** "hodnik levo-desno" - LOST
- **C32:** "pet, šest, sedem" specific numbers - LOST
- **C34:** "deset metrov široke" (10m width) - LOST
- **C36:** Women unbothered detail - simplified
- Multiple other scene details condensed

### Readability (R) - 1 failure = 11/15

- **R3:** Personal voice weakened due to summarization

### Length (L) - 0/5
- 50% ratio = below threshold

---

## Key Finding

**maverick behaves DIFFERENTLY with Slovenian vs English prompt:**

| Metric | dream_v10 (English) | dream_v10_slo (Slovenian) |
|--------|---------------------|---------------------------|
| T1 (temp=0.0) | 78% (best) | 50% (over-processes) |
| Best config | T1 | P2 |
| Best score | 94/100 | 82/100 |
| Consistency | High | Variable |

**Recommendation:** Use English prompt (dream_v10) for maverick.

---

## Production Recommendation

**maverick with P2 config (top_p=0.3):**
- Score: 82/100 (PASS)
- Best balance for Slovenian prompt
- Avoids over-processing of T1

**Better alternative:** Use dream_v10 (English prompt) with maverick T1 for score 94/100.
