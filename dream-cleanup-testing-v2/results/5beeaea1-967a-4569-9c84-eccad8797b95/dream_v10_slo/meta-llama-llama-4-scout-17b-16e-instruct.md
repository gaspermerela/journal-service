# meta-llama/llama-4-scout-17b-16e-instruct on dream_v10_slo

← [Back to dream_v10_slo](./README.md) | [Back to Index](../README.md)

---

**Status:** REVIEW | **Best Score:** 73/100 (T4)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v10_slo/meta-llama-llama-4-scout-17b-16e-instruct/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CRITICAL FINDING

**Scout performs ALMOST NO CLEANUP with Slovenian prompt.**

All configs produce 94-99% length ratio, meaning the model is essentially echoing the input with minimal changes. This is a fundamental failure to follow the prompt instructions.

---

## CASE 1: Temperature Only (top_p = null)

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| T1 | 0.0 | 95% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| T2 | 0.3 | 96% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| T3 | 0.5 | 95% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| **T4** | 0.8 | 94% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| T5 | 1.0 | 95% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| T6 | 1.5 | 98% | 10 | 44 | 15 | 10 | 3 | **72** | REVIEW |
| T7 | 2.0 | 97% | 10 | 44 | 15 | 10 | 3 | **72** | REVIEW |

---

## CASE 2: Top-p Only (temperature = null)

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| P1 | 0.1 | 99% | 10 | 44 | 15 | 10 | 3 | **72** | REVIEW |
| P2 | 0.3 | 96% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| P3 | 0.5 | 96% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| P4 | 0.7 | 94% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| P5 | 0.9 | 95% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| P6 | 1.0 | 95% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |

---

## CASE 3: Both Parameters

| Config | Temp | top_p | Len% | Total | Status |
|--------|------|-------|------|-------|--------|
| B1 | 0.3 | 0.9 | 96% | **73** | REVIEW |
| B2 | 0.5 | 0.5 | 96% | **73** | REVIEW |
| B3 | 0.5 | 0.9 | 99% | **72** | REVIEW |
| B4 | 0.8 | 0.5 | 96% | **73** | REVIEW |

---

## Failures Summary (T1 - Baseline Config)

### Grammar (G) - 14 failures = 11/25

- **G7:** "vzpodguja" remains (should be "vzpodbuja")
- **G13:** "nazdolj" / "nos dol" / "na vzdolj" remains (should be "navzdol")
- **G15:** "zdrževanju" remains (should be "vzdrževanju")
- **G17:** "mogo" remains (should be "moral")
- **G19:** "sečnem" remains (should be "začnem")
- **G20:** "predem" remains (should be "pridem")
- **G21:** "obhodnikov" remains (should be "hodnikov")
- **G22:** "Vzpomnim" remains (should be "Spomnim")
- **G23:** "prubleval čimprej pridet" garbled phrase remains
- **G24:** "nadelujem" remains (should be "nadaljujem")
- **G25:** "hori ta ljena vzgor" garbled phrase remains
- **G26:** "špricali" past tense remains (should be "špricam")
- **G27:** "nadreval" remains (should be "nadaljeval")
- **G28:** "notakrat" remains (should be "nato")

### Content (C) - 1 failure = 44/45

- **C1:** Uses "v bistvu bolnica" phrasing (awkward, but present)

### Artifacts (A) - 2 issues (not scored)

- **A2:** "Zdravstveno, da ste pripravljeni" NOT removed
- **A3:** Excessive fillers: "v bistvu", "torej", "a ne" all remain

### Length (L) - 3/5

- 95% ratio = slightly above optimal range

---

## Key Finding

**Scout performs NO effective cleanup with Slovenian prompt.**

The model fails to:
1. Remove STT artifacts ("Zdravstveno", fillers)
2. Correct STT errors (p↔b, e↔i patterns remain)
3. Fix garbled phrases
4. Clean up the text meaningfully

**Content preservation is excellent** but comes at the cost of zero grammar improvement.

---

## Comparison: dream_v10 vs dream_v10_slo

| Metric | dream_v10 (English) | dream_v10_slo (Slovenian) |
|--------|---------------------|---------------------------|
| T1 length | 98% | 95% |
| Best score | 91/100 | 73/100 |
| Cleanup level | Some (removes artifacts) | Almost none |
| STT correction | Minimal | Nearly zero |

**scout processes the English prompt slightly better**, but the Slovenian prompt causes even worse behavior.

---

## Production Recommendation

**DO NOT USE scout with Slovenian prompts for cleanup tasks.**

Use instead:
- **llama-3.3-70b** with T1 (82/100)
- **maverick** with P2 (82/100)
- Or use English prompt (dream_v10) with scout for better results (91/100)
