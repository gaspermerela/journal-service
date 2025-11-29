# Dream Transcription Cleanup Optimization

## Overview
You are optimizing Slovenian dream transcription cleanup. You have database access to:
- Raw Whisper transcriptions
- Cleanup prompts (fetch active prompt dynamically)
- Previous cleanup attempts and scores

## Models to Test

### Tier 1 - Priority Testing
| Model | Why | Watch For |
|-------|-----|-----------|
| openai/gpt-oss-120b | Best grammar, largest | Content changes |
| moonshotai/kimi-k2-instruct | Strong multilingual, 262K context | Unknown Slovenian quality |
| qwen/qwen3-32b | 100+ languages | May be too creative |

### Tier 2 - Secondary Testing
| Model | Why | Watch For |
|-------|-----|-----------|
| openai/gpt-oss-20b | Cheaper, good balance | Slightly worse grammar |
| llama-3.3-70b-versatile | Large, general purpose | Less multilingual focus |
| meta-llama/llama-4-maverick-17b-128e-instruct | Newer architecture | Unknown quality |

### Skip These Models
- playai-tts, playai-tts-arabic (TTS only)
- allam-2-7b (Arabic focused)
- meta-llama/llama-guard-* (safety classification)
- meta-llama/llama-prompt-guard-* (prompt injection detection)
- openai/gpt-oss-safeguard-20b (content moderation)
- groq/compound, groq/compound-mini (tool-use systems)

---

## Parameter Test Grid

### Case 1: Temperature Only (top_p = null/unset)

| Config | Temperature | Expected Behavior |
|--------|-------------|-------------------|
| T1 | 0.0 | Most deterministic, may over-correct |
| T2 | 0.3 | Focused, conservative |
| T3 | 0.5 | Balanced |
| T4 | 0.8 | Slightly creative |
| T5 | 1.0 | Default |
| T6 | 1.5 | More random |
| T7 | 2.0 | Maximum randomness |

### Case 2: Top-p Only (temperature = null/unset)

| Config | Top-p | Expected Behavior |
|--------|-------|-------------------|
| P1 | 0.1 | Very narrow (top 10% tokens) |
| P2 | 0.3 | Narrow sampling |
| P3 | 0.5 | Moderate restriction |
| P4 | 0.7 | Slight restriction |
| P5 | 0.9 | Minimal restriction |
| P6 | 1.0 | Default (no restriction) |

### Case 3: Both Set (not recommended by Groq, but worth testing)

| Config | Temperature | Top-p | Expected Behavior |
|--------|-------------|-------|-------------------|
| B1 | 0.3 | 0.9 | Conservative + slight restriction |
| B2 | 0.5 | 0.5 | Balanced both |
| B3 | 0.5 | 0.9 | Balanced temp + minimal top-p |
| B4 | 0.8 | 0.5 | Creative temp + moderate top-p |

### Recommended Test Order

1. **First:** Test Case 1 (Temperature only) - find best temperature
2. **Second:** Test Case 2 (Top-p only) - find best top-p
3. **Third:** Test Case 3 (Both) - only if Cases 1 & 2 don't reach target score
4. **Compare:** Best from each case against each other

---

## Testing Workflow

### Phase 1: Parameter Optimization

1. Fetch latest raw transcription from DB
2. Fetch current active cleanup prompt from DB
3. **Case 1 - Temperature Only (top_p = null):**
   - Run cleanup with configs T1-T7
   - Score each result
   - Identify best temperature-only config
4. **Case 2 - Top-p Only (temperature = null):**
   - Run cleanup with configs P1-P6
   - Score each result
   - Identify best top-p-only config
5. **Compare:** Best from Case 1 vs Best from Case 2
6. **Case 3 - Both (only if needed):**
   - If neither Case 1 nor Case 2 reaches target score (≥36/40)
   - Run cleanup with configs B1-B4
   - Score each result
7. **Final comparison:** Best from all cases
8. Record all results to results file

### Phase 2: Prompt Optimization
1. After finding best parameters, analyze common issues
2. Suggest prompt modifications to address issues
3. **WAIT FOR USER CONFIRMATION** before inserting new prompt
4. Mark old prompt as inactive, insert new prompt as active
5. Re-test with new prompt using best parameters
6. Iterate until stopping criteria met

### Phase 3: Model Comparison (Optional)
1. Using best prompt + parameters, test across Tier 1 models
2. Compare scores
3. Recommend best model for production use

---

## Evaluation Criteria

### Scoring (0-10 each, 40 total)
| Criterion | What to Check |
|-----------|---------------|
| **Content Accuracy** | Subject preserved, timing preserved, details intact |
| **Artifact Removal** | No "Hvala", no YouTube intro, no filler |
| **Grammar Quality** | Correct Slovenian, no English, coherent sentences |
| **Readability** | Natural flow, appropriate paragraphs, authentic voice |

### Red Flags (Automatic -2 points per flag)
- Subject changed (jaz → oni/ženske)
- Timing changed (preden → ko/potem)
- Specific terms altered (centrifugacija krvi → centrifugacijska sila)
- English words present
- Content duplicated
- Content hallucinated/added
- Artifacts remaining

### Green Flags (Confirm these are present)
- First person preserved throughout
- Timeline matches original
- Specific details intact
- Clean paragraph breaks at scene changes
- No artifacts
- Natural Slovenian

---

## Automated Checks (Before Scoring)

Verify these before assigning scores:

1. **Artifact Search:** Does cleanup contain "Hvala" or "Zdravstveno"?
2. **English Detection:** Any English words (and, the, but, with, for)?
3. **Length Ratio:** Is cleanup 70-95% of original length?
4. **Person Consistency:** Is first-person (jaz/sem) preserved?

---

## Stopping Criteria

### Stop Parameter Testing When:
- Total score ≥ 36/40 (90%)
- OR Content Accuracy = 10 AND Artifact Removal ≥ 9
- OR 3 consecutive tests show no improvement

### Stop Prompt Iteration When:
- Total score ≥ 38/40 (95%)
- AND no red flags present
- OR user confirms quality is acceptable

---

## Output Requirements

For each transcription/prompt, create/update a results file using the template: `dream-cleanup-testing/templates/RESULT_TEMPLATE.md`.

### File Naming
`results/cleanup_[transcription_id]_[date].md`

### Content Requirements
- Include raw transcription
- Include each cleanup attempt with full metadata
- Include scores and issues for each attempt
- Summarize best result at top
- Record prompt text used (fetched from DB)

---

## Reference examples
You can find reference examples in directory `dream-cleanup-testing/reference`. You MUST check all of them.

---

## Database Operations
This section serves as a knowledge base of the correct way to fetch data from the DB and insert new prompts! 

**IMPORTANT:** You MUST change/update this section with all necessary instructions for minimal friction with DB commands in the future. 

