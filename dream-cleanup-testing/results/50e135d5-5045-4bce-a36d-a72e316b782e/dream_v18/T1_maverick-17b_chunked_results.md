# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v18 (Chunked)

← [Back to dream_v18](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS | **Best Score:** 88.8/100 (v1, v6, v7, v8 tied)
**Cache:** `cache/50e135d5-5045-4bce-a36d-a72e316b782e/dream_v18/meta-llama-llama-4-maverick-17b-128e-instruct/chunked/`
**Test Date:** 2025-12-16
**Raw Length:** 5,093 characters
**Test Type:** Variance testing (10x T1 runs, chunking enabled)

---

## Summary Table

| Run | Temp | Length | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|------|--------|-------|------|------|------|------|-----|-------|--------|
| **v1** | 0.0 | 4829 | **94.8%** | 19.8 | 40.9 | 13.1 | 10 | 5 | **88.8** | PASS |
| v2 | 0.0 | 4898 | 96.2% | 19.3 | 40.9 | 13.1 | 10 | 3 | 86.3 | PASS |
| v3 | 0.0 | 4876 | 95.7% | 19.8 | 40.9 | 13.1 | 10 | 3 | 86.8 | PASS |
| v4 | 0.0 | 4938 | 97.0% | 19.3 | 40.9 | 13.1 | 10 | 3 | 86.3 | PASS |
| v5 | 0.0 | 4829 | 94.8% | 19.3 | 40.9 | 13.1 | 10 | 5 | 88.3 | PASS |
| **v6** | 0.0 | 4839 | **95.0%** | 19.8 | 40.9 | 13.1 | 10 | 5 | **88.8** | PASS |
| **v7** | 0.0 | 4751 | **93.3%** | 19.8 | 40.9 | 13.1 | 10 | 5 | **88.8** | PASS |
| **v8** | 0.0 | 4835 | **94.9%** | 19.8 | 40.9 | 13.1 | 10 | 5 | **88.8** | PASS |
| v9 | 0.0 | 4905 | 96.3% | 19.3 | 40.9 | 13.1 | 10 | 3 | 86.3 | PASS |
| v10 | 0.0 | 4852 | 95.3% | 19.8 | 41.9 | 13.1 | 10 | 3 | 87.8 | PASS |

**Pass Rate:** 100% (10/10) - Chunking eliminates bimodal failure mode

---

## Comparison: Chunked vs Non-Chunked (AssemblyAI)

| Metric | Non-Chunked | Chunked | Delta |
|--------|-------------|---------|-------|
| Best Score | 85.7 | **88.8** | +3.1 |
| Worst Score | 79.4 | **86.3** | +6.9 |
| Pass Rate | 100% | 100% | - |
| C26 Fixed | 1/10 | 0/10 | - |

---

## Best Run Analysis (v7 - 88.8/100)

Selected v7 as representative (lowest ratio at 93.3%, cleanest output).

### Automated Checks

- [x] No "Hvala" (A1)
- [x] No English (G+)
- [x] No Russian (G++)
- [x] Length: 93.3% - Optimal range

### Grammar (G) - 38/48 passed = 19.8/25 points

**Passed (38):** G6 (Odpiram), G9 (tema), G10 (Spomnim), G13 (Odprem), G14 (detajle), G16 (neenakomerne), G21 (stopnice ×8), G24 (navzdol), G42 (strme), most garbled phrases cleaned.

**Failed (10):**
- **G4:** "prizidku" instead of "pritličju" (annex vs ground floor)
- **G8:** "obhodnikov" not fixed to "hodnikov"
- **G27:** "Vidim se, vem" remnant (awkward)
- **G39:** "na pol tega" not fixed to "napol tek"
- G44-48: Some garbled phrases kept

### Content (C) - 40/44 passed = 40.9/45 points

**Failed (4):**
- **C5:** "prizidku" instead of "pritličje" (ground floor)
- **C7:** Sound description simplified ("všeč in me pomirja" vs "ugajal in govori")
- **C26:** "Nazaj in nazaj" instead of "navzdol in navzdol" ❌ CRITICAL
- **C44:** "smo prišli" instead of "sva prišla" (plural vs dual)

### Hallucinations (H) - 0 found = 10/10 points

No invented content. The "nazaj" error is misinterpretation, not invention.

### Readability (R) - 3.5/4 = 13.1/15 points

- R1: Paragraph breaks ✓
- R2: Sentence flow ⚠️ (some "Vidim se, vem" remnants)
- R3: Personal voice ✓
- R4: Dream coherence ✓

---

## Critical Issue: C26 "nazaj" Error (ALL RUNS)

**Raw:** "Nazdolj in nazdolj" (garbled navzdol)
**Expected:** "navzdol in navzdol" (down and down)
**All runs:** "Nazaj in nazaj" (back and back) ❌

Changes dream meaning - dreamer goes DOWN not BACK. Chunking does NOT fix this.

---

## Notable: v10 Has Correct Dual Form

Only v10 correctly preserves "sva prišla" (we two came) instead of "smo prišli" (we 3+ came).

---

## Key Finding

**Chunking improves maverick scores by ~5 points** and eliminates the bimodal failure mode seen in non-chunked runs. However, the C26 "nazaj" error persists regardless of chunking.

---

## Production Recommendation

Use maverick with chunking enabled for reliable results. Add prompt instruction to fix C26:
> "Interpret 'nazdolj' as 'navzdol' (downward), NOT 'nazaj' (backward)"
