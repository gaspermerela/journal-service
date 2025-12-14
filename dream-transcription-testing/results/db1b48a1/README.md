# Transcription Test: db1b48a1

**Entry:** db1b48a1-59be-49be-bac4-3da3bf8f82cd
**Date:** 2025-12-14
**Total runs:** 6 (3 Groq + 3 AssemblyAI)

## Results

| Provider | Score | Runs | Deterministic | Hvala |
|----------|-------|------|---------------|-------|
| **AssemblyAI** | **80/100** | 3 | Yes | 0 |
| Groq T=0.0 | 59/100 | 3 | No | 9-10 |

**Winner: AssemblyAI** (+21 points)

## Variance Testing

### AssemblyAI (3 runs)
All runs **identical** - 5093 chars, character-for-character same.

### Groq (3 runs at temp=0.0)
| Run | Chars | Hvala |
|-----|-------|-------|
| v1 | 4987 | 10 |
| v2 | 5004 | 10 |
| v3 | 5061 | 9 (+hallucinated intro) |

## Key Findings

| Issue | Groq | AssemblyAI |
|-------|------|------------|
| "Hvala" hallucinations | 10x per run | None |
| Determinism | Variable | Identical |
| Punctuation | Poor | Good |
| Word splits | Few | Some |

## Conclusion

**AssemblyAI recommended** for Slovenian transcription:
- Zero STT artifacts
- Deterministic output
- Better punctuation

Groq's "Hvala" hallucination is a dealbreaker.

## Files

- [analysis_temp_0.0.md](./analysis_temp_0.0.md) - Detailed scoring
- [compare_temp_0.0.md](./compare_temp_0.0.md) - Automated metrics
