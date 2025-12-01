# Prompt dream_v8_paragraphs Results

← [Back to Index](../README.md)

---

**Prompt Version:** dream_v8 with paragraphs schema (prompt_id: 390)
**Schema Change:** Output changed from `{"cleaned_text": "..."}` to `{"paragraphs": [...]}`
**Models Tested:** 1
**Testing Date:** 2025-12-01

---

## Schema Change from dream_v8

**Key Change:** JSON output format now requires `paragraphs` array instead of `cleaned_text` string.

```json
// OLD (dream_v8)
{"cleaned_text": "Full text as single string..."}

// NEW (dream_v8_paragraphs)
{"paragraphs": ["Scene 1...", "Scene 2...", "..."]}
```

**Goal:** Force consistent paragraph structure via schema, not just prompt instructions.

---

## Summary Table

| Model | Best Score | Best Config | Ratio | Paragraphs | Key Finding |
|-------|------------|-------------|-------|------------|-------------|
| [meta-llama-llama-4-maverick](./meta-llama-llama-4-maverick.md) | **35/40** | T5 (temp=1.0) | 63% | 11 | Best balance of quality and structure |

---

## Temperature Analysis

| Config | Temp | Score | Ratio | Paragraphs | Notes |
|--------|------|-------|-------|------------|-------|
| T1 | 0.0 | 31/40 | 69% | 18 | Over-fragmented |
| T2 | 0.3 | 30/40 | 76% | 19 | Over-fragmented, "v bistvu" kept |
| T3 | 0.5 | 32/40 | 65% | 11 | Tense mixing |
| T4 | 0.8 | 32/40 | 62% | 11 | Tense mixing |
| **T5** | **1.0** | **35/40** | **63%** | **11** | **Best quality** |
| T6 | 1.5 | 28/40 | 45% | 11 | Over-summarized |
| T7 | 2.0 | 17/40 | 41% | 9 | Gibberish in later paragraphs |

---

## Key Findings

1. **Paragraphs schema works** - Forces consistent scene-based structure
2. **T5 (temp=1.0) remains optimal** - Same winner as v8 without paragraphs
3. **Low temps over-fragment** - T1/T2 create 18-19 tiny paragraphs
4. **High temps degrade** - T6+ loses content, T7 produces gibberish
5. **Ratio is lower** - 63% vs 81% in v8, but content is preserved (more concise)

---

## Comparison: v8 vs v8_paragraphs

| Metric | v8 (cleaned_text) | v8_paragraphs |
|--------|-------------------|---------------|
| Best Score | 38/40 | 35/40 |
| Best Config | T5 (temp=1.0) | T5 (temp=1.0) |
| Output Length | 4106 chars (81%) | 3199 chars (63%) |
| Structure | 1 text blob | 11 paragraphs |
| Formatting | Inconsistent | Forced by schema |

---

## Recommendation

For production with **maverick + dream_v8_paragraphs**:
- **Temperature:** 1.0
- **Top-p:** null
- **Expected Score:** ~35/40
- **Processing Time:** ~22s

**Note:** Score dropped from 38/40 to 35/40, but paragraph structure is now guaranteed.
