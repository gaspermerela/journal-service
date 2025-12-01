# Prompt dream_v7 Results

← [Back to Index](../README.md)

---

**Prompt Version:** dream_v7 (version 1, prompt_id: 389)
**Prompt Type:** Multi-task (cleaned_text + themes + emotions + characters + locations)
**Models Tested:** 5
**Testing Date:** 2025-11-30

---

## Prompt Changes from dream_v5

- Much shorter and without nested instructions
- Stronger "Do NOT summarize. Do NOT shorten." instruction
- Emphasis on preserving "unusual or strange details"
- "Fix obvious mishearings" added

---

## Summary Table

| Model | Best Score | Best Config | Length Ratio | Key Issue |
|-------|------------|-------------|--------------|-----------|
| [llama-3.3-70b-versatile](./llama-3.3-70b-versatile.md) | 35/40 | T1 (temp=0.0) | 64.2% ⚠️ | Over-summarizes |
| [openai-gpt-oss-120b](./openai-gpt-oss-120b.md) | 35/40 | T1 (temp=0.0) | 51.9% ⚠️ | Over-summarizes |
| [meta-llama-llama-4-maverick](./meta-llama-llama-4-maverick.md) | 35/40 | T2 (temp=0.3) | 69.5% | Russian word bug |
| [moonshotai-kimi-k2-instruct](./moonshotai-kimi-k2-instruct.md) | 30/40 | T1 (temp=0.0) | 55.6% ⚠️ | Over-summarizes |
| [qwen-qwen3-32b](./qwen-qwen3-32b.md) | 0/40 | ALL FAIL | N/A | `<think>` mode breaks JSON |

---

## Key Finding: dream_v7 Performs Worse Than dream_v5

**NO model meets the 36/40 threshold with dream_v7.**

The shorter, more explicit prompt causes models to either:
1. Over-summarize at low temps (better grammar)
2. Keep transcription errors verbatim at higher temps (better length)

**Trade-off Discovered:**
- **T1 (temp=0.0):** Best grammar but over-summarizes
- **T2-T4 (temp=0.3-0.8):** Best length but keeps grammar errors

**Comparison with dream_v5:**
- dream_v5 T1: **36/40** at 83-86% length ✅
- dream_v7 T1: **35/40** at 64% length ⚠️

---

## qwen/qwen3-32b Critical Failure

**ALL 7 configs (T1-T7) FAILED to parse** due to `<think>` reasoning mode:
- Model outputs `<think>...</think>` tags before JSON
- Parser sees `<think>` at position 0 and fails immediately
- Even configs that worked with dream_v5 (T2-T4) now fail completely

This is a **complete regression** from dream_v5 where T2/T4 produced usable (28/40) output.

---

## Recommendation

❌ **dream_v7 is NOT recommended** - use dream_v5 instead.

For dream_v8 (simplified, single-task prompt), maverick achieves **38/40** - see [dream_v8 results](../prompt_dream_v8/README.md).
