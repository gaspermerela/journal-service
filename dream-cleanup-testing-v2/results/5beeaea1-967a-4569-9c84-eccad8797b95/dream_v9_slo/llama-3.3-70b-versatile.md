# llama-3.3-70b-versatile on dream_v9_slo

← [Back to dream_v9_slo](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS | **Best Score:** 86/100 (T3)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v9_slo/llama-3.3-70b-versatile/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T3 (temp=0.5) - 86/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| T1 | 0.0 | 86% | 18 | 40 | 8 | 10 | 5 | **79** | REVIEW |
| T2 | 0.3 | 90% | 18 | 40 | 8 | 10 | 5 | **79** | REVIEW |
| **T3** | 0.5 | 77% | 18 | 42 | 11 | 10 | 5 | **86** | PASS |
| T4 | 0.8 | 91% | 17 | 39 | 8 | 10 | 5 | **77** | REVIEW |
| T5 | 1.0 | 84% | 16 | 38 | 8 | 10 | 5 | **75** | REVIEW |
| T6 | 1.5 | 79% | 14 | 36 | 8 | 8 | 5 | **69** | ITERATE |
| T7 | 2.0 | 50% | 10 | 28 | 4 | 6 | 1 | **47** | FAIL |

### Config Analysis

#### T1 (temp=0.0) - 79/100
- **Length:** 4338 chars (86%) - optimal
- **Content:** Good preservation, all key details present
- **Grammar:** G1 fail (polnica), G2 pass (pritličju correct), garbled phrases remain
- **Readability:** No paragraph breaks (R1 fail)
- **Artifacts:** All "Hvala" removed

#### T3 (temp=0.5) - 86/100 WINNER
- **Length:** 3902 chars (77%) - optimal
- **Content:** Excellent preservation
- **Grammar:** G1 fail (polnica), most fixes applied
- **Readability:** HAS PARAGRAPHS (R1 pass) - unique for this model
- **Artifacts:** Clean

#### T7 (temp=2.0) - 47/100 FAIL
- **Length:** 2527 chars (50%) - borderline severe
- **Content:** Significant loss of details
- **Grammar:** Many issues due to randomness
- **Readability:** Choppy, incoherent

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P3 (top_p=0.5) - 80/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 78% | 18 | 39 | 8 | 10 | 5 | **78** | REVIEW |
| P2 | 0.3 | 78% | 18 | 39 | 8 | 10 | 5 | **78** | REVIEW |
| **P3** | 0.5 | 89% | 18 | 40 | 8 | 10 | 5 | **80** | PASS |
| P4 | 0.7 | 88% | 17 | 40 | 8 | 10 | 5 | **78** | REVIEW |
| P5 | 0.9 | 81% | 16 | 38 | 8 | 10 | 5 | **75** | REVIEW |
| P6 | 1.0 | 86% | 15 | 37 | 8 | 10 | 5 | **73** | REVIEW |

---

## Failures Summary (T3 - Best Config)

### Grammar (G) - 7 failures = 18/25
- **G1:** "polnica" NOT fixed to "bolnica"
- **G3:** "uspodbudo" NOT fixed to "spodbudo/vzpodbudo"
- **G20:** "Predem" NOT fixed to "Pridem"
- **G21:** "obhodnikov" NOT fixed to "hodnikov"
- **G25:** "ko hodi ta ljena vzgor" garbled phrase remains
- **G27:** "nadreval" NOT fixed to "nadaljeval"
- **G+:** Minor voice inconsistency (mix of past/present tense)

### Content (C) - 3 failures = 42/45
- **C23:** Flat areas + corridors mixed with stairs - MISSING (only describes stair variation)
- **C26:** "napol tek" (half-running down) - MISSING (only says "hojo navzdol")
- **C34:** "deset metrov široke" (10m wide stairs) - MISSING entirely
- **C+:** Minor voice penalty - uses past tense "Hodil sem" in some sections

### Hallucinations (H) - 0 failures = 10/10
- None detected in T3

### Readability (R) - 1 failure = 11/15
- **R1:** HAS paragraph breaks (PASS - unique for this config!)
- **R2:** Sentence flow good (PASS)
- **R3:** Personal voice preserved (PASS)
- **R4:** Minor coherence issue with tense shifts

---

## Key Finding

**T3 (temp=0.5) is the ONLY config that produces paragraph breaks for llama-3.3-70b.**

This is significant because:
- T1, T2, T4+ all produce block text without paragraphs
- T3 achieves best readability score (11/15)
- Paragraphs appear at scene transitions as intended

---

## Production Recommendation

**Use llama-3.3-70b-versatile with T3 config (temp=0.5):**
- Best score: **86/100** (PASS threshold: ≥80)
- Only config with proper paragraph structure
- Optimal length (77%)
- Processing time: ~4s
