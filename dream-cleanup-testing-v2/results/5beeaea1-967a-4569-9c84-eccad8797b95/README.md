# Cleanup Results: 5beeaea1-967a-4569-9c84-eccad8797b95

**Criteria:** [criteria/5beeaea1-967a-4569-9c84-eccad8797b95.md](../../criteria/5beeaea1-967a-4569-9c84-eccad8797b95.md) (not committed)

---

## Best Results (Tied)

| Prompt | Model | Config | Score | Status |
|--------|-------|--------|-------|--------|
| [dream_v8](./dream_v8/README.md) | maverick-17b | T5 | 87/100 | PASS |
| [dream_v8](./dream_v8/README.md) | llama-3.3-70b | P4 | 87/100 | PASS |

---

## Prompt Comparison

| Prompt | Best Model | Best Config | Score | G/25 | C/45 | R/15 | H/10 | L/5 | Key Failures |
|--------|------------|-------------|-------|------|------|------|------|-----|--------------|
| [dream_v8](./dream_v8/README.md) | maverick T5 / llama P4 | tied | 87/100 | 18-20 | 41-43 | 11 | 10 | 5 | R1 partial/none; Russian risk in maverick |
| [dream_v9_slo](./dream_v9_slo/README.md) | llama-3.3-70b T3 | temp=0.5 | 86/100 | 18 | 42 | 11 | 10 | 5 | G1 (polnica); garbled phrases |

---

## Overall Status

**PASS achieved!** Two models tied at 87/100: maverick T5 and llama P4.

### Current Best Performers

| Rank | Prompt | Model | Config | Score | Status | Notes |
|------|--------|-------|--------|-------|--------|-------|
| 1 | [dream_v8](./dream_v8/README.md) | maverick T5 | t=1.0 | 87/100 | PASS | Better grammar (G=20), partial paragraphs |
| 1 | [dream_v8](./dream_v8/README.md) | llama-3.3 P4 | p=0.7 | 87/100 | PASS | Better content (C=43), fixes G1! |
| 3 | [dream_v9_slo](./dream_v9_slo/README.md) | llama-3.3 T3 | t=0.5 | 86/100 | PASS | Slovenian prompt, best paragraphs |
| 4 | [dream_v8](./dream_v8/README.md) | maverick T3 | t=0.5 | 82/100 | PASS | Good alternative |

---

## Blocking Issues for EXCELLENT (≥90)

Issues that prevent reaching EXCELLENT:

### 1. Partial/No Paragraph Structure (R1)
- **Impact:** 3-4 points on Readability
- **Models affected:** llama-3.3 worst (R1=0), maverick partial
- **Solution:** Add paragraph requirement with \n\n

### 2. Garbled Phrases Not Fixed (G23, G25, G27, G28)
- **Impact:** ~2 points on Grammar
- **Models affected:** llama-3.3 worst
- **Solution:** Add examples of common garbled→fixed pairs

### 3. gpt-oss Over-summarization
- **Impact:** 14+ points on Content (C=27 vs 41)
- **Models affected:** gpt-oss-120b only
- **Solution:** Not fixable via prompt - avoid this model for content

---

## Recommended Next Steps

1. **Create dream_v9 prompt** with:
   - Russian/Cyrillic prohibition (fixes G++ leak in low top_p)
   - Paragraph requirement with scene breaks
   - Garbled phrase examples

2. **Test maverick with dream_v9**
   - Focus on T5 and P5 configs (both clean, P5 fixes G1!)
   - Avoid T1, T2, P1-P4 (Russian leak risk with G++ -5 penalty)

3. **Consider new models**
   - moonshotai/kimi-k2-instruct (multilingual)
   - qwen/qwen3-32b (100+ languages)

---

## Legend

### Scoring Components (100 points total)
- **G**: Grammar (25 max) - `25 × (passed/28)`
- **C**: Content (45 max) - `45 × (passed/44)`
- **R**: Readability (15 max) - `15 × (score/4)`
- **H**: Hallucinations (10 max) - `10 - (count × 2)`
- **L**: Length (5 max) - table lookup based on ratio

### Penalties
- **G+ (English words)**: -3 from Grammar
- **G++ (Russian/Cyrillic)**: -5 from Grammar
- **Voice issues (minor)**: -3 from Content
- **Voice issues (major)**: -7 from Content

---

## Test History

| Date | Prompt | Models Tested | Configs | Best Score |
|------|--------|---------------|---------|------------|
| 2025-12-01 | [dream_v8](./dream_v8/README.md) | llama-3.3, maverick, gpt-oss | 25 total | 87/100 (maverick T5, llama P4 tied) |
| 2025-12-04 | [dream_v9_slo](./dream_v9_slo/README.md) | llama-3.3, maverick, scout, gpt-oss | 52 total | 86/100 (llama T3) |
