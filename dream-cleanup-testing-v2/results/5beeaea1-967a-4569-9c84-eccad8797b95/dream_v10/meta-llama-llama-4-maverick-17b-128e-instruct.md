# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v10

← [Back to dream_v10](./README.md) | [Back to Index](../README.md)

---

**Status:** EXCELLENT | **Best Score:** 94/100 (T1)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v10/meta-llama-llama-4-maverick-17b-128e-instruct/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T1 (temp=0.0) - 94/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| **T1** | 0.0 | 78% | 21 | 43 | 15 | 10 | 5 | **94** | EXCELLENT |
| T2 | 0.3 | 69% | 18 | 36 | 15 | 10 | 3 | **82** | PASS |
| T3 | 0.5 | 54% | 16 | 32 | 11 | 10 | 1 | **70** | REVIEW |
| T4 | 0.8 | 66% | 17 | 35 | 11 | 10 | 3 | **76** | REVIEW |
| T5 | 1.0 | 57% | 16 | 33 | 11 | 10 | 1 | **71** | REVIEW |
| T6 | 1.5 | 65% | 15 | 34 | 11 | 10 | 3 | **73** | REVIEW |
| T7 | 2.0 | - | - | - | - | - | - | **FAIL** | JSON error |

### Config Analysis

#### T1 (temp=0.0) - 94/100 WINNER
- **Length:** 3941 chars (78%) - optimal
- **Content:** Excellent preservation, 42/44 details present
- **Grammar:** FIXED "polnica→bolnica" (only model to do this!)
- **Readability:** Proper paragraph breaks
- **Artifacts:** All "Hvala" removed, intro removed

#### T7 (temp=2.0) - FAIL
- **Error:** LLM response is not valid JSON (char 3073 delimiter error)
- **Processing time:** 85s before failure

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P6 (top_p=1.0) - 76/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 64% | 17 | 34 | 11 | 10 | 3 | **75** | REVIEW |
| P2 | 0.3 | 56% | 16 | 32 | 11 | 10 | 1 | **70** | REVIEW |
| P3 | 0.5 | 52% | 15 | 30 | 11 | 10 | 1 | **67** | ITERATE |
| P4 | 0.7 | 54% | 15 | 31 | 11 | 10 | 1 | **68** | ITERATE |
| P5 | 0.9 | 57% | 16 | 32 | 11 | 10 | 1 | **70** | REVIEW |
| **P6** | 1.0 | 67% | 17 | 35 | 11 | 10 | 3 | **76** | REVIEW |

---

## CASE 3: Both Parameters

| Config | Temp | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|-------|------|------|------|------|------|-----|-------|--------|
| B1 | 0.3 | 0.9 | 68% | 17 | 35 | 11 | 10 | 3 | **76** | REVIEW |
| B2 | 0.5 | 0.5 | 62% | 16 | 33 | 11 | 10 | 3 | **73** | REVIEW |
| B3 | 0.5 | 0.9 | 67% | 17 | 35 | 11 | 10 | 3 | **76** | REVIEW |
| B4 | 0.8 | 0.5 | 49% | 14 | 28 | 8 | 10 | 0 | **60** | ITERATE |

---

## Failures Summary (T1 - Best Config)

### Grammar (G) - 4 failures = 21/25
- **G13:** "nazdolj" NOT fixed (should be "navzdol") - appears as "nazdolj in nazdolj"
- **G20:** "predem" NOT fixed (should be "preden") - appears as "predem pridobim"
- **G21:** "obhodnikov" NOT fixed (should be "hodnikov")
- **G26:** "našpricali" kept in past tense (should be "špricam" present)

### Content (C) - 2 failures = 43/45
- **C23:** Flat areas + corridors mixed with stairs - simplified (only describes stair variation)
- **C34:** "deset metrov široke" (10m wide stairs) - MISSING entirely

---

## Key Finding

**T1 (temp=0.0) is the BEST config for maverick on dream_v10.**

This is significant because:
- **ONLY model to fix G1** (polnica→bolnica) - critical STT error
- Best grammar score of all models (21/25)
- Proper paragraph structure
- No hallucinations
- Optimal length (78%)

---

## Production Recommendation

**Use maverick with T1 config (temp=0.0):**
- Best score: **94/100** (EXCELLENT threshold: ≥90)
- Only model to fix critical "bolnica" error
- Processing time: ~3.7s
