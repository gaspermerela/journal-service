# Qualitative Analysis: db1b48a1 (temp=0.0)

## Summary

| Provider | Score | Runs | Deterministic |
|----------|-------|------|---------------|
| **AssemblyAI** | **80/100** | 3 | Yes (identical) |
| Groq | 59/100 | 3 | No (variable) |

**Winner: AssemblyAI** (+21 points)

---

## Groq Analysis (3 runs)

### Variance
| Run | Chars | Hvala | Notes |
|-----|-------|-------|-------|
| v1 | 4987 | 10 | Baseline |
| v2 | 5004 | 10 | +17 chars |
| v3 | 5061 | 9 | +hallucinated intro |

**Not deterministic** - text varies between runs.

### Groq Score: 59/100

| Criterion | Score | Details |
|-----------|-------|---------|
| STT artifacts /30 | 20 | -10 (10x "Hvala") |
| Spelling /25 | 16 | -9 (3 errors) |
| Word integrity /25 | 23 | -2 (1 merge) |
| Punctuation /20 | 0 | Poor |

**Errors:**
- **Hvala (10x):** Inserted throughout - "Hvala, predem...", "Hvala. Hvala." clusters
- **Spelling:**
  - "polnica" → "bolnica"
  - "praktyčno" → "praktično"
  - "ronotežje" → "ravnotežje"
- **Merged:** "vglavnem" → "v glavnem"
- **v3 only:** Hallucinated intro "Zdravstveno, da ste pripravljeni na kanal."

---

## AssemblyAI Analysis (3 runs)

### Variance
| Run | Chars | Hvala | Notes |
|-----|-------|-------|-------|
| v1 | 5093 | 0 | Baseline |
| v2 | 5093 | 0 | Identical |
| v3 | 5093 | 0 | Identical |

**Fully deterministic** - all runs character-for-character identical.

### AssemblyAI Score: 80/100

| Criterion | Score | Details |
|-----------|-------|---------|
| STT artifacts /30 | **30** | None |
| Spelling /25 | 16 | -9 (3 errors) |
| Word integrity /25 | 19 | -6 (3 splits) |
| Punctuation /20 | 15 | Good - proper "..." usage |

**Errors:**
- **Split words:**
  - "ne enakomirne" → "neenakomerne"
  - "rovno težje" → "ravnotežje"
  - "pot to stavo" → "pod to stavbo"
- **Spelling:**
  - "storme" → "strme"
  - "stoprnice/stupnice" → "stopnice" (inconsistent)
  - "Spanim se" → "Spomnim se"
- **Minor:** "Otviram/Otprem" → "Odpiram/Odprem" (dialectal)

---

## Head-to-Head Comparison

| Metric | Groq | AssemblyAI | Winner |
|--------|------|------------|--------|
| Determinism | No | **Yes** | AssemblyAI |
| STT artifacts | 20/30 | **30/30** | AssemblyAI |
| Spelling | 16/25 | 16/25 | Tie |
| Word integrity | **23/25** | 19/25 | Groq |
| Punctuation | 0/20 | **15/20** | AssemblyAI |
| **Total** | 59/100 | **80/100** | **AssemblyAI** |

---

## Conclusion

**AssemblyAI wins decisively:**

1. **No hallucinations** - Groq inserts "Hvala" 10x per run (dealbreaker)
2. **Deterministic** - Same result every time (reliable)
3. **Better punctuation** - Proper sentence boundaries

**Groq's only advantage:** Slightly better word integrity (fewer splits)

**Recommendation:** Use AssemblyAI for Slovenian transcription. The "Hvala" hallucination in Groq is a systemic flaw that disqualifies it for production use.
