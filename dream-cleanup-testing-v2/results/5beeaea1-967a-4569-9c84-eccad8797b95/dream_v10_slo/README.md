# dream_v10_slo Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v10_slo (Slovenian instructions with Slovenian STT patterns)
**Test Date:** 2025-12-04
**Transcription ID:** 5beeaea1-967a-4569-9c84-eccad8797b95
**Raw Length:** 5,051 characters

---

## Best Results Summary

| Model | Best Config | Score | Status | Key Finding |
|-------|-------------|-------|--------|-------------|
| **[llama-3.3-70b](./llama-3.3-70b-versatile.md)** | T1 | **82/100** | PASS | Best length ratio (89%), rate limited |
| **[maverick-17b](./meta-llama-llama-4-maverick-17b-128e-instruct.md)** | P2 | **82/100** | PASS | Variable lengths (50-81%), moderate cleanup |
| [scout-17b](./meta-llama-llama-4-scout-17b-16e-instruct.md) | T4 | **73/100** | REVIEW | Almost NO cleanup (94-99%) - FAILS |
| [gpt-oss-120b](./openai-gpt-oss-120b.md) | P4 | **60/100** | ITERATE | Severe over-summarization (39-58%) |

---

## Prompt Text (dream_v10_slo)

```
Očisti ta slovenski prepis sanj za osebni dnevnik. Vhodno besedilo je bilo zajeto s programsko opremo za prepoznavo govora (STT).

PRAVILA:

1. SLOVNICA IN POPRAVKI STT NAPAK
   - Popravi črkovanje, slovnico in ločila. Uporabljaj knjižno slovenščino.
   - Popravi pogoste napake prepoznave govora, kjer je program slišal napačno črko:
     * Zamenjava p↔b (npr. "polnica"→"bolnica", "stapo"→"stavbo")
     * Zamenjava e↔i (npr. "pretličje"→"pritličje", "predem"→"pridem")
     * Manjkajoči/dodatni zlogi (npr. "obhodnik"→"hodnik", "uspodbuda"→"vzpodbuda")
   - Pri nerazumljivih/popačenih frazah: rekonstruiraj verjeten pomen iz konteksta, ali če je res nejasno, poenostavi tako, da ohraniš dejanje/pomen.

2. OSEBA IN ČAS
   - Piši v sedanjiku, prvi osebi ednine ("jaz").
   - Ohrani osebni, pripovedni slog govora.

3. STRUKTURA ODSTAVKOV
   - Razdeli v kratke odstavke, ločene s prazno vrstico (\n\n).
   - Nov odstavek začni pri: menjavi prizora, menjavi lokacije, novem dogodku, čustveni spremembi.
   - Vsak odstavek naj ima 2-5 stavkov.

4. ODSTRANI SAMO ARTEFAKTE
   - Odstrani artefakte STT: polnilne besede ("v bistvu", "torej", "a ne", "no"), napačne začetke, ponovljene besede, oznake šuma ("Hvala").
   - Odstrani uvodni/zaključni govor snemanja (npr. "Zdravstveno, da ste pripravljeni" ali podobno).
   - NE odstranjuj vsebine, ki nosi pomen, tudi če je neformalna.

5. OHRANI VSO VSEBINO
   - OHRANI VSAK specifičen detajl: dejanja, predmete, opise, čutne zaznave, občutke, lokacije.
   - OHRANI specifične številke in mere natančno tako, kot so povedane (npr. "10 metrov", "5 ljudi", "ob 4h zjutraj").
   - OHRANI nenavadne ali čudne podrobnosti NATANČNO tako, kot so opisane - te so še posebej pomembne pri sanjah.
   - OHRANI opise gibanja natančno (npr. "napol tek" vs "hoja", "skok" vs "korak").

6. NE DELAJ
   - NE povzemaj in NE krajšaj.
   - NE združuj več podrobnosti v posplošitve.
   - NE izmišljuj, razlagaj ali dodajaj ničesar, česar ni v izvirniku.
   - NE uporabljaj ruščine, cirilice ali angleščine - izhod mora biti 100% slovenščina.

OBLIKA ODGOVORA:
Odgovori SAMO z veljavnim JSON v točno tej obliki (brez markdown, brez dodatnega besedila):
{{
  "cleaned_text": "Očiščena verzija tukaj"
}}
```

---

## Key Findings

### Critical Issue: Scout Almost No Cleanup

**scout-17b produces 94-99% length ratio** - effectively just echoing the input with minimal changes.

This is a MAJOR finding: the Slovenian prompt causes scout to under-process the text.

### Model-Specific Observations

1. **llama-3.3-70b** - Best performance (82/100)
   - T1 (temp=0.0): 89% length - optimal cleanup level
   - Rate limited after P2 (only 9/17 configs completed)
   - Good balance of cleanup and content preservation

2. **maverick-17b** - Tied for best (82/100)
   - Length varies widely: 50-81%
   - P2 (top_p=0.3): 81% - best config
   - T1 at 50% suggests over-processing at temp=0
   - Less consistent than with English prompt (dream_v10)

3. **scout-17b** - Under-processes (73/100)
   - All configs: 94-99% length
   - Almost no STT error correction
   - Does not follow cleanup instructions properly
   - **NOT recommended with Slovenian prompt**

4. **gpt-oss-120b** - Over-summarizes (60/100)
   - All configs: 39-58% length
   - Hallucinations detected
   - Same issue as with English prompt
   - **NOT recommended**

---

## Scoring Comparison

| Model | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-------|------|------|------|------|------|-----|-------|--------|
| [llama](./llama-3.3-70b-versatile.md) T1 | 89% | 12 | 40 | 15 | 10 | 5 | **82** | PASS |
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) P2 | 81% | 21 | 38 | 15 | 10 | 5 | **82** | PASS |
| [scout](./meta-llama-llama-4-scout-17b-16e-instruct.md) T4 | 94% | 11 | 44 | 15 | 10 | 3 | **73** | REVIEW |
| [gpt-oss](./openai-gpt-oss-120b.md) P4 | 58% | 22 | 30 | 11 | 6 | 1 | **60** | ITERATE |

---

## Comparison: dream_v10_slo vs dream_v10 (English)

| Metric | dream_v10 (English) | dream_v10_slo (Slovenian) | Winner |
|--------|---------------------|---------------------------|--------|
| Best Score | 94 (maverick T1) | 82 (llama T1 / maverick P2) | **v10 English** |
| Scout behavior | 91/100, good content | 73/100, minimal cleanup | **v10 English** |
| Maverick behavior | 94/100, consistent | 82/100, variable | **v10 English** |
| llama behavior | 84/100 | 82/100 | **v10 English** |

**Conclusion:** English prompt (dream_v10) outperforms Slovenian prompt (dream_v10_slo) across all models.

---

## Recommendations

### For Production Use

**Use dream_v10 (English prompt) instead of dream_v10_slo:**
- Better overall scores across all models
- More consistent model behavior
- maverick achieves 94/100 with English prompt vs 82/100 with Slovenian

### If Using Slovenian Prompt

**llama-3.3-70b with T1 (temp=0.0) OR maverick with P2 (top_p=0.3):**
- Score: 82/100 (PASS)
- Best performers with Slovenian prompt

### NOT Recommended

- **scout-17b:** Under-processes with Slovenian prompt (94-99% length)
- **gpt-oss-120b:** Severe over-summarization (39-58% length), hallucinations

---

## Model Files

- [llama-3.3-70b-versatile.md](./llama-3.3-70b-versatile.md)
- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md)
- [meta-llama-llama-4-scout-17b-16e-instruct.md](./meta-llama-llama-4-scout-17b-16e-instruct.md)
- [openai-gpt-oss-120b.md](./openai-gpt-oss-120b.md)
