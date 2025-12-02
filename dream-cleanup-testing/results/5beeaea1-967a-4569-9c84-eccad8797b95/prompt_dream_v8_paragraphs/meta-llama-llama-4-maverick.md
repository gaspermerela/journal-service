# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v8_paragraphs

← [Back to Prompt](./README.md) | [Back to Index](../README.md)

---

**Status:** ⚠️ Complete - REVISED | **Best Score:** ~~35/40~~ → **32/40** (80%) T3/T4 | **Best Content:** T2 31/40 (7/7 phrases)

**Cache:** `cache/prompt_dream_v8/5beeaea1-967a-4569-9c84-eccad8797b95_meta-llama-llama-4-maverick-17b-128e-instruct/T*_v2.json`

**Test Date:** 2025-12-01
**Revised:** 2025-12-02 (content loss verification)
**Raw transcription length:** 5051 characters
**Schema Change:** Output format changed from `{"cleaned_text": "..."}` to `{"paragraphs": [...]}`

### ⚠️ CRITICAL REVISION

Initial scoring (35/40) was **incorrect**. Detailed verification revealed **significant content loss** that was not caught in initial review. See [Verified Content Loss](#verified-content-loss-t5) section below.

---

## What Changed from dream_v8

The `OUTPUT_SCHEMAS` in `app/config.py` was modified:

```python
# OLD (dream_v8)
"cleaned_text": {"type": "string", "required": True}

# NEW (dream_v8_paragraphs)
"paragraphs": {"type": "array", "item_type": "string", "required": True}
```

**Goal:** Force LLM to output structured paragraphs instead of free-form text blob.

---

## CASE 1: Temperature Only (top_p = null)

**Winner (REVISED):** T3/T4 (temp=0.5-0.8) - **32/40** (balanced content + structure)

**Previous Winner:** ~~T5 (temp=1.0) - 35/40~~ → **27/40** (demoted due to 0/7 content preservation)

**Best Content:** T2 (temp=0.3) - **31/40** with **7/7 key phrases** preserved

### Automated Checks

| Config | Temp | Length | Ratio | Paragraphs | "Hvala" | "v bistvu" | Time |
|--------|------|--------|-------|------------|---------|------------|------|
| T1 | 0.0 | 3468 | 69% | 18 | ✅ None | ✅ None | 3.6s |
| T2 | 0.3 | 3854 | 76% | 19 | ✅ None | ❌ 1x | 4.3s |
| T3 | 0.5 | 3285 | 65% | 11 | ✅ None | ✅ None | 12.6s |
| T4 | 0.8 | 3148 | 62% | 11 | ✅ None | ✅ None | 19.9s |
| **T5** | **1.0** | **3199** | **63%** | **11** | ✅ None | ✅ None | 22.0s |
| T6 | 1.5 | 2286 | 45% | 11 | ✅ None | ✅ None | 21.0s |
| T7 | 2.0 | 2064 | 41% | 9 | ✅ None | ✅ None | 52.8s |

### Detailed Scores (REVISED)

| Config | Temp | Content | Artifacts | Grammar | Readability | **TOTAL** | Notes |
|--------|------|---------|-----------|---------|-------------|-----------|-------|
| T1 | 0.0 | 8/10 | 10/10 | 7/10 | 6/10 | **31/40** | 5/7 phrases |
| **T2** | **0.3** | ~~8~~ **9/10** | **9/10** | **7/10** | **6/10** | ~~30~~ **31/40** | ⭐ **7/7 phrases** |
| T3 | 0.5 | 7/10 | 10/10 | 7/10 | 8/10 | **32/40** | 5/7 phrases |
| T4 | 0.8 | 7/10 | 10/10 | 7/10 | 8/10 | **32/40** | 5/7 phrases |
| **T5** | **1.0** | ~~8~~ **4/10** | **10/10** | **8/10** | **9/10** | ~~35~~ **27/40** | ⚠️ **0/7 phrases** |
| T6 | 1.5 | ~~5~~ **4/10** | 10/10 | 7/10 | 6/10 | ~~28~~ **27/40** | 2/7 phrases |
| T7 | 2.0 | 2/10 | 10/10 | 2/10 | 3/10 | **17/40** | 1/7 gibberish |

**⚠️ Revisions based on content verification:**
- **T2:** Content 8→9/10 (7/7 key phrases preserved) → Total: 31/40
- **T5:** Content 8→4/10 (0/7 key phrases) → Total: 27/40
- **T6:** Content 5→4/10 (2/7 key phrases) → Total: 27/40

---

## Config Analysis

### T1 (temp=0.0) - 31/40
a- **Length:** 3468 chars (69%) - slightly below 70% target
- **Paragraphs:** 18 - over-fragmented (should be ~10-12)
- **Content Accuracy (8/10):** All details present
  - ❌ Misinterpretation: "Preden sem prišel v službo, ljudje odpirajo omare" (should be: I open cabinets before PEOPLE arrive)
  - ✅ Spray detail preserved
  - ✅ 10m stairs width mentioned
- **Artifact Removal (10/10):** All "Hvala" removed, no fillers
- **Grammar Quality (7/10):**
  - ❌ "polnica" not fixed (should be "bolnica")
  - ❌ Tense mixing throughout
  - ✅ No Russian word bug (unlike v8 T1!)
- **Readability (6/10):** Too many tiny paragraphs break narrative flow

### T2 (temp=0.3) - ~~30/40~~ → **31/40** ⭐ BEST CONTENT
- **Length:** 3854 chars (76.3%) ✅ Best ratio of all configs
- **Paragraphs:** 19 - most fragmented of all configs
- **Content Accuracy (~~8~~ 9/10):** ⭐ **BEST content preservation - 7/7 key phrases!**
  - ✅ "našpricali neke vrste sprej" - spray action preserved
  - ✅ "vzpodbudi in govori" - "speaks to me" preserved
  - ✅ "napol tek nazdolj" - "half-running" preserved
  - ✅ "okoli pet, šest, sedem" - specific numbers preserved
  - ✅ "Spetam par metrov v stran" - spatial detail preserved
  - ✅ "hodnik, levo-desno" - corridor direction preserved
  - ✅ "ne spomnim veliko detajlov" - memory marker preserved!
  - ✅ "deset metrov široke" - stairs width preserved
- **Artifact Removal (9/10):**
  - ✅ All "Hvala" removed
  - ❌ "v bistvu" still present once: "stopnice so bile tam v bistvu čisto zaobljene"
- **Grammar Quality (7/10):**
  - ✅ Fixed "bolnica" (only T2 in paragraphs schema!)
  - ❌ Tense mixing: "Sanje so se začele" (past) but "Hodim" (present)
  - ✅ No Russian word bug
- **Readability (6/10):** 19 paragraphs is excessive, breaks immersion

**⚠️ T2 Paradox:** Has BEST content preservation but worst structure. If content is prioritized over readability, T2 is the winner.

### T3 (temp=0.5) - 32/40
- **Length:** 3285 chars (65%) - below 70% target
- **Paragraphs:** 11 - optimal scene-based structure
- **Content Accuracy (7/10):**
  - ✅ All scenes present
  - ⚠️ Some details condensed
- **Artifact Removal (10/10):** Clean output
- **Grammar Quality (7/10):**
  - ❌ "Sanje so se začele" (past tense, should be present)
  - ❌ "Hkrati me je bilo strah" (grammatical error)
  - ❌ "polnica" not fixed
- **Readability (8/10):** Good structure, natural flow

### T4 (temp=0.8) - 32/40
- **Length:** 3148 chars (62%) - below target
- **Paragraphs:** 11 - optimal
- **Content Accuracy (7/10):**
  - ✅ All scenes present
  - ⚠️ Slightly condensed
- **Artifact Removal (10/10):** Clean output
- **Grammar Quality (7/10):**
  - ❌ "spodbud" typo (should be "spodbudo")
  - ❌ Tense mixing persists
  - ❌ "polnica" not fixed
- **Readability (8/10):** Good structure

### T5 (temp=1.0) - ~~35/40~~ → 27/40 ⚠️ REVISED
- **Length:** 3199 chars (63%) - below 70% target, **significant content loss confirmed**
- **Paragraphs:** 11 - good scene-based structure
- **Content Accuracy (~~8~~ 4/10):** ⚠️ **MAJOR REVISION** - 7+ important details lost (see verified content loss below)
- **Artifact Removal (10/10):** All artifacts removed, clean output
- **Grammar Quality (8/10):**
  - ✅ "Sanje se začnejo" - CORRECT present tense!
  - ✅ Consistent present tense throughout
  - ✅ No Russian word bug
  - ❌ "polnica" not fixed (should be "bolnica")
- **Readability (9/10):** Natural flow, authentic voice, clean paragraph breaks at scene transitions

---

## Verified Content Preservation (ALL Configs)

**Verification method:** Direct string comparison against 7 key phrases from raw transcription.

### Content Verification Matrix

| Config | Temp | Ratio | šprical | govori | napol tek | 5,6,7 | par metrov | levo-desno | ne spomnim | **Score** |
|--------|------|-------|---------|--------|-----------|-------|------------|------------|------------|-----------|
| T1 | 0.0 | 68.7% | ✅ škropijo | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | 5/7 |
| **T2** | **0.3** | **76.3%** | ✅ našpricali | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **7/7** ⭐ |
| T3 | 0.5 | 65.0% | ✅ | ✅ | ⚠️ skoraj tek | ✅ | ❌ | ✅ | ❌ | 5/7 |
| T4 | 0.8 | 62.3% | ✅ | ✅ | ✅ | ✅ | ⚠️ nekaj | ❌ | ❌ | 5/7 |
| **T5** | **1.0** | **63.3%** | ❌ vidim | ❌ | ❌ hojo/tekom | ❌ nekaj | ❌ | ❌ | ❌ | **0/7** ❌ |
| T6 | 1.5 | 45.3% | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | 2/7 |
| T7 | 2.0 | 40.9% | ⚠️ | gibberish | gibberish | gibberish | gibberish | gibberish | gibberish | 1/7 |

### ⚠️ Critical Discovery

**T2 (temp=0.3) has BEST content preservation (7/7 phrases)!**
**T5 (temp=1.0) has WORST content among mid-temps (0/7 phrases)!**

This reveals a **paradox**: T5 was rated highest overall (35/40) due to excellent readability, but has the WORST content preservation. T2 was rated lower (30/40) due to over-fragmentation but preserves ALL important details.

### Content vs Readability Trade-off

| Config | Content Score | Readability Score | Paragraphs | Trade-off |
|--------|---------------|-------------------|------------|-----------|
| **T2** | **9/10** (7/7 phrases) | 6/10 | 19 | Best content, worst structure |
| T5 | 4/10 (0/7 phrases) | 9/10 | 11 | Best structure, worst content |

---

## Verified Content Loss (T5)

**Verification method:** Direct string comparison between raw transcription and T5_v2 cleaned output.

| # | Original (Raw) | T5_v2 Cleanup | Problem |
|---|----------------|---------------|---------|
| 1 | "v njih **šprical** neke vrste sprej" | "v njih **vidim** nekakšen sprej" | ❌ **ACTION CHANGED** - spraying → seeing |
| 2 | "zvok ki mi vzpodguja **in govori**" | "vzpodbudi" | ❌ **LOST** - mystical "speaks to me" detail |
| 3 | "niso bile tako samo stopnice ampak... ravnine, pa spet na stopnic, pa v mestu odhodniki" | "malo več dogaja" | ❌ **LOST** - stair structure (platforms, corridors) |
| 4 | "hodnik, **levo-desno**" | Missing | ❌ **LOST** - corridor direction |
| 5 | "**napol tek** nazdolj in nazdolj" | "hojo oziroma tekom" | ❌ **GENERALIZED** - "half-running" → generic "running" |
| 6 | "jaz sem vsej **nadreval** dol" | Missing | ❌ **LOST** - rushing/hurrying urgency |
| 7 | "tako preko ene **pet, šest, sedem**" | "nekaj ljudi" | ❌ **LOST** - specific numbers |
| 8 | "**spedam par metrov** v stran" | Missing | ❌ **LOST** - spatial positioning |
| 9 | "In zgleda kot, da jih te stopnice nič ne motijo" | "Ženske ne delajo težav zaradi stopnic" | ❌ **MEANING CHANGED** - "stairs don't bother THEM" ≠ "they don't cause problems" |
| 10 | "notakrat naprej **se ne spomnim več** velik od tega dela" | Missing | ❌ **LOST** - dream ending marker |

**Impact:** 7+ verified content losses = Content Accuracy drops from 8/10 to **4/10**. Total score: 27/40.

### T6 (temp=1.5) - ~~28/40~~ → **27/40**
- **Length:** 2286 chars (45.3%) ❌ SEVERE - below 50% threshold
- **Paragraphs:** 11
- **Content Accuracy (~~5~~ 4/10):** Only 2/7 key phrases preserved
  - ❌ Over-summarized, many details lost
  - ❌ Stairs width not mentioned
  - ✅ "ne spomnim več" - memory marker preserved
  - ❌ Most other key phrases lost
- **Artifact Removal (10/10):** Clean
- **Grammar Quality (7/10):**
  - ❌ "neenakomern stopnicah" - typo/agreement error
  - ⚠️ Quality degrading
- **Readability (6/10):** Feels rushed, lacks dream-like immersion

### T7 (temp=2.0) - 17/40 ❌ UNUSABLE
- **Length:** 2064 chars (41%) ❌ SEVERE content loss
- **Paragraphs:** 9 - fewer than optimal
- **Content Accuracy (2/10):**
  - ❌ Later paragraphs are GIBBERISH
  - ❌ Many scenes missing or corrupted
- **Artifact Removal (10/10):** Technically clean (but text is broken)
- **Grammar Quality (2/10):**
  - ❌ Unintelligible: "rav storm v obl razil h. naz bil ni t."
  - ❌ Complete breakdown: "jaz z sk pl in po n sk n"
  - ❌ Temperature too high causes token prediction failure
- **Readability (3/10):** Broken, unusable for any purpose
- **Processing Time:** 52.8s (2.5x longer than T5 due to repeated token sampling failures)

---

## Paragraph Count Pattern

| Temp Range | Paragraph Count | Assessment |
|------------|-----------------|------------|
| 0.0 - 0.3 | 18-19 | ❌ Over-fragmented |
| 0.5 - 1.0 | 11 | ✅ Optimal |
| 1.5 | 11 | ⚠️ Count OK, content lost |
| 2.0 | 9 | ❌ Under-fragmented + gibberish |

**Optimal paragraph count:** 11 (maps to dream's natural scene structure)

**Pattern:** Temperature affects paragraph granularity:
- Low temps (deterministic) = more splits = tiny paragraphs
- Mid temps (balanced) = natural scene breaks
- High temps (random) = merging + content loss

---

## Key Findings (REVISED)

1. ⚠️ **Paragraphs schema causes over-summarization** - 63% ratio is NOT "concise", it's content loss
2. ⭐ **T2 has BEST content preservation (7/7 phrases)** - but worst readability (19 paragraphs)
3. ⚠️ **T5 loses 7+ important details (0/7 phrases)** - actions changed, numbers lost, spatial details removed
4. ⚠️ **Content vs Readability paradox** - higher temps improve readability but destroy content
5. **Low temps (0.0-0.3) over-fragment** - 18-19 paragraphs is too many, but PRESERVE CONTENT
6. **High temps (≥1.0) lose content** - T5, T6, T7 all have severe content loss (0-2/7 phrases)
7. **"polnica" only fixed by T2** - only low-temp T2 fixes the mishearing (unlike v8 T5)
8. **No Russian word bug** - paragraphs schema eliminates the "приходят" bug seen in v8 T1-T2

### Content Preservation Ranking

| Rank | Config | Temp | Content | Phrases | Trade-off |
|------|--------|------|---------|---------|-----------|
| 1 | **T2** | 0.3 | **9/10** | **7/7** | Best content, over-fragmented |
| 2 | T1/T3/T4 | 0.0-0.8 | 7-8/10 | 5/7 | Good content, varied structure |
| 3 | T5 | 1.0 | 4/10 | 0/7 | Best readability, worst content |
| 4 | T6 | 1.5 | 4/10 | 2/7 | Poor everything |
| 5 | T7 | 2.0 | 2/10 | 1/7 | Gibberish |

### Critical Learning

The paragraphs schema **encourages over-summarization**. When the LLM is forced to output structured paragraphs, it tends to condense content to fit the structure, losing:
- Specific action verbs (spray → see)
- Specific numbers (5,6,7 → "some")
- Spatial details (left-right, meters)
- Mystical/unusual details ("the sound speaks to me")
- Memory markers ("I don't remember")

**This is a prompt engineering failure, not a model failure.**

---

## Comparison Across All Prompts (maverick) - REVISED

| Prompt | Type | Best Score | Config | Ratio | Key Issue |
|--------|------|------------|--------|-------|-----------|
| dream_v5 | Multi-task | 32/40 | T4 | 46% | Over-summarized |
| dream_v7 | Multi-task | 35/40 | T2 | 69.5% | Russian word bug |
| **dream_v8** | Single-task | **38/40** | T5 | 81% | **BEST** - Fixed "bolnica" ⭐ |
| dream_v8_paragraphs | Single-task + schema | ~~35~~ **27/40** | T5 | 63% | ❌ **Content loss** |

**Conclusion:** v8_paragraphs is NOT an improvement. The paragraphs schema causes content loss.

---

## Comparison: v8 vs v8_paragraphs (T5) - REVISED

| Metric | v8 T5 | v8_paragraphs T5 |
|--------|-------|------------------|
| Score | **38/40** | ~~35~~ 27/40 |
| Length | 4106 chars | 3199 chars |
| Ratio | 81% ✅ | 63% ❌ |
| Structure | 1 blob | 11 paragraphs |
| Tense | Mixed | Present ✓ |
| "polnica" | Fixed ✅ | Not fixed ❌ |
| Content Loss | None verified | **7+ details lost** ❌ |

---

## Production Recommendation - REVISED

### ❌ DO NOT USE dream_v8_paragraphs

The paragraphs schema causes significant content loss. For production, use:

**Recommended:**
- **Prompt:** dream_v8 (original, without paragraphs schema)
- **Temperature:** 1.0
- **Top-p:** null
- **Expected Score:** 38/40
- **Processing Time:** ~21s

### Next Steps

1. **Create dream_v9** - new generic prompt with explicit content preservation rules
2. **Add RED FLAGS** to prompt: "Never change action verbs", "Never remove specific numbers"
3. **Add self-validation** checklist to prompt
4. **Test paragraph structure** via prompt instructions, not schema constraint
