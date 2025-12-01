# Prompt dream_v8 Results ⭐⭐⭐ BEST

← [Back to Index](../README.md)

---

**Prompt Version:** dream_v8 (version 1, prompt_id: 390)
**Prompt Type:** Single-task (cleaned_text ONLY - no theme extraction)
**Models Tested:** 3 (maverick, llama-3.3-70b, gpt-oss-120b)
**Testing Date:** 2025-12-01

---

## Prompt Changes from dream_v7

**Key Change:** Removed theme/emotion/character/location extraction instructions.
Only `cleaned_text` required in output.

This is a **single-task prompt** vs multi-task prompts (v5, v7).

---

## Summary Table (T* + P* Tests Complete)

| Model | Best Score | Best Config | Ratio | Key Achievement |
|-------|------------|-------------|-------|-----------------|
| [meta-llama/llama-4-maverick](./meta-llama-llama-4-maverick.md) | **38/40** ⭐⭐⭐ | T5 (temp=1.0) | 81.29% ✅ | **Fixed "bolnica"**, no Russian words |
| [llama-3.3-70b-versatile](./llama-3.3-70b-versatile.md) | **36/40** ✅ | P4 (top_p=0.7) | 81.8% ✅ | **Fixed "bolnica"** (only P4!) |
| [openai/gpt-oss-120b](./openai-gpt-oss-120b.md) | 35/40 | T2/T3/P1-P3/P6 | 46-58% ❌ | Best grammar, but over-summarizes |

---

## Key Finding: Single-Task Prompt WINS

**T5 (temp=1.0) scored 38/40 (95%)** - exceeds the ≥36/40 threshold! ✅

**Comparison with multi-task prompts:**

| Prompt | Maverick Best | Config | Improvement |
|--------|---------------|--------|-------------|
| dream_v5 | 32/40 | T4 (temp=0.8) | baseline |
| dream_v7 | 35/40 | T2 (temp=0.3) | +3 points |
| **dream_v8** | **38/40** | T5 (temp=1.0) | **+6 points from v5** |

---

## Critical Discovery: Parameter Sweet Spots

### Maverick - Russian Word Bug Pattern

| Parameter | Bug Threshold | Safe Values |
|-----------|---------------|-------------|
| Temperature | temp ≤ 0.3 | temp ≥ 0.5 |
| Top-p | top_p ≤ 0.7 | top_p ≥ 0.9 |

### "bolnica" Fix Requirements

| Model | Best Config | "bolnica" Fixed |
|-------|-------------|-----------------|
| **maverick** | T5 (temp=1.0) or P5 (top_p=0.9) | ✅ Yes |
| **llama-3.3-70b** | P4 (top_p=0.7) ONLY | ✅ Yes |
| gpt-oss-120b | N/A | ❌ Never |

---

## Hypothesis Validation

**Original question:** Can removing theme extraction improve results?

**Answer:** Yes, significantly! The simplified prompt (dream_v8) with only `cleaned_text` output:
- Improved maverick's best score from 35/40 to **38/40** (+3 points from v7)
- T5 (temp=1.0) is optimal for maverick - fixes "bolnica", no Russian words
- P* tests revealed llama-3.3-70b can achieve 36/40 with P4 (top_p=0.7)
- gpt-oss-120b fundamentally over-summarizes regardless of parameters

---

## Recommendation: Production Settings

### Primary: maverick + T5 ⭐⭐⭐
For `meta-llama/llama-4-maverick-17b-128e-instruct`:
- **Prompt:** dream_v8 (simplified, no theme extraction)
- **Temperature:** 1.0
- **Top-p:** null
- **Expected Score:** 38/40 (95%)
- **Processing Time:** ~21s

### Alternative: llama-3.3-70b + P4 ✅
For `llama-3.3-70b-versatile`:
- **Prompt:** dream_v8
- **Temperature:** null
- **Top-p:** 0.7
- **Expected Score:** 36/40 (90%)
- **Processing Time:** ~4s (5x faster!)

### Not Recommended: gpt-oss-120b ❌
- Over-summarizes regardless of parameters
- Best score 35/40 (below threshold)
