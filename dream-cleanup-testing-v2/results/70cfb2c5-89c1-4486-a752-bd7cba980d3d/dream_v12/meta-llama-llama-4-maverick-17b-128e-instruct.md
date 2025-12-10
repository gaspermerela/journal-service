# maverick on dream_v12

**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Model:** groq-meta-llama/llama-4-maverick-17b-128e-instruct

**Best:** T1_v1 | Score: 85/100 | Status: PASS

---

## Prompt Change

dream_v12 adds explicit length requirement:
```
⚠️ Cleaned text MUST be at least 75% of the original length.
```

---

## Variance Testing (T1 × 4 runs)

**Key finding:** Even with temperature=0.0, model produces significant variance in output length (74.9%-82.4%) and quality (82-85 points).

| Run | Chars | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|-------|-------|------|------|------|------|-----|-------|--------|
| T1_v1 | 4133 | 82.4% | 22 | 37 | 15 | 6 | 5 | **85** | PASS |
| T1_v2 | 3755 | 74.9% | 22 | 34 | 11 | 10 | 5 | **82** | PASS |
| T1_v3 | 3863 | 77.1% | 22 | 35 | 11 | 10 | 5 | **83** | PASS |
| T1_v4 | 4128 | 82.3% | 22 | 35 | 11 | 10 | 5 | **83** | PASS |

### Variance Summary

| Metric | Min | Max | Range |
|--------|-----|-----|-------|
| Length | 74.9% | 82.4% | 7.5% |
| Score | 82 | 85 | 3 pts |
| C_passed | 40/44 | 43/44 | 3 |

**Note:** All runs use temperature=0.0, yet produce different outputs. This is likely due to:
1. Groq's infrastructure (load balancing, different nodes)
2. Floating-point non-determinism in GPU inference

---

## Comparison: dream_v11_nojson vs dream_v12

| Metric | v11 | v12 (best) | v12 (avg) | Delta |
|--------|-----|------------|-----------|-------|
| **Total** | 86 | 85 | 83 | -1 to -3 |
| Content | 41 | 37 | 35 | -4 to -6 |
| Grammar | 23 | 22 | 22 | -1 |
| Length | 1 | 5 | 5 | **+4** |
| C_passed | 40/44 | 43/44 | 41/44 | +1 to +3 |

**Key insight:** Length constraint worked - more content preserved. But model switched to past tense, losing 7 points on voice penalty consistently across all runs.

---

## Failures Summary (Common across runs)

### Grammar (G) - 3 failures (consistent)

- **G13:** "nazdolj" ❌ (should be "navzdol")
- **G20:** "predem do obhodnikov" ❌ (should be "pridem do hodnikov")
- **G21:** "obhodnikov" ❌ (should be "hodnikov")

### Content (C) - Variable failures

**Always missing:**
- **C23:** Flat areas + corridors mixed with stairs
  - Original: "niso bile tako samo stopnice ampak le so neki čas stopnice pa je bilo malo spet ravnine"
  - Output: Not mentioned (in any run)

**Variable (present in v1, missing in v2-v4):**
- **C30:** "hodnik levo-desno" at landing
- **C34:** 10m width detail

**Voice penalty (-7):** All runs use past tense throughout ("Hodil sem", "sem hotel", "sem šel") instead of required present tense.

### Content NOW PRESERVED (vs v11)

- **C10:** Cabinet misunderstanding - big doors vs small compartments ✅
- **C26:** "napol tek nazdolj" (half-running down) ✅

### Hallucinations (H)

**T1_v1:** 2 found
- H1: "smo prišli" - implies they walked together
- H2: "vljudno nekakšna zemlja" - "vljudno" makes no sense

**T1_v2/v3/v4:** 0 hallucinations detected
- "vljudno" appears as garbled text but doesn't add meaning

### Readability (R)

**T1_v1:** 4/4 (full marks)
**T1_v2/v3/v4:** 3/4 (R1 fails - paragraph breaks via newlines, not `<break>` markers)

### Artifacts

- **A2:** "Here is the cleaned Slovenian dream transcription:" header (all runs)
- **A3:** "v bistvu" filler appears in some runs

---

## Detailed Scoring Breakdown

### T1_v1 (Best run)
```
Content:       45 × (43/44) - 7 = 37
Grammar:       25 × (25/28) - 0 = 22
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (2 × 2)    = 6
Length:        5 (82.4% optimal)= 5
─────────────────────────────────────
TOTAL:                          85/100
```

### T1_v2
```
Content:       45 × (40/44) - 7 = 34
Grammar:       25 × (25/28) - 0 = 22
Readability:   15 × (3/4)       = 11
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (74.9% optimal)= 5
─────────────────────────────────────
TOTAL:                          82/100
```

### T1_v3
```
Content:       45 × (41/44) - 7 = 35
Grammar:       25 × (25/28) - 0 = 22
Readability:   15 × (3/4)       = 11
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (77.1% optimal)= 5
─────────────────────────────────────
TOTAL:                          83/100
```

### T1_v4
```
Content:       45 × (41/44) - 7 = 35
Grammar:       25 × (25/28) - 0 = 22
Readability:   15 × (3/4)       = 11
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (82.3% optimal)= 5
─────────────────────────────────────
TOTAL:                          83/100
```

---

## Recommendations

1. **Fix voice/tense:** Add stronger instruction for present tense - model consistently defaults to past tense
2. **Remove meta-comments:** Add instruction to not include headers like "Here is the cleaned..."
3. **Accept variance:** With temp=0.0 still producing 7.5% length variance, consider running multiple attempts and selecting best
4. **Test other configs:** T2-T3 might produce more consistent present tense (or worse variance)
