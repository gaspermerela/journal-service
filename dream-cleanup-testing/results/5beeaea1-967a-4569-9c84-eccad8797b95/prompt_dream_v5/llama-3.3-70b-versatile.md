# llama-3.3-70b-versatile on dream_v5

← [Back to dream_v5](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ Phase 1 Complete | **Best Score:** 36/40 (90%) ⭐
**Cache:** `cache/prompt_dream_v5/5beeaea1-967a-4569-9c84-eccad8797b95_llama-3.3-70b-versatile/`

---

## CASE 1: Temperature Only (top_p = null)

**Status:** ✅ Complete (2025-11-29)
**Winner:** T1 (temp=0.0) - 36/40

---

### T1_v1: Temp: 0.0, Top-p: null
**Processing Time:** 4.09s | **Length:** 3389 chars (67.1% ⚠️ **TOO SHORT**)

**Automated Checks:**
- ✅ Artifacts: None
- ✅ English: None
- ❌ **Length: 67.1% (<70% threshold) → Over-summarization**
- ✅ Person: First person preserved
- ✅ Timeline: Preserved

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 6/10 | Base 9, -1 missing spray detail, -2 too short (<70%) |
| Artifact Removal | 10/10 | All "Hvala" + "Zdravstveno" removed |
| Grammar Quality | 9/10 | Excellent Slovenian, "polnica" not fixed |
| Readability | 9/10 | Good paragraphs, natural flow |
| **Total** | **34/40 (85%)** | ❌ **Below threshold** |

**Red Flags:**
- [x] Over-summarization (67.1% < 70% threshold)
- [x] Missing spray detail ("šprical neke vrste sprej")

---

#### T1 Verification (v2, v3, v4) - 2025-11-30

**Purpose:** Verify T1 consistency and production-readiness with additional runs.

**All runs: temp=0.0, top_p=null**

| Run | Length | Ratio | Content | Artifacts | Grammar | Readability | **Total** |
|-----|--------|-------|---------|-----------|---------|-------------|-----------|
| v2  | 4246 | 84.1% | 8/10 | 10/10 | 9/10 | 9/10 | **36/40** ✅ |
| v3  | 4339 | 85.9% | 8/10 | 10/10 | 9/10 | 9/10 | **36/40** ✅ |
| v4  | 4233 | 83.8% | 8/10 | 10/10 | 9/10 | 9/10 | **36/40** ✅ |

**Consistency Analysis:**
- ✅ **3/3 verification runs scored 36/40** (exactly at threshold)
- ✅ **100% success rate** for v2-v4 (no failures, no hallucinations)
- ✅ **Stable length:** 83.8-85.9% (all within 70-95%)
- ✅ **Identical scores across criteria:** All runs have same breakdown
- ⚠️ **Common issue:** All 4 runs miss spray detail (consistent behavior)
- ⚠️ **v1 outlier:** Only v1 scored below due to over-summarization (67%)

**Production Assessment:**
- **Reliable:** 3/4 verification runs meet threshold (36/40)
- **Deterministic quality:** Same scores, same issues across runs
- **Fast:** Average 4.0s processing time
- **Recommendation:** ✅ Production-ready at 36/40 (90%)

---

### T2: Temp: 0.3, Top-p: null

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 8/10 | Most details preserved, minor content reorganization |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 8/10 | Good Slovenian, some awkward phrasings |
| Readability | 7/10 | Some repetitive sections |
| **Total** | **33/40 (82.5%)** | |

**Red Flags:** Minor content duplication in structure
**Length:** 3,559 chars (70% of original)

---

### T3: Temp: 0.5, Top-p: null ⚠️ UNSTABLE

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 4/10 | MAJOR DUPLICATION - dream repeated 4 times! |
| Artifact Removal | 2/10 | "Hvala" appears multiple times! Length = 143% of original! |
| Grammar Quality | 7/10 | Grammar OK where not duplicated |
| Readability | 3/10 | Severely damaged by repetition |
| **Total** | **16/40 (40.0%)** | ⚠️ **WORST PERFORMER - ANOMALY** |

**Red Flags Found:**
- [x] Content duplicated (4 times!)
- [x] Artifacts remaining ("Hvala" multiple times)

**Length:** 7,219 chars (143% of original) ⚠️

**Critical Issue:** Catastrophic failure at temp=0.5

#### T3 Re-run (v2)

| Metric | T3_v1 (Nov 29) | T3_v2 (Nov 30) | Analysis |
|--------|----------------|----------------|----------|
| **Failure Mode** | Duplication (4x repeat) | Hallucination + Artifacts | Completely different! |
| **Length** | 7,219 chars (143%) | 4,481 chars (88.7%) | v1 too long, v2 acceptable |
| **Artifacts** | 1x "Hvala" | 6x "Hvala" | v2 much worse |
| **Score** | 16/40 (40%) | 23/40 (57.5%) | v2 better but still fails |

**Recommendation:** **AVOID temp=0.5 in production**

---

### T4: Temp: 0.8, Top-p: null

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 7/10 | Hallucinated "sobanje" and "gozd" locations NOT in original |
| Artifact Removal | 10/10 | All artifacts removed |
| Grammar Quality | 7/10 | Some original errors remain ("prublev") |
| Readability | 8/10 | Good flow, readable |
| **Total** | **32/40 (80.0%)** | |

**Red Flags Found:**
- [x] Content hallucinated ("sobanje", "gozd" added as locations)

**Length:** 4,202 chars (83% of original)

---

### T5: Temp: 1.0, Top-p: null

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 7/10 | Added "izklopim vse luči" - not in original |
| Artifact Removal | 9/10 | "Hvala" removed, but kept "Zdravstveno, sem pripravljen" |
| Grammar Quality | 7/10 | Generally OK with some errors |
| Readability | 8/10 | Decent flow |
| **Total** | **31/40 (77.5%)** | |

**Red Flags Found:**
- [x] Content hallucinated ("izklopim vse luči")

**Length:** 3,946 chars (78% of original)

---

### T6: Temp: 1.5, Top-p: null

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 6/10 | TOO SHORT (52%) - likely missing content |
| Artifact Removal | 9/10 | "Hvala" removed, kept "Zdravstveno, sem pripravljen" |
| Grammar Quality | 6/10 | More errors appearing |
| Readability | 6/10 | Choppy, condensed |
| **Total** | **27/40 (67.5%)** | |

**Length:** 2,622 chars (52% of original) ⚠️

---

### T7: Temp: 2.0, Top-p: null

**Status:** ❌ **FAILED - Invalid JSON**

**Error:** `Error code: 400 - Failed to generate JSON. Please adjust your prompt.`

---

## CASE 2: Top-p Only (temperature = null)

**Status:** ✅ Complete (2025-11-30)
**Winner:** P2 (top_p=0.3) - 36/40

---

### P1: Temp: null, Top-p: 0.1
**Processing Time:** 4.09s | **Length:** 4238 chars (84%)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 10/10 | All details preserved, no hallucinations |
| Artifact Removal | 9/10 | All "Hvala" + "Zdravstveno" removed |
| Grammar Quality | 6/10 | Multiple errors: "polnica", "ronotežje", "prublev", etc. |
| Readability | 8/10 | Good structure, some rough edges |
| **Total** | **33/40 (82.5%)** | |

---

### P2: Temp: null, Top-p: 0.3 ⭐ CASE 2 WINNER
**Processing Time:** 22.67s | **Length:** 3760 chars (74%)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 10/10 | All details intact, no hallucinations, good length |
| Artifact Removal | 10/10 | All artifacts removed, minimal filler |
| Grammar Quality | 7/10 | Errors: "polnica", "ta ljena vzgor", "greva" |
| Readability | 9/10 | Excellent paragraph structure, natural flow |
| **Total** | **36/40 (90%)** | ⭐ **MEETS CRITERIA** |

---

### P3: Temp: null, Top-p: 0.5
**Processing Time:** 17.13s | **Length:** 4201 chars (83%)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 10/10 | All content preserved |
| Artifact Removal | 9/10 | All "Hvala" + "Zdravstveno" removed |
| Grammar Quality | 6/10 | Errors: "polnica", "prublev", etc. |
| Readability | 5/10 | **Poor paragraph formatting** (wall of text) |
| **Total** | **30/40 (75%)** | |

---

### P4: Temp: null, Top-p: 0.7
**Processing Time:** 41.88s | **Length:** 2636 chars (52%) ⚠️ **TOO SHORT**

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 4/10 | Base 9, -2 hallucination, -3 over-summarization |
| Artifact Removal | 10/10 | Perfect |
| Grammar Quality | 9/10 | Excellent grammar |
| Readability | 9/10 | Very clean |
| **Total** | **32/40 (80%)** | |

**Red Flags:** Hallucinated ending, severe over-summarization (52%)

---

### P5: Temp: null, Top-p: 0.9
**Processing Time:** 8.00s | **Length:** 4142 chars (82%)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 10/10 | All details preserved |
| Artifact Removal | 9/10 | All artifacts removed |
| Grammar Quality | 5/10 | 6+ unfixed transcription errors |
| Readability | 8/10 | Good structure |
| **Total** | **32/40 (80%)** | |

---

### P6: Temp: null, Top-p: 1.0
**Processing Time:** 4.39s | **Length:** 3632 chars (72%)

| Criterion | Score | Details |
|-----------|-------|---------|
| Content Accuracy | 8/10 | -2 for hallucinated ending |
| Artifact Removal | 10/10 | Perfect |
| Grammar Quality | 7/10 | Gender error |
| Readability | 9/10 | Excellent structure |
| **Total** | **34/40 (85%)** | |

**Red Flags:** Hallucinated ending about helping the girl

---

## CASE 3: Both Parameters (temperature + top_p)

**Status:** ✅ Complete (2025-11-30)
**Config:** B1 (temp=0.0, top_p=0.3)
**Runs:** 3 attempts

---

### B1 Summary: Combining Parameters is WORSE

**3 runs, 3 different outcomes:**
- v1: 31/40 (poor grammar)
- v2: **FAILED** (invalid JSON)
- v3: 25/40 (massive hallucination)

| Metric | T1 (temp=0.0 only) | P2 (top_p=0.3 only) | B1 (both) |
|--------|-------------------|---------------------|-----------|
| **Best Score** | **36/40 (90%)** ⭐ | **36/40 (90%)** | **31/40 (77.5%)** |
| **Consistency** | 1/1 (100%) | 1/1 (100%) | 2/3 (66%) |
| **Failures** | 0 | 0 | **1/3** |
| **Hallucinations** | None | None | **1/3** |

**Groq Documentation Warning Confirmed:** "We generally recommend altering only temperature OR top_p, not both."

**Recommendation:** **AVOID combining parameters** - use T1 (temp=0.0, top_p=null) for production.
