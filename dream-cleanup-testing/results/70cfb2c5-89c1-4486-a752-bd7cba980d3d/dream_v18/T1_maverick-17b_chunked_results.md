# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v18 (Chunked)

← [Back to dream_v18](./README.md) | [Back to Index](../README.md)

---

**Status:** EXCELLENT | **Best Score:** 96.1/100 (v4, v8, v12)
**Cache:** `cache/70cfb2c5-89c1-4486-a752-bd7cba980d3d/dream_v18/meta-llama-llama-4-maverick-17b-128e-instruct/chunked/`
**Test Date:** 2025-12-16
**Raw Length:** 5,013 characters
**Test Type:** Variance testing (15x T1 runs, chunking enabled)

---

## Summary Table

| Run | Temp | Length | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|------|--------|-------|------|------|------|------|-----|-------|--------|
| v1 | 0.0 | 4544 | 90.6% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| v2 | 0.0 | 4573 | 91.2% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| v3 | 0.0 | 4494 | 89.6% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| **v4** | 0.0 | 4419 | **88.2%** | **24.1** | 44.0 | 15 | 8 | 5 | **96.1** | EXCELLENT |
| v5 | 0.0 | 4551 | 90.8% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| v6 | 0.0 | 4573 | 91.2% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| v7 | 0.0 | 4375 | 87.3% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| **v8** | 0.0 | 4362 | **87.0%** | **24.1** | 44.0 | 15 | 8 | 5 | **96.1** | EXCELLENT |
| v9 | 0.0 | 4480 | 89.4% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| v10 | 0.0 | 4514 | 90.0% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| v11 | 0.0 | 4541 | 90.6% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| **v12** | 0.0 | 4254 | **84.9%** | **24.1** | 44.0 | 15 | 8 | 5 | **96.1** | EXCELLENT |
| v13 | 0.0 | 4411 | 88.0% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| v14 | 0.0 | 4304 | 85.9% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |
| v15 | 0.0 | 4388 | 87.5% | 23.2 | 44.0 | 15 | 8 | 5 | 95.2 | EXCELLENT |

**Pass Rate:** 100% (15/15) - ALL runs score EXCELLENT (≥90)
**Best:** v4, v8, v12 (96.1) - Fix G1 "polnica" → "bolnica"
**Worst:** All others (95.2) - Only G1 unfixed

---

## Comparison: Chunked vs Non-Chunked

| Metric | Non-Chunked | Chunked | Delta |
|--------|-------------|---------|-------|
| Best Score | 94 | **96.1** | **+2.1** |
| Worst Score | 36.4 | **95.2** | **+58.8** |
| Pass Rate (≥70%) | 40% | **100%** | **+60%** |
| Pass Rate (≥80%) | 40% | **100%** | **+60%** |
| Pass Rate (≥90%) | 13% | **100%** | **+87%** |
| C30 (hodnik levo-desno) | 40% | **100%** | **+60%** |
| C34 (10m measurement) | 13% | 0% | -13% |

**Key Finding:** Chunking eliminates the bimodal failure mode (36-52% outputs) completely.

---

## Best Run Analysis (v4 - 96.1/100)

Selected v4 as representative best run (fixes G1, optimal 88.2% ratio).

### Automated Checks

- [x] No "Hvala" (A1)
- [x] No English (G+)
- [x] No Russian (G++)
- [x] Length: 88.2% - Optimal range

### Grammar (G) - 27/28 passed = 24.1/25 points

**Passed (27):** G2-G20, G22-G28, and G1 "nekakšna bolnica" ✓

**Failed (1):**
- **G21:** "obhodnikov" not fixed to "hodnikov"

### Content (C) - 43/44 passed = 44.0/45 points

**Passed (43):** All scene details preserved, including:
- **C26:** ✓ "napol tek nazdolj" (correct direction)
- **C30:** ✓ "hodnik, levo-desno" at landing

**Failed (1):**
- **C34:** "deset metrov široke" (10m wide) - MISSING

### Hallucinations (H) - 1 found = 8/10 points

- **H1:** "smo prišli" (we plural) instead of singular/dual

### Readability (R) - 4/4 = 15/15 points

- R1: Paragraph breaks ✓
- R2: Sentence flow ✓
- R3: Personal voice ✓
- R4: Dream coherence ✓

---

## Common Patterns (All 15 Runs)

### Grammar Failures

| Checkpoint | Pass Rate | Notes |
|------------|-----------|-------|
| G1 (polnica→bolnica) | 3/15 (20%) | v4, v8, v12 fix it |
| G21 (obhodnikov→hodnikov) | 0/15 (0%) | None fix it |

### Content Failures

| Checkpoint | Pass Rate | Notes |
|------------|-----------|-------|
| C26 (navzdol direction) | 15/15 (100%) | All correct! No "nazaj" error |
| C30 (hodnik levo-desno) | 15/15 (100%) | All preserve landing corridor |
| C34 (10m measurement) | 0/15 (0%) | All omit specific width |

### Hallucinations

| Hallucination | Occurrence | Notes |
|---------------|------------|-------|
| H1: "smo prišli" (plural) | 15/15 | All use wrong number |

---

## Key Findings

1. **Chunking eliminates bimodal failures** - Non-chunked had 60% failure rate (9/15 below 70%), chunked has 0% failures

2. **All runs score EXCELLENT (≥90)** - Range is 95.2-96.1, extremely consistent

3. **C30 fixed by chunking** - Non-chunked only preserved "hodnik levo-desno" in 40% of runs, chunked preserves it in 100%

4. **C34 not fixable** - The "deset metrov" measurement is consistently lost in both chunked and non-chunked runs

5. **G1 variance** - 3/15 runs (v4, v8, v12) correctly interpret "polnica" as "bolnica"

---

## Production Recommendation

**Use chunked maverick for production:**

| Approach | Pass Rate | Score Range | Recommendation |
|----------|-----------|-------------|----------------|
| Non-chunked | 40% | 36-94 | ❌ Unreliable |
| **Chunked** | **100%** | **95-96** | ✅ Production ready |

Chunking adds ~5-10s processing time but guarantees consistent high-quality output.
