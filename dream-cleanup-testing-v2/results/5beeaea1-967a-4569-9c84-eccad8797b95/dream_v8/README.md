# dream_v8 Results

← [Back to Index](../README.md)

**Prompt ID:** 390
**Prompt Type:** Single-task (cleaned_text only - themes/emotions/etc NOT populated)

---

## Prompt Text

<details>
<summary>Click to expand full prompt text</summary>

```
Clean this Slovenian dream transcription for a personal journal.

RULES:
1. Fix grammar, spelling, punctuation. Use "knjižna slovenščina".
2. Write in present tense, first person ("jaz").
3. Break into short paragraphs (one scene/moment each).
4. Remove only STT artifacts: filler words ("v bistvu", "torej"), false starts, repeated words, audio junk ("Hvala").
5. KEEP EVERY specific detail - actions, objects, descriptions, sensory details, feelings. Unusual or strange details are ESPECIALLY important to preserve exactly as stated.
6. Do NOT summarize. Do NOT shorten. Do NOT invent or explain anything not in the original.
7. Fix obvious mishearings

OUTPUT FORMAT:
Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "cleaned_text": "The cleaned version here"
}}',

TRANSCRIPTION:
"{transcription_text}"
```

</details>

---

## Best Results (Tied)

| Model | Config | Score | Status |
|-------|--------|-------|--------|
| meta-llama/llama-4-maverick-17b-128e-instruct | T5 | 87/100 | PASS |
| llama-3.3-70b-versatile | P4 | 87/100 | PASS |

---

## Model Comparison

| Model | Best Config | Score | G/25 | C/45 | R/15 | H/10 | L/5 | Status | Key Failures |
|-------|-------------|-------|------|------|------|------|-----|--------|--------------|
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T5 | 87/100 | 20 | 41 | 11 | 10 | 5 | PASS | G1 never fixed; R1 partial; Russian leak in T1/T2/P1 |
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) | P4 | 87/100 | 18 | 43 | 11 | 10 | 5 | PASS | G1 fixed in P4; G25, G27, G28 never fixed; R1 none |
| [gpt-oss-120b](./openai-gpt-oss-120b.md) | P1 | 73/100 | 20 | 27 | 15 | 10 | 1 | REVIEW | Over-summarized (52%); Best R1/paragraphs; Only fixes G1 |

---

## Summary Statistics

### Parameter Test Coverage

| Model | T1-T7 | P1-P6 | B1-B4 | Total Configs |
|-------|-------|-------|-------|---------------|
| llama-3.3-70b-versatile | ✅ 7/7 | ✅ 6/6 | ❌ 0/4 | 13 |
| maverick-17b | ✅ 7/7 | ✅ 6/6 | ❌ 0/4 | 13 |
| gpt-oss-120b | ✅ 7/7 | ✅ 6/6 | ❌ 0/4 | 13 |

## Key Findings

### Grammar (G)

| Checkpoint | llama-3.3 | maverick | gpt-oss | Notes |
|------------|-----------|----------|---------|-------|
| G1 (polnica→bolnica) | ✅ P4 only | ✅ P5 only | ✅ Fixed | llama P4, maverick P5, gpt-oss fix |
| G++ (Russian leak) | ✅ Clean | ⚠️ T1,T2,P1-P4 | ✅ Clean | maverick has "приходят" at low top_p |
| G25 (garbled phrase) | ❌ Never | ✅ Often | ✅ Often | maverick/gpt better |
| G27, G28 | ❌ Never | ⚠️ Sometimes | ✅ Often | llama worst |

### Content (C)

| Check | llama-3.3 | maverick | gpt-oss | Notes |
|-------|-----------|----------|---------|-------|
| C+++ (length 70-95%) | ✅ 70-88% | ✅ 69-82% | ❌ 49-58% | gpt severely over-summarizes |
| C++ (hallucinations) | ✅ None | ✅ None | ❌ Present | gpt adds content |
| Detail preservation | Good | Good | Poor | gpt loses 40-50% |

### Artifacts (A)

| Check | llama-3.3 | maverick | gpt-oss |
|-------|-----------|----------|---------|
| A1 (Hvala removed) | ✅ | ✅ | ✅ |
| A2 (intro kept) | Sometimes | ❌ Removed | Sometimes |
| A3 (fillers) | ⚠️ Some kept | ⚠️ Some kept | ✅ Reduced |

### Readability (R)

| Check | llama-3.3 | maverick | gpt-oss |
|-------|-----------|----------|---------|
| R1 (paragraphs) | ❌ None | ⚠️ Partial | ✅ Full |
| R2 (flow) | ✅ | ✅ | ✅ |
| R3 (voice) | ✅ | ✅ | ⚠️ Shifts |
| R4 (coherence) | ✅ | ✅ | ✅ |

---

## Recommendations

### Best Model for dream_v8

**Tied Winners:** maverick T5 and llama P4 (both 87/100 PASS)

**maverick T5:**
- Better grammar (G=20 vs 18)
- Partial paragraph structure
- Avoid T1, T2, P1 due to Russian contamination (G++ -5 penalty)

**llama P4:**
- Better content preservation (C=43 vs 41)
- Fixes G1 (polnica→bolnica)
- No paragraph structure
- More consistent across configs

### Model-Specific Notes

1. **maverick-17b** (Best: T5 @ 87/100)
   - Use T3 or T5 only
   - Highest overall score
   - Watch for Russian leak at low temperatures
   - G1 never fixed, R1 partial paragraphs

2. **llama-3.3-70b-versatile** (Best: P4 @ 87/100)
   - Use P4 (best config) - ties with maverick T5
   - P4 fixes G1! Best content preservation (C=43)
   - Never fixes G25, G27, G28
   - No paragraph structure (R1=0)
   - Very consistent across configs

3. **gpt-oss-120b** (Best: P1 @ 73/100)
   - NOT recommended for production
   - Severe over-summarization (loses 40-50% content)
   - Best paragraph structure (R1=1, only model with full paragraphs)
   - Fixes G1 consistently (llama/maverick only in best configs)
   - Useful for studying paragraph formatting

### Prompt v9 Suggestions

1. Add explicit G1 example: `"polnica" je narobe, pravilno: "bolnica"`
2. Add Russian prohibition: `Besedilo mora biti SAMO v slovenščini (brez cirilice, angleščine, ruščine)`
3. Require paragraphs: `Razdeli besedilo v odstavke, ločene s prazno vrstico (\n\n)`
4. Add over-summarization guard: `NE povzemaj. Ohrani VSE podrobnosti iz originalnega besedila.`

---

## Appendix: Grammar Checkpoint Status

| ID | Raw | Correct | Status |
|----|-----|---------|--------|
| G1 | polnica | bolnica | ✅ Fixed by llama P4, maverick P5, gpt-oss |
| G17 | mogo | moral | ❌ Rarely fixed |
| G23 | prublev čimprej | probam čimprej | ❌ Rarely fixed |
