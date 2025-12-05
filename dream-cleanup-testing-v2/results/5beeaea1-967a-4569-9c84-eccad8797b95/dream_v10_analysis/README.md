# dream_v10_analysis Results

<- [Back to Index](../README.md)

---

**Prompt:** dream_v10_analysis (English instructions with analysis fields + `<break>` markers)
**Test Date:** 2025-12-05
**Transcription ID:** 5beeaea1-967a-4569-9c84-eccad8797b95
**Raw Length:** 5,051 characters

---

## Best Results Summary

| Model | Best Config | Score | Status | Key Finding |
|-------|-------------|-------|--------|-------------|
| **[maverick-17b](./meta-llama-llama-4-maverick-17b-128e-instruct.md)** | T1 | **87/100** | **PASS** | Good cleanup but over-summarizes |
| [scout-17b](./meta-llama-llama-4-scout-17b-16e-instruct.md) | T5 | 83/100 | PASS | Only adds paragraphs, no grammar fixes |

---

## Prompt Text (dream_v10_analysis)

```
Clean this Slovenian dream transcription for a personal journal. The input was captured with speech-to-text (STT) software.

RULES:

1. GRAMMAR & STT FIXES
   - Fix spelling, grammar, punctuation. Use "knjižna slovenščina".
   - Fix common STT mishearings where the wrong letter was heard:
     * p↔b confusion (e.g., "polnica"→"bolnica", "stapo"→"stavbo")
     * e↔i confusion (e.g., "pretličje"→"pritličje", "predem"→"pridem")
     * Missing/extra syllables (e.g., "obhodnik"→"hodnik", "uspodbuda"→"vzpodbuda")
   - For garbled/unintelligible phrases: reconstruct the likely intended meaning from context, or if truly unclear, simplify to preserve the action/meaning.

2. VOICE & TENSE
   - Write in present tense, first person singular ("jaz").
   - Keep the personal, spoken narrative style.

3. PARAGRAPH STRUCTURE
   - Break into short paragraphs separated by a "<break>" and NOT BY \n characters!
   - Start a new paragraph at: scene changes, location changes, new events, emotional shifts.
   - Each paragraph should be 2-5 sentences.

4. REMOVE ARTIFACTS ONLY
   - Remove STT artifacts: filler words ("v bistvu", "torej", "a ne", "no"), false starts, repeated words, audio noise markers ("Hvala").
   - Remove recording intro/outro phrases (e.g., "Zdravstveno, da ste pripravljeni" or similar).
   - Do NOT remove content that carries meaning, even if informal.

5. PRESERVE ALL CONTENT
   - KEEP EVERY specific detail: actions, objects, descriptions, sensory details, feelings, locations.
   - KEEP specific numbers and measurements exactly as stated (e.g., "10 meters", "5 people", "4 AM").
   - KEEP unusual or strange details EXACTLY as described - these are especially important in dreams.
   - KEEP movement descriptions precisely (e.g., "half-running" vs "walking", "jumping" vs "stepping").

6. DO NOT
   - Do NOT summarize or shorten.
   - Do NOT combine multiple details into generalizations.
   - Do NOT invent, explain, or add anything not in the original.
   - Do NOT use Russian, Cyrillic, or English words - output must be 100% Slovenian.

OUTPUT FORMAT:
Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "cleaned_text": "string",
  "themes": ["string"],
  "emotions": ["string"],
  "characters": ["string"],
  "locations": ["string"]
}}
```

---

## JSON Parsing Fix Applied

The `<break>` marker solution was implemented to fix JSON parsing issues:

1. **Problem:** LLMs at higher temperatures output literal newlines instead of escaped `\n\n`, causing "Invalid control character" JSON errors
2. **Solution:** Prompt now instructs to use `<break>` markers; backend converts to `\n\n` after JSON parsing
3. **Result:**
   - Maverick: 29% → **100%** success (7/7)
   - Scout: 94% → **86%** success (6/7) - T6 fails with different error

---

## Model Comparison (Best Configs)

| Metric | Maverick T1 | Scout T5 | Winner |
|--------|-------------|----------|--------|
| **Score** | 87/100 | 83/100 | **Maverick** |
| **Status** | PASS | PASS | Tie |
| **Processing** | 3.66s | 4.96s | Maverick |
| **Length** | 51% | 94% | **Scout** (optimal range) |
| **Grammar (G/25)** | 24 | 18 | **Maverick** |
| **Content (C/45)** | 37 | 42 | **Scout** |
| **Readability (R/15)** | 15 | 8 | **Maverick** |
| **G1 (bolnica)** | FIXED | NOT fixed | **Maverick** |
| **C34 (10m width)** | MISSING | PRESERVED | **Scout** |

---

## Key Findings

### 1. Maverick over-summarizes with analysis prompt

- **51% of original** (should be 70-95%)
- Loses specific details: 10m width (C34), exact people count (C32)
- Good grammar and readability, but too aggressive
- Higher temps (T5, T6) preserve more details but introduce risks

### 2. Scout needs temp=1.0 to add structure

- T1-T4 (temp=0.0-0.8): **97-99% of original** - no cleanup at all
- **T5 (temp=1.0): 94%** - adds paragraph breaks, best scout config
- T7 (temp=2.0): Output degrades into gibberish

### 3. Analysis prompt degrades cleanup quality

Comparing to dream_v10 (same models, no analysis fields):

| Model | dream_v10 | dream_v10_analysis | Change |
|-------|-----------|-------------------|--------|
| Maverick T1 | 94/100 | 87/100 | -7 |
| Scout T1 | 91/100 | 83/100 (T5) | -8 |

**Adding analysis fields hurts cleanup quality for both models.**

### 4. Temperature findings

| Temp | Maverick | Scout |
|------|----------|-------|
| 0.0 | Safest, consistent | No cleanup |
| 0.3-0.8 | Over-summarizes | No cleanup |
| 1.0 | Preserves C34 | **Best** - adds paragraphs |
| 1.5 | Preserves C32, C26 | JSON errors |
| 2.0 | **Russian leak!** | **Garbled output!** |

---

## Recommendations

### For Production

**Use dream_v10 (without analysis)** for best cleanup quality:
- Maverick T1: 94/100
- Scout T1: 91/100

### For Analysis + Cleanup

If you need both:
1. **Two-pass approach:** Use dream_v10 for cleanup, then separate analysis prompt
2. **Or accept trade-off:** Use maverick T1 with dream_v10_analysis (87/100)

### Model + Config Choice

| Use Case | Model | Config | Score |
|----------|-------|--------|-------|
| **Best overall** | Maverick | T1 (temp=0.0) | 87/100 |
| Best content preservation | Scout | T5 (temp=1.0) | 83/100 |
| Most specific details | Maverick | T6 (temp=1.5) | 87/100 |

### Avoid

- Maverick T7 (temp=2.0) - Russian language leak
- Scout T7 (temp=2.0) - Output corruption
- Scout T1-T4 - No cleanup performed

---

## Model Files

- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md) - **87/100 PASS** (T1 best)
- [meta-llama-llama-4-scout-17b-16e-instruct.md](./meta-llama-llama-4-scout-17b-16e-instruct.md) - 83/100 PASS (T5 best)
