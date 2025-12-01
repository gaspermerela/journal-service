# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v8_paragraphs

← [Back to Prompt](./README.md) | [Back to Index](../README.md)

---

**Status:** ✅ Complete | **Best Score:** 35/40 (87.5%)

**Cache:** `cache/prompt_dream_v8/5beeaea1-967a-4569-9c84-eccad8797b95_meta-llama-llama-4-maverick-17b-128e-instruct/T*_v2.json`

**Test Date:** 2025-12-01
**Raw transcription length:** 5051 characters
**Schema Change:** Output format changed from `{"cleaned_text": "..."}` to `{"paragraphs": [...]}`

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

**Winner:** T5 (temp=1.0) - 35/40 ⭐

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

### Detailed Scores

| Config | Temp | Content | Artifacts | Grammar | Readability | **TOTAL** |
|--------|------|---------|-----------|---------|-------------|-----------|
| T1 | 0.0 | 8/10 | 10/10 | 7/10 | 6/10 | **31/40** |
| T2 | 0.3 | 8/10 | 9/10 | 7/10 | 6/10 | **30/40** |
| T3 | 0.5 | 7/10 | 10/10 | 7/10 | 8/10 | **32/40** |
| T4 | 0.8 | 7/10 | 10/10 | 7/10 | 8/10 | **32/40** |
| **T5** | **1.0** | **8/10** | **10/10** | **8/10** | **9/10** | **35/40** |
| T6 | 1.5 | 5/10 | 10/10 | 7/10 | 6/10 | **28/40** |
| T7 | 2.0 | 2/10 | 10/10 | 2/10 | 3/10 | **17/40** |

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

### T2 (temp=0.3) - 30/40
- **Length:** 3854 chars (76%) ✅ Good ratio
- **Paragraphs:** 19 - most fragmented of all configs
- **Content Accuracy (8/10):** Good detail preservation
  - ✅ All scenes present
  - ✅ "deset metrov široke" stairs width preserved
- **Artifact Removal (9/10):**
  - ✅ All "Hvala" removed
  - ❌ "v bistvu" still present once: "stopnice so bile tam v bistvu čisto zaobljene"
- **Grammar Quality (7/10):**
  - ✅ Fixed "bolnica" (only T2 in paragraphs schema!)
  - ❌ Tense mixing: "Sanje so se začele" (past) but "Hodim" (present)
  - ✅ No Russian word bug
- **Readability (6/10):** 19 paragraphs is excessive, breaks immersion

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

### T5 (temp=1.0) - 35/40 ⭐ BEST
- **Length:** 3199 chars (63%) - below 70% target but ALL content preserved
- **Paragraphs:** 11 - excellent scene-based structure matching dream narrative
- **Content Accuracy (8/10):** All scenes preserved:
  - ✅ Hospital intro: "Sanje se začnejo v veliki stavbi, ki je polnica"
  - ✅ Spray/cabinets: "odpiram omare in v njih vidim nekakšen sprej"
  - ✅ Dark corridor: "Praktično je skoraj samo tema"
  - ✅ Gyroscope: "giroskop, namenjen centrifugaciji krvi"
  - ✅ Hiding from people: "hitro grem skozi ena vrata na stran"
  - ✅ Difficult stairs: "Stopnice so zelo težke za hoditi, neenakomerne"
  - ✅ Falling: "izgubim ravnotežje in padnem po tleh"
  - ✅ Wide stairs with women: "Stopnice so bile zelo široke, deset metrov"
  - ✅ Deteriorating stairs: "zemlja in trava sta tam, kjer bi morale biti stopnice"
  - ✅ Girl who can't jump: "Ona si ne upa skočiti, jaz pa skočim"
- **Artifact Removal (10/10):** All artifacts removed, clean output
- **Grammar Quality (8/10):**
  - ✅ "Sanje se začnejo" - CORRECT present tense!
  - ✅ Consistent present tense throughout
  - ✅ No Russian word bug
  - ❌ "polnica" not fixed (should be "bolnica")
- **Readability (9/10):** Natural flow, authentic voice, clean paragraph breaks at scene transitions

### T6 (temp=1.5) - 28/40
- **Length:** 2286 chars (45%) ❌ SEVERE - below 50% threshold
- **Paragraphs:** 11
- **Content Accuracy (5/10):**
  - ❌ Over-summarized, many details lost
  - ❌ Stairs width not mentioned
  - ⚠️ Ending feels rushed
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

## Key Findings

1. **T5 (temp=1.0) is optimal** - best balance of quality, grammar, and structure
2. **Paragraphs schema works** - forces consistent scene breaks (11 paragraphs)
3. **Low temps (0.0-0.3) over-fragment** - 18-19 paragraphs is too many
4. **High temps (≥1.5) degrade** - content loss and gibberish
5. **Ratio is lower than v8** - 63% vs 81%, but output is more concise (not content loss)
6. **"polnica" still not fixed** - even T5 keeps the mishearing (unlike v8 T5 which fixed it!)
7. **No Russian word bug** - paragraphs schema eliminates the "приходят" bug seen in v8 T1-T2
8. **Better tense consistency** - T5 uses present tense throughout (v8 had mixing)

---

## Comparison Across All Prompts (maverick)

| Prompt | Type | Best Score | Config | Ratio | Key Achievement |
|--------|------|------------|--------|-------|-----------------|
| dream_v5 | Multi-task | 32/40 | T4 | 46% | - |
| dream_v7 | Multi-task | 35/40 | T2 | 69.5% | Russian word bug |
| **dream_v8** | Single-task | **38/40** | T5 | 81% | Fixed "bolnica" ⭐ |
| dream_v8_paragraphs | Single-task + schema | 35/40 | T5 | 63% | Guaranteed structure |

**Progression:** v5 → v7 → v8 improved scores. v8_paragraphs trades 3 points for structure guarantee.

---

## Comparison: v8 vs v8_paragraphs (T5)

| Metric | v8 T5 | v8_paragraphs T5 |
|--------|-------|------------------|
| Score | 38/40 | 35/40 |
| Length | 4106 chars | 3199 chars |
| Ratio | 81% | 63% |
| Structure | 1 blob | 11 paragraphs |
| Tense | Mixed | Present ✓ |
| "polnica" | Not fixed | Not fixed |

---

## Production Recommendation

For `meta-llama/llama-4-maverick-17b-128e-instruct`:
- **Prompt:** dream_v8_paragraphs
- **Temperature:** 1.0
- **Top-p:** null
- **Expected Score:** ~35/40
- **Processing Time:** ~22s
- **Output:** 11 paragraphs, ~3200 chars

**Trade-off:** Score drops 3 points (38→35) but paragraph structure is guaranteed.
