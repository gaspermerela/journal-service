# Cleanup Results: 5beeaea1-967a-4569-9c84-eccad8797b95

**Criteria:** [criteria/5beeaea1-967a-4569-9c84-eccad8797b95.md](../../criteria/5beeaea1-967a-4569-9c84-eccad8797b95.md) (not committed)

---

## Best Result

| Prompt | Model | Config | Score | Status |
|--------|-------|--------|-------|--------|
| **[dream_v10](./dream_v10/README.md)** | **maverick-17b** | **T1 (temp=0.0)** | **94/100** | **EXCELLENT** |

---

## Prompt Comparison

| Prompt | Best Model | Best Config | Score | G/25 | C/45 | R/15 | H/10 | L/5 | Key Finding |
|--------|------------|-------------|-------|------|------|------|------|-----|-------------|
| **[dream_v10](./dream_v10/README.md)** | maverick T1 | temp=0.0 | **94/100** | 21 | 43 | 15 | 10 | 5 | ONLY model to fix G1 (bolnica) |
| [dream_v10_analysis](./dream_v10_analysis/README.md) | maverick T1 | temp=0.0 | 87/100 | 24 | 37 | 15 | 10 | 1 | Analysis hurts cleanup; scout T5=83 |
| [dream_v10_slo](./dream_v10_slo/README.md) | llama T1 / maverick P2 | tied | 82/100 | 12-21 | 38-40 | 15 | 10 | 5 | Slovenian prompt underperforms |
| [dream_v9_slo](./dream_v9_slo/README.md) | llama-3.3-70b T3 | temp=0.5 | 86/100 | 18 | 42 | 11 | 10 | 5 | G1 (polnica) unfixed |
| [dream_v8](./dream_v8/README.md) | maverick T5 / llama P4 | tied | 87/100 | 18-20 | 41-43 | 11 | 10 | 5 | Russian leak risk in maverick |

---

## Overall Status

**EXCELLENT achieved!** maverick T1 with dream_v10 scores 94/100.

### Current Best Performers

| Rank | Prompt | Model | Config | Score | Status | Notes |
|------|--------|-------|--------|-------|--------|-------|
| 1 | **[dream_v10](./dream_v10/README.md)** | **maverick T1** | temp=0.0 | **94/100** | EXCELLENT | Best STT fixes, fixes G1! |
| 2 | [dream_v10](./dream_v10/README.md) | scout T1 | temp=0.0 | 91/100 | EXCELLENT | Best content, C23+C34 preserved |
| 3 | [dream_v8](./dream_v8/README.md) | maverick T5 | temp=1.0 | 87/100 | PASS | Good grammar |
| 3 | [dream_v8](./dream_v8/README.md) | llama-3.3 P4 | top_p=0.7 | 87/100 | PASS | Fixes G1 |
| 5 | [dream_v9_slo](./dream_v9_slo/README.md) | llama-3.3 T3 | temp=0.5 | 86/100 | PASS | Slovenian prompt |
| 6 | [dream_v10](./dream_v10/README.md) | llama-3.3 P3 | top_p=0.5 | 84/100 | PASS | Good balance |
| 7 | [dream_v10_slo](./dream_v10_slo/README.md) | llama T1 / maverick P2 | tied | 82/100 | PASS | Slovenian underperforms |

---

## Key Findings

### 1. English vs Slovenian Prompts

**English prompt (dream_v10) significantly outperforms Slovenian (dream_v10_slo):**

| Model | dream_v10 (English) | dream_v10_slo (Slovenian) |
|-------|---------------------|---------------------------|
| maverick | 94/100 (T1) | 82/100 (P2) |
| scout | 91/100 (T1) | 73/100 (T4) |
| llama | 84/100 (P3) | 82/100 (T1) |
| gpt-oss | 64/100 (T1) | 60/100 (P4) |

### 2. Model Recommendations

**Production:** maverick T1 with dream_v10 (94/100)
- Best grammar (21/25)
- ONLY model to fix critical "polnica→bolnica" (G1)
- Good content (43/45)
- No hallucinations

**Alternative:** scout T1 with dream_v10 (91/100)
- Best content preservation (43/45)
- Preserves C23 (flat areas) + C34 (10m width)
- Requires post-processing for grammar

**Avoid:** gpt-oss-120b
- Severe over-summarization (40-58% length)
- Hallucinations detected
- Loses personal voice

---

## Legend

### Scoring Components (100 points total)
- **G**: Grammar (25 max) - `25 × (passed/28)`
- **C**: Content (45 max) - `45 × (passed/44)`
- **R**: Readability (15 max) - `15 × (score/4)`
- **H**: Hallucinations (10 max) - `10 - (count × 2)`
- **L**: Length (5 max) - table lookup based on ratio

### Status Thresholds
- **EXCELLENT**: ≥90
- **PASS**: ≥80
- **REVIEW**: 70-79
- **ITERATE**: 60-69
- **FAIL**: <60

---

## Test History

| Date | Prompt | Models Tested | Best Score |
|------|--------|---------------|------------|
| 2025-12-05 | [dream_v10_analysis](./dream_v10_analysis/README.md) | maverick, scout | 87/100 (maverick T1), 83/100 (scout T5) |
| 2025-12-04 | [dream_v10](./dream_v10/README.md) | maverick, scout, llama, gpt-oss | **94/100** (maverick T1) |
| 2025-12-04 | [dream_v10_slo](./dream_v10_slo/README.md) | maverick, scout, llama, gpt-oss | 82/100 (llama T1 / maverick P2) |
| 2025-12-04 | [dream_v9_slo](./dream_v9_slo/README.md) | llama, maverick, scout, gpt-oss | 86/100 (llama T3) |
| 2025-12-01 | [dream_v8](./dream_v8/README.md) | llama, maverick, gpt-oss | 87/100 (maverick T5 / llama P4) |

---

## Prompt Files

- [dream_v10_analysis](./dream_v10_analysis/README.md) - English with STT patterns + analysis fields
- [dream_v10](./dream_v10/README.md) - English with STT patterns (BEST)
- [dream_v10_slo](./dream_v10_slo/README.md) - Slovenian with STT patterns
- [dream_v9_slo](./dream_v9_slo/README.md) - Slovenian prompt
- [dream_v8](./dream_v8/README.md) - Earlier English prompt
