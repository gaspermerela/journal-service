# Prompt dream_v8_paragraphs Results

← [Back to Index](../README.md)

---

**Prompt Version:** dream_v8 with paragraphs schema (prompt_id: 390)
**Schema Change:** Output changed from `{"cleaned_text": "..."}` to `{"paragraphs": [...]}`
**Models Tested:** 1
**Testing Date:** 2025-12-01
**Revised:** 2025-12-02 (content loss verification)

---

## ⚠️ CRITICAL: DO NOT USE

**This schema causes significant content loss.** Initial scoring (35/40) was incorrect. After detailed verification, best score revised to **27/40**. See [model results](./meta-llama-llama-4-maverick.md) for full analysis.

**Use dream_v8 instead (38/40).**

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

**Result:** ❌ Schema constraint causes over-summarization and content loss.

---

## Summary Table (REVISED)

| Model | Best Score | Best Config | Ratio | Paragraphs | Key Finding |
|-------|------------|-------------|-------|------------|-------------|
| [meta-llama-llama-4-maverick](./meta-llama-llama-4-maverick.md) | ~~35~~ **32/40** | T3/T4 (temp=0.5-0.8) | 62-65% | 11 | Balanced content + structure |

**Best Content:** T2 (temp=0.3) - 31/40 with **7/7 key phrases** preserved (but over-fragmented)

---

## Temperature Analysis (REVISED)

| Config | Temp | Score | Ratio | Paragraphs | Content | Notes |
|--------|------|-------|-------|------------|---------|-------|
| T1 | 0.0 | 31/40 | 68.7% | 18 | 5/7 | Over-fragmented |
| **T2** | **0.3** | ~~30~~ **31/40** | **76.3%** | 19 | **7/7** ⭐ | **Best content**, over-fragmented |
| **T3** | **0.5** | **32/40** | **65.0%** | **11** | 5/7 | **Best balanced** |
| **T4** | **0.8** | **32/40** | **62.3%** | **11** | 5/7 | **Best balanced** |
| T5 | 1.0 | ~~35~~ **27/40** | 63.3% | 11 | **0/7** ❌ | Content loss verified |
| T6 | 1.5 | ~~28~~ **27/40** | 45.3% | 11 | 2/7 | Over-summarized |
| T7 | 2.0 | 17/40 | 40.9% | 9 | 1/7 | Gibberish |

---

## Key Findings (REVISED)

1. ⚠️ **Paragraphs schema causes content loss** - 7+ important details lost in T5
2. ⚠️ **63% ratio is NOT "concise"** - it's content loss (action verbs, numbers, spatial details)
3. ⚠️ **Initial scoring was incorrect** - Content Accuracy was 4/10, not 8/10
4. **Low temps over-fragment** - T1/T2 create 18-19 tiny paragraphs
5. **High temps degrade** - T6+ loses even more content, T7 produces gibberish
6. **This is a prompt engineering failure** - Schema constraint encourages summarization

---

## Comparison: v8 vs v8_paragraphs (REVISED)

| Metric | v8 (cleaned_text) | v8_paragraphs |
|--------|-------------------|---------------|
| Best Score | **38/40** ⭐ | ~~35~~ **32/40** (T3/T4) |
| Best Config | T5 (temp=1.0) | T3/T4 (temp=0.5-0.8) |
| Best Content | T5 (all preserved) | **T2 (7/7 phrases)** |
| Output Length | 4106 chars (81%) | 3148-3285 chars (62-65%) |
| Structure | 1 text blob | 11 paragraphs |
| Content Loss | None verified | **T5 loses 7+ details** ❌ |
| "polnica" Fix | Fixed by T5 ✅ | Fixed by T2 only |

---

## Recommendation

### ❌ DO NOT USE dream_v8_paragraphs

For production, use **dream_v8** instead:
- **Prompt:** dream_v8 (without paragraphs schema)
- **Temperature:** 1.0
- **Top-p:** null
- **Expected Score:** 38/40
- **Processing Time:** ~21s

### If Using Paragraphs Schema (NOT RECOMMENDED)

| Priority | Config | Score | Content | Notes |
|----------|--------|-------|---------|-------|
| Best Balanced | T3/T4 | 32/40 | 5/7 | Good structure + decent content |
| Best Content | T2 | 31/40 | 7/7 | All details preserved, over-fragmented |
| ❌ Avoid | T5 | 27/40 | 0/7 | Best readability but WORST content |

### Next Steps

1. Create **dream_v9** with explicit content preservation rules
2. Add paragraph structure via prompt instructions, not schema constraint
3. Include RED FLAGS: "Never change action verbs", "Never remove specific numbers"
4. Test if prompt instructions can achieve T2's content with T5's readability
