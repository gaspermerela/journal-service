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

## CASE 2: Top-p Only (temperature = null)

**Winner:** P5 (top_p=0.9) - **37/40** ⭐

### Summary Tables

#### Automated Checks

| Config | top_p | Length | Ratio | "Hvala" | Foreign Words | Processing |
|--------|-------|--------|-------|---------|---------------|------------|
| P1 | 0.1 | 4146 | 82.1% ✅ | ✅ None | ❌ "приходят" (Russian) | 4.49s |
| P2 | 0.3 | 4030 | 79.8% ✅ | ✅ None | ❌ "приходят" (Russian) | 3.36s |
| P3 | 0.5 | 4055 | 80.3% ✅ | ✅ None | ❌ "приходят" (Russian) | 16.41s |
| P4 | 0.7 | 2667 | 52.8% ❌ | ✅ None | ❌ "приходят" (Russian) | 19.58s |
| **P5** | 0.9 | 3860 | 76.4% ✅ | ✅ None | ✅ None | 21.98s |
| P6 | 1.0 | 3724 | 73.7% ✅ | ✅ None | ✅ None | 21.82s |

#### Detailed Scores

| Config | top_p | Content | Artifacts | Grammar | Readability | **TOTAL** |
|--------|-------|---------|-----------|---------|-------------|-----------|
| P1 | 0.1 | 9/10 | 10/10 | 5/10 | 8/10 | **32/40** |
| P2 | 0.3 | 9/10 | 10/10 | 5/10 | 8/10 | **32/40** |
| P3 | 0.5 | 9/10 | 10/10 | 5/10 | 8/10 | **32/40** |
| P4 | 0.7 | 6/10 | 10/10 | 5/10 | 7/10 | **28/40** |
| **P5** | 0.9 | 9/10 | 10/10 | 9/10 | 9/10 | **37/40** ⭐ |
| P6 | 1.0 | 9/10 | 10/10 | 7/10 | 9/10 | **35/40** |

### P* Config Analysis

#### P1-P3 (top_p=0.1-0.5) - 32/40
- **Content:** Good preservation (79-82% ratio)
- **Grammar:** ❌ Russian word "приходят" bug (same as T1-T2)
- **"polnica"** not fixed

#### P4 (top_p=0.7) - 28/40
- **Length:** 2667 chars (52.8%) ❌ Over-summarized
- **Grammar:** ❌ Russian word bug + over-summarization penalty

#### P5 (top_p=0.9) - 37/40 ⭐ WINNER
- **Length:** 3860 chars (76.4%) ✅
- **Content:** All details preserved
- **Grammar:** ✅ **"bolnica" FIXED!** ✅ No Russian words
- **Readability:** Excellent flow

#### P6 (top_p=1.0) - 35/40
- **Length:** 3724 chars (73.7%) ✅
- **Grammar:** ✅ No Russian words, but "polnica" NOT fixed

### P* Key Finding

**Russian word bug pattern confirmed:** Appears at top_p ≤ 0.7 (same as temp ≤ 0.3)

| Parameter | Bug Threshold | Safe Values |
|-----------|---------------|-------------|
| Temperature | temp ≤ 0.3 | temp ≥ 0.5 |
| Top-p | top_p ≤ 0.7 | top_p ≥ 0.9 |

---

## Key Findings

1. **Overall Winner: T5 (temp=1.0) = 38/40** ⭐⭐⭐ - best score across all tests
2. **P5 (top_p=0.9) = 37/40** - second best, also fixes "bolnica"
3. **"bolnica" fix requires high randomness:** T5 (temp=1.0) or P5 (top_p=0.9)
4. **Russian word bug pattern:** Appears at low values (temp≤0.3 OR top_p≤0.7)
5. **High values cause over-summarization:** temp≥1.5 OR (top_p=0.7 with temp=null)
6. **Sweet spot:** temp=1.0 with top_p=null (T5 config)

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
