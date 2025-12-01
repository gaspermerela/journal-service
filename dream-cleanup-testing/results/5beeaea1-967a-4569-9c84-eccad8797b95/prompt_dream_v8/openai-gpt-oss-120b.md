# openai/gpt-oss-120b on dream_v8

← [Back to dream_v8](./README.md) | [Back to Index](../README.md)

---

**Status:** ❌ Not Recommended | **Best Score:** 35/40
**Cache:** `cache/prompt_dream_v8/5beeaea1-967a-4569-9c84-eccad8797b95_openai-gpt-oss-120b/`

**Test Date:** 2025-12-01
**Raw transcription length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T2, T3, T4, T6 (tied) - 35/40

### Critical Issue: Over-Summarization

**ALL configs produce output below 70% length threshold.** This is a fundamental model behavior, not fixable via parameters.

### Summary Tables

#### Automated Checks

| Config | Temp | Length | Ratio | "Hvala" | "Zdravstveno" | Processing |
|--------|------|--------|-------|---------|---------------|------------|
| T1 | 0.0 | 2925 | 57.9% ❌ | ✅ Removed | ❌ Kept | 15.44s |
| T2 | 0.3 | 2581 | 51.1% ❌ | ✅ Removed | ✅ Removed | 19.56s |
| T3 | 0.5 | 2466 | 48.8% ❌ | ✅ Removed | ✅ Removed | 18.59s |
| T4 | 0.8 | 2325 | 46.0% ❌ | ✅ Removed | ✅ Removed | 19.06s |
| T5 | 1.0 | 2579 | 51.1% ❌ | ✅ Removed | ❌ Kept | 17.33s |
| T6 | 1.5 | 2476 | 49.0% ❌ | ✅ Removed | ✅ Removed | 19.33s |
| T7 | 2.0 | 2940 | 58.2% ❌ | ✅ Removed | ✅ Removed | 17.40s |

#### Detailed Scores

| Config | Temp | Content | Artifacts | Grammar | Readability | **TOTAL** |
|--------|------|---------|-----------|---------|-------------|-----------|
| T1 | 0.0 | 7/10 | 8/10 | 9/10 | 9/10 | **33/40** |
| **T2** | 0.3 | 7/10 | 10/10 | 9/10 | 9/10 | **35/40** ⭐ |
| **T3** | 0.5 | 7/10 | 10/10 | 9/10 | 9/10 | **35/40** ⭐ |
| **T4** | 0.8 | 7/10 | 10/10 | 9/10 | 9/10 | **35/40** ⭐ |
| T5 | 1.0 | 7/10 | 8/10 | 9/10 | 9/10 | **33/40** |
| **T6** | 1.5 | 7/10 | 10/10 | 9/10 | 9/10 | **35/40** ⭐ |
| T7 | 2.0 | 6/10 | 10/10 | 7/10 | 7/10 | **30/40** |

---

## Config Analysis

### T1 (temp=0.0) - 33/40
- **Length:** 2925 chars (57.9%) ❌ Over-summarized
- **Content:** Missing many details due to compression (-3)
- **Artifacts:** Kept "Zdravstveno, da sem pripravljen" (-2)
- **Grammar:** Excellent - proper paragraphs, clean Slovenian
- **Readability:** Very good structure

### T2 (temp=0.3) - 35/40 ⭐
- **Length:** 2581 chars (51.1%) ❌ Over-summarized
- **Content:** Missing details (-3)
- **Artifacts:** All removed
- **Grammar:** Excellent
- **Readability:** Best paragraph structure

### T3 (temp=0.5) - 35/40 ⭐
- **Length:** 2466 chars (48.8%) ❌ Over-summarized
- **Content:** Missing details (-3)
- **Artifacts:** All removed
- **Grammar:** Excellent
- **Readability:** Very good

### T4 (temp=0.8) - 35/40 ⭐
- **Length:** 2325 chars (46.0%) ❌ Over-summarized
- **Content:** Missing details (-3)
- **Artifacts:** All removed
- **Grammar:** Excellent
- **Readability:** Very good

### T5 (temp=1.0) - 33/40
- **Length:** 2579 chars (51.1%) ❌ Over-summarized
- **Content:** Missing details (-3)
- **Artifacts:** Kept "Zdravstveno, da sem pripravljen" (-2)
- **Grammar:** Excellent
- **Readability:** Very good

### T6 (temp=1.5) - 35/40 ⭐
- **Length:** 2476 chars (49.0%) ❌ Over-summarized
- **Content:** Missing details (-3)
- **Artifacts:** All removed
- **Grammar:** Excellent
- **Readability:** Very good

### T7 (temp=2.0) - 30/40
- **Length:** 2940 chars (58.2%) ❌ Over-summarized
- **Content:** Missing details, some garbled sections (-4)
- **Artifacts:** All removed
- **Grammar:** Some errors ("Grop! Toka bo m...") (-3)
- **Readability:** Degraded (-3)

---

## Key Findings

1. **ALL configs over-summarize** - length ratio 46-58% (threshold: 70%)
2. **Best score: 35/40** - does NOT meet 36/40 threshold
3. **T1, T5 keep "Zdravstveno" artifact** - inconsistent artifact removal
4. **Excellent grammar** - better than llama-3.3-70b and maverick
5. **Good paragraph structure** - best readability of tested models
6. **Slower processing:** ~15-20s per config

---

## Comparison with Other Models on dream_v8

| Model | Best Score | Length Ratio | "bolnica" Fixed | Key Issue |
|-------|------------|--------------|-----------------|-----------|
| **maverick** | **38/40** ⭐ | 81% ✅ | ✅ Yes | Russian bug at temp≤0.3 |
| llama-3.3-70b | 35/40 | 82-88% ✅ | ❌ No | Grammar fixes lacking |
| **gpt-oss-120b** | 35/40 | 46-58% ❌ | N/A | **Over-summarizes** |

---

## Production Recommendation

**Do NOT use openai/gpt-oss-120b for dream cleanup.**

- **Fundamental issue:** Over-summarization is model behavior, not parameter tunable
- All configs produce <60% of original length
- Many dream details lost
- maverick achieves 38/40 with proper length preservation

**Note:** While grammar and readability are excellent, the content loss makes this model unsuitable for dream journaling where preserving details is critical.
