# meta-llama/llama-4-maverick on dream_v8 ⭐⭐⭐ WINNER

← [Back to dream_v8](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ **NEW WINNER** | **Best Score:** 38/40 (95%) ⭐⭐⭐
**Cache:** `cache/prompt_dream_v8/5beeaea1-967a-4569-9c84-eccad8797b95_meta-llama-llama-4-maverick-17b-128e-instruct/`

**Test Date:** 2025-12-01
**Raw transcription length:** 5051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T5 (temp=1.0) - **38/40** ⭐⭐⭐ **EXCEEDS THRESHOLD**

### Summary Tables

#### Automated Checks

| Config | Temp | Length | Ratio | "Hvala" | Foreign Words | Processing |
|--------|------|--------|-------|---------|---------------|------------|
| T1 | 0.0 | 3969 | 78.58% ✅ | ✅ None | ❌ "приходят" (Russian) | 6.72s |
| T2 | 0.3 | 3907 | 77.35% ✅ | ✅ None | ❌ "приходят" (Russian) | 2.65s |
| T3 | 0.5 | 3565 | 70.58% ⚠️ | ✅ None | ✅ None | 10.80s |
| T4 | 0.8 | 3490 | 69.10% ❌ | ✅ None | ✅ None | 20.39s |
| **T5** | 1.0 | 4106 | **81.29%** ✅ | ✅ None | ✅ None | 21.50s |
| T6 | 1.5 | 2790 | 55.24% ❌ | ✅ None | ✅ None | 19.60s |
| T7 | 2.0 | 2715 | 53.75% ❌ | ✅ None | ✅ None | 20.63s |

#### Detailed Scores

| Config | Temp | Content | Artifacts | Grammar | Readability | **TOTAL** |
|--------|------|---------|-----------|---------|-------------|-----------|
| T1 | 0.0 | 8/10 | 10/10 | 6/10 | 8/10 | **32/40** |
| T2 | 0.3 | 9/10 | 10/10 | 6/10 | 8/10 | **33/40** |
| T3 | 0.5 | 8/10 | 10/10 | 8/10 | 8/10 | **34/40** |
| T4 | 0.8 | 7/10 | 10/10 | 7/10 | 8/10 | **32/40** |
| **T5** | 1.0 | 10/10 | 10/10 | 9/10 | 9/10 | **38/40** ⭐⭐⭐ |
| T6 | 1.5 | 5/10 | 10/10 | 7/10 | 7/10 | **29/40** |
| T7 | 2.0 | 4/10 | 10/10 | 4/10 | 6/10 | **24/40** |

---

## Config Analysis

### T1 (temp=0.0) - 32/40
- **Length:** 3969 chars (78.58%) ✅
- **Content:** Spray detail preserved, but 10m stairs NOT mentioned
- **Grammar:** ❌ "приходят" Russian word instead of "prihajajo"

### T2 (temp=0.3) - 33/40
- **Length:** 3907 chars (77.35%) ✅
- **Content:** All major details preserved, "deset metrov široke" stairs width preserved
- **Grammar:** ❌ "приходят" Russian word

### T3 (temp=0.5) - 34/40
- **Length:** 3565 chars (70.58%) ⚠️
- **Content:** Core narrative preserved, spray detail included
- **Grammar:** ✅ No Russian words! Minor issues only.

### T4 (temp=0.8) - 32/40
- **Length:** 3490 chars (69.10%) ❌ Below threshold
- **Grammar:** ✅ No Russian words, but "stavo" instead of "stavbo"

### T5 (temp=1.0) - 38/40 ⭐⭐⭐ WINNER
- **Length:** 4106 chars (81.29%) ✅
- **Content Accuracy (10/10):** All details preserved, spray detail, "deset metrov široke" stairs, all scenes present
- **Artifact Removal (10/10):** All "Hvala" removed, clean output
- **Grammar Quality (9/10):** ✅ **"bolnica" FIXED!** (only config to fix this), ✅ No Russian words, minor issues only
- **Readability (9/10):** Excellent paragraph structure, natural flow, authentic voice preserved

### T6 (temp=1.5) - 29/40
- **Length:** 2790 chars (55.24%) ❌ Severe over-summarization
- Many details lost

### T7 (temp=2.0) - 24/40
- **Length:** 2715 chars (53.75%) ❌ Severe over-summarization
- Garbled ending: "Tudi se bota oba boriva čes, karkad moj namen"

---

## Key Findings

1. **Winner: T5 (temp=1.0)** - 38/40 (95%) ✅ **EXCEEDS THRESHOLD**
2. **T5 is the ONLY config that fixed "polnica" → "bolnica"**
3. **Russian word bug appears at temp=0.0 and temp=0.3**
4. **High temperatures (1.5, 2.0) cause severe over-summarization**
5. **Temp=1.0 is the sweet spot** - best grammar, best content preservation

---

## Comparison Across Prompts

| Prompt | Best Score | Config | Ratio | Key Issue |
|--------|------------|--------|-------|-----------|
| dream_v5 | 32/40 | T4 | 46% | Over-summarizes |
| dream_v7 | 35/40 | T2 | 69.5% | Russian word bug |
| **dream_v8** | **38/40** | T5 | 81.29% | **None - WINNER** |

**Improvement:** +6 points from dream_v5, +3 points from dream_v7

---

## Production Recommendation

For `meta-llama/llama-4-maverick-17b-128e-instruct`:
- **Prompt:** dream_v8 (single-task, no theme extraction)
- **Temperature:** 1.0
- **Top-p:** null (unset)
- **Expected Score:** 38/40 (95%)
- **Processing Time:** ~21s
- **Length Ratio:** ~81%
