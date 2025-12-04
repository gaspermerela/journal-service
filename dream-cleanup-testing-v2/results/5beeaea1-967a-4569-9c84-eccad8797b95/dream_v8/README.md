# dream_v8 Results

← [Back to Index](../README.md)

**Prompt ID:** 390
**Prompt Type:** Single-task (cleaned_text only - themes/emotions/etc NOT populated)

---

## Best Result

| Model | Config | Score | Status |
|-------|--------|-------|--------|
| meta-llama/llama-4-maverick-17b-128e-instruct | T5 | 87/100 | PASS |

---

## Model Comparison

| Model | Best Config | Score | G/25 | C/45 | R/15 | H/10 | L/5 | Status | Key Failures |
|-------|-------------|-------|------|------|------|------|-----|--------|--------------|
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T5 | 87/100 | 20 | 41 | 11 | 10 | 5 | PASS | G1 never fixed; R1 partial; Russian leak in T1/T2/P1 |
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) | P4 | 85/100 | 18 | 41 | 11 | 10 | 5 | PASS | G1, G25, G27, G28 never fixed; R1 none |
| [gpt-oss-120b](./openai-gpt-oss-120b.md) | P1 | 73/100 | 20 | 27 | 15 | 10 | 1 | REVIEW | Over-summarized (52%); Best R1/paragraphs; Only fixes G1 |

---

## Summary Statistics

### Parameter Test Coverage

| Model | T1-T7 | P1-P6 | B1-B4 | Total Configs |
|-------|-------|-------|-------|---------------|
| llama-3.3-70b-versatile | ✅ 7/7 | ✅ 6/6 | ❌ 0/4 | 13 |
| maverick-17b | ✅ 7/7 | ✅ 6/6 | ❌ 0/4 | 13 |
| gpt-oss-120b | ✅ 7/7 | ✅ 6/6 | ❌ 0/4 | 13 |

## Key Findings

### Grammar (G)

| Checkpoint | llama-3.3 | maverick | gpt-oss | Notes |
|------------|-----------|----------|---------|-------|
| G1 (polnica→bolnica) | ❌ Never | ✅ P5 only | ✅ Fixed | maverick P5 and gpt-oss fix |
| G++ (Russian leak) | ✅ Clean | ⚠️ T1,T2,P1-P4 | ✅ Clean | maverick has "приходят" at low top_p |
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

**Winner: maverick T5** (87/100 PASS)
- Best overall score
- Best balance of grammar, content, and structure
- Avoid T1, T2, P1 due to Russian contamination (G++ -5 penalty)

### Model-Specific Notes

1. **maverick-17b** (Best: T5 @ 87/100)
   - Use T3 or T5 only
   - Highest overall score
   - Watch for Russian leak at low temperatures
   - G1 never fixed, R1 partial paragraphs

2. **llama-3.3-70b-versatile** (Best: P4 @ 85/100)
   - Use P4 (best config)
   - Never fixes G1, G25, G27, G28
   - No paragraph structure (R1=0)
   - Very consistent across configs

3. **gpt-oss-120b** (Best: P1 @ 73/100)
   - NOT recommended for production
   - Severe over-summarization (loses 40-50% content)
   - Best paragraph structure (R1=1, only model with full paragraphs)
   - Only model to fix G1 (polnica→bolnica)
   - Useful for studying paragraph formatting

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
