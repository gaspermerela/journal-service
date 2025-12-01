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

## Summary Table

| Model | Best Score | Best Config | Ratio | Key Achievement |
|-------|------------|-------------|-------|-----------------|
| [meta-llama/llama-4-maverick](./meta-llama-llama-4-maverick.md) | **38/40** ⭐⭐⭐ | T5 (temp=1.0) | 81.29% ✅ | **Fixed "bolnica"**, no Russian words |
| [llama-3.3-70b-versatile](./llama-3.3-70b-versatile.md) | 35/40 | T1/T2/T5 | 78-88% ✅ | Fast (~4s), but "polnica" not fixed |
| [openai/gpt-oss-120b](./openai-gpt-oss-120b.md) | 35/40 | T2/T3/T4/T6 | 46-58% ❌ | Best grammar, but over-summarizes |

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

## Critical Discovery: Temperature Matters
**WARNING:** Rerun 2x - russian word "bug" persists!

| Temperature | Russian Word Bug | "bolnica" Fixed | Status |
|-------------|------------------|-----------------|--------|
| 0.0 | ❌ Yes ("приходят") | ❌ No | Avoid |
| 0.3 | ❌ Yes ("приходят") | ❌ No | Avoid |
| 0.5 | ✅ No | ❌ No | Acceptable |
| 0.8 | ✅ No | ❌ No | Below length threshold |
| **1.0** | ✅ No | ✅ **Yes** | **OPTIMAL** |
| 1.5 | ✅ No | ❌ No | Over-summarizes |
| 2.0 | ✅ No | ❌ No | Severe degradation |

---

## Hypothesis Validation

**Original question:** Can removing theme extraction improve results?

**Answer:** Yes, significantly! The simplified prompt (dream_v8) with only `cleaned_text` output:
- Improved maverick's best score from 35/40 to **38/40** (+3 points from v7)
- T5 (temp=1.0) is the optimal config - **only one that fixed "polnica -> bolnica"**
- Lower temperatures (0.0, 0.3) introduce Russian word bug -> **very interesting, need to test more! TODO** 

---

## Recommendation: Production Settings

For `meta-llama/llama-4-maverick-17b-128e-instruct`:
- **Use dream_v8 prompt** (simplified, no theme extraction)
- **Use temperature=1.0** (T5 config)
- **Avoid temperature≤0.3** (Russian word bug)
- **Avoid temperature≥1.5** (over-summarization)
- **Expected Score:** 38/40 (95%)
- **Processing Time:** ~21s
