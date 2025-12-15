# Analysis: Groq temp=0.05

## Groq temp=0.05 (3 runs)

### Variance
| Run | Chars | Hvala | Unique Issue |
|-----|-------|-------|--------------|
| v1 | 5096 | 10 | English hallucination |
| v2 | 5093 | 10 | "ZDAJEK" + gibberish |
| v3 | 4963 | 13 | Word repetition |

Not deterministic - text varies significantly between runs.

### Score: 47/100 (LLM Cleanup Suitability)

| Criterion | Score | Details |
|-----------|-------|---------|
| Hallucinations /30 | 0 | 10 "Hvala" (-30) + English phrase (-5) = floored at 0 |
| Semantic recoverability /30 | 10 | 1 unrecoverable (-5), 5 borderline (-15) |
| Vocabulary accuracy /20 | 17 | 1 misleading word (-3) |
| Punctuation /20 | 20 | Good - sentence breaks exist |

### Hallucination Check

**10 "Hvala" instances (v1):**

| Location | Count |
|----------|-------|
| "giroskopom. Hvala. Hvala." | 2 |
| "bistrani? Hvala. Hvala." | 2 |
| "te stave. Hvala." | 1 |
| "na vzdol Hvala. Hvala. Hvala. Hvala." | 4 |
| "dela Hvala." | 1 |

**Additional hallucinations (SEVERE):**

| Run | Hallucination | Type |
|-----|---------------|------|
| v1 | "Na eno Historic quietly above the ejst in thieves again. V Wildellingznar 44 setups." | English gibberish |
| v2 | "ZDAJEK Sanje so se začele..." | Hallucinated intro |
| v2 | "Hr Chrrr. Naa, in bist tu... ... kk mojej nadal jujem." | Gibberish |
| v3 | "pružil, pružil, pružil, pružil, čim prej" | Word repetition |

Score: 30 - (10 × 3) - 5 = **0/30** (floored)

### Semantic Recoverability Analysis

**Unrecoverable phrases (-5 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "Ali je bistrani?" | "na levi strani" | ❌ No | ❌ No |

**Borderline phrases (-3 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "horitele na vzgor" | "hodita le navzgor" | ❌ No | ✓ Yes |
| "stapo" | "stavbo" | ❌ No | ✓ Yes |
| "v mesec spra kaj vodijo" | "vmes se sprašujem kaj" | ❌ No | ✓ Yes |
| "vsej nadreval dol" | "vseeno nadaljeval dol" | ❌ No | ✓ Yes |
| "nja nek način uspodbuja" | "na nek način vspodbuja" | ❌ No | ✓ Yes |

Score: 30 - (1 × 5) - (5 × 3) = **10/30**

### Vocabulary Accuracy Analysis

**Misleading words (-3 each):**

| Error | Correct | Why misleading |
|-------|---------|----------------|
| "pretličju" | "pritličju" | "before floor" ≠ "ground floor" |

Score: 20 - (1 × 3) = **17/20**

### 5 Worst Errors

1. **English hallucination** - "Historic quietly above the ejst..." - ❌ CATASTROPHIC
2. **10 "Hvala" hallucinations** - ❌ SEVERE
3. "Ali je bistrani?" → "na levi strani" - ❌ Unrecoverable
4. "pretličju" → "pritličju" - ⚠️ Misleading
5. "horitele na vzgor" → "hodita le navzgor" - ⚠️ Borderline

### Notes

- **WORSE than temp=0.0** - English hallucinations are catastrophic
- **High variance** - each run has unique severe issues
- **Not suitable for production** - hallucinations too unpredictable