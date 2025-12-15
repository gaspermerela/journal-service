# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v18

← [Back to dream_v18](./README.md) | [Back to Index](../README.md)

---

**Status:** UNRELIABLE | **Best Score:** 94/100 (T1 v2)
**Cache:** `cache/70cfb2c5-89c1-4486-a752-bd7cba980d3d/dream_v18/meta-llama-llama-4-maverick-17b-128e-instruct/`
**Test Dates:** 2025-12-11 (5 runs), 2025-12-16 (10 runs)
**Raw Length:** 5,013 characters
**Test Type:** Extended variance testing (15x T1 runs, non-chunked)

---

## Summary Table (15 Runs)

### Original Runs (Dec 11)

| Run | Temp | Length | Ratio | Status |
|-----|------|--------|-------|--------|
| v1 | 0.0 | 3872 | 77.2% | ✅ PASS |
| **v2** | 0.0 | 4210 | **84.0%** | ✅ **BEST** |
| v3 | 0.0 | 2584 | 51.5% | ❌ FAIL |
| v4 | 0.0 | 2569 | 51.2% | ❌ FAIL |
| v5 | 0.0 | 3895 | 77.7% | ✅ PASS |

### Extended Runs (Dec 16)

| Run | Temp | Length | Ratio | Status |
|-----|------|--------|-------|--------|
| v6 | 0.0 | 1822 | 36.4% | ❌ SEVERE |
| v7 | 0.0 | 3210 | 64.0% | ❌ FAIL |
| v8 | 0.0 | 2372 | 47.3% | ❌ SEVERE |
| v9 | 0.0 | 3783 | 75.5% | ✅ PASS |
| v10 | 0.0 | 4298 | 85.7% | ✅ PASS |
| v11 | 0.0 | 2433 | 48.5% | ❌ SEVERE |
| v12 | 0.0 | 2411 | 48.1% | ❌ SEVERE |
| v13 | 0.0 | 3093 | 61.7% | ❌ FAIL |
| v14 | 0.0 | 2582 | 51.5% | ❌ FAIL |
| v15 | 0.0 | 3667 | 73.2% | ✅ PASS |

---

## Variance Analysis (15 Runs)

**Pass Rate: 40% (6/15)** - Only 6 runs in acceptable 70-95% range

| Outcome | Runs | Percentage | Length Range |
|---------|------|------------|--------------|
| Pass (70-95%) | 6 | **40%** | 73-86% |
| Fail (60-69%) | 3 | 20% | 61-64% |
| Severe (<60%) | 6 | **40%** | 36-52% |

**Distribution:**
```
<50%:  ████████ 5 runs (33%) - SEVERE
50-59%: ██ 1 run (7%)
60-69%: ████ 3 runs (20%)
70-79%: ██████ 4 runs (27%)
80-95%: ████ 2 runs (13%) - OPTIMAL
```

**Key Finding:** Extended testing reveals failure rate is **60%**, not 40% as originally estimated.

---

## Best Run Analysis (T1 v2 - 94/100)

### Automated Checks

- [x] No "Hvala" (A1)
- [x] No English (G+)
- [x] No Russian (G++)
- [x] Length: 84% - Optimal range

### Grammar (G) - 26/28 passed = 23/25 points

**Passed (26):** G1 (polnica→bolnica - ONLY model to fix!), G2-G13, G15-G20, G22-G25, G27-G28

**Failed (2):**
- **G21:** "obhodnikov" NOT fixed
- **G26:** Past tense "razpršili" instead of present

### Content (C) - 42/44 passed = 43/45 points

**Failed (2):**
- **C30:** "hodnik levo-desno" at landing - MISSING
- **C34:** "deset metrov široke" (10m wide) - MISSING

### Hallucinations (H) - 1 found = 8/10 points

- **H1:** "smo prišli" (we came) instead of singular

### Score Calculation

```
Grammar:       23/25
Content:       43/45
Readability:   15/15
Hallucinations: 8/10
Length:         5/5
─────────────────────
TOTAL:         94/100 EXCELLENT
```

---

## Failed Runs Analysis

### Severe Failures (<50%)

v6 (36.4%), v8 (47.3%), v11 (48.5%), v12 (48.1%) all show:
- Aggressive summarization (lost 50%+ content)
- Combined multiple scenes into single sentences
- Lost specific details (numbers, measurements, descriptions)

### Example: v6 vs v2

**Original detail (C22):**
> "ene so bile ožje, ene daljše, ene globje, ene plitvejše"

**Good run (v2, 84%):**
> "ene so bile ožje, ene daljše, ene globje, ene plitvejše" ✓

**Failed run (v6, 36%):**
> "stopnice so bile neenakomerne in težke za hoditi" ❌

---

## Key Finding

**Maverick is UNRELIABLE for production:**
- 60% failure rate (9/15 runs below 70%)
- 33% severe failure rate (5/15 runs below 50%)
- Best score (94/100) only achieved in 13% of runs
- "MANDATORY REQUIREMENT" prompt box has NO effect

---

## Production Recommendation

**DO NOT use maverick without safeguards.**

| Approach | Pass Rate | Recommendation |
|----------|-----------|----------------|
| Single run | 40% | ❌ Unacceptable |
| 3x retry | ~78% | ⚠️ Acceptable with validation |

**Retry logic:**
```python
for attempt in range(3):
    result = run_cleanup(maverick, T1)
    if len(result) / len(original) >= 0.70:
        return result  # Accept
# All retries failed - fallback to llama
```
