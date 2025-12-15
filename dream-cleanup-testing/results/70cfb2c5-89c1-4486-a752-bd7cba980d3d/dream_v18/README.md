# dream_v18 Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v18 (Explicit preservation rules with MANDATORY length requirement)
**Test Dates:** 2025-12-11 to 2025-12-16
**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Raw Length:** 5,013 characters
**Test Type:** Extended variance testing (15x maverick, 5x llama, 5x scout)

---

## Best Results Summary

| Model | Best Config | Score | Pass Rate | Key Finding |
|-------|-------------|-------|-----------|-------------|
| **[maverick-17b](./meta-llama-llama-4-maverick-17b-128e-instruct.md)** | T1 v2 | **94/100** | **40% (6/15)** | Best score but 60% failure rate |
| [scout-17b](./meta-llama-llama-4-scout-17b-16e-instruct.md) | T1 v2 | 89/100 | 100% (5/5) | Keeps "Hvala" artifact |
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) | T1 v2 | 88/100 | 100% (5/5) | Consistent but minimal cleanup |

---

## Extended Variance Testing (15x Maverick)

### Summary

| Metric | Original (5 runs) | Extended (+10 runs) | Total (15 runs) |
|--------|-------------------|---------------------|-----------------|
| Pass Rate | 60% (3/5) | 30% (3/10) | **40% (6/15)** |
| Best Ratio | 84.0% | 85.7% | 85.7% |
| Worst Ratio | 51.2% | 36.4% | **36.4%** |

### Distribution (15 Runs)

| Outcome | Runs | Percentage |
|---------|------|------------|
| Pass (70-95%) | 6 | 40% |
| Fail (60-69%) | 3 | 20% |
| Severe (<60%) | 6 | **40%** |

**Critical Finding:** Extended testing reveals maverick's failure rate is **60%**, not 40% as originally estimated. One third of runs produce severe over-summarization (<50%).

---

## Model Comparison

| Model | Runs | Pass Rate | Length Range | Variance | Usable |
|-------|------|-----------|--------------|----------|--------|
| **maverick** | 15 | 40% | 36-86% | **SEVERE** | ❌ Without safeguards |
| llama | 5 | 100% | 94-98% | Low | ✅ Consistent |
| scout | 5 | 100% | 95-99% | Low | ⚠️ Keeps artifacts |

---

## Key Findings

### 1. Maverick Variance is Architectural

Despite temp=0.0, maverick shows **trimodal behavior**:
- **Good (40%):** 70-86% length, proper cleanup
- **Bad (20%):** 60-69% length, over-condensed
- **Severe (40%):** 36-52% length, aggressive summarization

This is caused by MoE architecture with 128 experts, not prompt issues.

### 2. "MANDATORY REQUIREMENT" Has No Effect

Adding explicit requirements with warnings ("OUTPUT WILL BE REJECTED IF VIOLATED") has zero impact on compliance. The model ignores these instructions in 60% of runs.

---

## Recommendations

### For Production

1. **Retry logic:** Run maverick up to 3 times, accept if length ≥70%
2. **Alternative:** Use llama-3.3-70b for consistency (0% failure, lower quality)
3. **Next test:** Evaluate chunking approach

### Model Selection

| Priority | Model | Strategy |
|----------|-------|----------|
| Max quality | Maverick | 3x retry, accept if ≥70% |
| Consistency | Llama 3.3 70B | Single run, 88/100 |
| Avoid | Scout | Keeps "Hvala" artifacts |

---

## Model Files

- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md) - **60% failure rate**
- [llama-3.3-70b-versatile.md](./llama-3.3-70b-versatile.md)
- [meta-llama-llama-4-scout-17b-16e-instruct.md](./meta-llama-llama-4-scout-17b-16e-instruct.md)
