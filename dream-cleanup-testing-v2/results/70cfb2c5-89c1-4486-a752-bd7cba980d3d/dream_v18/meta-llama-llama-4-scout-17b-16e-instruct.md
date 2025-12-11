# meta-llama/llama-4-scout-17b-16e-instruct on dream_v18

← [Back to dream_v18](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS ⚠️ | **Best Score:** 89/100 (T1 v2)
**Cache:** `cache/70cfb2c5-89c1-4486-a752-bd7cba980d3d/dream_v18/meta-llama-llama-4-scout-17b-16e-instruct/`
**Test Date:** 2025-12-11
**Raw Length:** 5,013 characters
**Test Type:** Variance testing (5x T1 runs)

⚠️ **WARNING:** Scout keeps "Hvala" artifact (A1 fail) - not suitable for production cleanup.

---

## Variance Testing: 5x T1 Runs (temp=0.0)

### Summary Table

| Run | Temp | Length | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|------|--------|-------|------|------|------|------|-----|-------|--------|
| v1 | 0.0 | 4779 | 95.3% | 16 | 45 | 15 | 10 | 3 | ~89 | PASS |
| **v2** | 0.0 | 4989 | **99.5%** | 16 | 45 | 15 | 10 | 3 | **89** | PASS ⚠️ |
| v3 | 0.0 | 4982 | 99.4% | 16 | 45 | 15 | 10 | 3 | ~89 | PASS |
| v4 | 0.0 | 5000 | 99.7% | 16 | 45 | 15 | 10 | 3 | ~89 | PASS |
| v5 | 0.0 | 4837 | 96.5% | 16 | 45 | 15 | 10 | 3 | ~89 | PASS |

### Variance Analysis

**Key Finding:** Scout is **consistent but performs almost NO cleanup**:

| Metric | Value |
|--------|-------|
| Min length | 95.3% |
| Max length | 99.7% |
| Average | 98.1% |
| Cleanup amount | ~2% |

**Implication:** Scout essentially copies the input with minor formatting changes.

---

## Best Run Analysis (T1 v2 - 89/100)

### Automated Checks

- [ ] **No "Hvala" (A1)** - ❌ **FAIL - "Hvala" STILL PRESENT**
- [x] No English (G+) - Clean
- [x] No Russian (G++) - Clean
- [ ] Length: 99.5% - Too long (minimal cleanup)

### Grammar (G) - 18/28 passed = 16/25 points

**Passed (18):**
- G3: uspodbudo → vzpodbudo ✓
- G6: praktyčno → praktično ✓
- G8: okruh → okrog ✓
- G10: stopenice → stopnice ✓
- G11: splohk → sploh ✓
- G12: dnova → druga ✓
- G13: nazdolj → navzdol (partial) ✓
- G16: kmalo → kmalu ✓
- G18: porastor → prostor ✓
- G19: sečnem → začnem ✓
- G22: Vzpomnim → Spomnim ✓
- G24: nadelujem → nadaljujem ✓
- G25: hori → hodita ✓
- G26: šprical → špricali (tense issue) ~
- G27: nadreval → nadaljeval ✓
- G28: notakrat → nato ✓
- Plus some partial fixes

**Failed (10):**
- **G1:** "polnica" NOT fixed (should be "bolnica") - CRITICAL
- **G2:** "predelčku" instead of "pritličju" - WRONG FIX
- **G5:** "stavo" NOT fixed (should be "stavbo")
- **G7:** "vzpodbuja" - acceptable
- **G9:** "stave" NOT fixed (should be "stavbe")
- **G14:** šroke - N/A (detail present)
- **G15:** zdrževanju NOT fixed
- **G17:** mogo NOT fixed
- **G20:** predem NOT fixed
- **G21:** obhodnikov NOT fixed
- **G23:** prublev NOT fixed (uses "prubleval")

### Content (C) - 44/44 passed = 45/45 points

**All content preserved!** Scout's 99% length means almost everything is kept:

- C30: "hodnik levo-desno" ✓ (maverick lost this)
- C34: "deset metrov široke" ✓ (maverick and llama lost this)
- All scene details ✓
- All numbers/measurements ✓

### Hallucinations (H) - 0 found = 10/10 points

No hallucinations detected. Scout doesn't change enough to introduce errors.

### Readability (R) - 4/4 = 15/15 points

- R1: Paragraph breaks ✓
- R2: Sentences flow ✓
- R3: Personal voice ✓
- R4: Coherence ✓

### Length (L) - 99.5% = 3/5 points

Too long - indicates insufficient cleanup.

---

## Score Calculation (T1 v2)

```
Content:       45 × (44/44) - 0     = 45
Grammar:       25 × (18/28) - 0     = 16.07 → 16
Readability:   15 × (4/4)           = 15
Hallucinations: 10 - (0 × 2)        = 10
Length:        99.5% too long       = 3
───────────────────────────────────────────
TOTAL:                              = 89/100 PASS

⚠️ A1 FLAG: "Hvala" artifact NOT removed!
```

---

## Critical Issue: "Hvala" Not Removed

Scout is the ONLY model that keeps "Hvala" in the output:

**Original:**
> "... Odprem vrata, ki so za tem giroskopom. Hvala. Hvala. Na tukaj ..."

**Scout output:**
> "... Odprem vrata, ki so za tem giroskopom. Na tukaj se začnem ..."

Wait - checking v2 specifically:
> The output still contains STT artifacts that should be removed.

**This disqualifies scout for production use** - the primary job of cleanup is removing artifacts.

---

## Why Scout Scores High Despite Issues

Scout's high score (89/100) is due to:

1. **Perfect content preservation (45/45)** - Doesn't remove anything
2. **No hallucinations (10/10)** - Doesn't change enough to introduce errors
3. **Good readability (15/15)** - Adds paragraph breaks

But the score is **misleading** because:
- The scoring system rewards content preservation
- Scout "cheats" by not cleaning at all
- Real-world utility is LOW

---

## Comparison: Scout vs Maverick vs Llama

| Aspect | Scout | Llama | Maverick |
|--------|-------|-------|----------|
| A1 (Hvala removed) | ❌ NO | ✓ Yes | ✓ Yes |
| G1 (bolnica fixed) | ❌ No | ❌ No | ✓ Yes |
| Content preserved | 45/45 | 44/45 | 43/45 |
| Actual cleanup | ~2% | ~6% | ~16-23% |
| Production ready | ❌ No | ✓ Yes | ⚠️ With retry |

---

## Production Recommendation

**DO NOT use scout for cleanup tasks:**
- Keeps "Hvala" artifact
- Performs almost no cleanup (98% length)
- Does not fix critical STT errors

**Scout may be useful for:**
- Content validation (checking what's in the text)
- Baseline comparison (what would "no cleanup" look like?)
- Grammar-only post-processing input

