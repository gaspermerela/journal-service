# Transcription Test: db1b48a1

**Entry:** db1b48a1-59be-49be-bac4-3da3bf8f82cd
**Total runs:** 10
**Scoring:** LLM Cleanup Suitability (/100)

> **Note: Punctuation is the deciding factor**
>
> | Provider | Semantic + Vocab (quality) | Punctuation | Total |
> |----------|---------------------------|-------------|-------|
> | slovenscina.eu | 30 (13+17) | 10 | 70 |
> | AssemblyAI | 24 (10+14) | 20 | 74 |
>
> slovenscina.eu has **+6 better transcription quality** but loses on punctuation (-10).
>
> **Next step:** Test if transcription or LLM cleanup can fix missing sentence breaks. If yes, slovenscina.eu
> would be preferred for its superior semantic recoverability and vocabulary accuracy.

## Results

| Provider | Score | Halluc. | Semantic | Vocab | Punct. | Notes |
|----------|-------|---------|----------|-------|--------|-------|
| **AssemblyAI** | **74/100** | 30 | 10 | 14 | 20 | Deterministic, zero hallucinations |
| slovenscina.eu | 70/100 | 30 | 13 | 17 | 10 | Zero hallucinations, fair punctuation |
| Groq T=0.0 | 50/100 | 0 | 13 | 17 | 20 | 10 "Hvala" hallucinations |
| Groq T=0.05 | 47/100 | 0 | 10 | 17 | 20 | +English hallucinations |

**Winner: AssemblyAI** (+4 vs slovenscina.eu, +24 vs Groq)

## Scoring Criteria (LLM Cleanup Suitability)

| Criterion | Max | What it measures |
|-----------|-----|------------------|
| Hallucinations | /30 | -3 per "Hvala", -5 per inserted phrase |
| Semantic recoverability | /30 | -5 per unrecoverable, -3 per borderline |
| Vocabulary accuracy | /20 | -3 per misleading word |
| Punctuation | /20 | Good=20, Fair=10, Poor=0 |

## Key Findings

### Hallucinations (Most Important)
- **AssemblyAI:** Zero hallucinations - clean for LLM
- **slovenscina.eu:** Zero hallucinations - clean for LLM
- **Groq:** 9-13 "Hvala" per run + English gibberish (T=0.05) - catastrophic

### Semantic Recoverability
- All providers have ~1 unrecoverable + ~4-5 borderline phrases
- Most errors are recoverable with surrounding context
- "Ali je bistrani?" (Groq) and "bibre dko" (slovenscina.eu) are unrecoverable

### Vocabulary Accuracy
- All providers have 1-2 misleading words
- Common: "priključju/pretličju/pritličju" confusion (ground floor)
- AssemblyAI: "Spavim se" (sleeping) vs "Spomnim se" (remember)

### Punctuation
- **AssemblyAI/Groq:** Good (sentence breaks exist)
- **slovenscina.eu:** Fair (only commas, no sentence breaks)

## Recommendation

**For LLM cleanup:**
1. **AssemblyAI** - Best overall (74/100), zero hallucinations, deterministic
2. **slovenscina.eu** - Good alternative (70/100), but manual process required
3. **Avoid Groq** - "Hvala" hallucinations pollute text, unpredictable

## Files

- [analysis_assemblyai.md](./analysis_assemblyai.md)
- [analysis_groq_temp_0.0.md](./analysis_groq_temp_0.0.md)
- [analysis_groq_temp_0.05.md](./analysis_groq_temp_0.05.md)
- [analysis_slovenscina-eu.md](./analysis_slovenscina-eu.md)
- Full text: `cache/db1b48a1/` (gitignored)