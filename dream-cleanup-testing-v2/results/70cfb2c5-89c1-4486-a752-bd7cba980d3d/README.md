# Results: 70cfb2c5-89c1-4486-a752-bd7cba980d3d

**Transcription Date:** 2025-12-08
**Raw Length:** 5,013 chars

---

## Best Result

| Prompt | Model | Config | Score | Status |
|--------|-------|--------|-------|--------|
| **dream_v13** | maverick | T1 | **91/100** | EXCELLENT |

---

## Prompt Comparison

| Prompt | Best Model | Config | Score | G | C | R | H | L | Key Finding |
|--------|------------|--------|-------|---|---|---|---|---|-------------|
| [dream_v13](./dream_v13/) | maverick | T1 | **91** | 23 | 40 | 15 | 8 | 5 | Voice fixed, no header |
| [dream_v12](./dream_v12/) | maverick | T1 | 85 | 22 | 37 | 15 | 6 | 5 | Length OK, past tense |
| [dream_v11_nojson](./dream_v11_nojson/) | maverick | T1 | 86 | 23 | 41 | 15 | 6 | 1 | Over-compressed (58%) |

---

## Prompt Evolution

| Version | Key Change | Score | Result |
|---------|-----------|-------|--------|
| v11_nojson | Baseline (no JSON) | 86 | PASS - Over-compressed to 58% |
| v12 | Added >=75% length requirement | 85 | PASS - Length fixed, but past tense |
| **v13** | Added present tense instruction + OUTPUT FORMAT | **91** | **EXCELLENT** - Production ready |

### v13 Improvements

1. **Voice penalty:** -3 (minor) vs -7 (major) in v12
2. **No header artifact:** "Here is the cleaned..." removed
3. **Tighter variance:** 2.2% length range vs 7.5%
4. **All EXCELLENT:** 90-91 across 4 runs

---

## Variance Testing Summary

| Prompt | Length Range | Score Range | Best | Worst |
|--------|--------------|-------------|------|-------|
| dream_v13 | 73.7%-75.9% (2.2%) | 90-91 (1pt) | 91 | 90 |
| dream_v12 | 74.9%-82.4% (7.5%) | 82-85 (3pt) | 85 | 82 |

---

## Comparison with Previous Transcription (5beeaea1)

| Metric | Old (5beeaea1) | New (70cfb2c5) v11 | New (70cfb2c5) v13 |
|--------|----------------|--------------------|--------------------|
| Raw length | 5,051 chars | 5,013 chars | 5,013 chars |
| Best score | 94/100 | 86/100 | **91/100** |
| Status | PASS | PASS | **EXCELLENT** |

v13 closes the gap from 94→86 to 94→91 (-3 pts vs -8 pts).

---

## Next Steps

1. ✅ ~~Test T2-T7 configs~~ - T1 at temp=0.0 produces best results
2. ✅ ~~Fix voice/tense~~ - v13 fixes this with CRITICAL section instruction
3. Consider testing on other transcriptions to verify generalization
4. Optional: Add STT mishearings for "nazdolj→navzdol", "obhodnikov→hodnikov"
