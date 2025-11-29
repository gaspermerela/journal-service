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

### Target Transcription
**Transcription ID:** `5beeaea1-967a-4569-9c84-eccad8797b95`

All testing will be performed on this specific transcription for consistency.

### Phase 1: Parameter Optimization

**IMPORTANT - Optimization Strategies:**

1. **Token Optimization (Concurrent Processing):**
   - Execute ALL cleanups for a case, THEN analyze all results in ONE response
   - This saves 60-75% of Claude Code analysis tokens by sharing context once
   - Groq API costs remain the same (same number of cleanup calls)

2. **Caching Strategy (Resume Capability):**
   - **Cache every cleanup result immediately** after receiving from Groq API
   - Store as JSON files: `cache/{transcription_id}/{config_name}.json`
   - If Claude Code session ends, **resume from cached results**
   - Skip already-completed cleanups when resuming
   - **Protects expensive Groq API calls** from being lost
   - Cache file structure:
     ```json
     {
       "config": "T1",
       "model": "llama-3.3-70b-versatile",
       "temperature": 0.0,
       "top_p": null,
       "timestamp": "2025-11-29T10:30:00Z",
       "prompt_id": 123,
       "cleaned_text": "...",
       "raw_response": "...",
       "transcription_id": "5beeaea1-967a-4569-9c84-eccad8797b95"
     }
     ```

**Workflow:**

1. **Setup:**
   - Fetch transcription `5beeaea1-967a-4569-9c84-eccad8797b95` from DB
   - Fetch current active cleanup prompt from DB
   - Create directories:
     - `dream-cleanup-testing/cache/5beeaea1-967a-4569-9c84-eccad8797b95/`
     - `dream-cleanup-testing/results/`
   - Check for existing cached results (resume if found)

2. **Case 1 - Temperature Only (top_p = null):**
   - **Execute:** Run cleanups T1-T7 (cache each immediately)
   - **Check cache:** Skip configs that already have cached results
   - **Collect:** Load all 7 results (from cache or fresh API calls)
   - **Analyze:** Score all 7 results in ONE comprehensive response
   - **Compare:** Identify best temperature-only config
   - **Record:** Update results file with all 7 attempts

3. **Case 2 - Top-p Only (temperature = null):**
   - **Execute:** Run cleanups P1-P6 (cache each immediately)
   - **Check cache:** Skip configs that already have cached results
   - **Collect:** Load all 6 results (from cache or fresh API calls)
   - **Analyze:** Score all 6 results in ONE comprehensive response
   - **Compare:** Identify best top-p-only config
   - **Record:** Update results file with all 6 attempts

4. **Compare Best Results:**
   - Compare best from Case 1 vs best from Case 2
   - Determine if stopping criteria met (≥36/40)

5. **Case 3 - Both (only if needed):**
   - If neither Case 1 nor Case 2 reaches target score (≥36/40)
   - **Execute:** Run cleanups B1-B4 (cache each immediately)
   - **Check cache:** Skip configs that already have cached results
   - **Collect:** Load all 4 results (from cache or fresh API calls)
   - **Analyze:** Score all 4 results in ONE comprehensive response
   - **Record:** Update results file with all 4 attempts

6. **Final Analysis:**
   - Identify overall best configuration
   - Summarize findings at top of results file
   - Prepare recommendations for Phase 2 (if needed)

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
- "Hvala" artifacts remaining (Note: "Zdravstveno" is not penalized if in original transcription)

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

1. **Artifact Search:** Does cleanup contain "Hvala"? (Note: "Zdravstveno" may appear in transcription itself - removing it is a bonus but keeping it is not penalized)
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

### Database Setup

```python
from app.database import get_session
from sqlalchemy import select
from app.models.transcription import Transcription
from app.models.prompt_template import PromptTemplate

# Use get_session() context manager for async operations
async with get_session() as db:
    # Your database operations here
    await db.commit()  # Don't forget to commit!
```

### Fetching Latest Raw Transcription

```python
async with get_session() as db:
    # Get the most recent completed transcription
    stmt = (
        select(Transcription)
        .where(Transcription.status == "completed")
        .order_by(Transcription.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    latest_transcription = result.scalar_one_or_none()

    if latest_transcription:
        transcription_id = latest_transcription.id
        transcribed_text = latest_transcription.transcribed_text
        model_used = latest_transcription.model_used
```

### Fetching Active Cleanup Prompt

```python
async with get_session() as db:
    # Get active prompt template for a specific entry_type (e.g., "dream")
    entry_type = "dream"

    stmt = (
        select(PromptTemplate)
        .where(
            PromptTemplate.entry_type == entry_type,
            PromptTemplate.is_active == True
        )
        .order_by(PromptTemplate.updated_at.desc())
    )
    result = await db.execute(stmt)
    active_prompt = result.scalars().first()

    if active_prompt:
        prompt_text = active_prompt.prompt_text
        prompt_id = active_prompt.id
        prompt_version = active_prompt.version
        prompt_name = active_prompt.name
```

### Creating a New Prompt Template

**CRITICAL:** Always wait for user confirmation before inserting a new prompt!

```python
from app.models.prompt_template import PromptTemplate
from datetime import datetime

async with get_session() as db:
    # First, deactivate all existing prompts for this entry_type
    entry_type = "dream"
    stmt = (
        select(PromptTemplate)
        .where(
            PromptTemplate.entry_type == entry_type,
            PromptTemplate.is_active == True
        )
    )
    result = await db.execute(stmt)
    old_prompts = result.scalars().all()

    for old_prompt in old_prompts:
        old_prompt.is_active = False
        old_prompt.updated_at = datetime.utcnow()

    # Determine next version number
    stmt = (
        select(PromptTemplate)
        .where(PromptTemplate.entry_type == entry_type)
        .order_by(PromptTemplate.version.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    latest_prompt = result.scalar_one_or_none()
    next_version = (latest_prompt.version + 1) if latest_prompt else 1

    # Create new prompt template
    new_prompt = PromptTemplate(
        name=f"Dream Cleanup v{next_version}",
        entry_type=entry_type,
        prompt_text="Your prompt text here with {transcription_text} placeholder",
        description="Description of changes in this version",
        is_active=True,
        version=next_version,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_prompt)
    await db.commit()
    await db.refresh(new_prompt)

    print(f"Created new prompt template: {new_prompt.name} (ID: {new_prompt.id})")
```

### Fetching Previous Cleanup Attempts

```python
from app.models.cleaned_entry import CleanedEntry

async with get_session() as db:
    # Get all cleanup attempts for a specific transcription
    transcription_id = "your-transcription-uuid"

    stmt = (
        select(CleanedEntry)
        .where(CleanedEntry.transcription_id == transcription_id)
        .order_by(CleanedEntry.created_at.desc())
    )
    result = await db.execute(stmt)
    cleanup_attempts = result.scalars().all()

    for attempt in cleanup_attempts:
        cleaned_text = attempt.cleaned_text
        model_name = attempt.model_name
        temperature = attempt.temperature
        top_p = attempt.top_p
        prompt_template_id = attempt.prompt_template_id
``` 

