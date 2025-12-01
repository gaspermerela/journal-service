# llama-3.3-70b-versatile on dream_v8

← [Back to dream_v8](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ Complete | **Best Score:** 35/40
**Cache:** `cache/prompt_dream_v8/5beeaea1-967a-4569-9c84-eccad8797b95_llama-3.3-70b-versatile/`

**Test Date:** 2025-12-01
**Raw transcription length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T1, T2, T5 (tied) - 35/40

### Summary Tables

#### Automated Checks

| Config | Temp | Length | Ratio | "Hvala" | "Zdravstveno" | Processing |
|--------|------|--------|-------|---------|---------------|------------|
| T1 | 0.0 | 4466 | 88.4% ✅ | ✅ Removed | ✅ Removed | 3.84s |
| T2 | 0.3 | 4137 | 81.9% ✅ | ✅ Removed | ✅ Removed | 3.73s |
| T3 | 0.5 | 4445 | 88.0% ✅ | ✅ Removed | ✅ Removed | 3.59s |
| T4 | 0.8 | 4248 | 84.1% ✅ | ✅ Removed | ✅ Removed | 3.75s |
| T5 | 1.0 | 3944 | 78.1% ✅ | ✅ Removed | ✅ Removed | 11.06s |
| T6 | 1.5 | 2050 | 40.6% ❌ | ✅ Removed | ✅ Removed | 12.80s |
| T7 | 2.0 | 2073 | 41.0% ❌ | ✅ Removed | ✅ Removed | 31.57s |

#### Detailed Scores

| Config | Temp | Content | Artifacts | Grammar | Readability | **TOTAL** |
|--------|------|---------|-----------|---------|-------------|-----------|
| **T1** | 0.0 | 9/10 | 10/10 | 7/10 | 9/10 | **35/40** ⭐ |
| **T2** | 0.3 | 9/10 | 10/10 | 7/10 | 9/10 | **35/40** ⭐ |
| T3 | 0.5 | 9/10 | 9/10 | 7/10 | 9/10 | **34/40** |
| T4 | 0.8 | 9/10 | 10/10 | 7/10 | 8/10 | **34/40** |
| **T5** | 1.0 | 9/10 | 9/10 | 8/10 | 9/10 | **35/40** ⭐ |
| T6 | 1.5 | 6/10 | 10/10 | 8/10 | 7/10 | **31/40** |
| T7 | 2.0 | 3/10 | 10/10 | 3/10 | 3/10 | **19/40** |

---

## Config Analysis

### T1 (temp=0.0) - 35/40 ⭐
- **Length:** 4466 chars (88.4%) ✅
- **Content:** All details preserved, no hallucinations
- **Artifacts:** All "Hvala" removed, "Zdravstveno" removed
- **Grammar:** "polnica" not fixed to "bolnica", some garbled phrases remain ("ta ljena vzgor", "prublev")
- **Readability:** Good flow, natural voice preserved

### T2 (temp=0.3) - 35/40 ⭐
- **Length:** 4137 chars (81.9%) ✅
- **Content:** All details preserved
- **Artifacts:** Clean
- **Grammar:** Similar issues to T1 - "polnica" not fixed
- **Readability:** Slightly more polished than T1

### T3 (temp=0.5) - 34/40
- **Length:** 4445 chars (88.0%) ✅
- **Content:** All details preserved
- **Artifacts:** Has "Sem pripravljen" intro (model artifact) (-1)
- **Grammar:** "polnica" not fixed
- **Readability:** Good flow

### T4 (temp=0.8) - 34/40
- **Length:** 4248 chars (84.1%) ✅
- **Content:** Mostly preserved, some minor direction changes ("navzgor" instead of "navzdol")
- **Artifacts:** Clean
- **Grammar:** "polnica" not fixed, added "priđem" (Croatian form)
- **Readability:** Slightly less natural flow

### T5 (temp=1.0) - 35/40 ⭐
- **Length:** 3944 chars (78.1%) ✅
- **Content:** All key details preserved
- **Artifacts:** Has "Sem pripravljen" intro (-1)
- **Grammar:** Better than lower temps - cleaner sentences
- **Readability:** Excellent flow

### T6 (temp=1.5) - 31/40
- **Length:** 2050 chars (40.6%) ❌ **OVER-SUMMARIZED**
- **Content:** Severe summarization, many details lost (-4)
- **Artifacts:** Clean
- **Grammar:** Better quality in what remains
- **Readability:** Choppy due to compression

### T7 (temp=2.0) - 19/40
- **Length:** 2073 chars (41.0%) ❌
- **Content:** Severely garbled, barely coherent (-7)
- **Artifacts:** Clean
- **Grammar:** Nearly unreadable gibberish (-7)
- **Readability:** Unusable (-7)

---

## Key Findings

1. **Best score: 35/40** - does NOT meet 36/40 threshold
2. **Three-way tie:** T1, T2, T5 all scored 35/40
3. **"polnica" NOT fixed** in any config (unlike maverick at temp=1.0)
4. **T3, T5 artifact:** "Sem pripravljen" intro (model responding to prompt)
5. **High temps degrade quality:** T6, T7 severely over-summarize
6. **Faster processing:** ~4s for T1-T4 vs ~11-31s for T5-T7

---

## Comparison with Maverick

| Model | Best Score | Best Config | "bolnica" Fixed | Key Issue |
|-------|------------|-------------|-----------------|-----------|
| **maverick** | **38/40** ⭐ | T5 (temp=1.0) | ✅ Yes | Russian bug at temp≤0.3 |
| llama-3.3-70b | 35/40 | T1/T2/T5 | ❌ No | Grammar fixes lacking |

**Verdict:** maverick with dream_v8 remains the best configuration.

---

## Production Recommendation

**Do NOT use llama-3.3-70b-versatile with dream_v8 prompt.**

- Best score (35/40) is below 36/40 threshold
- Does not fix "polnica" → "bolnica" typo
- maverick achieves 38/40 with same prompt

If llama-3.3-70b must be used:
- **Temperature:** 0.0 or 0.3 (fastest, most consistent)
- **Top-p:** null
- **Expected Score:** 35/40 (87.5%)
- **Processing Time:** ~4s
