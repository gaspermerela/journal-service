# Transcription Test: db1b48a1

**Entry:** db1b48a1-59be-49be-bac4-3da3bf8f82cd
**Total runs:** 9

## Results

| Provider | Score | Hvala | Notes |
|----------|-------|-------|-------|
| **AssemblyAI** | **80/100** | 0 | Deterministic |
| Groq T=0.0 | 59/100 | 9-10 | Best Groq config |
| Groq T=0.05 | 56/100 | 10-13 | +English hallucinations |

**Winner: AssemblyAI** (+21 points)

## Key Findings

- **AssemblyAI:** Deterministic (3 identical runs), zero hallucinations
- **Groq:** "Hvala" hallucination is systemic (all runs)
- **Temperature:** Lower is better (0.0 > 0.05)

## Files

- [analysis_assemblyai.md](./analysis_assemblyai.md)
- [analysis_groq_temp_0.0.md](./analysis_groq_temp_0.0.md)
- [analysis_groq_temp_0.05.md](./analysis_groq_temp_0.05.md)
- Full text: `cache/db1b48a1/` (gitignored)
