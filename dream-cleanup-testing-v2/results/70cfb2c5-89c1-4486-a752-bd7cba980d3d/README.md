# Results: 70cfb2c5-89c1-4486-a752-bd7cba980d3d

**Transcription Date:** 2025-12-08
**Raw Length:** 5,013 chars

---

## Summary

**Status:** NOT PRODUCTION READY (without retry logic)

Extended variance testing reveals high non-determinism even at temp=0.0:
- Maverick produces best results (94/100) but has 40% failure rate
- HARD REQUIREMENT prompts are ignored by the model
- Bimodal length distribution in maverick (good or over-summarized, nothing in between)
- Llama 3.3 70B is consistent but performs minimal cleanup

---

## Best Result

| Prompt | Model | Config | Score | Status |
|--------|-------|--------|-------|--------|
| **dream_v18** | maverick | T1_v2 | **94/100** | EXCELLENT |

---

## Prompt Comparison

| Prompt | Best Model | Config | Best | Worst | Range | EXCELLENT% | Key Finding |
|--------|------------|--------|------|-------|-------|------------|-------------|
| [dream_v18](./dream_v18/) | maverick | T1 | **94** | ~60 | 34 pts | 60% | Best score, 40% variance issue |
| [dream_v14](./dream_v14/) | maverick | T1 | 93 | 82 | 11 pts | 40% | HARD REQUIREMENT ignored |
| [dream_v13](./dream_v13/) | maverick | T1 | 93 | 79 | 14 pts | 64% | High variance (23%) |
| [dream_v12](./dream_v12/) | maverick | T1 | 85 | 82 | 3 pts | 0% | Past tense issues |
| [dream_v11_nojson](./dream_v11_nojson/) | maverick | T1 | 86 | - | - | - | Over-compressed (58%) |

---

## dream_v18 Testing (5x3 Runs - Multi-Model)

**Test Type:** Variance testing with 3 models × 5 runs each at temp=0.0

### Model Comparison

| Model | Best Score | Variance | Pass Rate | Key Issue |
|-------|------------|----------|-----------|-----------|
| **maverick-17b** | **94/100** | HIGH (51-84%) | 60% | Over-summarizes 40% of runs |
| llama-3.3-70b | 88/100 | Low (94-98%) | 100% | Minimal cleanup, many grammar errors |
| scout-17b | 89/100 | Low (95-99%) | 100% | Keeps "Hvala" artifact (A1 fail) |

### Maverick Variance (5 Runs)

| Run | Ratio | Status |
|-----|-------|--------|
| v1 | 77.2% | Good |
| **v2** | **84.0%** | **BEST (94/100)** |
| v3 | 51.5% | FAIL |
| v4 | 51.2% | FAIL |
| v5 | 77.7% | Good |

**Key Finding:** Maverick's variance is **architectural** (MoE with 128 experts), not prompt-related. See [MAVERICK_VARIANCE_RESEARCH.md](../../docs/MAVERICK_VARIANCE_RESEARCH.md) for full analysis.

---

## dream_v14 Testing (10 Runs)

**Critical Finding:** Adding HARD REQUIREMENT for 75% minimum length did NOT improve compliance.

| Run | Ratio | Score | Status |
|-----|-------|-------|--------|
| v1 | 89.2% | **93** | EXCELLENT (BEST) |
| v2 | 69.6% | 84 | PASS |
| v3 | 61.7% | 82 | PASS |
| v4 | 91.1% | 89 | VOICE ISSUE |
| v5 | 85.2% | **93** | EXCELLENT |
| v6 | 69.4% | 87 | PASS |
| v7 | 89.9% | **93** | EXCELLENT |
| v8 | 68.8% | 87 | PASS |
| v9 | 91.7% | **93** | EXCELLENT |
| v10 | 63.3% | 83 | PASS |

### Statistics

| Metric | dream_v13 | dream_v14 |
|--------|-----------|-----------|
| Best Score | 93 | 93 |
| Worst Score | 79 | 82 |
| Length Range | 55%-78% | 62%-92% |
| EXCELLENT (>=90) | 64% (9/14) | 40% (4/10) |
| >=75% Length | 64% (9/14) | 50% (5/10) |
| Cyrillic Bug | 7% (1/14) | 0% (0/10) |
| G13 Fixed | 0% | **100%** |

---

## dream_v13 Testing (14 Runs)

**Critical Finding:** Initial 4 runs showed 2.2% variance. Extended 14 runs reveal **23% true variance**.

| Run | Ratio | Score | Status |
|-----|-------|-------|--------|
| v1 | 74.6% | 91 | EXCELLENT |
| v2 | 75.9% | 91 | EXCELLENT |
| v3 | 75.7% | 90 | EXCELLENT |
| v4 | 73.7% | 90 | EXCELLENT |
| v5 | 57.0% | 79 | REVIEW |
| v6 | 74.8% | 85 | **CYRILLIC BUG** |
| v7 | 73.7% | **93** | EXCELLENT (BEST) |
| v8 | 75.7% | 91 | EXCELLENT |
| v9 | 59.3% | 81 | PASS |
| v10 | 75.3% | 91 | EXCELLENT |
| v11 | 61.5% | 86 | PASS |
| v12 | 74.6% | 91 | EXCELLENT |
| v13 | 55.4% | 82 | PASS |
| v14 | 78.4% | 92 | EXCELLENT |

---

## Prompt Evolution

| Version | Key Change | Best Score | >=75% | Result |
|---------|-----------|------------|-------|--------|
| v11_nojson | Baseline (no JSON) | 86 | - | PASS - Over-compressed to 58% |
| v12 | Added >=75% length requirement | 85 | - | PASS - Length fixed, but past tense |
| v13 | Added present tense + OUTPUT FORMAT | 93 | 64% | HIGH VARIANCE - 36% failure rate |
| v14 | Added HARD REQUIREMENT section | 93 | 50% | WORSE - Model ignores requirement |
| **v18** | Explicit preservation rules + multi-model | **94** | 60% | **BEST** - Maverick peak, variance confirmed architectural |

---

## Critical Issues

### 1. HARD REQUIREMENT Prompts Are Ignored

Adding explicit requirements with warnings ("OUTPUT WILL BE REJECTED") has no effect.
The model compresses to 60-70% in 50% of runs regardless of prompt instructions.

### 2. Bimodal Length Distribution

Runs cluster at either 85%+ or 60-70%. No middle ground.
This suggests an early decision point in generation that determines compression level.

### 3. High Variance at temp=0.0

Even with temperature=0.0, the maverick model produces wildly different outputs:
- Some runs achieve 93/100 EXCELLENT
- Other runs compress to 60% with scores in low 80s

### 4. Consistent Failures (All Runs)

- **G21:** "obhodnikov" -> "hodnikov" (never fixed)
- **C23:** Flat areas + corridors detail (always missing)
- **H1:** "smo prisli" hallucination (100% in v14)

### 5. Improvement: G13 Now Fixed

In v14, all runs correctly convert "nazdolj" -> "navzdol".
This was a 100% failure in v13. Likely model training improvement, not prompt.

---

## Recommendations

### For Production

1. **NOT ready** with single-run maverick approach (40% failure rate)
2. **Retry logic required:** Run maverick up to 3 times, accept if length ≥70%
3. **Validation required:**
   - Reject if length < 70%
   - Reject if Cyrillic detected
   - Reject if "Hvala" present
4. **Alternative:** Use llama-3.3-70b for consistency (0% failure, lower quality)

### Key Insight from v18 Testing

**Maverick's variance is architectural, not prompt-related:**
- MoE architecture with 128 experts creates routing instability
- Groq's temp=0 → 1e-8 conversion allows non-determinism
- Floating-point non-associativity in GPU parallel compute
- No prompt modification can fix this - use retry logic instead

See [MAVERICK_VARIANCE_RESEARCH.md](../../docs/MAVERICK_VARIANCE_RESEARCH.md) for full technical analysis.

### Model Selection Guide

| Priority | Model | Strategy |
|----------|-------|----------|
| Max quality | Maverick | 3x retry, accept if ≥70% |
| Consistency | Llama 3.3 70B | Single run, lower grammar score |
| Content only | Scout | Not recommended (keeps artifacts) |

### Specific Fixes Needed

1. Add "obhodnikov -> hodnikov" to STT mishearings (G21)
2. Add instruction against "smo prisli" hallucination (H1)

---

## Next Steps

1. ~~Test different model (llama-3.3-70b-versatile)~~ ✓ Done in v18
2. Implement retry logic with length validation
3. Consider two-pass approach: Llama for content → Maverick for grammar
