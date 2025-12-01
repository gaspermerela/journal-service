# meta-llama/llama-4-maverick on dream_v7

← [Back to dream_v7](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ Complete | **Best Score:** 35/40 (T2) ⚠️ Below 36/40 threshold
**Cache:** `cache/prompt_dream_v7/5beeaea1-967a-4569-9c84-eccad8797b95_meta-llama-llama-4-maverick-17b-128e-instruct/`

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T2 (temp=0.3) - 35/40 ⚠️ **Below threshold**

| Config | Temp | Length | Ratio | Content | Artifacts | Grammar | Readability | **Total** |
|--------|------|--------|-------|---------|-----------|---------|-------------|-----------|
| T1 | 0.0 | 2730 | 54.0% | 5/10 | 10/10 | 6/10 | 7/10 | **28/40** |
| **T2** | 0.3 | 3511 | 69.5% | 8/10 | 10/10 | 9/10 | 8/10 | **35/40** ⭐ |
| T3 | 0.5 | 3268 | 64.7% | 7/10 | 10/10 | 8/10 | 8/10 | **33/40** |
| T4 | 0.8 | 2963 | 58.7% | 6/10 | 10/10 | 7/10 | 7/10 | **30/40** |
| T5 | 1.0 | 3180 | 63.0% | 6/10 | 10/10 | 8/10 | 8/10 | **32/40** |
| T6 | 1.5 | 3287 | 65.1% | 6/10 | 10/10 | 8/10 | 8/10 | **32/40** |
| T7 | 2.0 | 3491 | 69.1% | 6/10 | 10/10 | 7/10 | 7/10 | **30/40** |

---

## Key Findings

### T1 Issues (temp=0.0)

- ❌ **RUSSIAN WORD BUG:** Uses "bolнища" (Cyrillic) instead of "bolnica"
- ❌ Over-summarizes (54% length)
- This bug appears at low temperatures and is a known maverick issue

### T2 Details (temp=0.3) ⭐

- **Processing Time:** ~20s
- **Length:** 3511 chars (69.5% - just below 70% target)
- ✅ All artifacts removed
- ✅ Excellent grammar (9/10)
- ✅ No Russian word bug at this temperature

### Temperature Stability

Unlike llama-3.3-70b, maverick maintains coherent output even at T7 (temp=2.0), scoring 30/40 without gibberish.

---

## Comparison: dream_v5 vs dream_v7

| Metric | dream_v5 T4 | dream_v7 T2 |
|--------|-------------|-------------|
| Score | 32/40 | 35/40 |
| Length | 46% | 69.5% |
| Winner | dream_v7 | ✅ |

**Interesting:** dream_v7 actually performs BETTER for maverick than dream_v5.

---

## Phase 2 Result

With dream_v8 (simplified single-task prompt), maverick achieves **38/40** at T5 (temp=1.0).

See [dream_v8 results](../prompt_dream_v8/README.md) for details.
