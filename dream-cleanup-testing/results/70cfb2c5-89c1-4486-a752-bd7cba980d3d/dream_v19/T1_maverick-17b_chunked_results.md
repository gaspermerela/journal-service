# T1 maverick-17b Chunked Results (dream_v19)

**Transcription:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Model:** groq-meta-llama/llama-4-maverick-17b-128e-instruct
**Prompt:** dream_v19 (preservation-focused)
**Config:** T1 (temp=0.0, top_p=null)
**Chunking:** ENABLED
**Runs:** 15

---

## Summary

| Metric | Value |
|--------|-------|
| Pass Rate | **100%** (15/15) |
| Best Score | 94/100 (EXCELLENT) |
| Worst Score | 91/100 (EXCELLENT) |
| Average Score | ~92.7/100 |
| Ratio Range | 93.0% - 97.6% |

---

## Individual Run Scores

| Run | Chars | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|-------|-------|------|------|------|------|-----|-------|--------|
| v1 | 4747 | 94.7% | 21 | 45 | 15 | 8 | 5 | 94 | EXCELLENT |
| v2 | 4719 | 94.1% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v3 | 4689 | 93.5% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v4 | 4661 | 93.0% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v5 | 4702 | 93.8% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v14 | 4690 | 93.6% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v15 | 4767 | 95.1% | 21 | 44 | 15 | 8 | 3 | 91 | EXCELLENT |
| v16 | 4735 | 94.5% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v17 | 4802 | 95.8% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v18 | 4705 | 93.9% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v19 | 4666 | 93.1% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v20 | 4723 | 94.2% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |
| v21 | 4847 | 96.7% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v22 | 4892 | 97.6% | 21 | 45 | 15 | 8 | 3 | 92 | EXCELLENT |
| v23 | 4672 | 93.2% | 21 | 44 | 15 | 8 | 5 | 93 | EXCELLENT |

**Note:** v1, v17, v21, v22 preserved C34 (10m width detail). All other runs lost it (-1 to C).

---

## Checkpoint Analysis

### Grammar (G) - ~23/28 passed consistently

| Checkpoint | Status | Notes |
|------------|--------|-------|
| G1 polnica→bolnica | 15/15 ✓ | Always fixed |
| G2 pretličju→pritličju | 14/15 ✓ | v16 uses "preddverju" (minor variant) |
| G3 uspodbudo→spodbudo | 0/15 ✗ | Preservation keeps original |
| G13 nazdolj→navzdol | ~10/15 ✓ | Inconsistent |
| G20 predem→pridem | ~8/15 ✓ | Inconsistent |
| G21 obhodnikov→hodnikov | 0/15 ✗ | Preservation keeps raw |
| G26 špricali→špricam | 0/15 ✗ | Past tense kept |

**Grammar Score:** 25 × (23/28) ≈ 21

### Content (C) - 43/44 or 44/44

| Checkpoint | Status | Notes |
|------------|--------|-------|
| C1-C33 | 15/15 ✓ | All preserved |
| C34 (10m width) | **4/15 ✓** | ONLY v1, v17, v21, v22 preserved |
| C35-C44 | 15/15 ✓ | All preserved |

**Content Score:**
- 4 runs (v1, v17, v21, v22): 45 × (44/44) = 45
- 11 runs: 45 × (43/44) = 44

### Readability (R) - 4/4 all runs

| Check | Score | Notes |
|-------|-------|-------|
| R1 Paragraph breaks | 1/1 | 4-6 paragraphs per run |
| R2 Sentence flow | 1/1 | Logical connections |
| R3 Personal voice | 1/1 | "jaz" preserved |
| R4 Dream coherence | 1/1 | Dream logic maintained |

**Readability Score:** 15 × (4/4) = 15

### Hallucinations (H) - 1 found in all runs

| ID | Description | Occurrences |
|----|-------------|-------------|
| H1 | "smo prišli/prišla" (we arrived) instead of "sem prišel" (I arrived) | 15/15 |

**Hallucination Score:** 10 - (1 × 2) = 8

### Length (L)

Raw length: 5013 chars

| Ratio Range | Runs | Points |
|-------------|------|--------|
| 70-95% (optimal) | v1-v5, v14, v16, v18-v20, v23 (11 runs) | 5 |
| 96-100% | v15, v17, v21, v22 (4 runs) | 3 |

---

## Comparison: Chunked vs Non-Chunked (dream_v19)

| Metric | Chunked | Non-Chunked |
|--------|---------|-------------|
| Pass Rate | 100% | 100% |
| Best Score | 94 | 93 |
| Worst Score | 91 | 91 |
| Average Score | ~92.7 | ~92.0 |
| G1 (bolnica) | **100%** | **100%** |
| C34 (10m) | **27% (4/15)** | **80% (12/15)** |
| Optimal Length (L=5) | 73% (11/15) | 20% (3/15) |

---

## Conclusions

1. **100% reliability** - All runs pass with EXCELLENT scores
2. **Best score: 94** - v1 achieved both C34 preservation AND optimal length
3. **C34 trade-off** - Chunking loses 10m width detail 73% of the time (vs 20% non-chunked)
4. **Better compression** - 73% of chunked runs achieve optimal length (vs 20% non-chunked)
5. **H1 persistent** - "smo prišli" hallucination in all runs
6. **Consistent grammar** - ~23/28 checkpoints fixed across all runs

### Key Finding

Chunked runs achieve **slightly higher average scores** (92.7 vs 92.0) due to better length compression, but **lose C34 detail more often** (73% vs 20%). The trade-off is:
- Chunked: More runs at optimal length, but higher C34 loss
- Non-chunked: Better C34 preservation, but more runs above optimal length

### Recommendation

For this transcription (5013 chars), **non-chunked is preferred** because:
1. C34 preservation is more reliable (80% vs 27%)
2. Score difference is minimal (~0.7 points)
3. Chunking overhead not justified for short text

Use chunking for longer transcriptions where length compression benefits outweigh C34 loss risk.

---

## Raw Data

Cache: `cache/70cfb2c5.../dream_v19/meta-llama-llama-4-maverick-17b-128e-instruct/chunked/T1*.json`
