# openai/gpt-oss-120b on dream_v7

← [Back to dream_v7](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ Complete | **Best Score:** 35/40 (T1) ⚠️ Below 36/40 threshold
**Cache:** `cache/prompt_dream_v7/5beeaea1-967a-4569-9c84-eccad8797b95_openai-gpt-oss-120b/`

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T1 (temp=0.0) - 35/40 ⚠️ **Below threshold**

**Key Finding:** This model **consistently over-summarizes** - ALL configs below 70% target length.

| Config | Temp | Length | Ratio | Content | Artifacts | Grammar | Readability | **Total** |
|--------|------|--------|-------|---------|-----------|---------|-------------|-----------|
| **T1** | 0.0 | ~2621 | 51.9% | 7/10 | 10/10 | 9/10 | 9/10 | **35/40** ⭐ |
| T2 | 0.3 | ~2674 | 52.9% | 7/10 | 10/10 | 8/10 | 9/10 | **34/40** |
| T3 | 0.5 | ~2511 | 49.7% | 6/10 | 10/10 | 8/10 | 8/10 | **32/40** |
| T4 | 0.8 | ~2738 | 54.2% | 7/10 | 10/10 | 8/10 | 9/10 | **34/40** |
| T5 | 1.0 | ~2730 | 54.0% | 7/10 | 10/10 | 7/10 | 8/10 | **32/40** |
| T6 | 1.5 | ~3144 | 62.2% | 5/10 | 9/10 | 7/10 | 7/10 | **28/40** |
| T7 | 2.0 | ~2896 | 57.3% | 6/10 | 9/10 | 5/10 | 6/10 | **26/40** |

---

## Key Findings

### T1 Details (temp=0.0) ⭐

- **Processing Time:** 8.42s
- **Length:** ~2621 chars (51.9% - moderate over-summarization)
- ✅ All artifacts removed perfectly
- ✅ Excellent clean Slovenian, uses "pritličju"
- ✅ Spray detail preserved: "sprijem neko vrsto spreja"
- ⚠️ Over-summarization penalty (-2 content accuracy)

**Note:** T1 produces the cleanest Slovenian of all models tested with dream_v7.

### T6 Critical Issue (temp=1.5)

- ❌ **HALLUCINATION:** "medtem ko se pod njima razprostira ognjeno nebo" (fiery sky) - NOT IN ORIGINAL!
- ❌ **TIMING CHANGED:** "okoli šele desetih" instead of "štirih petih"

### T7 Issues (temp=2.0)

- Garbled text: "Strežljivka iz dneva", "levoprosojna vrata"
- Gender change: "ne bi smela biti" (feminine instead of masculine)
- Uses "gyroskop" (English spelling) instead of "giroskop"

---

## Summary

All configs over-summarize (50-62% of original length vs 70-95% target), but T1 produces excellent grammar quality (9/10).

**Recommendation:** Use dream_v5 instead - achieves 33/40 with similar over-summarization but no regression.
