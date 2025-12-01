# Results Directory Structure Template

This template documents the multi-file structure for recording cleanup test results.

**Why multi-file?** Single-file results can grow to 35k+ tokens, exceeding Claude Code's read limits. This structure keeps each file under ~4k tokens for efficient updates.

---

## Directory Structure

```
results/
├── cleanup_{transcription_id}_{date}.md    # (legacy - kept for reference)
└── {transcription_id}/                     # New multi-file structure
    ├── README.md                           # Main index (~500 tokens)
    ├── source-data.md                      # Transcription metadata
    ├── prompt_{name}/                      # One directory per prompt version
    │   ├── README.md                       # Prompt summary + model comparison
    │   ├── {model-slug}.md                 # Detailed results per model
    │   └── ...
    └── prompt_{name2}/
        └── ...
```

---

## File Templates

### Main Index: `{transcription_id}/README.md`

```markdown
# Cleanup Results: [Transcription ID]

**Testing Date:** [Date]
**Status:** [In Progress / Complete]

---

## Best Result Summary

| Field | Value |
|-------|-------|
| **Best Prompt** | [prompt_name] |
| **Best Model** | [model name] |
| **Best Config** | [T1-T7 or P1-P6] |
| **Best Score** | [XX/40] ⭐ |

---

## Prompt Comparison

| Prompt | Best Model | Score | Config | Status |
|--------|------------|-------|--------|--------|
| [prompt_dream_v5](./prompt_dream_v5/README.md) | [model] | XX/40 | [config] | ✅/❌ |
| [prompt_dream_v7](./prompt_dream_v7/README.md) | [model] | XX/40 | [config] | ✅/❌ |

---

## Quick Links

- [Source Data](./source-data.md)
- [Prompt v5 Results](./prompt_dream_v5/README.md)
- [Prompt v7 Results](./prompt_dream_v7/README.md)
```

---

### Source Data: `{transcription_id}/source-data.md`

```markdown
# Source Data

← [Back to Index](./README.md)

---

## Transcription Info

| Field | Value |
|-------|-------|
| **Transcription ID** | [uuid] |
| **Transcription Model** | [model] |
| **Language** | [language] |
| **Raw Length** | [X] characters |

---

## Major Artifacts in Raw Transcription

| Artifact | Type | Notes |
|----------|------|-------|
| "[artifact text]" | [type] | [expected fix] |

---

## Scoring Criteria

| Criterion | Max Score | Description |
|-----------|-----------|-------------|
| Content Accuracy | 10 | Details preserved, no hallucinations, 70-95% length ratio |
| Artifact Removal | 10 | "Hvala", "Zdravstveno" removed, fillers cleaned |
| Grammar Quality | 10 | Proper Slovenian, errors corrected |
| Readability | 10 | Paragraph structure, natural flow |
| **Total** | **40** | ≥36/40 (90%) = threshold |

---

## Cache Location

JSON results cached at: `cache/prompt_{name}/{transcription_id}_{model}/T*.json`
```

---

### Prompt README: `{transcription_id}/prompt_{name}/README.md`

```markdown
# Prompt {name} Results

← [Back to Index](../README.md)

---

**Prompt Version:** {name} (version X, prompt_id: XXX)
**Prompt Type:** [Single-task / Multi-task]
**Models Tested:** [X]
**Testing Date:** [Date]

---

## Prompt Changes from {previous}

**Key Change:** [Brief description]

---

## Summary Table

| Model | Best Score | Best Config | Ratio | Key Achievement |
|-------|------------|-------------|-------|-----------------|
| [{model-slug}](./{model-slug}.md) | XX/40 | [config] | XX% | [note] |

---

## Key Findings

1. [Finding 1]
2. [Finding 2]

---

## Recommendation

[Production settings recommendation]
```

---

### Model Results: `{transcription_id}/prompt_{name}/{model-slug}.md`

```markdown
# {model-name} on {prompt_name}

← [Back to {prompt_name}](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅/❌ [Complete/Failed] | **Best Score:** XX/40
**Cache:** `cache/prompt_{name}/{transcription_id}_{model}/`

**Test Date:** [Date]
**Raw transcription length:** [X] characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** [config] - XX/40

### Summary Tables

#### Automated Checks

| Config | Temp | Length | Ratio | "Hvala" | Foreign Words | Processing |
|--------|------|--------|-------|---------|---------------|------------|
| T1 | 0.0 | XXXX | XX% | ✅/❌ | ✅/❌ | X.XXs |
| T2 | 0.3 | XXXX | XX% | ✅/❌ | ✅/❌ | X.XXs |
| ... | ... | ... | ... | ... | ... | ... |

#### Detailed Scores

| Config | Temp | Content | Artifacts | Grammar | Readability | **TOTAL** |
|--------|------|---------|-----------|---------|-------------|-----------|
| T1 | 0.0 | X/10 | X/10 | X/10 | X/10 | **XX/40** |
| ... | ... | ... | ... | ... | ... | ... |

---

## Config Analysis

### T1 (temp=0.0) - XX/40
- **Length:** XXXX chars (XX%) ✅/❌
- **Content:** [observations]
- **Grammar:** [observations]

[Repeat for each config...]

---

## Key Findings

1. [Finding 1]
2. [Finding 2]

---

## Comparison Across Prompts

| Prompt | Best Score | Config | Ratio | Key Issue |
|--------|------------|--------|-------|-----------|
| dream_v5 | XX/40 | [config] | XX% | [issue] |
| dream_v7 | XX/40 | [config] | XX% | [issue] |

---

## Production Recommendation

For `{model}`:
- **Prompt:** {name}
- **Temperature:** X.X
- **Top-p:** null/X.X
- **Expected Score:** XX/40
- **Processing Time:** ~XXs
```

---

## Naming Conventions

### Model Slug Format
Convert model ID to filesystem-safe slug:
- `llama-3.3-70b-versatile` → `llama-3.3-70b-versatile.md`
- `openai/gpt-oss-120b` → `openai-gpt-oss-120b.md`
- `meta-llama/llama-4-maverick-17b-128e-instruct` → `meta-llama-llama-4-maverick.md`
- `qwen/qwen3-32b` → `qwen-qwen3-32b.md`

### Prompt Directory Format
- `prompt_dream_v5/`
- `prompt_dream_v7/`
- `prompt_dream_v8/`

---

## Navigation Pattern

Every file should have navigation links:
- `← [Back to Index](../README.md)` - at top of file
- Cross-links to related files in tables
- Use relative paths for all links

---

## Token Optimization Benefits

| Old Structure | New Structure |
|---------------|---------------|
| Single 35k+ token file | Multiple 500-4000 token files |
| Cannot read full file | Each file easily readable |
| Full rewrite on updates | Update only affected file |
| Risk of context overflow | Safe, predictable sizes |
