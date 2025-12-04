# dream_v9_slo Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v9_slo (Slovenian instructions)
**Test Date:** 2025-12-04
**Transcription ID:** 5beeaea1-967a-4569-9c84-eccad8797b95
**Raw Length:** 5,051 characters

---

## Best Results Summary

| Model | Best Config | Score | Status | Key Finding |
|-------|-------------|-------|--------|-------------|
| **[llama-3.3-70b-versatile](./llama-3.3-70b-versatile.md)** | T3 | **86/100** | PASS | Best paragraphs, good length |
| [maverick-17b](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | P3 | **81/100** | PASS | Preserves 10m detail, no paragraphs |
| [scout-17b](./meta-llama-llama-4-scout-17b-16e-instruct.md) | T3 | **78/100** | REVIEW | Too many fillers retained |
| [gpt-oss-120b](./openai-gpt-oss-120b.md) | P1 | **51/100** | FAIL | Severe over-summarization |

---

## Prompt Text (dream_v9_slo)

```
Očisti ta slovenski prepis sanj za osebni dnevnik. Vhodno besedilo je bilo zajeto s programsko opremo za prepoznavo govora (STT).

PRAVILA:
1. Popravi slovnico, črkovanje in ločila. Uporabljaj knjižno slovenščino.
2. Piši v sedanjiku, prvi osebi ednine ("jaz").
3. Razdeli v kratke odstavke (en prizor/trenutek na odstavek).
4. Odstrani SAMO napake prepoznave govora: polnilne besede ("v bistvu", "torej"), napačne začetke, ponovljene besede, šum ("Hvala").
5. OHRANI VSAK specifičen detajl - dejanja, predmete, opise, čutne zaznave, občutke. Nenavadne ali čudne podrobnosti so ŠE POSEBEJ pomembne - ohrani jih natančno tako, kot so povedane.
6. NE povzemaj. NE krajšaj. NE izmišljuj in NE razlagaj ničesar, česar ni v izvirniku.
7. Popravi očitne napake pri prepoznavi besed (kjer je program slišal napačno).

OBLIKA ODGOVORA:
Odgovori SAMO z veljavnim JSON v točno tej obliki (brez markdown, brez dodatnega besedila):
{{
  "cleaned_text": "Očiščena verzija tukaj"
}}
```

---

## Key Findings

### Common Issues (All Models)
- **G1 (polnica→bolnica):** ALL models fail - Slovenian prompt doesn't help fix this STT error
- **G2 (pretličju→pritličju):** Most models fail this too
- **Garbled phrases remain:** "prublev", "nadelujem", "ta ljena vzgor" persist

### Model-Specific Observations

1. **llama-3.3-70b-versatile** - Best overall balance
   - T3 produces paragraphs (unlike T1 which is block text)
   - Length: 77-88% (optimal range)
   - Artifacts removed properly

2. **maverick-17b** - Good but missing paragraphs
   - Preserves C34 (10m width)
   - Length: 74-86% (optimal)
   - No paragraph breaks in most configs

3. **scout-17b** - Too verbose
   - Keeps "Zdravstveno, da ste pripravljeni" artifact
   - Retains excessive fillers ("torej", "a ne", "v bistvu")
   - Length: 92% (borderline too long)

4. **gpt-oss-120b** - FAILS
   - Severe over-summarization: 39-56% length
   - Loses significant content details
   - Has hallucination: "jaz skočim in ji pomagam" (he helped her - NOT in original)

---

## Scoring Comparison

| Model | Length | G | C | R | H | L | Total | Status |
|-------|--------|---|---|---|---|---|-------|--------|
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) T3 | 77% | 18 | 42 | 11 | 10 | 5 | **86** | PASS |
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) P3 | 86% | 17 | 43 | 8 | 10 | 5 | **81** | PASS |
| [scout](./meta-llama-llama-4-scout-17b-16e-instruct.md) T3 | 97% | 15 | 44 | 8 | 8 | 3 | **78** | REVIEW |
| [gpt-oss](./openai-gpt-oss-120b.md) P1 | 51% | 16 | 25 | 11 | 6 | 1 | **51** | FAIL |

---

## Recommendations

### For Production Use
**llama-3.3-70b-versatile with T3 (temp=0.5)** is the best choice:
- Score: 86/100 (PASS threshold: ≥80)
- Good paragraph structure
- Proper length (77%)
- All artifacts removed

### Alternative
**maverick-17b with P3 (top_p=0.5)** if more detail preservation is needed:
- Score: 81/100 (PASS)
- Preserves 10m width detail (C34)
- Needs manual paragraph insertion

### NOT Recommended
- **gpt-oss-120b:** Severe over-summarization, content loss
- **scout-17b:** Too many fillers, artifacts retained

---

## Model Files

- [llama-3.3-70b-versatile.md](./llama-3.3-70b-versatile.md)
- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md)
- [meta-llama-llama-4-scout-17b-16e-instruct.md](./meta-llama-llama-4-scout-17b-16e-instruct.md)
- [openai-gpt-oss-120b.md](./openai-gpt-oss-120b.md)
