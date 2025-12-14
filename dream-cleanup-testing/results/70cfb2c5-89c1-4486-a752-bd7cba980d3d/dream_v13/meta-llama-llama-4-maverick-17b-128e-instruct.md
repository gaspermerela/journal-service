# maverick on dream_v13

**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Model:** groq-meta-llama/llama-4-maverick-17b-128e-instruct

**Best:** T1_v7 | Score: 93/100 | Status: EXCELLENT

---

## Extended Variance Testing (T1 × 14 runs)

**CRITICAL FINDING:** Initial 4 runs showed 2.2% variance, but extended testing (14 runs) reveals **true variance is 23%**.

### Full Results Table

| Run | Chars | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|-------|-------|------|------|------|------|-----|-------|--------|
| T1_v1 | 3740 | 74.6% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v2 | 3806 | 75.9% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v3 | 3796 | 75.7% | 23 | 39 | 15 | 8 | 5 | **90** | EXCELLENT |
| T1_v4 | 3695 | 73.7% | 22 | 40 | 15 | 8 | 5 | **90** | EXCELLENT |
| T1_v5 | 2858 | 57.0% | 23 | 34 | 15 | 6 | 1 | **79** | REVIEW |
| T1_v6 | 3748 | 74.8% | 18 | 39 | 15 | 8 | 5 | **85** | CYRILLIC BUG |
| T1_v7 | 3694 | 73.7% | 23 | 40 | 15 | 10 | 5 | **93** | EXCELLENT |
| T1_v8 | 3794 | 75.7% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v9 | 2974 | 59.3% | 23 | 36 | 15 | 6 | 1 | **81** | PASS |
| T1_v10 | 3777 | 75.3% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v11 | 3085 | 61.5% | 23 | 37 | 15 | 8 | 3 | **86** | PASS |
| T1_v12 | 3738 | 74.6% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v13 | 2777 | 55.4% | 23 | 35 | 15 | 8 | 1 | **82** | PASS |
| T1_v14 | 3931 | 78.4% | 23 | 41 | 15 | 8 | 5 | **92** | EXCELLENT |

### Variance Summary

| Metric | Initial 4 Runs | Extended 14 Runs | Finding |
|--------|----------------|------------------|---------|
| Length Range | 73.7%-75.9% | 55.4%-78.4% | **23% variance** |
| Score Range | 90-91 | 79-93 | **14 pt variance** |
| EXCELLENT Rate | 100% (4/4) | 64% (9/14) | **36% failure rate** |
| ≥70% Length | 100% | 64% (9/14) | **36% over-compress** |

### Run Categories

**EXCELLENT (≥90):** v1, v2, v3, v4, v7, v8, v10, v12, v14 = 9 runs (64%)
**PASS (80-89):** v6, v9, v11, v13 = 4 runs (29%)
**REVIEW (70-79):** v5 = 1 run (7%)

**Critical Issues:**
- **v6:** Contains Cyrillic characters ("приходят") - model bug, G++ penalty -5
- **v5, v9, v13:** Over-compressed below 60% - severe content loss
- **v11:** Compressed to 61.5% - moderate content loss

---

## Critical Bug: Cyrillic Characters in v6

**T1_v6 contains Russian/Cyrillic words:**
- `preden ljudje приходят v službo` - Russian "приходят" (they come)
- `pridем do obhodnikov` - Cyrillic letter "е" in "pridem"

This is a severe model bug. Even though v6 scores 85, it is **UNACCEPTABLE for production**.

---

## Failures Analysis

### Grammar (G) - Common Failures

| Checkpoint | Description | Failure Rate |
|------------|-------------|--------------|
| G13 | "nazdolj" → "navzdol" | 14/14 (100%) |
| G21 | "obhodnikov" → "hodnikov" | 14/14 (100%) |

### Content (C) - Variable Failures

| Checkpoint | Description | Failure Rate |
|------------|-------------|--------------|
| C23 | Flat areas + corridors mixed with stairs | 14/14 (100%) |
| C30 | "hodnik levo-desno" at landing | 7/14 (50%) |
| C34 | 10m width detail | 6/14 (43%) |
| C36 | Women unbothered by stairs | 4/14 (29%) |

**Over-compressed runs (v5, v9, v11, v13) have additional failures:**
- C6: Spray action detail
- C7: Sound "speaks" detail
- C18: Space transformation
- C25: Fear of being seen (Scene 7)

### Hallucinations (H)

| Type | Description | Occurrence |
|------|-------------|------------|
| H1 | "smo prišli" / "Skupaj pridemo" - implies together | 13/14 runs |
| H2 | "gledam navzgor" - changed women walking to looking up | 2/14 runs (v5, v9) |

**Best run (v7):** No hallucinations detected - uses "Prišla je" (she came) separately.

### Artifacts

| Artifact | Presence |
|----------|----------|
| "Hvala" | 0/14 (all removed) |
| "v bistvu" filler | 3/14 (v3, v8, v14) |
| Header artifact | 0/14 (none) |
| Cyrillic chars | 1/14 (v6 only) |

---

## Detailed Scoring: Best Run (T1_v7)

```
Config: T1_v7 | Length: 3694 chars (73.7%)

AUTOMATED CHECKS:
[✓] No "Hvala" (A1)
[✓] No English (G+)
[✓] No Cyrillic (G++)
[✓] Length: 73.7% optimal

CRITERIA COUNTS:
G_total: 28 | G_failed: 2 (G13, G21) | G_passed: 26
C_total: 44 | C_failed: 2 (C23, C30) | C_passed: 42
H_count: 0
R_score: 4/4
Voice: Minor (-3)
Language: OK (0)

CALCULATION:
Content:       45 × (42/44) - 3 = 40
Grammar:       25 × (26/28) - 0 = 23
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (73.7% optimal)= 5
─────────────────────────────────────
TOTAL:                          93/100

STATUS: EXCELLENT
```

### Why v7 is best:
1. **No hallucinations** - correctly describes meeting woman separately
2. **Clean output** - no "v bistvu" artifacts
3. **No Cyrillic** - unlike v6
4. **Optimal length** - 73.7% preserves content without over-compression

---

## Detailed Scoring: Worst Runs

### T1_v5 (57.0% - Over-compressed)

```
Content:       45 × (36/44) - 3 = 34
Grammar:       25 × (26/28) - 0 = 23
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (2 × 2)    = 6
Length:        1 (57.0% low)    = 1
─────────────────────────────────────
TOTAL:                          79/100

STATUS: REVIEW

Content failures: C6, C7, C18, C23, C25, C30, C34, C36 (8 total)
Hallucinations: H1 (changed actor), H2 (looking up vs women walking)
```

### T1_v6 (74.8% - Cyrillic Bug)

```
Content:       45 × (41/44) - 3 = 39
Grammar:       25 × (26/28) - 5 = 18  ← G++ Cyrillic penalty!
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (1 × 2)    = 8
Length:        5 (74.8% optimal)= 5
─────────────────────────────────────
TOTAL:                          85/100

STATUS: PASS (but UNACCEPTABLE - Cyrillic)
```

---

## Comparison: Initial vs Extended Testing

| Metric | Initial (v1-v4) | Extended (v5-v14) | Combined (v1-v14) |
|--------|-----------------|-------------------|-------------------|
| Best Score | 91 | 93 | **93** |
| Worst Score | 90 | 79 | **79** |
| Score Variance | 1 pt | 14 pts | **14 pts** |
| Length Variance | 2.2% | 23% | **23%** |
| EXCELLENT Rate | 100% | 50% | **64%** |
| Cyrillic Issues | 0 | 1 | **1** |

**Conclusion:** Initial 4 runs were statistically lucky. True model behavior shows:
- 36% of runs over-compress below 70%
- 23% length variance at temp=0.0
- Occasional Cyrillic character injection (model bug)

---

## Recommendations

1. **NOT production ready:** 36% failure rate is too high
2. **Consider retry logic:** Run 2-3 times, take best result by length
3. **Add Cyrillic detection:** Reject outputs containing Cyrillic chars
4. **Prompt improvements needed:**
   - Add "nazdolj→navzdol" to STT mishearings
   - Add "obhodnikov→hodnikov" to STT mishearings
   - Add stronger length enforcement or validation
   - Add instruction against "smo prišli" hallucination

---

## Appendix: All Run Details

### Over-compressed Runs (L < 70%)

| Run | Ratio | Key Losses | Score |
|-----|-------|------------|-------|
| v5 | 57.0% | C6, C7, C18, C23, C25, C30, C34, C36 | 79 |
| v9 | 59.3% | C23, C30, C34, C36 + H2 | 81 |
| v11 | 61.5% | C23, C30, C36 | 86 |
| v13 | 55.4% | C6, C7, C18, C23, C25, C30, C34, C36 | 82 |

### Good Runs (L ≥ 70%)

| Run | Ratio | Failures | Score | Notes |
|-----|-------|----------|-------|-------|
| v1 | 74.6% | C23, C36 | 91 | - |
| v2 | 75.9% | C23, C34 | 91 | - |
| v3 | 75.7% | C23, C30 | 90 | Has "v bistvu" |
| v4 | 73.7% | C23 | 90 | - |
| v6 | 74.8% | C18, C23, C30 | 85 | **CYRILLIC BUG** |
| v7 | 73.7% | C23, C30 | **93** | **BEST - No H** |
| v8 | 75.7% | C23, C30 | 91 | Has "v bistvu" |
| v10 | 75.3% | C23, C36 | 91 | Has C30 ✓ |
| v12 | 74.6% | C23, C34 | 91 | Has C30 ✓ |
| v14 | 78.4% | C23 | 92 | Has "v bistvu" |
