# Analysis: Groq temp=0.0

## Groq temp=0.0 (3 runs)

### Variance
| Run | Chars | Hvala |
|-----|-------|-------|
| v1 | 4987 | 10 |
| v2 | 5004 | 10 |
| v3 | 5061 | 9 |

Not deterministic - text varies between runs.

### Score: 59/100

| Criterion | Score | Details |
|-----------|-------|---------|
| STT artifacts /30 | 20 | -10 (10x "Hvala") |
| Spelling /25 | 16 | -9 (3 errors) |
| Word integrity /25 | 23 | -2 (1 merge) |
| Punctuation /20 | 0 | Poor |

### Errors
- **Hvala (10x):** "Hvala, predem...", "Hvala. Hvala." clusters
- **Spelling:**
  - "polnica" → "bolnica"
  - "praktyčno" → "praktično"
  - "ronotežje" → "ravnotežje"
- **Merged:** "vglavnem" → "v glavnem"
- **v3 only:** Hallucinated intro "Zdravstveno, da ste pripravljeni na kanal."
