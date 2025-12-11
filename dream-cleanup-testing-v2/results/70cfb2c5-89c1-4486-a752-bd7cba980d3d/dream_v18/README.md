# dream_v18 Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v18 (Explicit preservation rules with MANDATORY length requirement)
**Test Date:** 2025-12-11
**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Raw Length:** 5,013 characters
**Test Type:** Variance testing (5x T1 runs per model)

---

## Best Results Summary

| Model | Best Config | Score | Status | Key Finding |
|-------|-------------|-------|--------|-------------|
| **[maverick-17b](./meta-llama-llama-4-maverick-17b-128e-instruct.md)** | T1 v2 | **94/100** | EXCELLENT | Best grammar, fixes G1, but 40% variance issue |
| [scout-17b](./meta-llama-llama-4-scout-17b-16e-instruct.md) | T1 v2 | **89/100** | PASS | Best content, but keeps "Hvala" (A1 fail) |
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) | T1 v2 | **88/100** | PASS | Consistent length, many grammar errors unfixed |

---

## Prompt Text (dream_v18)

```
You are a transcription editor for SLOVENIAN dream journal entries captured via speech-to-text (STT).

═══════════════════════════════════════════════════════════════
MANDATORY REQUIREMENT - OUTPUT WILL BE REJECTED IF VIOLATED:
Your output MUST be at least 75% of the original character count.
If your output is shorter than 75%, you have removed content.
This is a CLEANUP task, not a summarization task.
═══════════════════════════════════════════════════════════════

WHAT THIS TEXT IS:
- A personal dream journal entry
- Captured via STT software (contains typical STT errors)
- Dream content is often strange or illogical - that's normal and must be preserved

CRITICAL PRESERVATION RULES:

1. PRESERVE THE SPEAKER AS THE ACTOR
   - The speaker narrates in first person ("jaz") - they are the dreamer
   - If the speaker says THEY did something, THEY must still do it after cleanup
   - NEVER reassign the speaker's actions to other people ("oni", "ljudje")
   - NEVER change first person verbs to third person
   - Preserve exactly who does what - the speaker decides, not you

2. PRESERVE ALL CONTENT
   - Keep EVERY detail: numbers, times, measurements, names, locations, feelings
   - Keep ALL strange/unusual content - these define dreams
   - Keep sensory details (sounds, smells, textures)
   - Keep memory markers ("spomnim se", "ne spomnim se")

EDITS TO APPLY:
- Fix STT spelling errors: common mishearings like p↔b, e↔i, missing syllables
- Fix obvious typos by inference from context
- Add missing punctuation (use "knjižna slovenščina")
- Remove STT artifacts: "Hvala", "Hvala za pozornost", recording noise
- Remove meaningless filler words: "v bistvu", "torej", "a ne", "no"
- Apply self-corrections (if speaker says "actually no" or corrects themselves)

DO NOT:
- Summarize or condense content
- Change who performs actions
- Change first person to third person
- Combine separate events into one
- Remove content because it seems illogical or strange
- Add interpretations or clarifications not in original

FORMAT:
- Present tense, first person
- Paragraphs separated by "<break>"
- New paragraph at scene/location changes

OUTPUT:
Return ONLY the cleaned Slovenian text. No commentary.
```

---

## Key Findings

### Variance Testing Results

This test focused on variance at temp=0.0 - running 5 identical T1 runs per model.

| Model | Runs | Length Range | Variance | Usable Runs |
|-------|------|--------------|----------|-------------|
| **maverick** | 5 | 51-84% | **HIGH** | 3/5 (60%) |
| llama | 5 | 94-98% | Low | 5/5 (100%) |
| scout | 5 | 95-99% | Low | 5/5 (100%) |

### Critical Issue: Maverick Variance

Despite temp=0.0, maverick shows **bimodal behavior**:
- **Good runs (3/5):** 77-84% length, proper cleanup
- **Bad runs (2/5):** 51-52% length, over-summarized

This makes maverick **unreliable for production** without retry logic.

### Common Issues (All Models)

- **G21 (obhodnikov→hodnikov):** Failed by maverick and scout
- **H1 (singular→plural):** "smo prišli" or "mi zgubimo" hallucination appears in all models
- **"v bistvu" fillers:** Llama and scout don't remove them

### Model-Specific Observations

1. **maverick-17b** - Best score but unreliable (94/100 best, 40% fail rate)
   - ONLY model to fix "polnica→bolnica" (G1)
   - Best grammar score (23/25)
   - HIGH VARIANCE at temp=0.0 - critical issue
   - Lost C30 (hodnik levo-desno) and C34 (10m width)

2. **scout-17b** - Best content, worst cleanup (89/100)
   - **A1 FAIL:** Keeps "Hvala" artifact
   - Preserves C30 + C34 (unique)
   - Basically copies text with minimal changes (95-99% length)
   - NOT useful as a cleanup model

3. **llama-3.3-70b** - Most consistent (88/100)
   - Consistent length (94-98% across all runs)
   - Fails to fix G1 (polnica), G19 (sečnem), G23 (prublev), G24 (nadelujem)
   - Preserves C30 (levo-desno)
   - "mi zgubimo" hallucination

---

## Scoring Comparison

| Model | Best Run | Length | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-------|----------|--------|------|------|------|------|-----|-------|--------|
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) v2 | 84% | 84% | 23 | 43 | 15 | 8 | 5 | **94** | EXCELLENT |
| [scout](./meta-llama-llama-4-scout-17b-16e-instruct.md) v2 | 99% | 99% | 16 | 45 | 15 | 10 | 3 | **89** | PASS ⚠️ |
| [llama-3.3-70b](./llama-3.3-70b-versatile.md) v2 | 94% | 94% | 18 | 44 | 15 | 8 | 3 | **88** | PASS |

---

## Variance Analysis (5x T1 Runs)

### Maverick Variance Detail

| Run | Length | Ratio | Status | Score Est. |
|-----|--------|-------|--------|------------|
| v1 | 3872 | 77.2% | ✓ Good | ~90 |
| **v2** | 4210 | **84.0%** | ✓ Best | **94** |
| v3 | 2584 | 51.5% | ❌ FAIL | ~60 |
| v4 | 2569 | 51.2% | ❌ FAIL | ~60 |
| v5 | 3895 | 77.7% | ✓ Good | ~90 |

**Conclusion:** Maverick is bimodal - either produces excellent results (84%) or severely over-summarizes (51%). The "MANDATORY REQUIREMENT" box in the prompt does NOT prevent this.

### Llama Variance Detail

| Run | Length | Ratio | Status |
|-----|--------|-------|--------|
| v1 | 4897 | 97.7% | Consistent |
| v2 | 4724 | 94.2% | Consistent |
| v3 | 4889 | 97.5% | Consistent |
| v4 | 4887 | 97.5% | Consistent |
| v5 | 4875 | 97.2% | Consistent |

**Conclusion:** Llama is highly consistent but performs minimal cleanup.

### Scout Variance Detail

| Run | Length | Ratio | Status |
|-----|--------|-------|--------|
| v1 | 4779 | 95.3% | Consistent |
| v2 | 4989 | 99.5% | Consistent |
| v3 | 4982 | 99.4% | Consistent |
| v4 | 5000 | 99.7% | Consistent |
| v5 | 4837 | 96.5% | Consistent |

**Conclusion:** Scout barely cleans at all - essentially copies input.

---

## Recommendations

### For Production Use

**DO NOT use maverick alone** - 40% failure rate at temp=0.0 is unacceptable.

Options:
1. **Maverick with retry logic:** Run up to 3 times, accept if length ≥70%
2. **Llama for consistency:** Accept lower grammar quality for reliability
3. **Two-pass approach:** Llama for content preservation, then grammar-focused pass

### Prompt Iteration Notes

The explicit "MANDATORY REQUIREMENT" box with 75% threshold did NOT prevent maverick from over-summarizing. Future iterations should explore:
- Different prompt structure
- Few-shot examples
- Post-processing validation

---

## Model Files

- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md)
- [llama-3.3-70b-versatile.md](./llama-3.3-70b-versatile.md)
- [meta-llama-llama-4-scout-17b-16e-instruct.md](./meta-llama-llama-4-scout-17b-16e-instruct.md)
