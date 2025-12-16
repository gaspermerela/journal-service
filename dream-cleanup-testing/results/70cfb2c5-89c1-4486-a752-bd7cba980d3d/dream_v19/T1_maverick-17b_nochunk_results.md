# T1 maverick-17b Non-Chunked Results (dream_v19)

**Transcription:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Model:** groq-meta-llama/llama-4-maverick-17b-128e-instruct
**Prompt:** dream_v19 (preservation-focused)
**Config:** T1 (temp=0.0, top_p=null)
**Chunking:** DISABLED
**Runs:** 15

---

## Summary

| Metric | Value |
|--------|-------|
| Pass Rate | **100%** (15/15) |
| Best Score | 93/100 (EXCELLENT) |
| Worst Score | 91/100 (EXCELLENT) |
| Average Score | ~92/100 |
| Ratio Range | 91.5% - 97.9% |

---

## Individual Run Scores

| Run | Chars | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|-------|-------|------|------|------|------|-----|-------|--------|
| v1 | 4908 | 97.9% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v2 | 4855 | 96.9% | 20 | 45 | 15 | 8 | 3 | 91 | EXCELLENT |
| v3 | 4799 | 95.7% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v4 | 4803 | 95.8% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v5 | 4802 | 95.8% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v6 | 4843 | 96.6% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v7 | 4804 | 95.8% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v8 | 4687 | 93.5% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v9 | 4788 | 95.5% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v10 | 4634 | 92.4% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v11 | 4893 | 97.6% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v12 | 4907 | 97.9% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v13 | 4795 | 95.7% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v14 | 4588 | 91.5% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v15 | 4909 | 97.9% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |

**Note:** v8, v10, v14 achieved optimal length (L=5) but lost C34 content (-1 to C). Net effect: +2 -1 = +1 point.

---

## Checkpoint Analysis

### Grammar (G) - 23/28 passed consistently

| Checkpoint | Status | Notes |
|------------|--------|-------|
| G1 polnica→bolnica | 15/15 ✓ | Always fixed |
| G2 pretličju→pritličju | 15/15 ✓ | Always fixed |
| G3 uspodbudo→spodbudo | 10/15 ✓ | Some runs keep error |
| G13 nazdolj→navzdol | ~12/15 ✓ | Inconsistent |
| G20 predem→pridem | ~10/15 ✓ | Inconsistent |
| G21 obhodnikov→hodnikov | 0/15 ✗ | Preservation keeps raw |
| G26 špricali→špricam | 0/15 ✗ | Past tense kept |

**Grammar Score:** 25 × (23/28) = 20.5 ≈ 21

### Content (C) - 44/44 or 43/44

| Checkpoint | Status | Notes |
|------------|--------|-------|
| C1-C33 | 15/15 ✓ | All preserved |
| C34 (10m width) | 12/15 ✓ | **MISSING in v8, v10, v14** |
| C35-C44 | 15/15 ✓ | All preserved |

**Content Score:**
- 12 runs: 45 × (44/44) = 45
- 3 runs (v8, v10, v14): 45 × (43/44) = 44

### Readability (R) - 4/4 all runs

| Check | Score | Notes |
|-------|-------|-------|
| R1 Paragraph breaks | 1/1 | 5-7 paragraphs per run |
| R2 Sentence flow | 1/1 | Logical connections |
| R3 Personal voice | 1/1 | "jaz" preserved |
| R4 Dream coherence | 1/1 | Dream logic maintained |

**Readability Score:** 15 × (4/4) = 15

### Hallucinations (H) - 1 found in all runs

| ID | Description | Occurrences |
|----|-------------|-------------|
| H1 | "smo prišli" (we arrived) instead of "sem prišel" (I arrived) | 15/15 |

**Hallucination Score:** 10 - (1 × 2) = 8

### Length (L)

Raw length: 5013 chars

| Ratio Range | Runs | Points |
|-------------|------|--------|
| 70-95% (optimal) | v8 (93.5%), v10 (92.4%), v14 (91.5%) | 5 |
| 95-100% | v1-v7, v9, v11-v13, v15 | 3 |

---

## Comparison: dream_v19 vs dream_v18 chunked

| Metric | dream_v19 nochunk | dream_v18 chunked |
|--------|-------------------|-------------------|
| Pass Rate | 100% | 100% |
| Best Score | 93 | 96 |
| Worst Score | 91 | 95 |
| G1 (bolnica) | **100%** | 20% |
| C34 (10m) | 80% (12/15) | 0% |
| Bimodal Failures | 0% | 0% |

---

## Conclusions

1. **100% reliability** - No bimodal failures without chunking
2. **All EXCELLENT** - Scores 91-93 across all runs
3. **G1 always fixed** - "bolnica" 100% (vs 20% in dream_v18)
4. **C34 trade-off** - Shorter runs (v8, v10, v14) lost 10m detail for L=5
5. **H1 persistent** - "smo prišli" hallucination in all runs
6. **Consistent grammar** - ~23/28 checkpoints fixed

### Recommendation

dream_v19 with maverick-17b non-chunked provides:
- Reliable 100% pass rate without chunking complexity
- Excellent scores (91-93) with room for improvement
- Better G1 fix rate than dream_v18 chunked

Trade-off: Slightly lower overall scores than dream_v18 chunked (91-93 vs 95-96) due to preservation focus keeping some grammar errors.

---

## Raw Data

Cache: `cache/70cfb2c5.../dream_v19/meta-llama-llama-4-maverick-17b-128e-instruct/nochunk/T1*.json`