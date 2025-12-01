# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v5

← [Back to dream_v5](./README.md) | [Back to Index](../README.md)

---

**Status:** ⚠️ **CONDITIONAL** | **Best Score:** 32/40 (80%) - T4
**Cache:** `cache/prompt_dream_v5/5beeaea1-967a-4569-9c84-eccad8797b95_meta-llama-llama-4-maverick-17b-128e-instruct/`

**Key Findings:**
1. **100% JSON Parse Success** - All 7 configs produced valid JSON
2. **❌ CRITICAL: Aggressive Over-summarization** - ALL outputs 35-51% of original (target: 70-95%)
3. **Stable at High Temperatures** - Even T7 (temp=2.0) produces coherent Slovenian
4. **Fast Processing** - T1/T2 complete in ~3s
5. **Excellent Artifact Removal** - 10/10 across all configs
6. **❌ DOES NOT MEET 36/40 THRESHOLD** - Best score 32/40 (T4)

**Critical Weakness:** Model treats cleanup as summarization, losing 50-65% of content.

---

## CASE 1: Temperature Only (top_p = null)

**Status:** ✅ Complete (2025-11-30)
**Winner:** T4 (temp=0.8) - 32/40 (only config with proper paragraph structure)

**Length Ratio Analysis (Raw = 5051 chars, Target = 70-95%):**

| Config | Cleaned Length | Ratio | Status |
|--------|----------------|-------|--------|
| T1 | ~1890 chars | 37% | ❌ Severe (<50%) |
| T2 | ~2100 chars | 42% | ❌ Severe (<50%) |
| T3 | ~1780 chars | 35% | ❌ Severe (<50%) |
| T4 | ~2300 chars | 46% | ❌ Severe (<50%) |
| T5 | ~2040 chars | 40% | ❌ Severe (<50%) |
| T6 | ~2140 chars | 42% | ❌ Severe (<50%) |
| T7 | ~2600 chars | 51% | ⚠️ Short (50-70%) |

---

### T1: Temp: 0.0, Top-p: null
**Processing Time:** 2.47s | **Length:** ~1890 chars (37% ❌)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 5/10 | Base 9, -4 severe over-summarization |
| Artifact Removal | 10/10 | All artifacts removed cleanly |
| Grammar Quality | 8/10 | Good Slovenian, "neuporbljive" typo |
| Readability | 5/10 | Single block, no paragraph breaks |
| **Total** | **28/40 (70%)** | ❌ **BELOW THRESHOLD** |

**Red Flags:**
- [x] Severe over-summarization (37%)
- [x] No paragraph breaks

---

### T2: Temp: 0.3, Top-p: null
**Processing Time:** 2.97s | **Length:** ~2100 chars (42% ❌)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 6/10 | Base 9, -3 severe over-summarization, timeline preserved |
| Artifact Removal | 10/10 | Perfect artifact removal |
| Grammar Quality | 7/10 | "v bistvu" kept, emotions list has error |
| Readability | 5/10 | Single block, no paragraph breaks |
| **Total** | **28/40 (70%)** | ❌ **BELOW THRESHOLD** |

---

### T3: Temp: 0.5, Top-p: null
**Processing Time:** 27.69s | **Length:** ~1780 chars (35% ❌ **MOST SEVERE**)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 5/10 | Base 9, -4 severe over-summarization (worst ratio) |
| Artifact Removal | 10/10 | Perfect cleanup |
| Grammar Quality | 8/10 | "v bistvu" kept |
| Readability | 5/10 | Single block |
| **Total** | **28/40 (70%)** | ❌ **BELOW THRESHOLD** |

---

### T4: Temp: 0.8, Top-p: null ⭐ BEST
**Processing Time:** 27.91s | **Length:** ~2300 chars (46% ⚠️)

**Why T4 Stands Out:**
- ✅ Only configuration with proper paragraph breaks
- ✅ Best balance of content preservation and structure

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 6/10 | Base 9, -3 over-summarization, most events preserved |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 8/10 | Generally good |
| Readability | **8/10** | **Only config with proper paragraph structure!** |
| **Total** | **32/40 (80%)** | ⭐ **BEST CONFIG** |

---

### T5: Temp: 1.0, Top-p: null
**Processing Time:** 28.83s | **Length:** ~2040 chars (40% ❌)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 4/10 | Base 9, -3 over-summarization, -2 hallucination ("hladno") |
| Artifact Removal | 10/10 | Perfect |
| Grammar Quality | 8/10 | OK |
| Readability | 7/10 | Has paragraphs |
| **Total** | **29/40 (72.5%)** | ❌ **BELOW THRESHOLD** |

**Red Flags:**
- [x] Hallucination: "hladno" (cold) not in original
- [x] Subject change: "smo" (we) instead of singular

---

### T6: Temp: 1.5, Top-p: null
**Processing Time:** 26.52s | **Length:** ~2140 chars (42% ❌)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 6/10 | Base 9, -3 over-summarization |
| Artifact Removal | 10/10 | Perfect |
| Grammar Quality | 8/10 | Good |
| Readability | 5/10 | Single block |
| **Total** | **29/40 (72.5%)** | ❌ **BELOW THRESHOLD** |

**Notes:** Remarkably stable at temp=1.5 - still produces coherent Slovenian.

---

### T7: Temp: 2.0, Top-p: null
**Processing Time:** 31.29s | **Length:** ~2600 chars (51% ⚠️)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 4/10 | Base 9, -2 over-summarization, -2 hallucination, -2 subject change |
| Artifact Removal | 10/10 | Perfect |
| Grammar Quality | 6/10 | "znanžnost" not a real word |
| Readability | 6/10 | Has paragraphs but hallucinated ending |
| **Total** | **26/40 (65%)** | ❌ **BELOW THRESHOLD** |

**Red Flags:**
- [x] Hallucinated philosophical ending
- [x] Subject change: workers opening cabinets
- [x] Made-up word: "znanžnost"

**Notes:** Even at temp=2.0, output is COHERENT SLOVENIAN (unlike qwen gibberish).

---

## Case 1 Summary

| Rank | Config | Temp | Length | Content | Artifacts | Grammar | Readability | **Total** | Key Issue |
|------|--------|------|--------|---------|-----------|---------|-------------|-----------|-----------|
| 🥇 | **T4** | 0.8 | 46% | 6/10 | 10/10 | 8/10 | **8/10** | **32/40** | Only one with paragraphs |
| 🥈 | T5 | 1.0 | 40% | 4/10 | 10/10 | 8/10 | 7/10 | **29/40** | Hallucination |
| 🥈 | T6 | 1.5 | 42% | 6/10 | 10/10 | 8/10 | 5/10 | **29/40** | Over-summarization |
| 4 | T1 | 0.0 | 37% | 5/10 | 10/10 | 8/10 | 5/10 | **28/40** | No paragraphs |
| 4 | T2 | 0.3 | 42% | 6/10 | 10/10 | 7/10 | 5/10 | **28/40** | No paragraphs |
| 4 | T3 | 0.5 | 35% | 5/10 | 10/10 | 8/10 | 5/10 | **28/40** | Most severe over-summ |
| 7 | T7 | 2.0 | 51% | 4/10 | 10/10 | 6/10 | 6/10 | **26/40** | Hallucination + made-up word |

**Strengths:**
- ✅ Excellent artifact removal (10/10 across all configs)
- ✅ Fast processing (2-30s)
- ✅ 100% JSON success rate
- ✅ Stable at high temperatures

**Critical Weakness:**
- ❌ **Treats cleanup as summarization** - consistently loses 50-65% of content

**Recommendation:** ⚠️ **CONDITIONAL - Use only if content loss is acceptable**

**Note:** Phase 2 testing with simplified prompt (dream_v8) achieved **38/40** with this model at temp=1.0.
