# dream_v13 Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v13 (Fixed present tense + output format)
**Test Date:** 2025-12-10
**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Raw Length:** 5,013 characters

---

## Best Results Summary

| Model | Best Config | Score | Status | Key Finding |
|-------|-------------|-------|--------|-------------|
| **[maverick-17b](./meta-llama-llama-4-maverick-17b-128e-instruct.md)** | T1_v1/v2 | **91/100** | EXCELLENT | Voice fixed, no header artifact |

---

## Variance Testing Results

**Key finding:** Very consistent results - all runs in EXCELLENT range (90-91).

| Run | Length | Score | Status |
|-----|--------|-------|--------|
| T1_v1 | 74.6% | **91** | EXCELLENT |
| T1_v2 | 75.9% | **91** | EXCELLENT |
| T1_v3 | 75.7% | **90** | EXCELLENT |
| T1_v4 | 73.7% | **90** | EXCELLENT |

| Metric | Min | Max | Range |
|--------|-----|-----|-------|
| Length | 73.7% | 75.9% | 2.2% |
| Score | 90 | 91 | 1 pt |

---

## Key Changes from v12

1. **Added present tense in CRITICAL:** `⚠️ DO write in present tense, first person singular ("jaz")`
2. **Added OUTPUT FORMAT:** `Respond ONLY with the cleaned text.`
3. **Reorganized REMOVE section:** Clearer structure

---

## Prompt Text (dream_v13)

```
Clean this Slovenian dream transcription for a personal journal. The input was captured with speech-to-text (STT) software.

CRITICAL - DO NOT LOSE CONTENT:
⚠️ Cleaned text MUST be at least 75% of the original length.
⚠️ KEEP EVERY detail: actions, objects, people, numbers, locations, feelings.
⚠️ KEEP ALL unusual/strange details exactly as stated - these are the most important in dreams.
⚠️ DO NOT change who performs an action (if "I" do something, don't change it to "they did").
⚠️ DO write in present tense, first person singular ("jaz") and keep the personal, spoken narrative style.

FIX:
- Grammar, spelling, punctuation (use "knjižna slovenščina")
- STT mishearings: p↔b (polnica→bolnica), e↔i (predem→pridem), missing syllables
- Garbled phrases: reconstruct meaning from context

REMOVE:
- Filler words (not exhaustive list): "v bistvu", "torej", "a ne", "no"
- STT noise: "Hvala", "Hvala za pozornost", recording intros/outros
- False starts and word repetitions that do not make sense
- Do NOT remove content that carries meaning, even if informal.

FORMAT:
- Present tense, first person ("jaz")
- Paragraphs separated by "<break>" (NOT \n)
- New paragraph at: scene changes, location changes, new events

OUTPUT FORMAT:
Respond ONLY with the cleaned text.

TRANSCRIPTION:
"{transcription_text}"
```

---

## Key Findings

### What Worked
- **Voice fixed:** Present tense instruction in CRITICAL section worked (-3 penalty vs -7 in v12)
- **No header artifact:** OUTPUT FORMAT instruction prevented "Here is the cleaned..."
- **Tight variance:** 2.2% length range vs 7.5% in v12
- **All EXCELLENT:** Every run scores 90-91

### Remaining Issues
- **C23:** Flat areas + corridors still missing (all runs)
- **G13/G20/G21:** Same STT fixes still failing ("nazdolj", "obhodnikov")
- **H1:** "smo prišli" hallucination (implies walked together)

---

## Comparison: v12 vs v13

| Metric | v12 (best) | v13 (best) | Delta |
|--------|------------|------------|-------|
| **Total** | 85 | **91** | **+6** |
| Content | 37 | 40 | +3 |
| Grammar | 22 | 23 | +1 |
| Readability | 15 | 15 | 0 |
| Voice penalty | -7 | -3 | **+4** |
| Length variance | 7.5% | 2.2% | **-5.3%** |
| Score variance | 3 pts | 1 pt | **-2 pts** |

---

## Scoring Comparison (All Runs)

| Model | Run | Length | G | C | R | H | L | Total | Status |
|-------|-----|--------|---|---|---|---|---|-------|--------|
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T1_v1 | 74.6% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T1_v2 | 75.9% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T1_v3 | 75.7% | 23 | 39 | 15 | 8 | 5 | **90** | EXCELLENT |
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T1_v4 | 73.7% | 22 | 40 | 15 | 8 | 5 | **90** | EXCELLENT |

---

## Recommendations

1. **Production ready:** v13 achieves EXCELLENT threshold consistently
2. **Optional improvements:**
   - Add "nazdolj→navzdol" to STT mishearings
   - Add "obhodnikov→hodnikov" to STT mishearings
   - Add instruction about preserving individual agency

---

## Model Files

- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md) - Detailed scoring for all T1 runs
