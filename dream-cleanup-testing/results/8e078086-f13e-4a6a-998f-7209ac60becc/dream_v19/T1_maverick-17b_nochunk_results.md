# T1 maverick-17b Non-Chunked Results (dream_v19)

**Transcription:** 8e078086-f13e-4a6a-998f-7209ac60becc
**Transcription Provider:** clarinsi_slovene_asr (Slovene_ASR_e2e)
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
| Best Score | 93/100 (v2, v15) |
| Worst Score | 90/100 (v1, v6-v8, v11-v12) |
| Average Score | ~91.1/100 |
| Ratio Range | 78.8% - 96.3% |

---

## Individual Run Scores

| Run | Chars | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|-------|-------|------|------|------|------|-----|-------|--------|
| v1 | 4258 | 86.2% | 20 | 42 | 15 | 8 | 5 | 90 | EXCELLENT |
| v2 | 4254 | 86.1% | 20 | 43 | 15 | **10** | 5 | **93** | EXCELLENT |
| v3 | 4594 | 93.0% | 20 | 44 | 15 | 8 | 5 | 92 | EXCELLENT |
| v4 | 4647 | 94.1% | 20 | 44 | 15 | 8 | 5 | 92 | EXCELLENT |
| v5 | 4372 | 88.5% | 20 | 43 | 15 | 8 | 5 | 91 | EXCELLENT |
| v6 | 4742 | 96.0% | 20 | 44 | 15 | 8 | 3 | 90 | EXCELLENT |
| v7 | 4719 | 95.6% | 20 | 44 | 15 | 8 | 3 | 90 | EXCELLENT |
| v8 | 4752 | 96.2% | 20 | 44 | 15 | 8 | 3 | 90 | EXCELLENT |
| v9 | 4191 | 84.9% | 20 | 43 | 15 | 8 | 5 | 91 | EXCELLENT |
| v10 | 4303 | 87.1% | 20 | 43 | 15 | 8 | 5 | 91 | EXCELLENT |
| v11 | 4758 | 96.3% | 20 | 44 | 15 | 8 | 3 | 90 | EXCELLENT |
| v12 | 4705 | 95.3% | 20 | 44 | 15 | 8 | 3 | 90 | EXCELLENT |
| v13 | 4475 | 90.6% | 20 | 44 | 15 | 8 | 5 | 92 | EXCELLENT |
| v14 | 3894 | 78.8% | 20 | 43 | 15 | 8 | 5 | 91 | EXCELLENT |
| v15 | 4440 | 89.9% | 20 | **45** | 15 | 8 | 5 | **93** | EXCELLENT |

**Notable runs:**
- **v2:** Only run with NO "Rekla je" hallucination (H=10)
- **v15:** Only run that preserved C34 (10m stair width) (C=45)

---

## Checkpoint Analysis

### Grammar (G) - ~30/38 passed consistently

**Grammar Score:** 25 × (30/38) = 19.74 ≈ 20

Key grammar fixes applied in all runs:
- G1 toda→da smrdi ✓
- G2 utopiramo→odpiram ✓
- G3 govorija→govori ✓
- G4 pohodnikov→hodnika ✓
- G12 straja→strah ✓
- G14 navzdor→navzdol ✓
- G18 kiroskop→giroskop ✓

Consistently unfixed (preservation behavior):
- G24-G28: 10m width section often simplified/removed
- G35: "remla je" → sometimes "Rekla je" (hallucination) instead of "bila je"

### Content (C) - Variable preservation

| Checkpoint | Description | Preservation Rate |
|------------|-------------|-------------------|
| C1-C29 | Scenes 1-8 core details | 15/15 (100%) |
| C30 | "hodnik levo-desno" at landing | **9/15 (60%)** |
| C31-C33 | Different environment, 5-7 people, stairs zaobljene/strme | 15/15 (100%) |
| C34 | "deset metrov široke" (10m width) | **1/15 (7%)** - only v15 |
| C35-C42 | Two women, gyroscope question, deteriorating stairs | 15/15 (100%) |
| C43 | She doesn't dare to jump | **14/15 (93%)** |
| C44 | He jumps successfully | 15/15 (100%) |

**Content breakdown by run:**
- 41/44: v1 (C30✗, C34✗, C43✗)
- 42/44: v2, v5, v9, v10, v14 (C30✗, C34✗)
- 43/44: v3, v4, v6, v7, v8, v11, v12, v13 (C34✗)
- 44/44: v15 (ALL preserved!)

### Readability (R) - 4/4 all runs

| Check | Score | Notes |
|-------|-------|-------|
| R1 Paragraph breaks | 1/1 | 5-7 paragraphs per run |
| R2 Sentence flow | 1/1 | Logical connections throughout |
| R3 Personal voice | 1/1 | "jaz" preserved in all runs |
| R4 Dream coherence | 1/1 | Dream logic maintained |

**Readability Score:** 15 × (4/4) = 15

### Hallucinations (H) - "Rekla je" pattern

| ID | Description | Occurrences |
|----|-------------|-------------|
| H1 | "remla je" → "Rekla je" (she said) instead of "bila je" (it was) | **14/15** |

**Hallucination-free run:** v2 correctly rendered "Bilo je nekako zemlja in mokro je bilo vse" (it was kind of dirt and wet everything was)

**Hallucination Score:**
- v2: 10 - (0 × 2) = 10
- All others: 10 - (1 × 2) = 8

### Length (L)

Raw length: 4939 chars

| Ratio Range | Runs | Points |
|-------------|------|--------|
| 70-95% (optimal) | v1-v5, v9-v10, v13-v15 (10 runs) | 5 |
| 96-100% | v6-v8, v11-v12 (5 runs) | 3 |

---

## Key Findings

### Strengths

1. **100% EXCELLENT pass rate** - All 15 runs scored 90+
2. **Successfully handles zero-punctuation input** - All punctuation added correctly
3. **Excellent structure** - 5-7 well-placed paragraph breaks in every run
4. **High C43 preservation (93%)** - Young woman being afraid/unable to jump preserved
5. **Moderate C30 preservation (60%)** - Corridor left-right detail preserved in majority

### Weaknesses

1. **C34 almost always lost (93%)** - 10m stair width detail removed in 14/15 runs
2. **H1 "Rekla je" hallucination (93%)** - Model misreads "remla je" as dialogue in most runs
3. **Length variability** - 5 runs exceeded optimal compression (96%+)

### Notable Patterns

1. **v2 is unique** - Only run that avoided "Rekla je" hallucination, rendering it correctly as "Bilo je"
2. **v15 is unique** - Only run that preserved 10m stair width (C34)
3. **C30 correlates with length** - Longer runs (>95%) tend to preserve C30 more often

---

## Comparison: clarinsi vs Groq Whisper (70cfb2c5)

| Metric | clarinsi (8e078086) | Groq Whisper (70cfb2c5) |
|--------|---------------------|-------------------------|
| Raw punctuation | **None** | Good |
| Raw "Hvala" artifacts | **None** | ~10-12 occurrences |
| Pass rate | 100% | 100% |
| Score range | 90-93 | 91-93 |
| Best score | 93 | 93 |
| C30 preservation | 60% (9/15) | ~80% |
| C34 preservation | 7% (1/15) | ~20% |
| Hallucination type | "Rekla je" (93%) | "smo prišli" (100%) |
| Hallucination-free runs | 1/15 (7%) | 0/15 (0%) |

---

## Conclusions

1. **Reliable 100% EXCELLENT** - All runs production-ready despite zero-punctuation input
2. **C34 (10m width) is the hardest detail** - Only 1 run preserved it
3. **C43 (she didn't jump) mostly preserved** - 93% preservation rate is excellent
4. **"Rekla je" hallucination is common** - But not universal (v2 avoided it)
5. **clarinsi_slovene_asr works well** - Model handles missing punctuation effectively

### Best Configurations

| Rank | Run | Score | Notable |
|------|-----|-------|---------|
| 1 | **v2** | 93 | No hallucination (H=10) |
| 1 | **v15** | 93 | C34 preserved (C=45) |
| 3 | v3, v4, v13 | 92 | C30 + C43 preserved |
| 6 | v5, v9, v10, v14 | 91 | C43 preserved, optimal length |
| 10 | v1, v6-v8, v11-v12 | 90 | Baseline EXCELLENT |

---

## Raw Data

Cache: `cache/8e078086-f13e-4a6a-998f-7209ac60becc/dream_v19/meta-llama-llama-4-maverick-17b-128e-instruct/nochunk/T1*.json`
