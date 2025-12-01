# llama-3.3-70b-versatile on dream_v8

← [Back to dream_v8](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ Complete | **Best Score:** 36/40 (P4)
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

## CASE 2: Top-p Only (temperature = null)

**Winner:** P4 (top_p=0.7) - **36/40** ⭐ **MEETS THRESHOLD**

### Summary Tables

#### Automated Checks

| Config | top_p | Length | Ratio | "Hvala" | "Zdravstveno" | Processing |
|--------|-------|--------|-------|---------|---------------|------------|
| P1 | 0.1 | 3847 | 76.2% ✅ | ✅ Removed | ✅ Removed | 3.80s |
| P2 | 0.3 | 3950 | 78.2% ✅ | ✅ Removed | ✅ Removed | 3.43s |
| P3 | 0.5 | 4436 | 87.8% ✅ | ✅ Removed | ✅ Removed | 3.74s |
| **P4** | 0.7 | 4130 | 81.8% ✅ | ✅ Removed | ✅ Removed | 4.00s |
| P5 | 0.9 | 3743 | 74.1% ✅ | ✅ Removed | ✅ Removed | 8.76s |
| P6 | 1.0 | 3517 | 69.6% ❌ | ✅ Removed | ✅ Removed | 12.73s |

#### Detailed Scores

| Config | top_p | Content | Artifacts | Grammar | Readability | **TOTAL** |
|--------|-------|---------|-----------|---------|-------------|-----------|
| P1 | 0.1 | 9/10 | 10/10 | 6/10 | 8/10 | **33/40** |
| P2 | 0.3 | 9/10 | 10/10 | 6/10 | 8/10 | **33/40** |
| P3 | 0.5 | 9/10 | 9/10 | 6/10 | 9/10 | **33/40** |
| **P4** | 0.7 | 9/10 | 10/10 | 8/10 | 9/10 | **36/40** ⭐ |
| P5 | 0.9 | 9/10 | 10/10 | 6/10 | 8/10 | **33/40** |
| P6 | 1.0 | 8/10 | 10/10 | 6/10 | 8/10 | **32/40** |

### P* Config Analysis

#### P1-P3 (top_p=0.1-0.5) - 33/40
- **Content:** Good preservation (76-88% ratio)
- **Grammar:** "polnica" not fixed, garbled phrases remain
- **P3 artifact:** "Sem pripravljen" intro

#### P4 (top_p=0.7) - 36/40 ⭐ WINNER
- **Length:** 4130 chars (81.8%) ✅
- **Content:** All details preserved
- **Grammar:** ✅ **"bolnica" FIXED!** (first time for this model)
- **Readability:** Excellent flow, natural voice

#### P5-P6 (top_p=0.9-1.0) - 32-33/40
- **Grammar:** "polnica" NOT fixed (surprisingly)
- **P6:** Slightly below length threshold (69.6%)

### P* Key Finding

**P4 (top_p=0.7) is the ONLY config for llama-3.3-70b that fixes "bolnica"!**

This is significant because:
- No T* config fixed "bolnica" (max score was 35/40)
- P4 achieves 36/40, meeting the threshold
- The fix happens at a specific top_p value (0.7)

---

## Key Findings

1. **Best overall: P4 (top_p=0.7) = 36/40** ⭐ - MEETS threshold!
2. **Best T*: T1/T2/T5 = 35/40** - below threshold
3. **"bolnica" fix:** Only P4 (top_p=0.7) fixes it - unique behavior vs maverick
4. **T3, T5, P3 artifact:** "Sem pripravljen" intro (model responding to prompt)
5. **High temps degrade quality:** T6, T7 severely over-summarize
6. **Fast processing:** ~4s for most configs

---

## Comparison with Maverick

| Model | Best Score | Best Config | "bolnica" Fixed | Key Issue |
|-------|------------|-------------|-----------------|-----------|
| **maverick** | **38/40** ⭐ | T5 (temp=1.0) | ✅ Yes | Russian bug at temp≤0.3 |
| llama-3.3-70b | **36/40** | P4 (top_p=0.7) | ✅ Yes | Unique top_p behavior |

**Verdict:** maverick with dream_v8 remains the best configuration (38/40 vs 36/40).

---

## Production Recommendation

**llama-3.3-70b-versatile CAN be used with dream_v8 prompt (meets threshold).**

- Best score: **36/40** with P4 (top_p=0.7) - meets 36/40 threshold ✅
- Only P4 fixes "polnica" → "bolnica" typo
- maverick still achieves better score (38/40)

If llama-3.3-70b is preferred:
- **Temperature:** null (unset)
- **Top-p:** 0.7 (P4 config)
- **Expected Score:** 36/40 (90%)
- **Processing Time:** ~4s

If fastest config needed (with slight quality tradeoff):
- **Temperature:** 0.0 or 0.3
- **Top-p:** null
- **Expected Score:** 35/40 (87.5%)
- **Processing Time:** ~3.5s
