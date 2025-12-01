# Cleanup Analysis: 5beeaea1-967a-4569-9c84-eccad8797b95

**Date Started:** 2025-11-29
**Last Updated:** 2025-12-01
**Status:** Phase 2 - Testing `dream_v8` prompt (simplified, no theme extraction)

---

## Best Result Summary

### Overall Winner (Phase 2) ⭐⭐⭐
| Field | Value |
|-------|-------|
| **Best Config** | **T5 (temperature=1.0, top_p=null)** |
| Best Model | meta-llama/llama-4-maverick-17b-128e-instruct |
| Best Prompt | **dream_v8** (version 1, prompt_id: 390) |
| **Final Score** | **38/40 (95%)** ⭐⭐⭐ |
| Processing Time | ~21.5s |
| Length Ratio | 81.29% |
| **Key Achievement** | **Only config that fixed "polnica" → "bolnica"** |

### Previous Winner (Phase 1)
| Field | Value |
|-------|-------|
| Best Config | T1 (temperature=0.0, top_p=null) |
| Best Model | llama-3.3-70b-versatile |
| Best Prompt | dream_v5 (version 2, prompt_id: 378) |
| Final Score | 36/40 (90%) |

**Status:** ✅ **EXCEEDS STOPPING CRITERIA** (38/40 > 36/40 threshold)

---

## Model Comparison (All Tested Models)

| Model | Prompt | Prompt Type | Best Score | Status | Best Config | Length Ratio | JSON Success | Speed | Key Issue |
|-------|--------|-------------|------------|--------|-------------|--------------|--------------|-------|-----------|
| **meta-llama/llama-4-maverick** | **dream_v8** | **Single-task** ✨ | **38/40** ⭐⭐⭐ | ✅ **NEW WINNER** | T5 (temp=1.0) | **81.29%** ✅ | 100% (7/7) | ~21s | None - **fixed "bolnica"** |
| llama-3.3-70b-versatile | dream_v5 | Multi-task | 36/40 ⭐ | ✅ Previous Winner | T1 (temp=0.0) | 83.8% ✅ | 86% (6/7) | 4-5s | None |
| openai/gpt-oss-120b | dream_v5 | Multi-task | 33/40 | ❌ Not Recommended | T3 (temp=0.5) | 45.8% ❌ | 100% | 5-6s | Over-summarizes |
| moonshotai/kimi-k2-instruct | dream_v5 | Multi-task | 29/40 | ❌ Not Recommended | T2 (temp=0.3) | 51.5% | 71% | 5-10s | Hallucinations |
| qwen/qwen3-32b | dream_v7 | Multi-task | 0/40 | ❌ Not Recommended | N/A | N/A | 0% | 80-100s | `<think>` mode breaks JSON |

**Legend:**
- ✅ **NEW WINNER**: Exceeds 38/40 threshold with excellent content preservation
- ✅ Previous Winner: Met 36/40 threshold
- ❌ Not Recommended: Does not meet quality requirements

**⚠️ IMPORTANT: What is "Simplified Prompt"?**

The winning configuration uses **dream_v8**, a simplified prompt that **removes all theme/emotion/character extraction** - the model only outputs `cleaned_text`. Previous prompts (v5, v7) required multi-task output: cleaned text + themes + emotions + characters + locations.

**Key Insights:**
1. **maverick + dream_v8 + temp=1.0 achieves 38/40** - best result so far, 2 points above previous winner
2. **maverick is the ONLY model to fix "polnica" → "bolnica"** grammar error
3. **🎯 Simplified single-task prompt (dream_v8) unlocked maverick's potential** - removing analysis section improved score from 35/40 to 38/40 (+3 points)
4. **Temperature=1.0 is optimal for maverick** - lower temps introduce Russian word bug, higher temps over-summarize
5. **qwen3-32b unusable** - `<think>` reasoning mode breaks JSON parsing completely

**Conclusion:** For dream cleanup, a **single-task prompt (text only)** with maverick outperforms multi-task prompts with any model.

---

## Source Data

→ [source-data.md](./source-data.md)

---

## Prompt Results

| Prompt | Models Tested | Best Score | Winner | Details |
|--------|---------------|------------|--------|---------|
| [dream_v5](./prompt_dream_v5/README.md) | 5 | 36/40 ⭐ | llama-3.3-70b-versatile | Multi-task (themes + emotions) |
| [dream_v7](./prompt_dream_v7/README.md) | 5 | 35/40 | Multiple (tied) | Multi-task, shorter prompt |
| [dream_v8](./prompt_dream_v8/README.md) ⭐ | 1 | **38/40** ⭐⭐⭐ | **maverick** | **Single-task (cleaned_text only)** |
| [dream_v8_paragraphs](./prompt_dream_v8_paragraphs/README.md) | 1 | 35/40 | maverick | **Paragraphs schema** (guaranteed structure) |
