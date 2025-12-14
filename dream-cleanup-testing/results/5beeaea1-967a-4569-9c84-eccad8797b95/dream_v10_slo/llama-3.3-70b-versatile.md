# llama-3.3-70b-versatile on dream_v10_slo

← [Back to dream_v10_slo](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS | **Best Score:** 82/100 (T1)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v10_slo/llama-3.3-70b-versatile/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters
**Note:** Rate limited - only 9/17 configs completed

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T1 (temp=0.0) - 82/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| **T1** | 0.0 | 89% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| T2 | 0.3 | 83% | 12 | 39 | 15 | 10 | 5 | **81** | PASS |
| T3 | 0.5 | 88% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| T4 | 0.8 | 84% | 12 | 39 | 15 | 10 | 5 | **81** | PASS |
| T5 | 1.0 | 73% | 11 | 37 | 15 | 10 | 5 | **78** | REVIEW |
| T6 | 1.5 | 57% | 10 | 32 | 11 | 10 | 1 | **64** | ITERATE |
| T7 | 2.0 | 60% | 10 | 33 | 11 | 10 | 3 | **67** | ITERATE |

### Config Analysis

#### T1 (temp=0.0) - 82/100 WINNER
- **Length:** 4497 chars (89%) - optimal range
- **Grammar:** Good STT correction
- **Content:** Good preservation
- **Best performer** with Slovenian prompt

---

## CASE 2: Top-p Only (temperature = null)

**Note:** Rate limited after P2 - configs P3-P6 failed

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 80% | 12 | 38 | 15 | 10 | 5 | **80** | PASS |
| P2 | 0.3 | 80% | 12 | 38 | 15 | 10 | 5 | **80** | PASS |
| P3 | 0.5 | - | - | - | - | - | - | - | FAILED (rate limit) |
| P4 | 0.7 | - | - | - | - | - | - | - | FAILED (rate limit) |
| P5 | 0.9 | - | - | - | - | - | - | - | FAILED (rate limit) |
| P6 | 1.0 | - | - | - | - | - | - | - | FAILED (rate limit) |

---

## CASE 3: Both Parameters

**Note:** All configs failed due to rate limiting

| Config | Status |
|--------|--------|
| B1-B4 | FAILED (rate limit) |

---

## Failures Summary (T1 - Best Config)

### Grammar (G) - 13 failures = 12/25

- **G3:** "uspodbudo" remains (should be "vzpodbudo")
- **G13:** "nazdolj" remains multiple times (should be "navzdol")
- **G15:** "zdrževanje" remains (should be "vzdrževanje")
- **G16:** "kmalo" remains (should be "kmalu")
- **G17:** "mogo" remains (should be "moral")
- **G19:** "sečnem" remains (should be "začnem")
- **G21:** "obhodnikov" remains (should be "hodnikov")
- **G22:** "Vzpomnim" remains (should be "Spomnim")
- **G23:** "prublev čimprej" garbled phrase remains
- **G24:** "nadelujem" remains (should be "nadaljujem")
- **G27:** "nadreval" remains (should be "nadaljeval")
- **G28:** "notakrat" remains (should be "nato")

### Content (C) - 4 failures = 40/45

**SIMPLIFIED/LOST:**
- **C23:** Flat areas + corridors - partially simplified
- **C30:** "hodnik levo-desno" - simplified
- **C34:** "deset metrov široke" - NOT explicitly stated
- Minor detail simplifications

---

## Key Finding

**T1 (temp=0.0) is the best config for llama with Slovenian prompt.**

- Optimal length ratio (89%)
- Consistent performance across low-temperature configs
- Best performer among all models with dream_v10_slo

**Compare to dream_v10 (English):**
- Similar performance (~82 with Slovenian vs ~84 with English)
- llama handles both prompt languages equally well

---

## Production Recommendation

**llama-3.3-70b with T1 config (temp=0.0):**
- Score: 82/100 (PASS)
- Best balance for Slovenian prompt
- Consistent behavior
- Processing time: ~3.5s
