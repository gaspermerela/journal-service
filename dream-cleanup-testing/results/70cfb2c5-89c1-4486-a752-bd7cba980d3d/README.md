# Results: 70cfb2c5-89c1-4486-a752-bd7cba980d3d

**Transcription Provider:** Groq (Whisper)
**Transcription Date:** 2025-12-08
**Raw Length:** 5,013 chars

---

## Summary

**Status:** NOT PRODUCTION READY (without safeguards)

Extended variance testing (15 runs) reveals severe non-determinism at temp=0.0:
- Maverick produces best results (94/100) but has **60% failure rate**
- HARD REQUIREMENT prompts are completely ignored
- Trimodal length distribution (good/bad/severe)

---

## Best Result

| Prompt | Model | Config | Score | Pass Rate |
|--------|-------|--------|-------|-----------|
| **dream_v18** | maverick | T1 v2 | **94/100** | 40% (6/15) |

---

## Prompt Comparison

| Prompt | Best Model | Best | Worst | Pass Rate | Key Finding |
|--------|------------|------|-------|-----------|-------------|
| [dream_v18](./dream_v18/) | maverick | **94** | ~36 | 40% (6/15) | **60% failure rate** |
| [dream_v14](./dream_v14/) | maverick | 93 | 82 | 40% | HARD REQUIREMENT ignored |
| [dream_v13](./dream_v13/) | maverick | 93 | 79 | 64% | High variance (23%) |
| [dream_v12](./dream_v12/) | maverick | 85 | 82 | - | Past tense issues |
| [dream_v11_nojson](./dream_v11_nojson/) | maverick | 86 | - | - | Over-compressed (58%) |

---

## dream_v18 Testing (Extended)

**Test Type:** Extended variance testing - 15x maverick + 5x llama + 5x scout

### Model Comparison

| Model | Runs | Best Score | Pass Rate | Key Issue |
|-------|------|------------|-----------|-----------|
| **maverick-17b** | 15 | **94/100** | **40%** | 60% failure rate |
| llama-3.3-70b | 5 | 88/100 | 100% | Minimal cleanup |
| scout-17b | 5 | 89/100 | 100% | Keeps "Hvala" artifact |

### Maverick Variance (15 Runs)

| Outcome | Runs | Percentage | Length Range |
|---------|------|------------|--------------|
| Pass (70-95%) | 6 | 40% | 73-86% |
| Fail (60-69%) | 3 | 20% | 61-64% |
| Severe (<60%) | 6 | **40%** | 36-52% |

**Key Finding:** Maverick's variance is **architectural** (MoE with 128 experts), not prompt-related. See [MAVERICK_VARIANCE_RESEARCH.md](../../docs/MAVERICK_VARIANCE_RESEARCH.md).

---

## Critical Issues

### 1. 60% Failure Rate

Extended testing reveals the true failure rate:
- Original 5 runs: 40% failure (2/5)
- Extended 10 runs: 70% failure (7/10)
- **Total 15 runs: 60% failure (9/15)**

### 2. Severe Over-Summarization

40% of runs produce outputs below 50% length:
- Lost 50%+ of original content
- Combined multiple scenes
- Missing specific details (numbers, measurements)

### 3. HARD REQUIREMENT Prompts Ignored

Adding explicit requirements ("OUTPUT WILL BE REJECTED") has zero effect on compliance.

---

## Recommendations

### For Production

1. **Retry logic required:** Run maverick up to 3 times, accept if length ≥70%
2. **Validation required:** Reject if length < 70%, Cyrillic detected, or "Hvala" present
3. **Alternative:** Use llama-3.3-70b for consistency (88/100, 0% failure)

### Model Selection

| Priority | Model | Strategy |
|----------|-------|----------|
| Max quality | Maverick | 3x retry, accept if ≥70% |
| Consistent | Llama 3.3 70B | Single run, acceptable quality |
| Avoid | Scout | Keeps "Hvala" artifacts |

---

## Next Steps

1. ~~Extended variance testing~~ ✓ Done (15 runs)
2. Test chunking approach on this transcription
3. Implement retry logic with length validation
