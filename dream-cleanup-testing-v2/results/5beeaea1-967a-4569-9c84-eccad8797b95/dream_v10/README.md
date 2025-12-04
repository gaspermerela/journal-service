# dream_v10 Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v10 (English instructions with Slovenian STT patterns)
**Test Date:** 2025-12-04
**Transcription ID:** 5beeaea1-967a-4569-9c84-eccad8797b95
**Raw Length:** 5,051 characters

---

## Best Results Summary

| Model | Best Config | Score | Status | Key Finding |
|-------|-------------|-------|--------|-------------|
| **[maverick-17b](./meta-llama-llama-4-maverick-17b-128e-instruct.md)** | T1 | **94/100** | EXCELLENT | ONLY model to fix "bolnica", best grammar |
| [scout-17b](./meta-llama-llama-4-scout-17b-16e-instruct.md) | T1 | **91/100** | EXCELLENT | Best content preservation (has C23+C34), minimal cleanup |
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) | P3 | **84/100** | PASS | Good balance, many grammar errors unfixed |
| [gpt-oss-120b](./openai-gpt-oss-120b.md) | T1 | **64/100** | ITERATE | Over-summarizes, 3 hallucinations |

---

## Prompt Text (dream_v10)

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
   - Break into short paragraphs separated by blank lines (\n\n).
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
  "cleaned_text": "The cleaned version here"
}}
```

---

## Key Findings

### Common Issues (All Models)
- **G1 (polnica→bolnica):** Only maverick fixes this - all others fail
- **C34 (10m width):** Only scout preserves this detail
- **Garbled phrases:** Most remain unfixed across all models

### Model-Specific Observations

1. **maverick-17b** - Best overall (94/100)
   - ONLY model to fix "polnica→bolnica" (G1)
   - Best grammar score (21/25)
   - Good paragraph structure
   - Lost some detail (C23 flat areas, C34 10m width missing)

2. **scout-17b** - Best content (91/100)
   - Preserves C23 (flat areas) + C34 (10m široke) - unique
   - Keeps "Zdravstveno" artifact (A2)
   - Some STT errors remain unfixed (G13, G15, G20, G22, G23, G26)
   - Length: 98% (minimal cleanup)

3. **llama-3.3-70b** - Balanced (84/100)
   - Fails to fix "polnica" (G1)
   - Many garbled phrases preserved verbatim
   - Optimal length range (75-93%)
   - Preserves C23 (flat areas)

4. **gpt-oss-120b** - FAILS (64/100)
   - Severe over-summarization: 40-58% length
   - 3 hallucinations detected
   - Good grammar but loses content
   - NOT recommended

---

## Scoring Comparison

| Model | Length | G | C | R | H | L | Total | Status |
|-------|--------|---|---|---|---|---|-------|--------|
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) T1 | 78% | 21 | 43 | 15 | 10 | 5 | **94** | EXCELLENT |
| [scout](./meta-llama-llama-4-scout-17b-16e-instruct.md) T1 | 98% | 20 | 43 | 15 | 10 | 3 | **91** | EXCELLENT |
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) P3 | 93% | 12 | 42 | 15 | 10 | 5 | **84** | PASS |
| [gpt-oss](./openai-gpt-oss-120b.md) T1 | 55% | 21 | 30 | 8 | 4 | 1 | **64** | ITERATE |

---

## Comparison: dream_v10 vs dream_v9_slo

| Metric | dream_v9_slo (Slovenian) | dream_v10 (English) | Winner |
|--------|--------------------------|---------------------|--------|
| Best Score | 86 (llama T3) | 94 (maverick T1) | **v10** |
| G1 Fix | None | maverick only | **v10** |
| Content Preservation | Similar | Similar | Tie |
| Hallucination Risk | Low | Low | Tie |

**Conclusion:** dream_v10 (English prompt) outperforms dream_v9_slo, with maverick T1 achieving the highest score (94) vs llama T3 (86).

---

## Recommendations

### For Production Use
**maverick-17b with T1 (temp=0.0)** is the best choice:
- Score: 94/100 (highest achieved)
- ONLY model to fix critical "bolnica" STT error
- Good paragraph structure
- No hallucinations
- Processing time: ~3.7s

### Alternative
**scout-17b with T1 (temp=0.0)** if maximum content preservation is needed:
- Score: 91/100 (EXCELLENT)
- Preserves C23 (flat areas) + C34 (10m width)
- Minimal cleanup - requires post-processing for grammar

### NOT Recommended
- **gpt-oss-120b:** Severe over-summarization, hallucinations
- **llama-3.3-70b:** Lower grammar score, doesn't fix G1

---

## Model Files

- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md)
- [meta-llama-llama-4-scout-17b-16e-instruct.md](./meta-llama-llama-4-scout-17b-16e-instruct.md)
- [llama-3.3-70b-versatile.md](./llama-3.3-70b-versatile.md)
- [openai-gpt-oss-120b.md](./openai-gpt-oss-120b.md)
