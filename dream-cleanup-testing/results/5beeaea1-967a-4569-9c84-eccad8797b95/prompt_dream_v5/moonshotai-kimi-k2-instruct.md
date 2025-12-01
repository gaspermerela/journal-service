# moonshotai/kimi-k2-instruct on dream_v5

← [Back to dream_v5](./README.md) | [Back to Index](../README.md)

---

**Status:** ❌ NOT RECOMMENDED | **Best Score:** 29/40 (72.5%)
**Cache:** `cache/prompt_dream_v5/5beeaea1-967a-4569-9c84-eccad8797b95_moonshotai-kimi-k2-instruct/`

**Critical Issue:** Model performs CREATIVE REWRITING instead of cleanup. Systematically hallucmates a "spray/smell" detail across ALL configurations that does NOT exist in original transcription.

---

## CASE 1: Temperature Only (top_p = null)

**Status:** ✅ Complete (2025-11-30)
**Winner:** None - all configs fail due to hallucinations

---

### T1: Temp: 0.0, Top-p: null
**Processing Time:** 10.20s | **Length:** 4190 chars (82.9%)

**Automated Checks:**
- ✅ Artifacts removed
- ✅ Length within range
- ❌ **30+ hallucinations** - creative rewriting, not cleanup

**Key Issues:**
- Invents spray/smell detail (original says "listening to a sound that inspires")
- Adds invented dialogue, descriptions, characters details
- Invents entire final paragraph
- Missing details (time, people count)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 2/10 | 30+ hallucinations, creative rewriting |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 8/10 | Good (but content is fiction) |
| Readability | 9/10 | Reads well (but not the original) |
| **Total** | **29/40 (72.5%)** | ❌ **FAILS** |

---

### T2: Temp: 0.3, Top-p: null
**Processing Time:** 5.78s | **Length:** 2601 chars (51.5%)

**Key Issues:** Same spray hallucination + over-summarization (51.5%)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 3/10 | Spray hallucination + over-summarization |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 8/10 | Good |
| Readability | 8/10 | Clean |
| **Total** | **29/40 (72.5%)** | |

---

### T3: Temp: 0.5, Top-p: null
**Processing Time:** 5.45s | **Length:** 2541 chars (50.3%)

**Key Issues:** Same spray hallucination + over-summarization

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 3/10 | Spray hallucination + over-summarization |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 8/10 | Good |
| Readability | 8/10 | Good |
| **Total** | **29/40 (72.5%)** | |

---

### T4: Temp: 0.8, Top-p: null
**Processing Time:** 5.18s | **Length:** 2236 chars (44.3%)

**Key Issues:** Spray hallucination + many other invented details + severe over-summarization

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 2/10 | Multiple hallucinations + 44% length |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 7/10 | Some issues |
| Readability | 8/10 | Condensed |
| **Total** | **27/40 (67.5%)** | |

---

### T5: Temp: 1.0, Top-p: null
**Processing Time:** 5.69s | **Length:** 2875 chars (56.9%)

**Key Issues:** Same spray hallucination + over-summarization

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 3/10 | Spray hallucination + over-summarization |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 8/10 | Good |
| Readability | 8/10 | Good |
| **Total** | **29/40 (72.5%)** | |

---

### T6: Temp: 1.5, Top-p: null
**Status:** ❌ **FAILED - Invalid JSON**

---

### T7: Temp: 2.0, Top-p: null
**Processing Time:** 29.32s | **Length:** 942 chars (18.6%)

**Status:** ❌ **GIBBERISH - Incoherent output**

| Criterion | Score |
|-----------|-------|
| **Total** | **0/40 (0%)** |

---

## Case 1 Summary

| Config | Temp | Length | Content | Artifacts | Grammar | Readability | **Total** | Issue |
|--------|------|--------|---------|-----------|---------|-------------|-----------|-------|
| T1 | 0.0 | 82.9% | 2/10 | 10/10 | 8/10 | 9/10 | **29/40** | 30+ hallucinations |
| T2 | 0.3 | 51.5% | 3/10 | 10/10 | 8/10 | 8/10 | **29/40** | Halluc + over-summ |
| T3 | 0.5 | 50.3% | 3/10 | 10/10 | 8/10 | 8/10 | **29/40** | Halluc + over-summ |
| T4 | 0.8 | 44.3% | 2/10 | 10/10 | 7/10 | 8/10 | **27/40** | Many hallucinations |
| T5 | 1.0 | 56.9% | 3/10 | 10/10 | 8/10 | 8/10 | **29/40** | Halluc + over-summ |
| T6 | 1.5 | - | - | - | - | - | **FAILED** | Invalid JSON |
| T7 | 2.0 | 18.6% | 0/10 | 0/10 | 0/10 | 0/10 | **0/40** | Gibberish |

**Critical Finding: SYSTEMATIC HALLUCINATION**

ALL configs (T1-T5) invent a "spray/smell" detail that does NOT exist in original. Original says "listening to a sound that inspires" - model consistently changes this to "spraying something that smells bad."

**Recommendation:** ❌ **DO NOT USE** - Model systematically invents content rather than cleaning up transcription.
