# meta-llama/llama-4-scout-17b-16e-instruct on dream_v10

← [Back to dream_v10](./README.md) | [Back to Index](../README.md)

---

**Status:** EXCELLENT | **Best Score:** 91/100 (T1)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v10/meta-llama-llama-4-scout-17b-16e-instruct/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T1 (temp=0.0) - 91/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| **T1** | 0.0 | 98% | 20 | 43 | 15 | 10 | 3 | **91** | EXCELLENT |
| T2 | 0.3 | 70% | 18 | 38 | 15 | 10 | 5 | **86** | PASS |
| T3 | 0.5 | 86% | 18 | 39 | 15 | 10 | 5 | **87** | PASS |
| T4 | 0.8 | 89% | 18 | 39 | 15 | 10 | 5 | **87** | PASS |
| T5 | 1.0 | 55% | 16 | 35 | 11 | 10 | 1 | **73** | REVIEW |
| T6 | 1.5 | 89% | 18 | 39 | 15 | 10 | 5 | **87** | PASS |
| T7 | 2.0 | 32% | 10 | 25 | 8 | 10 | 0 | **53** | FAIL |

### Config Analysis

#### T1 (temp=0.0) - 91/100 WINNER
- **Length:** 4929 chars (98%) - minimal cleanup
- **Content:** Best content preservation of all models
- **Grammar:** Many STT errors remain unfixed
- **Unique:** ONLY model to preserve "deset metrov široke" (C34) and flat areas (C23)
- **Issue:** Keeps "Zdravstveno" artifact (A2), excessive fillers remain

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P5/P6 (top_p=0.9/1.0) - 89/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 71% | 18 | 38 | 15 | 10 | 5 | **86** | PASS |
| P2 | 0.3 | 54% | 16 | 34 | 11 | 10 | 1 | **72** | REVIEW |
| P3 | 0.5 | 87% | 18 | 39 | 15 | 10 | 5 | **87** | PASS |
| P4 | 0.7 | 85% | 18 | 39 | 15 | 10 | 5 | **87** | PASS |
| P5 | 0.9 | 93% | 19 | 41 | 15 | 10 | 5 | **90** | EXCELLENT |
| **P6** | 1.0 | 94% | 19 | 41 | 15 | 10 | 5 | **90** | EXCELLENT |

---

## CASE 3: Both Parameters

| Config | Temp | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|-------|------|------|------|------|------|-----|-------|--------|
| B1 | 0.3 | 0.9 | 65% | 17 | 36 | 11 | 10 | 3 | **77** | REVIEW |
| B2 | 0.5 | 0.5 | 73% | 18 | 37 | 15 | 10 | 5 | **85** | PASS |
| B3 | 0.5 | 0.9 | 57% | 16 | 34 | 11 | 10 | 1 | **72** | REVIEW |
| B4 | 0.8 | 0.5 | 64% | 17 | 35 | 11 | 10 | 3 | **76** | REVIEW |

---

## Failures Summary (T1 - Best Config)

### Grammar (G) - 6 failures = 20/25
- **G13:** "nazdolj" NOT fixed (should be "navzdol") - appears as "nazdolj in nazdolj"
- **G15:** "zdrževanju" NOT fixed (should be "vzdrževanju")
- **G20:** "predem" NOT fixed (should be "preden") - appears as "predem do hodnikov"
- **G22:** "Vzpomnim" NOT fixed (should be "Spomnim")
- **G23:** "prubleval" garbled phrase not fixed
- **G26:** "špricali" kept in past tense (should be "špricam" present)

### Content (C) - 2 failures = 43/45
- **C1:** Location phrased oddly as "stavbi, ki je bila v bistvu bolnica" instead of direct "bolnica"
- Minor simplification of some details

### Artifacts (A) - 1 issue (not scored)
- **A2:** "Zdravstveno, da ste pripravljeni" NOT removed

---

## Key Finding

**T1 (temp=0.0) preserves content best but performs minimal cleanup.**

Scout is unique among all tested models for:
- **Preserving C23** (flat areas mixed with stairs)
- **Preserving C34** (10m wide stairs detail)
- **Best content score** (43/45)
- **Length close to original** (98%)

However, it fails to:
- Fix several STT errors (G13, G15, G20, G22, G23, G26)
- Remove intro artifact "Zdravstveno" (A2)
- Reduce excessive fillers ("v bistvu", "torej")

---

## Production Recommendation

**Consider scout T1 if content preservation is priority:**
- Score: 91/100 (EXCELLENT)
- Best content preservation
- Requires post-processing for grammar fixes

**Trade-off vs maverick:**
- Scout: Better content (43/45 vs 43/45), worse grammar (20/25 vs 21/25)
- Maverick: Fixes critical "polnica→bolnica" that scout also fixes
- Scout preserves C23, C34 that maverick loses
