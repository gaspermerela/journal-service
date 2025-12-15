# Analysis: slovenscina.eu

## slovenscina.eu (1 run, manual via web)

### Variance
| Run | Chars | Hvala |
|-----|-------|-------|
| v1 | 5765 | 0 |

Single manual run (chunked into 275s segments, manually reassembled).

### Score: 70/100 (LLM Cleanup Suitability)

| Criterion | Score | Details |
|-----------|-------|---------|
| Hallucinations /30 | 30 | Zero hallucinations (verified) |
| Semantic recoverability /30 | 13 | 1 unrecoverable (-5), 4 borderline (-12) |
| Vocabulary accuracy /20 | 17 | 1 misleading word (-3) |
| Punctuation /20 | 10 | Fair - commas provide clause structure |

### Hallucination Check

**Verified: No hallucinations found.**

| Checked | Result |
|---------|--------|
| "Hvala" | Zero instances |
| Inserted phrases | None |
| English/gibberish | None |
| `<spn>` markers | Intentional pause markers, not hallucinations |

Unlike Groq, slovenscina.eu has **zero hallucinations**.

### Semantic Recoverability Analysis

**Unrecoverable phrases (-5 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "bibre dko" | "bile tako" | ❌ No | ⚠️ Borderline (context: "stopnice so _ zelo široke") |

**Borderline phrases (-3 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "bileko" | "bile tako" | ❌ No | ✓ Yes (same pattern as above) |
| "progo ostat" | "probal ostati" | ❌ No | ✓ Yes (context: "neopažen") |
| "tomeni" | "ti nameni/te nameni" | ❌ No | ✓ Yes (context: "prostori") |
| "horitale" | "hodita le" | ❌ No | ✓ Yes (context: "dve ženski") |

Score: 30 - (1 × 5) - (4 × 3) = **13/30**

### Vocabulary Accuracy Analysis

**Misleading words (-3 each):**

| Error | Correct | Why misleading |
|-------|---------|----------------|
| "Marlo" | "malo" | Looks like proper noun (name) |

**Not misleading (phonetic, recoverable):**
- "groskopom" / "kiroskop" → "giroskopom" (phonetic g/gi)
- "postare" → "postale" (phonetic r/l)
- "sporem" → "spomnim" (phonetic)

Score: 20 - (1 × 3) = **17/20**

### Punctuation Analysis

- Almost no sentence breaks - runs on with commas
- Has `<spn>` markers indicating pauses
- Commas provide clause structure
- LLMs handle missing sentence breaks well

Score: **10/20** (Fair - commas exist, no sentence breaks)

### 5 Worst Errors

1. "bibre dko" → "bile tako" - ❌ Unrecoverable (severely garbled)
2. "Marlo" → "malo" - ⚠️ Misleading (looks like proper noun)
3. "bileko" → "bile tako" - ⚠️ Borderline
4. "progo ostat" → "probal ostati" - ⚠️ Borderline
5. "horitale" → "hodita le" - ⚠️ Borderline

### Notes

- **Zero hallucinations** - major advantage over Groq
- **Most garbles are borderline** - recoverable with context
- **Punctuation is Fair** - commas provide structure, LLMs handle it
- **Manual process required** - 275s chunks via web, manually reassembled