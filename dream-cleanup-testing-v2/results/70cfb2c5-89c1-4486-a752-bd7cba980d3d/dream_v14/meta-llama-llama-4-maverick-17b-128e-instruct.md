# maverick on dream_v14

**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Model:** groq-meta-llama/llama-4-maverick-17b-128e-instruct

**Best:** T1_v1 | Score: 93/100 | Status: EXCELLENT

---

## Extended Variance Testing (T1 x 10 runs)

**CRITICAL FINDING:** HARD REQUIREMENT (75% minimum) in prompt did NOT improve compliance. Only 50% of runs meet the threshold.

### Full Results Table

| Run | Chars | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|-------|-------|------|------|------|------|-----|-------|--------|
| T1_v1 | 4472 | 89.2% | 24 | 41 | 15 | 8 | 5 | **93** | EXCELLENT |
| T1_v2 | 3491 | 69.6% | 24 | 36 | 15 | 6 | 3 | **84** | PASS |
| T1_v3 | 3091 | 61.7% | 22 | 34 | 15 | 8 | 3 | **82** | PASS |
| T1_v4 | 4568 | 91.1% | 24 | 37 | 15 | 8 | 5 | **89** | VOICE ISSUE |
| T1_v5 | 4270 | 85.2% | 24 | 41 | 15 | 8 | 5 | **93** | EXCELLENT |
| T1_v6 | 3481 | 69.4% | 24 | 37 | 15 | 8 | 3 | **87** | PASS |
| T1_v7 | 4505 | 89.9% | 24 | 41 | 15 | 8 | 5 | **93** | EXCELLENT |
| T1_v8 | 3447 | 68.8% | 24 | 37 | 15 | 8 | 3 | **87** | PASS |
| T1_v9 | 4597 | 91.7% | 24 | 41 | 15 | 8 | 5 | **93** | EXCELLENT |
| T1_v10 | 3173 | 63.3% | 23 | 36 | 15 | 6 | 3 | **83** | PASS |

### Variance Summary

| Metric | dream_v13 (14 runs) | dream_v14 (10 runs) | Change |
|--------|---------------------|---------------------|--------|
| Length Range | 55.4%-78.4% | 61.7%-91.7% | Wider range |
| Score Range | 79-93 | 82-93 | Slightly better |
| EXCELLENT Rate | 64% (9/14) | 40% (4/10) | **Worse** |
| >=75% Length | 64% (9/14) | 50% (5/10) | **Worse** |
| Cyrillic Bug | 7% (1/14) | 0% (0/10) | **Fixed** |

### Run Categories

**EXCELLENT (>=90):** v1, v5, v7, v9 = 4 runs (40%)
**PASS (80-89):** v2, v3, v4, v6, v8, v10 = 6 runs (60%)
**REVIEW (<80):** None

**Critical Issues:**
- **v4:** Past tense throughout ("Hodil sem", "se je začelo") - major voice penalty (-7)
- **v2, v3, v6, v8, v10:** Below 75% HARD REQUIREMENT (50% failure rate)
- **v3, v10:** Additional H2 hallucination ("gledam navzgor")

---

## Key Improvement: G13 Fixed

**dream_v13 had 100% failure on G13** ("nazdolj" not fixed to "navzdol").

**dream_v14 has 100% success on G13** - all runs correctly use "navzdol".

This is likely due to the model's internal training changes, not the prompt.

---

## Consistent Failures (All 10 Runs)

### Grammar (G) - Common Failures

| Checkpoint | Description | Failure Rate |
|------------|-------------|--------------|
| G21 | "obhodnikov" -> "hodnikov" | 10/10 (100%) |

Note: G13 is now FIXED in all runs (improvement from v13)

### Content (C) - Variable Failures

| Checkpoint | Description | Failure Rate |
|------------|-------------|--------------|
| C23 | Flat areas + corridors mixed with stairs | 10/10 (100%) |
| C30 | "hodnik levo-desno" at landing | 4/10 (40%) |
| C34 | 10m width detail | 6/10 (60%) |
| C36 | Women unbothered by stairs | 5/10 (50%) |

### Hallucinations (H)

| Type | Description | Occurrence |
|------|-------------|------------|
| H1 | "smo prisli" / "Skupaj pridemo" - implies together | 10/10 runs (100%) |
| H2 | "gledam navzgor" - changed women walking to looking up | 2/10 runs (v2, v10) |

---

## Detailed Scoring: Best Run (T1_v1)

```
Config: T1_v1 | Length: 4472 chars (89.2%)

AUTOMATED CHECKS:
[x] No "Hvala" (A1)
[x] No English (G+)
[x] No Cyrillic (G++)
[x] Length: 89.2% optimal

CRITERIA COUNTS:
G_total: 28 | G_failed: 1 (G21) | G_passed: 27
C_total: 44 | C_failed: 2 (C23, C30) | C_passed: 42
H_count: 1 (H1)
R_score: 4/4
Voice: Minor (-3)
Language: OK (0)

CALCULATION:
Content:       45 x (42/44) - 3 = 40 (voice: minor -3)
Grammar:       25 x (27/28) - 0 = 24
Readability:   15 x (4/4)       = 15
Hallucinations: 10 - (1 x 2)    = 8
Length:        5 (89.2% optimal)= 5
-------------------------------------------
TOTAL:                          93/100

STATUS: EXCELLENT
```

### Why v1 is best:
1. **Optimal length** - 89.2% preserves nearly all content
2. **Present tense** - correctly uses present throughout
3. **No Cyrillic** - clean output
4. **Fixed G13** - correctly has "navzdol"

---

## Detailed Scoring: Problem Runs

### T1_v4 (91.1% - Voice Issue)

```
Content:       45 x (39/44) - 7 = 33  <- Major voice penalty!
Grammar:       25 x (27/28) - 0 = 24
Readability:   15 x (4/4)       = 15
Hallucinations: 10 - (1 x 2)    = 8
Length:        5 (91.1% optimal)= 5
-------------------------------------------
TOTAL:                          89/100

STATUS: PASS (but VOICE ISSUE - past tense)

Examples:
- "Sanje so se zacele" (should be "Sanje se zacrejo")
- "Hodil sem" (should be "Hodim")
- "so odpirali omare" (should be "odpiram omare")
```

### T1_v3 (61.7% - Over-compressed)

```
Content:       45 x (36/44) - 3 = 34
Grammar:       25 x (25/28) - 0 = 22
Readability:   15 x (4/4)       = 15
Hallucinations: 10 - (1 x 2)    = 8
Length:        3 (61.7% low)    = 3
-------------------------------------------
TOTAL:                          82/100

STATUS: PASS

Content failures: C7, C18, C23, C25, C30, C34, C36, C44 (8 total)
Over-compressed despite HARD REQUIREMENT in prompt
```

---

## Comparison: v13 vs v14

| Metric | dream_v13 | dream_v14 | Winner |
|--------|-----------|-----------|--------|
| Best Score | 93 | 93 | Tie |
| Worst Score | 79 | 82 | v14 |
| EXCELLENT Rate | 64% | 40% | **v13** |
| >=75% Compliance | 64% | 50% | **v13** |
| Cyrillic Bugs | 7% | 0% | **v14** |
| G13 Fixed | 0% | 100% | **v14** |
| H1 Hallucination | 93% | 100% | **v13** |

**Conclusion:** dream_v14's HARD REQUIREMENT prompt addition:
- Did NOT improve length compliance (worse: 50% vs 64%)
- Did NOT reduce hallucinations (worse: 100% vs 93%)
- Did fix G13 (likely model behavior, not prompt)
- Did eliminate Cyrillic bugs (possibly luck with small sample)

---

## Recommendations

1. **HARD REQUIREMENT ineffective:** The model ignores explicit length requirements
2. **Consider different approach:**
   - Post-processing validation + retry
   - Different model (llama-3.3-70b-versatile)
   - Structured output format
3. **G21 still failing:** Add "obhodnikov -> hodnikov" to explicit STT fixes
4. **H1 universal:** Hallucination "smo prisli" appears in 100% of runs

---

## Appendix: Length Distribution

| Length Bucket | Runs | Rate |
|---------------|------|------|
| 90%+ | v4, v9 | 20% |
| 85-89% | v1, v5, v7 | 30% |
| 75-84% | - | 0% |
| 70-74% | - | 0% |
| 60-69% | v2, v3, v6, v8, v10 | 50% |

**Bimodal distribution:** Runs either preserve 85%+ or compress to 60-70%. No middle ground.

This suggests the model makes an early decision about compression level and maintains it throughout.
