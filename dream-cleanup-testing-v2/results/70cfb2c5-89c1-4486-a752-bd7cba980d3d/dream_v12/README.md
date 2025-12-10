# dream_v12 Results

← [Back to Index](../README.md)

---

**Prompt:** dream_v12 (Added >=75% length requirement)
**Test Date:** 2025-12-10
**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Raw Length:** 5,013 characters

---

## Best Results Summary

| Model | Best Config | Score | Status | Key Finding |
|-------|-------------|-------|--------|-------------|
| **[maverick-17b](./meta-llama-llama-4-maverick-17b-128e-instruct.md)** | T1_v1 | **85/100** | PASS | Length constraint worked (82%), but switched to past tense |

---

## Variance Testing Results

**Key finding:** Even with temperature=0.0, model produces significant variance in output length and quality.

| Run | Length | Score | Status |
|-----|--------|-------|--------|
| T1_v1 | 82.4% | **85** | PASS |
| T1_v2 | 74.9% | **82** | PASS |
| T1_v3 | 77.1% | **83** | PASS |
| T1_v4 | 82.3% | **83** | PASS |

| Metric | Min | Max | Range |
|--------|-----|-----|-------|
| Length | 74.9% | 82.4% | 7.5% |
| Score | 82 | 85 | 3 pts |

---

## Key Changes from v11

- Added explicit length requirement: `⚠️ Cleaned text MUST be at least 75% of the original length.`
- Simplified structure with CRITICAL section at top
- More concise formatting

---

## Prompt Text (dream_v12)

```
Clean this Slovenian dream transcription for a personal journal. The input was captured with speech-to-text (STT) software.

CRITICAL - DO NOT LOSE CONTENT:
⚠️ Cleaned text MUST be at least 75% of the original length.
⚠️ KEEP EVERY detail: actions, objects, people, numbers, locations, feelings.
⚠️ KEEP ALL unusual/strange details exactly as stated - these are the most important in dreams.
⚠️ DO NOT change who performs an action (if "I" do something, don't change it to "they did").

FIX:
- Grammar, spelling, punctuation (use "knjižna slovenščina")
- STT mishearings: p↔b (polnica→bolnica), e↔i (predem→pridem), missing syllables
- Garbled phrases: reconstruct meaning from context

REMOVE ONLY:
- Filler words: "v bistvu", "torej", "a ne", "no"
- STT noise: "Hvala", "Hvala za pozornost", recording intros/outros
- False starts and word repetitions

FORMAT:
- Present tense, first person ("jaz")
- Short paragraphs separated by "<break>" (NOT \n)
- New paragraph at: scene changes, location changes, new events

TRANSCRIPTION:
"{transcription_text}"
```

---

## Key Findings

### What Worked
- **Length constraint effective:** 74.9%-82.4% vs 58% in v11
- **More content preserved:** 40-43/44 vs 40/44 checkpoints passed
- **C10, C26 now consistently preserved** (were missing in v11)

### New Issues
- **Voice penalty:** Model consistently switched to past tense (-7 points in all runs)
- **Header artifact:** "Here is the cleaned Slovenian dream transcription:"
- **Variance:** 7.5% length range even at temp=0.0
- **Variable content:** C30, C34 preserved in v1 but lost in v2-v4

---

## Comparison: v11 vs v12

| Metric | v11 | v12 (best) | v12 (avg) | Notes |
|--------|-----|------------|-----------|-------|
| **Total** | 86 | 85 | 83 | Voice penalty hurts |
| Content | 41 | 37 | 35 | -7 voice penalty |
| Grammar | 23 | 22 | 22 | 3 failures |
| Length | 1 | 5 | 5 | **+4** (58% → 75-82%) |
| C_passed | 40/44 | 43/44 | 41/44 | Variable |

---

## Scoring Comparison (All Runs)

| Model | Run | Length | G | C | R | H | L | Total | Status |
|-------|-----|--------|---|---|---|---|---|-------|--------|
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T1_v1 | 82.4% | 22 | 37 | 15 | 6 | 5 | **85** | PASS |
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T1_v2 | 74.9% | 22 | 34 | 11 | 10 | 5 | **82** | PASS |
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T1_v3 | 77.1% | 22 | 35 | 11 | 10 | 5 | **83** | PASS |
| [maverick](./meta-llama-llama-4-maverick-17b-128e-instruct.md) | T1_v4 | 82.3% | 22 | 35 | 11 | 10 | 5 | **83** | PASS |

---

## Recommendations

1. **Fix voice/tense:** Add stronger instruction for present tense - model consistently defaults to past
2. **Remove meta-comments:** Add instruction to not include headers
3. **Accept variance:** With temp=0.0 still producing variance, consider running multiple attempts
4. **Test other configs:** T2-T3 might produce more consistent present tense

---

## Model Files

- [meta-llama-llama-4-maverick-17b-128e-instruct.md](./meta-llama-llama-4-maverick-17b-128e-instruct.md) - Detailed scoring for all T1 runs
