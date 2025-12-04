# openai/gpt-oss-120b on dream_v10_slo

← [Back to dream_v10_slo](./README.md) | [Back to Index](../README.md)

---

**Status:** FAIL | **Best Score:** 60/100 (P4)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v10_slo/openai-gpt-oss-120b/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CRITICAL FINDING

**gpt-oss-120b severely over-summarizes with both English and Slovenian prompts.**

All configs produce 39-58% length ratio - losing nearly half or more of the original content. Additionally, hallucinations were detected.

---

## CASE 1: Temperature Only (top_p = null)

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| T1 | 0.0 | 45% | 21 | 26 | 11 | 6 | 0 | **56** | FAIL |
| T2 | 0.3 | 39% | 20 | 22 | 11 | 6 | 0 | **51** | FAIL |
| T3 | 0.5 | 39% | 20 | 22 | 11 | 6 | 0 | **51** | FAIL |
| T4 | 0.8 | 45% | 21 | 26 | 11 | 6 | 0 | **56** | FAIL |
| T5 | 1.0 | 43% | 20 | 24 | 11 | 6 | 0 | **53** | FAIL |
| T6 | 1.5 | 39% | 20 | 22 | 11 | 6 | 0 | **51** | FAIL |
| T7 | 2.0 | 47% | 21 | 27 | 11 | 6 | 0 | **57** | FAIL |

---

## CASE 2: Top-p Only (temperature = null)

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 46% | 21 | 26 | 11 | 6 | 0 | **56** | FAIL |
| P2 | 0.3 | 41% | 20 | 23 | 11 | 6 | 0 | **52** | FAIL |
| P3 | 0.5 | 43% | 20 | 24 | 11 | 6 | 0 | **53** | FAIL |
| **P4** | 0.7 | 58% | 22 | 30 | 11 | 6 | 1 | **60** | ITERATE |
| P5 | 0.9 | 54% | 21 | 28 | 11 | 6 | 1 | **58** | FAIL |
| P6 | 1.0 | 39% | 20 | 22 | 11 | 6 | 0 | **51** | FAIL |

---

## CASE 3: Both Parameters

| Config | Temp | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|-------|------|------|------|------|------|-----|-------|--------|
| B1 | 0.3 | 0.9 | 50% | 21 | 27 | 11 | 6 | 0 | **57** | FAIL |
| B2 | 0.5 | 0.5 | 43% | 20 | 24 | 11 | 6 | 0 | **53** | FAIL |
| B3 | 0.5 | 0.9 | 40% | 20 | 22 | 11 | 6 | 0 | **51** | FAIL |
| B4 | 0.8 | 0.5 | 40% | 20 | 22 | 11 | 6 | 0 | **51** | FAIL |

---

## Failures Summary (T1 - Baseline Config)

### Grammar (G) - 4 failures = 21/25

- **G26:** Tense inconsistencies remain
- Some garbled phrases removed rather than fixed
- Minor issues in rephrased sections

### Content (C) - 18 failures = 26/45 (SEVERE LOSS)

**LOST/SUMMARIZED:**
- **C4:** Instructions + encouragement - simplified
- **C7:** Sound that speaks to him - LOST
- **C10:** Cabinet description - heavily simplified
- **C18-C20:** Space transformation details - LOST
- **C21:** "zelo globoko pod" - simplified
- **C22:** Stair variations - simplified to generic
- **C23:** Flat areas + corridors - LOST
- **C26:** "napol tek" movement - LOST
- **C29:** Others unhappy with stairs - LOST
- **C30:** "hodnik levo-desno" - LOST
- **C32:** "pet, šest, sedem" - has "približno pet do sedem" (modified)
- **C34:** "deset metrov" - present but rephrased
- **C36:** Women unbothered - simplified
- **C39-C40:** Grass/earth details - simplified
- Multiple scene details condensed

### Readability (R) - 1 failure = 11/15

- **R3:** Personal voice LOST - reads like third-party summary

### Hallucinations (H) - 2 failures = 6/10 (CRITICAL!)

- **H1:** "ji pomagam" (I help her) - INVENTED action
  - Original: He jumps immediately, she doesn't - no mention of helping
- **H2:** "predmet, ki spominja na pastora" - unclear/garbled translation that may introduce incorrect meaning

### Length (L) - 0/5

- 45% ratio = severe over-summarization

---

## Key Finding

**gpt-oss-120b is NOT suitable for dream cleanup tasks.**

Critical issues:
1. **39-58% length** across ALL configs - over-summarization is systematic
2. **Hallucinations detected** - model invents content not in original
3. **Lost personal narrative voice** - output reads like summary, not personal journal
4. **Best grammar but worst content** - trade-off is unacceptable

---

## Comparison: dream_v10 vs dream_v10_slo

| Metric | dream_v10 (English) | dream_v10_slo (Slovenian) |
|--------|---------------------|---------------------------|
| Best length | 55% (T1) | 58% (P4) |
| Length range | 40-58% | 39-58% |
| Hallucinations | 3 detected | 2 detected |
| Best score | 64/100 | 60/100 |

**Similar poor performance with both prompts.** The model consistently over-summarizes regardless of prompt language.

---

## Production Recommendation

**DO NOT USE gpt-oss-120b for Slovenian STT cleanup.**

- Score: 60/100 (ITERATE - below PASS threshold)
- Hallucinations detected
- Severe over-summarization (all configs <60% length)
- Loses personal voice

**Use instead:**
- **llama-3.3-70b** with T1 (82/100) - best with Slovenian prompt
- **maverick** with P2 (82/100) - best overall
