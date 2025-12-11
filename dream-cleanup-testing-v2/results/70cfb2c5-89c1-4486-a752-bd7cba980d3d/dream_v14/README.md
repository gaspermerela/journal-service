# dream_v14 Results

<- [Back to Index](../README.md)

---

**Prompt:** dream_v14 (HARD REQUIREMENT: 75% minimum length)
**Test Date:** 2025-12-10
**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Raw Length:** 5,013 characters

---

## Summary

| Metric | Value |
|--------|-------|
| **Best Score** | 93/100 (T1_v1, v5, v7, v9) |
| **Worst Score** | 82/100 (T1_v3) |
| **EXCELLENT Rate** | 40% (4/10 runs) |
| **Status** | **NOT PRODUCTION READY** |

---

## Critical Finding: HARD REQUIREMENT Ineffective

dream_v14 added explicit HARD REQUIREMENT for 75% minimum length:

```
HARD REQUIREMENT - OUTPUT WILL BE REJECTED IF VIOLATED:
The cleaned text MUST contain at least 75% of the original character count.
If your output is shorter than 75%, START OVER and include more details.
```

**Result: The model ignores this requirement.**

| Metric | dream_v13 | dream_v14 | Change |
|--------|-----------|-----------|--------|
| >=75% Length | 64% | **50%** | -14% worse |
| EXCELLENT Rate | 64% | **40%** | -24% worse |
| Cyrillic Bugs | 7% | 0% | Fixed |
| G13 (nazdolj) | 0% fixed | **100% fixed** | Major improvement |

---

## Extended Variance Testing (10 Runs)

| Run | Ratio | G | C | R | H | L | Total | Status |
|-----|-------|---|---|---|---|---|-------|--------|
| T1_v1 | 89.2% | 24 | 41 | 15 | 8 | 5 | **93** | EXCELLENT |
| T1_v2 | 69.6% | 24 | 36 | 15 | 6 | 3 | **84** | PASS |
| T1_v3 | 61.7% | 22 | 34 | 15 | 8 | 3 | **82** | PASS |
| T1_v4 | 91.1% | 24 | 37 | 15 | 8 | 5 | **89** | VOICE |
| T1_v5 | 85.2% | 24 | 41 | 15 | 8 | 5 | **93** | EXCELLENT |
| T1_v6 | 69.4% | 24 | 37 | 15 | 8 | 3 | **87** | PASS |
| T1_v7 | 89.9% | 24 | 41 | 15 | 8 | 5 | **93** | EXCELLENT |
| T1_v8 | 68.8% | 24 | 37 | 15 | 8 | 3 | **87** | PASS |
| T1_v9 | 91.7% | 24 | 41 | 15 | 8 | 5 | **93** | EXCELLENT |
| T1_v10 | 63.3% | 23 | 36 | 15 | 6 | 3 | **83** | PASS |

---

## Key Observations

### Improvement: G13 Now Fixed (100%)

All runs correctly convert "nazdolj" -> "navzdol". This was a 100% failure in v13.
Likely due to model training changes, not the prompt.

### Problem: Bimodal Length Distribution

| Length Bucket | Runs | Rate |
|---------------|------|------|
| 85%+ | v1, v4, v5, v7, v9 | 50% |
| 60-70% | v2, v3, v6, v8, v10 | 50% |

No runs in 70-84% range. Model decides early on compression level.

### Problem: Voice Issues (v4)

v4 uses past tense throughout despite prompt requiring present tense:
- "Sanje so se zacele" (should be "Sanje se zacnejo")
- "Hodil sem" (should be "Hodim")

### Problem: Universal Hallucination (H1)

100% of runs contain "smo prisli" or "Skupaj pridemo" - implying walking together with the woman. Original says he MET her, not walked with her.

---

## Consistent Failures (100% of runs)

- **G21:** "obhodnikov" not fixed to "hodnikov"
- **C23:** Flat areas + corridors detail always missing
- **H1:** "smo prisli" hallucination

---

## Prompt Text (dream_v14)

```
Clean this Slovenian dream transcription for a personal journal. The input was captured with speech-to-text (STT) software.

HARD REQUIREMENT - OUTPUT WILL BE REJECTED IF VIOLATED:
The cleaned text MUST contain at least 75% of the original character count.
If your output is shorter than 75%, START OVER and include more details.
Calculate: If original is ~5000 chars, your output must be >=3750 chars.

CRITICAL - DO NOT LOSE CONTENT:
- KEEP EVERY detail: actions, objects, people, numbers, locations, feelings.
- KEEP ALL unusual/strange details exactly as stated - these are the most important in dreams.
- DO NOT change who performs an action (if "I" do something, don't change it to "they did").
- DO write in present tense, first person singular ("jaz") and keep the personal, spoken narrative style.

FIX:
- Grammar, spelling, punctuation (use "knjizna slovenscina")
- STT mishearings: p<->b (polnica->bolnica), e<->i (predem->pridem), missing syllables
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

## Recommendations

### HARD REQUIREMENT Does Not Work

Explicit length requirements in prompts are ignored by the maverick model.
Alternative approaches needed:
1. Post-processing validation with retry
2. Different model (llama-3.3-70b-versatile)
3. Structured output format with token counting

### Add STT Fix for G21

Add "obhodnikov -> hodnikov" to explicit STT mishearings list.

### H1 Hallucination Unavoidable

May need explicit instruction: "If the narrator MET someone, do not imply they walked TOGETHER."

---

## Model Files

- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md) - Full 10-run analysis
