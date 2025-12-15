# Dream Transcription Testing

This directory contains a testing framework for comparing transcription providers (Groq vs AssemblyAI) on Slovenian dream recordings.

**Read `README.md` first for setup and usage instructions.**

## Overview

- `switch_provider.py` - Switches transcription provider (kills app, updates .env, restarts)
- `run_transcriptions.py` - Triggers transcription on existing entries via API
- `score.py` - Automated comparison (text length, word count, diacritics)

## How Claude Can Help

After running transcriptions and `score.py compare`, Claude can provide **qualitative analysis**.

Read transcriptions from cache (results only contains metrics):
- Groq: `cache/{audio_id}/groq/temp_*.json` → field `transcribed_text`
- AssemblyAI: `cache/{audio_id}/assemblyai/result.json` → field `transcribed_text`

## Important Notes

- **Time doesn't matter** - As long as transcription completes in reasonable time (<= 1 min per hour of audio for third-party providers), speed is not a scoring factor
- Focus on **quality**, not performance

## Scoring System /100 (LLM Cleanup Suitability)

**Goal:** Score transcriptions for how well an LLM can clean them up, NOT raw transcription perfection.

| Criterion | Points | What it measures |
|-----------|--------|------------------|
| Hallucinations | /30 | -3 per "Hvala", -5 per inserted phrase |
| Semantic recoverability | /30 | -5 per unrecoverable, -3 per borderline |
| Vocabulary accuracy | /20 | -3 per wrong content word that misleads |
| Punctuation | /20 | Good=20, Fair=10, Poor=0 |

### Priority Order (most to least important)

1. **HALLUCINATIONS** - Inserted words that weren't spoken
   - "Hvala" at segment boundaries is common and severe
   - Inserted phrases can mislead LLM cleanup

2. **SEMANTIC RECOVERABILITY** - Can an LLM reconstruct meaning?
   - A phrase is "unrecoverable" if the original meaning cannot be guessed
   - Example: "bibre dko" → "bile tako" (unrecoverable without context)

3. **VOCABULARY ACCURACY** - Are content words correct?
   - Wrong words that could mislead the LLM
   - Example: "Marlo" instead of "malo" (looks like proper noun)

4. **PUNCTUATION** - LOW priority
   - LLMs handle missing punctuation well
   - Commas provide clause structure = "Fair" (10)
   - No structure at all = "Poor" (0)

### DO NOT penalize for:
- Simple phonetic variations (š↔s, g↔gi, r↔l)
- Missing punctuation (if commas exist)
- Dialect variations
- Spacing issues easily fixed ("spetnova" → "spet nova")

### DO penalize heavily for:
- Phrases where meaning is completely lost
- Wrong words that could mislead the LLM
- Inserted content (hallucinations)
- "Hvala" artifacts

### What counts as an error?

**Spelling - Only count if it MISLEADS:**
- ❌ "groskopom" → NOT an error (phonetic g/gi, LLM recovers)
- ❌ "konecu" → NOT an error (phonetic, trivially recoverable)
- ✓ "Marlo" → ERROR (looks like proper noun, should be "malo")

**Word integrity - Only count if UNRECOVERABLE:**
- ❌ "spetnova" → NOT an error (spacing issue, trivial)
- ❌ "straniker" → NOT an error (spacing, easily recoverable)
- ✓ "bibre dko" → ERROR (garbled, meaning unclear without context)

**Punctuation thresholds:**
- **Good (20):** Sentence breaks exist, readable structure
- **Fair (10):** Commas provide clause structure, no sentence breaks
- **Poor (0):** No structure at all, completely run-on

### Unrecoverable Phrase Test

Ask: **"If I showed ONLY this phrase to a native speaker (no surrounding context), could they guess the meaning?"**
- If no → Count as unrecoverable (-5)
- If no alone, but yes with surrounding context → Borderline (-3)
- If yes (even with effort) → Don't count

### 5 Worst Errors Test

For each transcription, identify the **5 worst errors** and assess:
1. Can an LLM recover the intended meaning?
2. Would this error mislead the LLM?
3. Is this a hallucination (inserted content)?

If most of the 5 worst errors are recoverable, the transcription is suitable for LLM cleanup.

## Scoring Template

When analyzing, provide a summary like:

```
## Transcription Quality Analysis (LLM Cleanup Suitability)

### Groq (temp=0.0)
| Criterion | Score | Notes |
|-----------|-------|-------|
| Hallucinations /30 | XX | X "Hvala" instances |
| Semantic recoverability /30 | XX | X unrecoverable phrases |
| Vocabulary accuracy /20 | XX | X misleading words |
| Punctuation /20 | XX | Good/Fair/Poor |
| **Total** | **XX/100** | |

### 5 Worst Errors
1. "error phrase" → should be "correct" - Recoverable? Yes/No
2. ...

### AssemblyAI
| Criterion | Score | Notes |
|-----------|-------|-------|
| ... | ... | ... |

### Recommendation
[Which provider is better for LLM cleanup and why]
```

## IMPORTANT: Provide Specific Examples

**Always include concrete examples from the transcription for each error found.**

Example output format:

```
### Errors Found

#### Groq
- **Hallucinations:** "Hvala" appears 5 times at random positions (not spoken)
- **Merged words:**
  - "jebil" → should be "je bil"
  - "nanek" → should be "na nek"
- **Split words:**
  - "stop nice" → should be "stopnice"
- **Missing diacritics:**
  - "cas" → should be "čas"
  - "ze" → should be "že"

#### AssemblyAI
- **Hallucinations:** None detected
- **Merged words:**
  - "vbistvu" → should be "v bistvu"
- ...
```

This helps identify patterns and compare providers objectively.

## Typical Workflow

```bash
# 1. Run transcriptions
python switch_provider.py groq
python run_transcriptions.py <entry_id> --provider groq

python switch_provider.py assemblyai
python run_transcriptions.py <entry_id> --provider assemblyai

# 2. Generate automated comparison
python score.py <audio_id> compare

# 3. Ask Claude to analyze results
# "Read cache/<audio_id>/groq/temp_0.0.json and cache/<audio_id>/assemblyai/result.json, then score both transcriptions"
```

## Cache Structure

Never overwrites - auto-creates versions (v2, v3, ...) if base file exists.

```
cache/{audio_id}/
├── groq/
│   ├── temp_0.0.json        # First run
│   ├── temp_0.0_v2.json     # Second run
│   ├── temp_0.0_v3.json     # Third run
│   └── temp_0.5.json
└── assemblyai/
    ├── result.json          # First run
    └── result_v2.json       # Second run
```

## Results Structure

```
results/{audio_id}/
├── README.md                      # Comparison across all providers/temps
├── analysis_assemblyai.md         # AssemblyAI detailed analysis
├── analysis_groq_temp_0.0.md      # Groq temp=0.0 detailed analysis
└── analysis_groq_temp_0.05.md     # Groq temp=0.05 detailed analysis
```

**File naming:** `analysis_<provider>[_temp_<temperature>].md`
- Temperature suffix only for Groq (AssemblyAI doesn't support it)

## Result File Templates

### README.md Template (Comparison)

```markdown
# Transcription Test: {audio_id}

**Entry:** {entry_id}
**Total runs:** {count}

## Results

| Provider | Score | Hvala | Notes |
|----------|-------|-------|-------|
| **AssemblyAI** | **XX/100** | 0 | ... |
| Groq T=0.0 | XX/100 | X-X | ... |

**Winner: {provider}** (+X points)

## Key Findings

- **AssemblyAI:** ...
- **Groq:** ...

## Files

- [analysis_assemblyai.md](./analysis_assemblyai.md)
- [analysis_groq_temp_0.0.md](./analysis_groq_temp_0.0.md)
- Full text: `cache/{audio_id}/` (gitignored)
```

### analysis_*.md Template (Provider Details)

```markdown
# Analysis: {Provider} [temp={X}]

## {Provider} [temp={X}] ({N} runs)

### Variance
| Run | Chars | Hvala |
|-----|-------|-------|
| v1 | XXXX | X |
| v2 | XXXX | X |

{Deterministic or not}

### Score: XX/100 (LLM Cleanup Suitability)

| Criterion | Score | Details |
|-----------|-------|---------|
| Hallucinations /30 | XX | X "Hvala", X inserted phrases |
| Semantic recoverability /30 | XX | X unrecoverable phrases |
| Vocabulary accuracy /20 | XX | X misleading words |
| Punctuation /20 | XX | Good/Fair/Poor |

### 5 Worst Errors
1. "error" → "correct" - Recoverable? Yes/No
2. ...

### Notes
- Key strengths/weaknesses for LLM cleanup
```
