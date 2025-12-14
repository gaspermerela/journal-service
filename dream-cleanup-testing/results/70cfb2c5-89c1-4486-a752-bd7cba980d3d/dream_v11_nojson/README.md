# dream_v11_nojson Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v11_nojson (No JSON output format, uses `<break>` markers)
**Test Date:** 2025-12-08
**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Raw Length:** 5,013 characters

---

## Best Results Summary

| Model | Best Config | Score | Status | Key Finding |
|-------|-------------|-------|--------|-------------|
| **[maverick-17b](./maverick.md)** | T1 | **86/100** | PASS | Over-compressed (58%), 4 content losses |

---

## Prompt Text (dream_v11_nojson)

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
Respond ONLY with the cleaned text.

TRANSCRIPTION:
"{transcription_text}"
```

---

## Key Findings

### Common Issues
- **Over-compression:** Model compressed to 58% (should be 70-95%)
- **Content losses:** C10, C23, C26, C30 missing
- **Hallucinations:** 2 found ("Skupaj pridemo", "nazaj" instead of "navzdol")

### What Worked
- All "Hvala" artifacts removed
- Good paragraph structure
- Present tense maintained
- Most grammar errors fixed

---

## Scoring Comparison

| Model | Length | G | C | R | H | L | Total | Status |
|-------|--------|---|---|---|---|---|-------|--------|
| [maverick](./maverick.md) T1 | 58% | 23 | 41 | 15 | 6 | 1 | **86** | PASS |

---

## Model Files

- [maverick.md](./maverick.md) - Detailed T1 scoring
