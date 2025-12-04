# dream_v8 Results

← [Back to Index](../README.md)

**Prompt ID:** 390
**Prompt Type:** Single-task (cleaned_text only - themes/emotions/etc NOT populated)

---

## Best Result

| Model | Config | Score | Status |
|-------|--------|-------|--------|
| meta-llama/llama-4-maverick-17b-128e-instruct | T5 | 32/40 | ITERATE |

---

## Model Comparison

| Model | Best Config | Score | G | C | A | R | Status | Key Failures |
|-------|-------------|-------|---|---|---|---|--------|--------------|
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T5 | 32/40 | 6.5 | 8.5 | 10 | 7 | ITERATE | G1, G13, G16, G17; R1 partial |
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) | P4 | 30.5/40 | 6 | 8.5 | 10 | 6 | ITERATE | G1, G3, G13, G16, G17, G23, G27, G28; R1 |
| [gpt-oss-120b](./openai-gpt-oss-120b.md) | P1 | 30/40 | 7 | 5 | 10 | 8 | ITERATE | C+++ (over-summarized 52%); many C failures |

---

## Summary Statistics

### Parameter Test Coverage

| Model | T1-T7 | P1-P6 | B1-B4 | Total Configs |
|-------|-------|-------|-------|---------------|
| llama-3.3-70b-versatile | ✅ 7/7 | ✅ 6/6 | ❌ 0/4 | 13 |
| maverick-17b | ✅ 7/7 | ⚠️ 1/6 | ❌ 0/4 | 8 |
| gpt-oss-120b | ⚠️ 3/7 | ⚠️ 1/6 | ❌ 0/4 | 4 |

### Score Distribution

| Score Range | Count | Configs |
|-------------|-------|---------|
| ≥38 (PASS) | 0 | - |
| 36-37 (REVIEW) | 0 | - |
| 30-35 (ITERATE) | 5 | maverick T3/T5, llama P4, gpt P1 |
| <30 (ITERATE) | Many | Most configs |
| Unusable | 2 | llama T7 (gibberish), maverick T7 (degraded) |

---

## Key Findings

### Grammar (G)

| Checkpoint | llama-3.3 | maverick | gpt-oss | Notes |
|------------|-----------|----------|---------|-------|
| G1 (polnica→bolnica) | ❌ Never | ❌ Never | ✅ Fixed | Critical - only gpt-oss fixes |
| G++ (Russian leak) | ✅ Clean | ⚠️ T1,T2,P1 | ✅ Clean | maverick has "приходят" |
| G25 (garbled phrase) | ❌ Never | ✅ Often | ✅ Often | maverick/gpt better |
| G27, G28 | ❌ Never | ⚠️ Sometimes | ✅ Often | llama worst |

### Content (C)

| Check | llama-3.3 | maverick | gpt-oss | Notes |
|-------|-----------|----------|---------|-------|
| C+++ (length 70-95%) | ✅ 70-88% | ✅ 69-82% | ❌ 49-58% | gpt severely over-summarizes |
| C++ (hallucinations) | ✅ None | ✅ None | ❌ Present | gpt adds content |
| Detail preservation | Good | Good | Poor | gpt loses 40-50% |

### Artifacts (A)

| Check | llama-3.3 | maverick | gpt-oss |
|-------|-----------|----------|---------|
| A1 (Hvala removed) | ✅ | ✅ | ✅ |
| A2 (intro kept) | Sometimes | ❌ Removed | Sometimes |
| A3 (fillers) | ⚠️ Some kept | ⚠️ Some kept | ✅ Reduced |

### Readability (R)

| Check | llama-3.3 | maverick | gpt-oss |
|-------|-----------|----------|---------|
| R1 (paragraphs) | ❌ None | ⚠️ Partial | ✅ Full |
| R2 (flow) | ✅ | ✅ | ✅ |
| R3 (voice) | ✅ | ✅ | ⚠️ Shifts |
| R4 (coherence) | ✅ | ✅ | ✅ |

---

## Recommendations

### Best Model for dream_v8

**Winner: maverick T3 or T5**
- Best balance of grammar, content, and structure
- Avoid T1, T2, P1 due to Russian contamination
- Score: 32/40

### Model-Specific Notes

1. **llama-3.3-70b-versatile**
   - Use P4 (best config)
   - Never fixes G1, G25, G27, G28
   - No paragraph structure

2. **maverick-17b**
   - Use T3 or T5 only
   - Best overall score
   - Watch for Russian leak at low temperatures

3. **gpt-oss-120b**
   - NOT recommended
   - Over-summarizes (loses 40-50% content)
   - Has hallucinations
   - Best paragraph structure if that's the only concern

### Prompt v9 Suggestions

1. Add explicit G1 example: `"polnica" je narobe, pravilno: "bolnica"`
2. Add Russian prohibition: `Besedilo mora biti SAMO v slovenščini (brez cirilice, angleščine, ruščine)`
3. Require paragraphs: `Razdeli besedilo v odstavke, ločene s prazno vrstico (\n\n)`
4. Add over-summarization guard: `NE povzemaj. Ohrani VSE podrobnosti iz originalnega besedila.`

---

## Appendix: Unfixed Grammar Checkpoints

These checkpoints are NOT fixed by ANY model in ANY config:

| ID | Raw | Correct | Status |
|----|-----|---------|--------|
| G1 | polnica | bolnica | Only gpt-oss fixes |
| G17 | mogo | moral | Rarely fixed |
| G23 | prublev čimprej | probam čimprej | Rarely fixed |
