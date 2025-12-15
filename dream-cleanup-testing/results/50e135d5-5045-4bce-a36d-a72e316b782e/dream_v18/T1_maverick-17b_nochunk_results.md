# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v18 (Non-Chunked)

← [Back to dream_v18](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS | **Best Score:** 85.7/100 (v6)
**Cache:** `cache/50e135d5-5045-4bce-a36d-a72e316b782e/dream_v18/meta-llama-llama-4-maverick-17b-128e-instruct/nochunk/`
**Test Date:** 2025-12-15
**Raw Length:** 5,093 characters
**Test Type:** Variance testing (10x T1 runs, no chunking)

---

## Summary Table

| Run | Temp | Length | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|------|--------|-------|------|------|------|------|-----|-------|--------|
| v1 | 0.0 | 4490 | 88.2% | 19.8 | 38.9 | 12.0 | 10 | 5 | 85.7 | PASS |
| v2 | 0.0 | 4459 | 87.6% | 19.3 | 35.8 | 11.3 | 8 | 5 | 79.4 | REVIEW |
| v3 | 0.0 | 4754 | 93.3% | 19.8 | 38.9 | 12.0 | 10 | 5 | 85.7 | PASS |
| v4 | 0.0 | 4775 | 93.8% | 19.3 | 37.9 | 11.3 | 6 | 5 | 79.5 | REVIEW |
| v5 | 0.0 | 4575 | 89.8% | 19.8 | 37.9 | 12.0 | 10 | 5 | 84.7 | PASS |
| **v6** | 0.0 | 4505 | **88.5%** | 19.8 | **40.9** | 12.0 | 8 | 5 | **85.7** | PASS |
| v7 | 0.0 | 4936 | 96.9% | 19.3 | 38.9 | 11.3 | 8 | 3 | 80.5 | PASS |
| v8 | 0.0 | 5023 | 98.6% | 19.3 | 38.9 | 11.3 | 8 | 3 | 80.5 | PASS |
| v9 | 0.0 | 4553 | 89.4% | 19.3 | 35.8 | 11.3 | 8 | 5 | 79.4 | REVIEW |
| v10 | 0.0 | 4648 | 91.3% | 19.8 | 37.9 | 12.0 | 10 | 5 | 84.7 | PASS |

**Pass Rate:** 100% (10/10)
**Best:** v6 (85.7) - Only run with C26 correct
**Worst:** v2, v9 (79.4) - Missing C26, C34, has hallucinations

---

## Best Run Analysis (v6 - 85.7/100)

### Automated Checks

- [x] No "Hvala" (A1)
- [x] No English (G+)
- [x] No Russian (G++)
- [x] Length: 88.5% - Optimal range

### Grammar (G) - 38/48 passed = 19.8/25 points

**Passed (38):** G6 (Odpiram), G9 (tema), G10 (Spomnim), G13 (Odprem), G16 (neenakomerne), G21 (stopnice ×8), G24 (navzdol), G42 (strme), most garbled phrases cleaned.

**Failed (10):**
- **G4:** "prizidku" instead of "pritličju"
- **G8:** "obhodnikov" not fixed
- **G27:** "Vidim se, vem" remnant
- **G39:** "na pol tega" not fixed
- G44-48: Some garbled phrases kept

### Content (C) - 40/44 passed = 40.9/45 points

**v6 is unique - passes C26:**
- **C26:** ✓ "navzdol in navzdol" (only run!)
- **C34:** ✓ "deset metrov široke"
- **C44:** ✓ "sva prišla" (dual form)

**Failed (4):**
- **C5:** "prizidku" instead of "pritličje"
- **C7:** Sound description simplified
- Minor: some detail condensation

### Hallucinations (H) - 1 found = 8/10 points

- **H1:** "hotel na vrhu" - invented from garbled "horitele na vzgor"

### Readability (R) - 3.2/4 = 12.0/15 points

- R1: Paragraph breaks ✓
- R2: Sentence flow ⚠️ (minor remnants)
- R3: Personal voice ✓
- R4: Dream coherence ✓

---

## Critical Issues

### C26: "nazaj" Error (9/10 runs fail)

**Only v6 correct.** All others produce "nazaj in nazaj" (back) instead of "navzdol in navzdol" (down).

| Run | C26 Output | Status |
|-----|------------|--------|
| v6 | "navzdol in navzdol" | ✓ |
| All others | "nazaj in nazaj" | ❌ |

### "hotel" Hallucination (5/10 runs)

Runs v2, v4, v6, v7, v9 generate "hotel" from garbled "horitele na vzgor".

### C34: "10m" Detail (5/10 runs miss)

Runs v1, v2, v5, v9, v10 omit the specific "deset metrov" measurement.

---

## Key Finding

**v6 is the only run that correctly handles C26** ("navzdol in navzdol"). This makes it the best run despite having a hallucination. The "nazaj" error systematically affects 90% of runs.

---

## Production Recommendation

Non-chunked maverick produces acceptable results (79-86 range) but has high variance on critical checkpoints. Consider:
1. Use chunking (improves to 86-89 range)
2. Add prompt instruction for C26: "Interpret 'nazdolj' as 'navzdol' (down), NOT 'nazaj' (back)"
3. Validate output for "hotel" hallucination
