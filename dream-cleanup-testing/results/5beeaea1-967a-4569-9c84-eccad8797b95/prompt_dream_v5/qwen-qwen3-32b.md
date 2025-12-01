# qwen/qwen3-32b on dream_v5

← [Back to dream_v5](./README.md) | [Back to Index](../README.md)

---

**Status:** ❌ NOT RECOMMENDED | **Best Score:** 28/40 (70%) - T2/T4
**Cache:** `cache/prompt_dream_v5/5beeaea1-967a-4569-9c84-eccad8797b95_qwen-qwen3-32b/`

**Critical Issues:**
1. **`<think>` mode incompatibility** - Model outputs reasoning in `<think>` tags before JSON, causing parse failures
2. **Severe over-summarization** - All outputs are 35-40% of original length (target: 70-95%)
3. **High temperature instability** - T6/T7 produce garbled/incomprehensible output

---

## CASE 1: Temperature Only (top_p = null)

**Status:** ✅ Complete (2025-11-30)
**Winner:** T2/T4 (tied at 28/40) - but both FAIL threshold

**Root Cause Analysis:**
The qwen/qwen3-32b model uses "thinking mode" which outputs `<think>...</think>` tags containing reasoning before the actual JSON response. Our JSON parser sees `<think>` at position 0 and fails.

---

### T1: Temp: 0.0, Top-p: null
**Processing Time:** 58.97s
**Status:** ❌ **FAILED - Infinite Thinking Loop**

**Raw Response:** 15,615 chars of repeated text in `<think>` tags, NO `</think>` closing tag.

**Issue:** Model got stuck in an infinite reasoning loop, repeatedly analyzing "Zdravstveno, da ste pripravljeni" phrase without ever producing output.

**Scores:** N/A - No output produced

---

### T2: Temp: 0.3, Top-p: null
**Processing Time:** ~84s | **Length:** 1,993 chars (**39.5%** of raw - SEVERE)

**Automated Checks:**
- ✅ Artifacts: No "Hvala" found
- ✅ Grammar: Uses correct "bolnišnica"
- ❌ **Length: 39.5% (<50% = severe content loss)**

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 3/10 | Base 9, -6 severe over-summarization |
| Artifact Removal | 10/10 | All "Hvala" removed |
| Grammar Quality | 8/10 | Good Slovenian |
| Readability | 7/10 | Flows well despite truncation |
| **Total** | **28/40 (70%)** | ❌ **Below threshold** |

---

### T3: Temp: 0.5, Top-p: null
**Processing Time:** ~100s | **Length:** 1,772 chars (**35.1%** of raw)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 3/10 | Severe over-summarization |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 6/10 | Uses wrong "polica" instead of "bolnica" |
| Readability | 7/10 | Decent flow |
| **Total** | **26/40 (65%)** | ❌ **Below threshold** |

---

### T4: Temp: 0.8, Top-p: null
**Processing Time:** ~84s | **Length:** 1,750 chars (**34.6%** of raw)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 3/10 | Severe over-summarization |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 8/10 | Good grammar, correct "bolnišnica" |
| Readability | 7/10 | Good flow |
| **Total** | **28/40 (70%)** | ❌ **Below threshold** |

---

### T5: Temp: 1.0, Top-p: null
**Processing Time:** ~105s | **Length:** 1,973 chars (**39.1%** of raw)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 3/10 | Severe over-summarization |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 5/10 | Wrong word "polica" + garbled phrases |
| Readability | 6/10 | Some rough patches |
| **Total** | **24/40 (60%)** | ❌ **Below threshold** |

---

### T6: Temp: 1.5, Top-p: null
**Processing Time:** ~105s
**Status:** ❌ **SEVERELY GARBLED OUTPUT**

**Sample of garbled text:**
```
"Imel/-sna sem stvarilno osvilen/-eno občutek prihodne usposabljanja..."
```

**Issues:**
- Gender-neutral markers "/-a", "/-la" throughout (inappropriate)
- Garbled words: "usposabljanja", "odsleparjanje", "klončen"

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 1/10 | Barely recognizable as dream |
| Artifact Removal | 8/10 | No "Hvala" but text is garbled |
| Grammar Quality | 1/10 | Mostly incomprehensible |
| Readability | 1/10 | Unreadable |
| **Total** | **11/40 (27.5%)** | ❌ **SEVERE FAILURE** |

---

### T7: Temp: 2.0, Top-p: null
**Processing Time:** ~100s
**Status:** ❌ **COMPLETE GIBBERISH**

**Issues:**
- Wrong JSON key: `"cleared text"` instead of `"cleaned_text"`
- Contains artifact: "Hvale" at start
- Text is complete gibberish: "jutrnjin zgodav", "klonarji zorlj"

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 0/10 | Complete gibberish |
| Artifact Removal | 0/10 | Contains "Hvale" artifact |
| Grammar Quality | 0/10 | Not valid Slovenian |
| Readability | 0/10 | Completely unreadable |
| **Total** | **0/40 (0%)** | ❌ **WORST PERFORMER - GIBBERISH** |

---

## Case 1 Summary

| Config | Temp | Length | Content | Artifacts | Grammar | Readability | **Total** | Issue |
|--------|------|--------|---------|-----------|---------|-------------|-----------|-------|
| T1 | 0.0 | N/A | N/A | N/A | N/A | N/A | **N/A** | Infinite thinking loop |
| T2 | 0.3 | 39.5% ⚠️ | 3/10 | 10/10 | 8/10 | 7/10 | **28/40** | Over-summarization |
| T3 | 0.5 | 35.1% ⚠️ | 3/10 | 10/10 | 6/10 | 7/10 | **26/40** | Over-summ + wrong word |
| T4 | 0.8 | 34.6% ⚠️ | 3/10 | 10/10 | 8/10 | 7/10 | **28/40** | Over-summarization |
| T5 | 1.0 | 39.1% ⚠️ | 3/10 | 10/10 | 5/10 | 6/10 | **24/40** | Over-summ + garbled |
| T6 | 1.5 | - | 1/10 | 8/10 | 1/10 | 1/10 | **11/40** | Severely garbled |
| T7 | 2.0 | - | 0/10 | 0/10 | 0/10 | 0/10 | **0/40** | Complete gibberish |

**Key Findings:**

1. **`<think>` Mode Issue:** Model uses `<think>...</think>` tags for reasoning before JSON.
2. **Severe Over-summarization:** ALL working configs (T2-T5) produce 35-40% of original length.
3. **Temperature Sensitivity:**
   - T1 (0.0): Infinite loop - too deterministic
   - T2-T5 (0.3-1.0): Usable but over-summarized
   - T6-T7 (1.5-2.0): Garbled/gibberish output

**Recommendation:** ❌ **DO NOT USE qwen/qwen3-32b for dream cleanup**

Multiple issues:
1. Uses `<think>` mode which breaks JSON parsing
2. Severely over-summarizes content (35-40% vs target 70-95%)
3. High temperatures produce unusable output
4. Best configs score only 28/40 (70%)

**Case 2 Testing:** Skipped - model fundamentally unsuitable for this task.
