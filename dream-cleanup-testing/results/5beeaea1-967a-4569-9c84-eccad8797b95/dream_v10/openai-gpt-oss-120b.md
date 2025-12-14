# openai/gpt-oss-120b on dream_v10

← [Back to dream_v10](./README.md) | [Back to Index](../README.md)

---

**Status:** ITERATE | **Best Score:** 64/100 (T1)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v10/openai-gpt-oss-120b/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T1 (temp=0.0) - 64/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| **T1** | 0.0 | 55% | 21 | 30 | 8 | 4 | 1 | **64** | ITERATE |
| T2 | 0.3 | 48% | 20 | 26 | 8 | 4 | 0 | **58** | FAIL |
| T3 | 0.5 | 51% | 20 | 28 | 8 | 4 | 1 | **61** | ITERATE |
| T4 | 0.8 | 54% | 20 | 29 | 8 | 4 | 1 | **62** | ITERATE |
| T5 | 1.0 | 45% | 19 | 24 | 8 | 4 | 0 | **55** | FAIL |
| T6 | 1.5 | 50% | 20 | 27 | 8 | 4 | 0 | **59** | FAIL |
| T7 | 2.0 | 40% | 18 | 22 | 8 | 4 | 0 | **52** | FAIL |

### Config Analysis

#### T1 (temp=0.0) - 64/100 WINNER (but still FAILS quality threshold)
- **Length:** 2803 chars (55%) - SEVERE over-summarization
- **Grammar:** Best raw score but at cost of content
- **Content:** Heavily condensed, loses many details
- **Critical:** 3 hallucinations detected

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P2 (top_p=0.3) - 64/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 51% | 20 | 28 | 8 | 4 | 1 | **61** | ITERATE |
| **P2** | 0.3 | 56% | 21 | 30 | 8 | 4 | 1 | **64** | ITERATE |
| P3 | 0.5 | 48% | 20 | 26 | 8 | 4 | 0 | **58** | FAIL |
| P4 | 0.7 | 42% | 18 | 23 | 8 | 4 | 0 | **53** | FAIL |
| P5 | 0.9 | 54% | 20 | 29 | 8 | 4 | 1 | **62** | ITERATE |
| P6 | 1.0 | 47% | 19 | 25 | 8 | 4 | 0 | **56** | FAIL |

---

## CASE 3: Both Parameters

| Config | Temp | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|-------|------|------|------|------|------|-----|-------|--------|
| B1 | 0.3 | 0.9 | 47% | 19 | 25 | 8 | 4 | 0 | **56** | FAIL |
| B2 | 0.5 | 0.5 | 48% | 20 | 26 | 8 | 4 | 0 | **58** | FAIL |
| B3 | 0.5 | 0.9 | 46% | 19 | 25 | 8 | 4 | 0 | **56** | FAIL |
| B4 | 0.8 | 0.5 | 58% | 21 | 31 | 8 | 4 | 1 | **65** | ITERATE |

---

## Failures Summary (T1 - Best Config)

### Grammar (G) - 4 failures = 21/25

- **G20:** "pridem" variations remain inconsistent
- **G26:** Some tense issues remain
- **G27:** Minor garbled remnants
- **G28:** "nato" variations

### Content (C) - 15 failures = 30/45 (SEVERE LOSS)

**LOST/SUMMARIZED:**
- **C4:** "vzpodbudo" - summarized away
- **C10:** Cupboard description - heavily simplified
- **C18:** Second person sighting - LOST
- **C20:** Door detail "bistranska" - LOST
- **C23:** Flat areas + corridors - SUMMARIZED (not fully preserved)
- **C36:** Two women description - simplified
- **C40:** Grass/earth section - simplified
- **C42:** Young woman meeting - simplified
- Multiple other scene details condensed

### Readability (R) - 2 failures = 8/15
- **R3:** Personal voice LOST - reads like third-party summary
- **R4:** Dream coherence WEAKENED - feels disconnected

### Hallucinations (H) - 3 failures = 4/10 (CRITICAL!)
- **H1:** "čutim hladno kovino pod prsti" (feel cold metal under fingers) - INVENTED
- **H2:** "Morda je to razlog, zakaj se v celotni stavbi čuti neprestano vibriranje" - INVENTED explanation
- **H3:** "ji pomagam" (I help her) - INVENTED action (original: he just jumped, no helping)

---

## Key Finding

**gpt-oss-120b severely over-summarizes and HALLUCINATES content.**

Critical issues:
1. **40-58% length** across ALL configs - over-summarization is systematic
2. **3 hallucinations detected** - model invents content not in original
3. **Lost personal narrative voice** - output reads like summary, not personal journal
4. **Best grammar but worst content** - trade-off is unacceptable

This model is **NOT suitable** for this task despite having good grammar scores.

---

## Production Recommendation

**DO NOT USE gpt-oss-120b for dream cleanup:**
- Score: 64/100 (ITERATE - below PASS threshold)
- Hallucinations detected (H1, H2, H3)
- Severe over-summarization (all configs <60% length)
- Loses personal voice

**Alternatives:**
- maverick-17b (94/100) - best overall
- scout-17b (91/100) - best content preservation
- llama-3.3-70b (84/100) - good balance
