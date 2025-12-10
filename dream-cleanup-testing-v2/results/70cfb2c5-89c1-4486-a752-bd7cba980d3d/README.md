# Results: 70cfb2c5-89c1-4486-a752-bd7cba980d3d

**Transcription Date:** 2025-12-08
**Raw Length:** 5,013 chars

---

## Best Result

| Prompt | Model | Config | Score | Status |
|--------|-------|--------|-------|--------|
| dream_v11_nojson | maverick | T1 | 86/100 | PASS |

---

## Comparison with Previous Transcription (5beeaea1)

| Metric | Old (5beeaea1) | New (70cfb2c5) |
|--------|----------------|----------------|
| Raw length | 5,051 chars | 5,013 chars |
| Best score | 94/100 (T1) | 86/100 (T1) |
| Status | PASS | PASS |

### Score Drop Analysis (-8 points)

| Category | Old | New | Delta | Cause |
|----------|-----|-----|-------|-------|
| Length | 4 | 1 | -3 | Over-compression (58% vs 72%) |
| Hallucinations | 10 | 6 | -4 | 2 inventions ("Skupaj", "nazaj") |
| Content | 42 | 41 | -1 | 4 detail losses (no voice penalty) |
| Grammar | 23 | 23 | 0 | Same |
| Readability | 15 | 15 | 0 | Same |

### Transcription Quality

Both transcriptions capture all criteria details identically. **No transcription-level failures.**

All content losses are **cleanup failures** - the LLM did not preserve details that were present in the input.

---

## Prompt Comparison

| Prompt | Best Model | Config | Score | G | C | R | H | L |
|--------|------------|--------|-------|---|---|---|---|---|
| dream_v11_nojson | maverick | T1 | 86/100 | 23 | 41 | 15 | 6 | 1 |
| dream_v12 | maverick | T1 | 85/100 | 22 | 37 | 15 | 6 | 5 |

**dream_v12 notes:** Length constraint (>=75%) worked - 82% vs 58%. But model switched to past tense (-7 voice penalty). More content preserved (43/44 vs 40/44 C_passed).

---

## Next Steps

1. Test T2-T7 configs to see if different temperatures reduce over-compression
2. Consider P1-P6 (top-p only) configs
3. Compare with llama-3.3-70b-versatile on same transcription
