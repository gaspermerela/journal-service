# Analysis: Groq temp=0.0

## Groq temp=0.0 (3 runs)

### Variance
| Run | Chars | Hvala |
|-----|-------|-------|
| v1 | 4987 | 10 |
| v2 | 5004 | 10 |
| v3 | 5061 | 9 |

Not deterministic - text varies between runs. v3 has hallucinated intro.

### Score: 50/100 (LLM Cleanup Suitability)

| Criterion | Score | Details |
|-----------|-------|---------|
| Hallucinations /30 | 0 | 10 "Hvala" × -3 = -30 (floored at 0) |
| Semantic recoverability /30 | 13 | 1 unrecoverable (-5), 4 borderline (-12) |
| Vocabulary accuracy /20 | 17 | 1 misleading word (-3) |
| Punctuation /20 | 20 | Good - sentence breaks exist |

### Hallucination Check

**10 "Hvala" instances found:**

| Location | Count |
|----------|-------|
| "Hvala, predem do obhodnikov" | 1 |
| "giroskopom. Hvala. Hvala." | 2 |
| "bistrani? Hvala. Hvala." | 2 |
| "te stave. Hvala." | 1 |
| "na vzdol Hvala. Hvala. Hvala. Hvala." | 4 |

**Additional hallucination (v3 only):** "Zdravstveno, da ste pripravljeni na kanal."

Score: 30 - (10 × 3) = **0/30**

### Semantic Recoverability Analysis

**Unrecoverable phrases (-5 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "Ali je bistrani?" | "na levi strani" | ❌ No | ❌ No |

**Borderline phrases (-3 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "hori ta ljena vzgor" | "hodita le navzgor" | ❌ No | ✓ Yes (context: "dve ženske") |
| "stapo" | "stavbo" | ❌ No | ✓ Yes (context: "pod to") |
| "v mesec spra kaj vodijo" | "vmes se sprašujem kaj" | ❌ No | ✓ Yes |
| "vsej nadreval dol" | "vseeno nadaljeval dol" | ❌ No | ✓ Yes |

Score: 30 - (1 × 5) - (4 × 3) = **13/30**

### Vocabulary Accuracy Analysis

**Misleading words (-3 each):**

| Error | Correct | Why misleading |
|-------|---------|----------------|
| "predličju" | "pritličju" | "before floor" ≠ "ground floor" |

**Not misleading (phonetic, recoverable):**
- "polnica" → "bolnica" (phonetic p/b, LLM can guess)
- "ronotežje" → "ravnotežje" (phonetic, clear from context)

Score: 20 - (1 × 3) = **17/20**

### 5 Worst Errors

1. **10 "Hvala" hallucinations** - ❌ SEVERE, pollutes text
2. "Ali je bistrani?" → "na levi strani" - ❌ Unrecoverable
3. "hori ta ljena vzgor" → "hodita le navzgor" - ⚠️ Borderline
4. "predličju" → "pritličju" - ⚠️ Misleading
5. "v mesec spra kaj vodijo" → "vmes se sprašujem kaj" - ⚠️ Borderline

### Notes

- **10 "Hvala" hallucinations** - catastrophic for LLM cleanup
- **Good punctuation** - sentence structure exists
- **Most garbles are borderline** - recoverable with context
- **v3 has additional hallucinated intro** - even worse variance