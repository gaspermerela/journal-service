# Prompt dream_v5 Results

← [Back to Index](../README.md)

---

**Prompt Version:** dream_v5 (version 2, prompt_id: 378)
**Prompt Type:** Multi-task (cleaned_text + themes + emotions + characters + locations)
**Models Tested:** 5
**Testing Date:** 2025-11-29 to 2025-11-30

---

## Summary Table

| Model | Best Score | Best Config | Length Ratio | JSON Success | Key Issue |
|-------|------------|-------------|--------------|--------------|-----------|
| [llama-3.3-70b-versatile](./llama-3.3-70b-versatile.md) | **36/40** ⭐ | T1 (temp=0.0) | 83.8% ✅ | 86% (6/7) | None - **WINNER** |
| [openai-gpt-oss-120b](./openai-gpt-oss-120b.md) | 33/40 | T3 (temp=0.5) | 45.8% ❌ | 100% | Over-summarizes |
| [meta-llama-llama-4-maverick](./meta-llama-llama-4-maverick.md) | 32/40 | T4 (temp=0.8) | 35-51% ❌ | 100% | Over-summarizes |
| [moonshotai-kimi-k2-instruct](./moonshotai-kimi-k2-instruct.md) | 29/40 | T2 (temp=0.3) | 51.5% | 71% | Hallucinations |
| [qwen-qwen3-32b](./qwen-qwen3-32b.md) | 28/40 | T2/T4 | Variable | 86% | Russian word bug |

---

## Key Finding: dream_v5 Establishes Baseline

**Only llama-3.3-70b-versatile reached 36/40 threshold** - all other models over-summarize content.

**Maverick Potential Noted:** Despite scoring only 32/40, maverick showed 100% JSON reliability and superior temperature stability, suggesting prompt optimization could unlock better performance.

---

## Analysis & Recommendations

### Issues Identified Across Tests

1. **T3 Anomaly (temp=0.5):** Catastrophic duplication failure - avoid this temperature
2. **Hallucinations at higher temps:** T4+ start adding content not in original
3. **Length instability:** T6 too short (52%), T3 too long (143%)
4. **Structural failure:** T7 cannot produce valid JSON at temp=2.0

### Score Rankings

1. **T1 (0.0):** 36/40 (90%) ⭐ WINNER - verified 3x
2. **P2 (0.3 top-p):** 36/40 (90%) - Case 2 winner
3. **T2 (0.3 temp):** 33/40 (82.5%)
4. **T4 (0.8):** 32/40 (80.0%)
5. **T5 (1.0):** 31/40 (77.5%)
6. **T6 (1.5):** 27/40 (67.5%)
7. **T3 (0.5):** 16/40 (40.0%) - unstable
8. **T7 (2.0):** FAILED

### Recommended Production Settings

**Primary Option (WINNER):**
- **Model:** llama-3.3-70b-versatile
- **Temperature:** 0.0
- **Top-p:** null
- **Expected Score:** 36/40 (90%)
- **Reliability:** 3/4 runs meet threshold

**Stopping Criteria Met:** ✅ Yes (≥36/40) - Only llama-3.3-70b-versatile meets threshold

---

## Future Optimization: Maverick Potential

⚠️ **HIGH POTENTIAL:** If the over-summarization can be fixed through prompt engineering, maverick would likely become the winner due to superior technical characteristics:

| Characteristic | llama-3.3-70b | llama-4-maverick | Advantage |
|----------------|---------------|------------------|-----------|
| JSON Success | 86% (6/7) | **100%** (7/7) | Maverick |
| Processing Speed | 4-5s | **2-3s** | Maverick |
| Temperature Stability | Poor ≥1.5 | **Excellent** | Maverick |
| T7 (temp=2.0) | FAILED | 26/40 (coherent) | Maverick |
| Content Preservation | **83.8%** | 35-51% ❌ | llama-3.3 |

**Result:** Phase 2 with dream_v8 (simplified prompt) achieved this potential → **38/40**
