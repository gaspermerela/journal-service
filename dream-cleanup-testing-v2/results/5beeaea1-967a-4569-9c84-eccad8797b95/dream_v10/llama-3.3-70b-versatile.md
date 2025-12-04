# llama-3.3-70b-versatile on dream_v10

← [Back to dream_v10](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS | **Best Score:** 84/100 (P3)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v10/llama-3.3-70b-versatile/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T2 (temp=0.3) - 82/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| T1 | 0.0 | 84% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| **T2** | 0.3 | 88% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| T3 | 0.5 | 75% | 12 | 39 | 15 | 10 | 5 | **81** | PASS |
| T4 | 0.8 | 79% | 12 | 39 | 15 | 10 | 5 | **81** | PASS |
| T5 | 1.0 | 86% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| T6 | 1.5 | 51% | 10 | 32 | 11 | 10 | 1 | **64** | ITERATE |
| T7 | 2.0 | 54% | 10 | 33 | 11 | 10 | 1 | **65** | ITERATE |

### Config Analysis

#### T1/T2 (temp=0.0/0.3) - 82/100
- **Length:** 84-88% - optimal range
- **Grammar:** Many STT errors remain unfixed
- **Content:** Good preservation
- **Issue:** "polnica" NOT fixed (critical G1)

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P3 (top_p=0.5) - 84/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 82% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| P2 | 0.3 | 87% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| **P3** | 0.5 | 93% | 12 | 42 | 15 | 10 | 5 | **84** | PASS |
| P4 | 0.7 | 86% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| P5 | 0.9 | 85% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| P6 | 1.0 | 74% | 12 | 39 | 15 | 10 | 5 | **81** | PASS |

---

## CASE 3: Both Parameters

| Config | Temp | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|-------|------|------|------|------|------|-----|-------|--------|
| B1 | 0.3 | 0.9 | 84% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| B2 | 0.5 | 0.5 | 89% | 12 | 41 | 15 | 10 | 5 | **83** | PASS |
| B3 | 0.5 | 0.9 | 88% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| B4 | 0.8 | 0.5 | 88% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |

---

## Failures Summary (P3 - Best Config)

### Grammar (G) - 13 failures = 12/25
- **G1:** "polnica" NOT fixed (should be "bolnica") - critical STT error
- **G3:** "uspodbudo" NOT fixed (should be "vzpodbudo")
- **G15:** "zdrževanju" NOT fixed (should be "vzdrževanju")
- **G16:** "kmalo" NOT fixed (should be "kmalu")
- **G17:** "mogo" NOT fixed (should be "moglo")
- **G19:** "sečnem" NOT fixed (should be "začnem")
- **G21:** "obhodnikov" NOT fixed (should be "hodnikov")
- **G22:** "Vzpomnim" NOT fixed (should be "Spomnim")
- **G23:** "prublev čimprej" garbled phrase not fixed
- **G24:** "nadelujem" NOT fixed (should be "nadaljujem")
- **G26:** "šprical" past tense NOT fixed
- **G27:** "nadreval" NOT fixed (should be "nadaljeval")
- **G28:** "notakrat" NOT fixed (should be "nato")

### Content (C) - 3 failures = 42/45
- **C34:** "deset metrov široke" (10m wide stairs) - MISSING

---

## Key Finding

**P3 (top_p=0.5) provides good balance but fails to fix many grammar issues.**

llama-3.3-70b characteristics:
- Consistent across configs (most score 81-84)
- Optimal length ratios (74-93%)
- Good artifact removal
- Poor STT error correction
- Preserves C23 (flat areas) unlike maverick

Critical failure:
- **G1 NOT fixed** (polnica→bolnica) - only maverick fixes this

---

## Production Recommendation

**llama-3.3-70b with P3 config (top_p=0.5):**
- Score: 84/100 (PASS)
- Good balance of content and cleanup
- Consistent behavior across configs
- Processing time: ~15s

**Consider maverick instead** if grammar correction is priority (maverick is ONLY model to fix G1).
