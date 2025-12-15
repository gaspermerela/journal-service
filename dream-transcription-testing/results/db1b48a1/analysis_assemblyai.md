# Analysis: AssemblyAI

## AssemblyAI (3 runs)

### Variance
| Run | Chars | Hvala |
|-----|-------|-------|
| v1 | 5093 | 0 |
| v2 | 5093 | 0 |
| v3 | 5093 | 0 |

Fully deterministic - all runs identical.

### Score: 74/100 (LLM Cleanup Suitability)

| Criterion | Score | Details |
|-----------|-------|---------|
| Hallucinations /30 | 30 | Zero hallucinations (verified - see below) |
| Semantic recoverability /30 | 10 | 1 unrecoverable (-5), 5 borderline (-15) |
| Vocabulary accuracy /20 | 14 | 2 misleading words (-6) |
| Punctuation /20 | 20 | Good - sentence breaks exist |

### Hallucination Check

**Verified: No hallucinations found.**

| Suspicious phrase | Assessment |
|-------------------|------------|
| "Vidim se, vedam" | Garble of "Vidim seveda" - not hallucination |
| "pa pa so" | Stutter artifact - not hallucination |
| "pa to to stavo" | Stutter artifact - not hallucination |
| "tenko hodim dal" | Likely garble of "medtem ko" - not pure hallucination |

Unlike Groq's clear "Hvala" insertions, AssemblyAI errors are **garbles/mishearings**, not invented content.

### Semantic Recoverability Analysis

**Unrecoverable phrases (-5 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "prisetot" | unclear | ❌ No | ❌ No |

**Borderline phrases (-3 each):**

| Phrase | Should be | Alone? | With context? |
|--------|-----------|--------|---------------|
| "zgubrono teže zraz" | "zgubil ravnotežje zaradi" | ❌ No | ✓ Yes (context: "stopnic") |
| "sen on je nekater način" | "ampak vseeno je na nek način" | ❌ No | ✓ Yes |
| "progub ostati" | "probal ostati" | ❌ No | ✓ Yes (context: "neopažen") |
| "nja nek način uspotkuja" | "na nek način vspodbuja" | ❌ No | ✓ Yes |
| "Bive še nek podoben" | "Bil je še nek podoben" | ❌ No | ✓ Yes |

Score: 30 - (1 × 5) - (5 × 3) = **10/30**

### Vocabulary Accuracy Analysis

**Misleading words (-3 each):**

| Error | Correct | Why misleading |
|-------|---------|----------------|
| "priključju" | "pritličju" | "connection" ≠ "ground floor" |
| "Spavim se" | "Spomnim se" | "I'm sleeping" ≠ "I remember" |

Score: 20 - (2 × 3) = **14/20**

### 5 Worst Errors

1. "prisetot" → unclear - ❌ Unrecoverable (even with context)
2. "zgubrono teže zraz" → "zgubil ravnotežje zaradi" - ⚠️ Borderline (context helps)
3. "Spavim se" → "Spomnim se" - ⚠️ Misleading ("sleeping" vs "remember")
4. "priključju" → "pritličju" - ⚠️ Misleading ("connection" vs "ground floor")
5. "progub ostati" → "probal ostati" - ⚠️ Borderline (context: "neopažen")

### Notes

- **Zero hallucinations** - major advantage for LLM cleanup
- **Good punctuation** - sentence structure is clear
- **1 unrecoverable + 5 borderline phrases** - most recoverable with context
- **2 misleading words** - "Spavim" and "priključju" could cause wrong interpretation
