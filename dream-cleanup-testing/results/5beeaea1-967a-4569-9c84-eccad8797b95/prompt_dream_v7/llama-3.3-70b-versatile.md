# llama-3.3-70b-versatile on dream_v7

← [Back to dream_v7](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ Complete | **Best Score:** 35/40 (T1) ⚠️ Below 36/40 threshold
**Cache:** `cache/prompt_dream_v7/5beeaea1-967a-4569-9c84-eccad8797b95_llama-3.3-70b-versatile/`

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T1 (temp=0.0) - 35/40 ⚠️ **Below threshold**

| Config | Temp | Length | Ratio | Content | Artifacts | Grammar | Readability | **Total** |
|--------|------|--------|-------|---------|-----------|---------|-------------|-----------|
| **T1** | 0.0 | 3243 | 64.2% | 7/10 | 10/10 | 9/10 | 9/10 | **35/40** ⭐ |
| T2 | 0.3 | 4419 | 87.5% | 9/10 | 10/10 | 5/10 | 8/10 | **32/40** |
| T3 | 0.5 | 4544 | 90.0% | 9/10 | 10/10 | 5/10 | 8/10 | **32/40** |
| T4 | 0.8 | 4378 | 86.7% | 9/10 | 10/10 | 5/10 | 8/10 | **32/40** |
| T5 | 1.0 | 3238 | 64.1% | 7/10 | 10/10 | 6/10 | 7/10 | **30/40** |
| T6 | 1.5 | 2498 | 49.5% | 4/10 | 9/10 | 4/10 | 5/10 | **22/40** |
| T7 | 2.0 | 4763 | 94.3% | 1/10 | 2/10 | 1/10 | 1/10 | **5/40** |

---

## Key Findings

### T1 Details (temp=0.0) ⭐

- **Processing Time:** 3.75s
- **Length:** 3243 chars (64.2% - below 70% target)
- ✅ All artifacts removed
- ✅ Uses correct "bolnica", "pritličju"
- ✅ Spray detail preserved: "šprical sprej, ki smrdi"
- ⚠️ Over-summarizes (-2 content accuracy)

### T7 Critical Failure (temp=2.0)

- Contains Russian Cyrillic: "болница" mixed into text
- Made-up words: "korporativnega", "tisočem koridorju"
- Text degenerates into complete nonsense

---

## Trade-off Discovered

| Approach | Temperature | Length | Grammar | Total |
|----------|-------------|--------|---------|-------|
| Better grammar | 0.0 (T1) | 64% ⚠️ | 9/10 | **35/40** |
| Better length | 0.3-0.8 | 87-90% ✅ | 5/10 | **32/40** |

**Conclusion:** dream_v7 forces a trade-off that dream_v5 doesn't have.

---

## Comparison with dream_v5

| Metric | dream_v5 T1 | dream_v7 T1 |
|--------|-------------|-------------|
| Score | **36/40** ✅ | 35/40 ⚠️ |
| Length | 83-86% | 64% |
| Threshold | Met | Not met |

**Recommendation:** Use dream_v5 instead of dream_v7 for this model.
