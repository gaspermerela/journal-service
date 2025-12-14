# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v18

← [Back to dream_v18](./README.md) | [Back to Index](../README.md)

---

**Status:** EXCELLENT (best run) | **Best Score:** 94/100 (T1 v2)
**Cache:** `cache/70cfb2c5-89c1-4486-a752-bd7cba980d3d/dream_v18/meta-llama-llama-4-maverick-17b-128e-instruct/`
**Test Date:** 2025-12-11
**Raw Length:** 5,013 characters
**Test Type:** Variance testing (5x T1 runs)

---

## Variance Testing: 5x T1 Runs (temp=0.0)

### Summary Table

| Run | Temp | Length | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|------|--------|-------|------|------|------|------|-----|-------|--------|
| v1 | 0.0 | 3872 | 77.2% | 23 | 43 | 15 | 8 | 5 | ~92 | EXCELLENT |
| **v2** | 0.0 | 4210 | **84.0%** | 23 | 43 | 15 | 8 | 5 | **94** | EXCELLENT |
| v3 | 0.0 | 2584 | 51.5% | - | - | - | - | 0 | ~60 | **FAIL** |
| v4 | 0.0 | 2569 | 51.2% | - | - | - | - | 0 | ~60 | **FAIL** |
| v5 | 0.0 | 3895 | 77.7% | 23 | 43 | 15 | 8 | 5 | ~92 | EXCELLENT |

### Variance Analysis

**Critical Finding:** Maverick shows **bimodal behavior** at temp=0.0:

| Outcome | Runs | Percentage | Length Range |
|---------|------|------------|--------------|
| Good | 3 | 60% | 77-84% |
| Over-summarized | 2 | **40%** | 51-52% |

**Implication:** Cannot reliably use maverick without retry logic or length validation.

---

## Best Run Analysis (T1 v2 - 94/100)

### Automated Checks

- [x] No "Hvala" (A1) - All removed
- [x] No English (G+) - Clean
- [x] No Russian (G++) - Clean
- [x] Length: 84% - Optimal range

### Grammar (G) - 26/28 passed = 23/25 points

**Passed (26):**
- G1: polnica → bolnica ✓ (ONLY model to fix this!)
- G2: pretličju → pritličju ✓
- G3: uspodbudo → spodbud ✓
- G4: ronotežje → ravnotežje ✓
- G5: stapo → stavbo ✓
- G6: praktyčno → praktično ✓
- G7: vzpodguja → vzpodbudi ✓
- G8: okruh → okoli ✓
- G9: stave → stavbe ✓
- G10: stopenice → stopnice ✓
- G11: splohk → sploh ✓
- G12: dnova → druga ✓
- G13: nazdolj → navzdol ✓
- G15: zdrževanju → vzdrževanju ✓
- G16: kmalo → kmalu ✓
- G17: mogo → moral ✓
- G18: porastor → prostor ✓
- G19: sečnem → začnem ✓
- G20: predem → preden ✓
- G22: Vzpomnim → Spomnim ✓
- G23: prublev → poskušal ✓
- G24: nadelujem → nadaljujem ✓
- G25: hori → hodita ✓
- G27: nadreval → nadaljeval ✓
- G28: notakrat → potem ✓

**Failed (2):**
- **G21:** "obhodnikov" NOT fixed (should be "hodnikov")
- **G26:** Uses past tense "razpršili" (should be present "špricam")

### Content (C) - 42/44 passed = 43/45 points

**Passed:** C1-C29, C31-C33, C35-C44 (42 total)

**Failed (2):**
- **C30:** "hodnik levo-desno" at landing - MISSING
  - Original: "je bil tudi hodnik, levo-desno"
  - Output: Just mentions "hodnik" without direction detail
- **C34:** "deset metrov široke" (10m wide stairs) - MISSING entirely

### Hallucinations (H) - 1 found = 8/10 points

- **H1:** "smo prišli" (we came) instead of singular
  - Original: "so prišla do enega dela" (garbled grammar)
  - Output: "smo prišli do enega dela" (we came)
  - Impact: Changes actor from ambiguous to "we"

### Readability (R) - 4/4 = 15/15 points

- R1: Paragraph breaks at scene changes ✓ (6 paragraphs)
- R2: Sentences flow logically ✓
- R3: Personal voice preserved ✓
- R4: Dream coherence maintained ✓

### Length (L) - 84% = 5/5 points

Optimal range (70-95%).

---

## Score Calculation (T1 v2)

```
Content:       45 × (42/44) - 0     = 42.95 → 43
Grammar:       25 × (26/28) - 0     = 23.21 → 23
Readability:   15 × (4/4)           = 15
Hallucinations: 10 - (1 × 2)        = 8
Length:        84% optimal          = 5
───────────────────────────────────────────
TOTAL:                              = 94/100 EXCELLENT
```

---

## Failed Runs Analysis (v3, v4)

Both v3 and v4 over-summarized to ~51% length despite identical prompt and temp=0.0.

### Characteristics of Failed Runs

- Length: 2569-2584 chars (51%)
- Aggressive condensation of descriptions
- Combined multiple scenes
- Lost significant detail

### Example Comparison

**Original detail (C22):**
> "ene so bile ožje, ene daljše, ene globje, ene plitvejše"

**Good run (v2):**
> "ene so bile ožje, ene daljše, ene globje, ene plitvejše" ✓

**Failed run (v3):**
> "bile so neenakomerne in težke za premagovanje" ❌ (condensed)

---

## Key Finding

**Maverick produces EXCELLENT results (94/100) when it works, but fails 40% of the time.**

The "MANDATORY REQUIREMENT" box in dream_v18 prompt did NOT prevent over-summarization.

---

## Production Recommendation

**DO NOT use maverick without safeguards:**

Option 1: **Retry logic**
```python
for attempt in range(3):
    result = run_cleanup(maverick, T1)
    if len(result) / len(original) >= 0.70:
        return result  # Accept
# All retries failed - fallback to llama
```

Option 2: **Ensemble approach**
- Run maverick + llama in parallel
- Accept maverick if length ≥70%, else use llama

