# Cleanup Results: 5beeaea1-967a-4569-9c84-eccad8797b95

**Criteria:** [criteria/5beeaea1-967a-4569-9c84-eccad8797b95.md](../../criteria/5beeaea1-967a-4569-9c84-eccad8797b95.md) (not committed)

---

## Best Result

| Prompt | Model | Config | Score | Status |
|--------|-------|--------|-------|--------|
| dream_v8 | meta-llama/llama-4-maverick-17b-128e-instruct | T5 | 32/40 | ITERATE |

---

## Prompt Comparison

| Prompt | Best Model | Best Config | Score | G | C | A | R | Key Failures |
|--------|------------|-------------|-------|---|---|---|---|--------------|
| [dream_v8](./dream_v8/) | maverick-17b | T5 | 32/40 | 6.5 | 8.5 | 10 | 7 | G1, G13, G16, G17; R1 partial |

---

## Overall Status

**No PASS results yet.** All tested configurations score below 38/40.

### Score Thresholds
- **≥38: PASS** - Production ready
- **36-37: REVIEW** - Close, check specific failures
- **<36: ITERATE** - Needs prompt/model changes

### Current Best Performers

| Rank | Prompt | Model | Config | Score | Notes |
|------|--------|-------|--------|-------|-------|
| 1 | dream_v8 | maverick T5 | t=1.0 | 32/40 | Best overall, good content |
| 2 | dream_v8 | maverick T3 | t=0.5 | 32/40 | Same score, also good |
| 3 | dream_v8 | llama-3.3 P4 | p=0.7 | 30.5/40 | Best llama config |
| 4 | dream_v8 | gpt-oss P1 | p=0.1 | 30/40 | Over-summarizes |

---

## Blocking Issues

Issues that prevent reaching PASS (≥38):

### 1. G1 "polnica→bolnica" Not Fixed
- **Impact:** -0.5 per occurrence
- **Models affected:** llama-3.3, maverick (gpt-oss fixes this)
- **Solution:** Add explicit example in prompt

### 2. No Paragraph Structure (R1)
- **Impact:** -3 to -4 on Readability
- **Models affected:** llama-3.3 worst, maverick partial
- **Solution:** Add paragraph requirement with \n\n

### 3. Garbled Phrases Not Fixed (G23, G25, G27, G28)
- **Impact:** -2 to -4 on Grammar
- **Models affected:** llama-3.3 worst
- **Solution:** Add examples of common garbled→fixed pairs

### 4. gpt-oss Over-summarization
- **Impact:** -4 on Content (C+++ violation)
- **Models affected:** gpt-oss-120b only
- **Solution:** Not fixable via prompt - avoid this model

---

## Recommended Next Steps

1. **Create dream_v9 prompt** with:
   - G1 explicit fix example
   - Russian/Cyrillic prohibition
   - Paragraph requirement
   - Garbled phrase examples

2. **Test maverick with dream_v9**
   - Focus on T3 and T5 configs
   - Avoid T1, T2, P1 (Russian leak risk)

3. **Complete P-series testing for maverick**
   - Currently only P1 tested
   - P2-P6 may yield better results

4. **Consider new models**
   - moonshotai/kimi-k2-instruct (multilingual)
   - qwen/qwen3-32b (100+ languages)

---

## Legend

- **G**: Grammar (G1-G28, G+, G++)
- **C**: Content (C1-C44, C+, C++, C+++)
- **A**: Artifacts (A1-A3)
- **R**: Readability (R1-R4)
- **Score**: Total out of 40
- **Status**: PASS (≥38), REVIEW (36-37), ITERATE (<36)

---

## Test History

| Date | Prompt | Models Tested | Configs | Best Score |
|------|--------|---------------|---------|------------|
| 2025-12-01 | dream_v8 | llama-3.3, maverick, gpt-oss | 25 total | 32/40 |
