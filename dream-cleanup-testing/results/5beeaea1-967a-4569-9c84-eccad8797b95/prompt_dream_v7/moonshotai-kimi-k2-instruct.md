# moonshotai/kimi-k2-instruct on dream_v7

← [Back to dream_v7](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ Complete | **Best Score:** 30/40 (T1) ❌ Below threshold
**Cache:** `cache/prompt_dream_v7/5beeaea1-967a-4569-9c84-eccad8797b95_moonshotai-kimi-k2-instruct/`

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T1 (temp=0.0) - 30/40 ❌ **Below threshold**

| Config | Temp | Length | Ratio | Content | Artifacts | Grammar | Readability | **Total** |
|--------|------|--------|-------|---------|-----------|---------|-------------|-----------|
| **T1** | 0.0 | ~2807 | 55.6% | 5/10 | 10/10 | 7/10 | 8/10 | **30/40** ⭐ |
| T2 | 0.3 | ~2576 | 51.0% | 5/10 | 10/10 | 6/10 | 7/10 | **28/40** |
| T3 | 0.5 | ~2480 | 49.1% | 4/10 | 10/10 | 6/10 | 7/10 | **27/40** |
| T4 | 0.8 | ~2340 | 46.3% | 4/10 | 10/10 | 6/10 | 7/10 | **27/40** |
| T5 | 1.0 | ~2620 | 51.9% | 5/10 | 10/10 | 6/10 | 7/10 | **28/40** |
| T6 | 1.5 | FAILED | - | - | - | - | - | **N/A** |
| T7 | 2.0 | GIBBERISH | - | 0/10 | 0/10 | 0/10 | 0/10 | **0/40** |

---

## Key Findings

### Consistent Over-summarization

ALL working configs (T1-T5) produce 46-56% of original length (target: 70-95%).

### T1 Details (temp=0.0)

- **Processing Time:** ~8s
- **Length:** ~2807 chars (55.6%)
- ✅ All artifacts removed
- ⚠️ Over-summarizes significantly

### T6/T7 Failures

- **T6 (temp=1.5):** Invalid JSON - failed to parse
- **T7 (temp=2.0):** Complete gibberish, unreadable output

---

## Comparison with dream_v5

| Metric | dream_v5 T2 | dream_v7 T1 |
|--------|-------------|-------------|
| Score | 29/40 | 30/40 |
| Status | Both below threshold |

**Conclusion:** Similar performance to dream_v5 - both prompts produce over-summarized output with this model.

**Recommendation:** ❌ Do not use moonshotai/kimi-k2-instruct for dream cleanup.
