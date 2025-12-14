# Analysis: Groq temp=0.05

## Groq temp=0.05 (3 runs)

### Variance
| Run | Chars | Hvala | Unique Issue |
|-----|-------|-------|--------------|
| v1 | 5096 | 10 | English hallucination |
| v2 | 5093 | 10 | "ZDAJEK" + gibberish |
| v3 | 4963 | 13 | Word repetition |

Not deterministic - text varies between runs.

### Score: 56/100

| Criterion | Score | Details |
|-----------|-------|---------|
| STT artifacts /30 | 17 | -10 (Hvala) -3 (extra hallucinations) |
| Spelling /25 | 16 | -9 (3 errors) |
| Word integrity /25 | 23 | -2 (1 merge) |
| Punctuation /20 | 0 | Poor |

### Errors

**v1 - Random English hallucination:**
> "Na eno Historic quietly above the ejst in thieves again. V Wildellingznar 44 setups."

**v2 - Hallucinated intro + gibberish:**
> "ZDAJEK Sanje so se začele..."
> "Hr Chrrr. Naa, in bist tu... ... kk mojej nadal jujem."

**v3 - Word repetition:**
> "pružil, pružil, pružil, pružil, čim prej"

### Common Errors (all runs)
- **Hvala (10-13x):** Hallucinated throughout
- **Spelling:**
  - "polnica" → "bolnica"
  - "ronotežje" → "ravnotežje"
- **Merged:** "vglavnem" → "v glavnem"
