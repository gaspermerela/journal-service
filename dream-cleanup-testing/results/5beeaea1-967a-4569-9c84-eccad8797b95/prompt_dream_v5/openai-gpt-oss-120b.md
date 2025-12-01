# openai/gpt-oss-120b on dream_v5

← [Back to dream_v5](./README.md) | [Back to Index](../README.md)

---

**Status:** ❌ NOT RECOMMENDED | **Best Score:** 33/40 (82.5%)
**Cache:** `cache/prompt_dream_v5/5beeaea1-967a-4569-9c84-eccad8797b95_openai-gpt-oss-120b/`

**Critical Issue:** All configurations produce severe over-summarization (<50% of original length).

---

## CASE 1: Temperature Only (top_p = null)

**Status:** ✅ Complete (2025-11-30)
**Winner:** T1 (temp=0.0) - 33/40 ❌ Below threshold

---

### T1: Temp: 0.0, Top-p: null
**Processing Time:** 5.48s | **Length:** ~2315 chars (**45.8%** ⚠️ **SEVERE OVER-SUMMARIZATION**)

**Automated Checks:**
- ✅ Artifacts: No "Hvala" or "Zdravstveno" found
- ✅ English: None
- ❌ **Length: 45.8% (<50% = severe content loss)**
- ✅ Person: First person preserved
- ✅ Timeline: Preserved

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 5/10 | Base 9, -4 severe over-summarization (<50% length) |
| Artifact Removal | 10/10 | All artifacts removed cleanly |
| Grammar Quality | 9/10 | Good Slovenian, fixed "polnica" → "bolnišnico" |
| Readability | 9/10 | Well-structured paragraphs, natural flow |
| **Total** | **33/40 (82.5%)** | ❌ **Below 36/40 threshold** |

**Red Flags:**
- [x] Severe over-summarization (45.8% < 70% threshold)
- [x] Lost significant dream detail due to aggressive compression

---

### T2: Temp: 0.3, Top-p: null
**Processing Time:** 6.28s | **Length:** ~1980 chars (**39.2%** ⚠️)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 5/10 | Severe over-summarization (39.2% length) |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 8/10 | Good grammar, some awkward phrasings |
| Readability | 9/10 | Well-structured, flows naturally |
| **Total** | **32/40 (80%)** | |

---

### T3: Temp: 0.5, Top-p: null
**Processing Time:** 23.28s | **Length:** ~2240 chars (**44.3%** ⚠️)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 4/10 | Over-summarization + subject shift |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 6/10 | **Subject shift: "mislimo" (we think) instead of "mislim" (I think)** |
| Readability | 8/10 | Good structure despite errors |
| **Total** | **28/40 (70%)** | |

**Red Flags:**
- [x] Subject shift from first person singular to plural ("mislimo")
- [x] Severe over-summarization (44.3%)

---

### T4: Temp: 0.8, Top-p: null
**Processing Time:** 25.17s | **Length:** ~2290 chars (**45.3%** ⚠️)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 4/10 | Over-summarization + subject shift |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 5/10 | Subject shift "mislimo", "polnica" NOT fixed |
| Readability | 8/10 | Decent flow |
| **Total** | **27/40 (67.5%)** | |

---

### T5: Temp: 1.0, Top-p: null
**Processing Time:** 25.33s | **Length:** ~2340 chars (**46.3%** ⚠️)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 6/10 | Over-summarization, BUT preserved spray detail |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 7/10 | Some errors, but maintains first person |
| Readability | 8/10 | Good paragraph structure |
| **Total** | **31/40 (77.5%)** | |

**Notes:** Only config that preserved spray detail ("špricanje neke vrste spreja").

---

### T6: Temp: 1.5, Top-p: null
**Processing Time:** 22.37s | **Length:** ~2025 chars (**40.1%** ⚠️)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 4/10 | Severe over-summarization (40.1%) |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 6/10 | More errors appearing at higher temp |
| Readability | 8/10 | Condensed but readable |
| **Total** | **28/40 (70%)** | |

---

### T7: Temp: 2.0, Top-p: null
**Processing Time:** 40.18s | **Length:** ~1835 chars (**36.3%** ⚠️ **WORST**)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 2/10 | Extreme over-summarization + garbled ending |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 5/10 | Garbled ending: "podobno težavo z navzem" (incomplete) |
| Readability | 3/10 | Ending is incomprehensible |
| **Total** | **20/40 (50%)** | ⚠️ **WORST PERFORMER** |

---

## Case 1 Summary

**All configurations FAIL the 36/40 threshold.**

| Config | Temp | Length Ratio | Content | Artifacts | Grammar | Readability | **Total** |
|--------|------|--------------|---------|-----------|---------|-------------|-----------|
| T1 | 0.0 | 45.8% ⚠️ | 5/10 | 10/10 | 9/10 | 9/10 | **33/40** |
| T2 | 0.3 | 39.2% ⚠️ | 5/10 | 10/10 | 8/10 | 9/10 | **32/40** |
| T3 | 0.5 | 44.3% ⚠️ | 4/10 | 10/10 | 6/10 | 8/10 | **28/40** |
| T4 | 0.8 | 45.3% ⚠️ | 4/10 | 10/10 | 5/10 | 8/10 | **27/40** |
| T5 | 1.0 | 46.3% ⚠️ | 6/10 | 10/10 | 7/10 | 8/10 | **31/40** |
| T6 | 1.5 | 40.1% ⚠️ | 4/10 | 10/10 | 6/10 | 8/10 | **28/40** |
| T7 | 2.0 | 36.3% ⚠️ | 2/10 | 10/10 | 5/10 | 3/10 | **20/40** |

**Critical Finding: openai/gpt-oss-120b fundamentally over-summarizes**

- **ALL configs produce <50% of original length** (target: 70-95%)
- Best score: 33/40 (T1) - 3 points below threshold
- Model excels at artifact removal (10/10 across all configs)
- Model fails at content preservation - treats cleanup as summarization

**Recommendation:** ❌ **DO NOT USE openai/gpt-oss-120b for dream cleanup**

**Case 2 Testing:** Skipped - model fundamentally unsuitable for this task.
