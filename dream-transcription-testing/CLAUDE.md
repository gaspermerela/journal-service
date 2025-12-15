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

## Scoring System /100

Score only what's **objectively verifiable** without audio:

| Criterion | Points | Deduction |
|-----------|--------|-----------|
| STT artifacts | /30 | -1 per "Hvala" |
| Spelling errors | /25 | -3 per error |
| Word integrity | /25 | -2 per split/merge |
| Punctuation | /20 | Good=20, Fair=10, Poor=0 |

**NOT scoreable** (would need audio):
- Missing content
- Other hallucinations (can't prove they weren't said)
- Overall accuracy

## Scoring Criteria

When analyzing transcriptions, evaluate these specific categories:

### 1. Diacritics (č, š, ž)
- Are Slovenian diacritics used correctly?
- Missing diacritics: "c" instead of "č", "s" instead of "š", "z" instead of "ž"
- Incorrect diacritics in wrong places
- **Example error:** "cas" instead of "čas", "ze" instead of "že"

### 2. Grammar
- Correct Slovenian grammar and sentence structure
- Proper verb conjugations
- Correct noun cases

### 3. Punctuation
- Appropriate sentence boundaries
- Correct use of commas, periods, question marks
- Missing or excessive punctuation

### 4. Hallucinated Words
- Words inserted that weren't spoken
- **Common issue:** "Hvala" (Thank you) hallucinated at end of segments
- Random filler words added by the model

### 5. Merged Words
- Two words incorrectly joined together
- **Example:** "je bil" → "jebil"
- **Example:** "na nek" → "nanek"

### 6. Split Words
- Single word incorrectly split into multiple
- **Example:** "stopnice" → "stop nice"
- **Example:** "praktično" → "prakti čno"

### 7. Repeated Phrases
- Stuttering artifacts from audio repeated in text
- Same phrase transcribed multiple times
- Looping/stuck transcription segments

### 8. Missing Words
- Words clearly spoken but not transcribed
- Dropped syllables or word endings

## Scoring Template

When analyzing, provide a summary like:

```
## Transcription Quality Analysis

### Groq (temp=0.0)
| Criterion | Score | Notes |
|-----------|-------|-------|
| Diacritics | Good/Fair/Poor | specific issues... |
| Grammar | Good/Fair/Poor | ... |
| Punctuation | Good/Fair/Poor | ... |
| Hallucinations | None/Few/Many | ... |
| Merged words | None/Few/Many | ... |
| Split words | None/Few/Many | ... |
| Repeated phrases | None/Few/Many | ... |
| Missing words | None/Few/Many | ... |

### AssemblyAI
| Criterion | Score | Notes |
|-----------|-------|-------|
| ... | ... | ... |

### Recommendation
[Which provider performed better and why]
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

### Score: XX/100

| Criterion | Score | Details |
|-----------|-------|---------|
| STT artifacts /30 | XX | ... |
| Spelling /25 | XX | ... |
| Word integrity /25 | XX | ... |
| Punctuation /20 | XX | ... |

### Errors
- **{Error type}:**
  - "error" → "correct"
```
