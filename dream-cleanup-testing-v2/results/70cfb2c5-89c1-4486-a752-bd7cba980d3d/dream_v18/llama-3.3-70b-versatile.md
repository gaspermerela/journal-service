# llama-3.3-70b-versatile on dream_v18

← [Back to dream_v18](./README.md) | [Back to Index](../README.md)

---

**Status:** PASS | **Best Score:** 88/100 (T1 v2)
**Cache:** `cache/70cfb2c5-89c1-4486-a752-bd7cba980d3d/dream_v18/llama-3.3-70b-versatile/`
**Test Date:** 2025-12-11
**Raw Length:** 5,013 characters
**Test Type:** Variance testing (5x T1 runs)

---

## Variance Testing: 5x T1 Runs (temp=0.0)

### Summary Table

| Run | Temp | Length | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|------|--------|-------|------|------|------|------|-----|-------|--------|
| v1 | 0.0 | 4897 | 97.7% | 18 | 44 | 15 | 8 | 3 | ~88 | PASS |
| **v2** | 0.0 | 4724 | **94.2%** | 18 | 44 | 15 | 8 | 3 | **88** | PASS |
| v3 | 0.0 | 4889 | 97.5% | 18 | 44 | 15 | 8 | 3 | ~88 | PASS |
| v4 | 0.0 | 4887 | 97.5% | 18 | 44 | 15 | 8 | 3 | ~88 | PASS |
| v5 | 0.0 | 4875 | 97.2% | 18 | 44 | 15 | 8 | 3 | ~88 | PASS |

### Variance Analysis

**Key Finding:** Llama is **highly consistent** at temp=0.0:

| Metric | Value |
|--------|-------|
| Min length | 94.2% |
| Max length | 97.7% |
| Variance | 3.5% |
| All runs pass | ✓ |

**Implication:** Llama is reliable but performs minimal cleanup.

---

## Best Run Analysis (T1 v2 - 88/100)

### Automated Checks

- [x] No "Hvala" (A1) - Removed
- [x] No English (G+) - Clean
- [x] No Russian (G++) - Clean
- [ ] Length: 94% - Edge of optimal (minor penalty)

### Grammar (G) - 20/28 passed = 18/25 points

**Passed (20):**
- G2: pretličju → pritličju ✓
- G4: ronotežje → ravnotežje ✓
- G5: stapo → stavbo ✓
- G6: praktyčno → praktično ✓
- G8: okruh → okoli ✓
- G9: stave → stavbe ✓
- G10: stopenice → stopnice ✓
- G11: splohk → sploh ✓
- G12: dnova → dvorna ✓
- G13: nazdolj → navzdol ✓
- G15: zdrževanju → vzdrževanju ✓
- G16: kmalo → kmalu ✓
- G18: porastor → prostor ✓
- G20: predem → preden ✓
- G21: obhodnikov - different wording ✓
- G22: Vzpomnim → Spomnim ✓
- G25: hori → hodita (partially) ✓
- G26: šprical → špricam ✓
- G27: nadreval → nadaljeval (context) ✓
- G28: notakrat → potem ✓

**Failed (8):**
- **G1:** "polnica" NOT fixed (should be "bolnica") - CRITICAL
- **G3:** "uspodbudo" NOT fixed (should be "spodbudo/vzpodbudo")
- **G7:** "vzpodguja" uses "vzbuja" - acceptable variant
- **G17:** "mogo" NOT fully fixed
- **G19:** "sečnem" NOT fixed (should be "začnem")
- **G23:** "prublev" NOT fixed (should be "probam/poskušal")
- **G24:** "nadelujem" NOT fixed (should be "nadaljujem")
- Plus: Keeps many "v bistvu" fillers

### Content (C) - 43/44 passed = 44/45 points

**Passed:** C1-C33, C35-C44 (43 total)

**Failed (1):**
- **C34:** "deset metrov široke" (10m wide stairs) - MISSING

**Notable:** Preserves C30 "hodnik levo-desno" (maverick lost this)

### Hallucinations (H) - 1 found = 8/10 points

- **H1:** "mi zgubimo" (we lose balance) instead of singular
  - Original: "mi zgubimo ravnoteže" (garbled STT)
  - Should be: "zgubim ravnotežje" (I lose balance)
  - Impact: Changes actor from "I" to "we"

### Readability (R) - 4/4 = 15/15 points

- R1: Paragraph breaks ✓
- R2: Sentences flow ✓
- R3: Personal voice ✓
- R4: Coherence ✓

### Length (L) - 94% = 3/5 points

Edge of optimal range (penalty for >95% typical, 94% is borderline).

---

## Score Calculation (T1 v2)

```
Content:       45 × (43/44) - 0     = 43.98 → 44
Grammar:       25 × (20/28) - 0     = 17.86 → 18
Readability:   15 × (4/4)           = 15
Hallucinations: 10 - (1 × 2)        = 8
Length:        94% edge             = 3
───────────────────────────────────────────
TOTAL:                              = 88/100 PASS
```

---

## Key Issues

### 1. G1 Failure (polnica→bolnica)

Llama consistently fails to fix the critical "polnica" → "bolnica" STT error across ALL runs. This is significant because:
- "polnica" is not a real Slovenian word
- "bolnica" (hospital) is clearly intended from context
- Maverick is the ONLY model that fixes this

### 2. Minimal Cleanup (94-98% length)

Llama preserves content excellently but performs minimal cleanup:
- Keeps most "v bistvu" fillers
- Keeps garbled phrases verbatim
- Keeps awkward sentence structures

### 3. "mi zgubimo" Hallucination

The STT captured "mi zgubimo" (we lose) which is grammatically incorrect. Llama keeps it verbatim instead of fixing to "zgubim" (I lose). This creates a first→plural actor change.

---

## Comparison with Maverick

| Aspect | Llama | Maverick |
|--------|-------|----------|
| Consistency | ✓ Excellent (100% pass) | ❌ Poor (60% pass) |
| G1 Fix (bolnica) | ❌ Never | ✓ Always |
| Grammar Score | 18/25 | 23/25 |
| Content Score | 44/45 | 43/45 |
| Reliability | ✓ Production-ready | ❌ Needs retry logic |

---

## Production Recommendation

**Use llama for:**
- Reliable, consistent output
- Maximum content preservation
- Cases where grammar can be fixed in post-processing

**Do NOT use llama for:**
- High-quality grammar cleanup (use maverick with retry)
- Filler word removal (keeps "v bistvu" etc.)

