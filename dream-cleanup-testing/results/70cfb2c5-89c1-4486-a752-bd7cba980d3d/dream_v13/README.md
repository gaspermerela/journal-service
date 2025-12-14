# dream_v13 Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v13 (Present tense + output format)
**Test Date:** 2025-12-10
**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Raw Length:** 5,013 characters

---

## Summary

| Metric | Value |
|--------|-------|
| **Best Score** | 93/100 (T1_v7) |
| **Worst Score** | 79/100 (T1_v5) |
| **EXCELLENT Rate** | 64% (9/14 runs) |
| **Status** | **NOT PRODUCTION READY** |

---

## Critical Finding: High Variance at temp=0.0

Initial testing (4 runs) showed tight 2.2% variance. Extended testing (14 runs) reveals:

| Metric | Initial (v1-v4) | Extended (v1-v14) |
|--------|-----------------|-------------------|
| Length Variance | 2.2% | **23%** |
| Score Variance | 1 pt | **14 pts** |
| EXCELLENT Rate | 100% | **64%** |
| Failure Rate | 0% | **36%** |

**Conclusion:** Initial results were statistically lucky. True model behavior is highly variable.

---

## Extended Variance Testing (14 Runs)

| Run | Ratio | G | C | R | H | L | Total | Status |
|-----|-------|---|---|---|---|---|-------|--------|
| T1_v1 | 74.6% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v2 | 75.9% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v3 | 75.7% | 23 | 39 | 15 | 8 | 5 | **90** | EXCELLENT |
| T1_v4 | 73.7% | 22 | 40 | 15 | 8 | 5 | **90** | EXCELLENT |
| T1_v5 | 57.0% | 23 | 34 | 15 | 6 | 1 | **79** | REVIEW |
| T1_v6 | 74.8% | 18 | 39 | 15 | 8 | 5 | **85** | CYRILLIC |
| T1_v7 | 73.7% | 23 | 40 | 15 | 10 | 5 | **93** | EXCELLENT |
| T1_v8 | 75.7% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v9 | 59.3% | 23 | 36 | 15 | 6 | 1 | **81** | PASS |
| T1_v10 | 75.3% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v11 | 61.5% | 23 | 37 | 15 | 8 | 3 | **86** | PASS |
| T1_v12 | 74.6% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v13 | 55.4% | 23 | 35 | 15 | 8 | 1 | **82** | PASS |
| T1_v14 | 78.4% | 23 | 41 | 15 | 8 | 5 | **92** | EXCELLENT |

---

## Critical Issues Found

### 1. Cyrillic Character Bug (v6)

v6 contains Russian/Cyrillic characters:
```
preden ljudje приходят v službo  ← Russian "приходят"
```

This is a severe Groq/model bug. Output is **UNACCEPTABLE** despite scoring 85.

### 2. Over-compression (36% of runs)

| Run | Ratio | Impact |
|-----|-------|--------|
| v5 | 57.0% | 8 content failures |
| v9 | 59.3% | 4 content failures |
| v11 | 61.5% | 3 content failures |
| v13 | 55.4% | 8 content failures |

### 3. Consistent Failures (100% of runs)

- **G13:** "nazdolj" not fixed to "navzdol"
- **G21:** "obhodnikov" not fixed to "hodnikov"
- **C23:** Flat areas + corridors detail always missing

### 4. Hallucination (93% of runs)

- **H1:** "smo prišli" / "Skupaj pridemo" - implies walking together
- Original says he MET her, not walked with her

---

## Prompt Text (dream_v13)

```
Clean this Slovenian dream transcription for a personal journal. The input was captured with speech-to-text (STT) software.

CRITICAL - DO NOT LOSE CONTENT:
⚠️ Cleaned text MUST be at least 75% of the original length.
⚠️ KEEP EVERY detail: actions, objects, people, numbers, locations, feelings.
⚠️ KEEP ALL unusual/strange details exactly as stated - these are the most important in dreams.
⚠️ DO NOT change who performs an action (if "I" do something, don't change it to "they did").
⚠️ DO write in present tense, first person singular ("jaz") and keep the personal, spoken narrative style.

FIX:
- Grammar, spelling, punctuation (use "knjižna slovenščina")
- STT mishearings: p↔b (polnica→bolnica), e↔i (predem→pridem), missing syllables
- Garbled phrases: reconstruct meaning from context

REMOVE:
- Filler words (not exhaustive list): "v bistvu", "torej", "a ne", "no"
- STT noise: "Hvala", "Hvala za pozornost", recording intros/outros
- False starts and word repetitions that do not make sense
- Do NOT remove content that carries meaning, even if informal.

FORMAT:
- Present tense, first person ("jaz")
- Paragraphs separated by "<break>" (NOT \n)
- New paragraph at: scene changes, location changes, new events

OUTPUT FORMAT:
Respond ONLY with the cleaned text.

TRANSCRIPTION:
"{transcription_text}"
```

---

## Recommendations

### Not Production Ready

With 36% failure rate (over-compression + Cyrillic bug), dream_v13 is **NOT suitable for production**.

### Potential Mitigations

1. **Retry Logic:** Run 2-3 times, select best by length ratio
2. **Cyrillic Detection:** Reject outputs containing Cyrillic characters
3. **Length Validation:** Reject outputs below 70% ratio
4. **Prompt Fixes:**
   - Add "nazdolj→navzdol" to STT mishearings
   - Add "obhodnikov→hodnikov" to STT mishearings
   - Add instruction about preserving individual encounters

---

## Model Files

- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md) - Full 14-run analysis
