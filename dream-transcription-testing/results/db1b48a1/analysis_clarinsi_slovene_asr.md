# Analysis: clarinsi_slovene_asr

## clarinsi_slovene_asr (1 run)

### Variance
| Run | Chars | Hvala |
|-----|-------|-------|
| v1 | 4951 | 0 |

Single run via API (runpod-rsdo-slovenian-asr model).

### Score: 62/100 (LLM Cleanup Suitability)

| Criterion | Score | Details |
|-----------|-------|---------|
| Hallucinations /30 | 30 | Zero hallucinations |
| Semantic recoverability /30 | 12 | 1 unrecoverable (-5), 5 borderline (-13) |
| Vocabulary accuracy /20 | 20 | No misleading words |
| Punctuation /20 | 0 | Poor - no breaks, no commas |

### Hallucination Check

| Checked | Result |
|---------|--------|
| "Hvala" | Zero instances |
| Inserted phrases | None |
| English/gibberish | None |

### Semantic Recoverability Analysis

**Unrecoverable phrases (-5 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "da in ga dela kejer" | "do enega dela, kjer" | No | Borderline |

**Borderline phrases (-3 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "njimpra skačit" | "ni upala skočiti" | No | Yes |
| "remla je nekako" | "bila je nekako" | No | Yes |
| "bledko zelo široke" | "bile tako zelo široke" | No | Yes |
| "detajltek imamka" | "detajl tu ki manjka" | No | Yes |
| "spejempk" | "spet en" | No | Yes |

Score: 30 - (1 × 5) - (5 × 3) = **12/30**

### Vocabulary Accuracy Analysis

**Misleading words:** None found

**Phonetic variations (not penalized):**
- "kiroskop" → "giroskop" (k/g)
- "postare" → "postale" (r/l)
- "spoanim" → "spomnim" (phonetic)
- "skačl" → "skočil" (phonetic)

Score: **20/20**

### Punctuation Analysis

- No sentence breaks
- No commas
- Completely run-on text
- LLM will need to infer all structure

Score: **0/20** (Poor)

### 5 Worst Errors

1. "da in ga dela kejer" → "do enega dela, kjer" - Unrecoverable
2. "njimpra skačit" → "ni upala skočiti" - Borderline
3. "remla je nekako" → "bila je nekako" - Borderline
4. "bledko zelo široke" → "bile tako zelo široke" - Borderline
5. "detajltek imamka" → "detajl tu ki manjka" - Borderline

### Notes

- **Zero hallucinations** - clean for LLM
- **Good Slovenian vocabulary** - "pritličju", "vzpodbudo" correct
- **Poor punctuation** - no structure at all, worse than manual web version
- **Automated API** - no manual chunking required
