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

**Raw Transcription Location:** `cache/fetched_data.json`
- Contains the raw Whisper transcription text and prompt used for this test
- **CRITICAL:** Always score cleanup results by comparing against THIS raw transcription
- The reference example (`reference/reference-cleanup-example.md`) is for understanding what good cleanup quality looks like, but do NOT make hard comparisons against it

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

#### 1. Content Accuracy (0-10)
**What it measures:** Whether the dream's actual content is preserved correctly

**Check for:**
- ✅ Subject preserved (1st person "jaz" throughout)
- ✅ Timeline preserved (temporal markers: "preden", "ko", "potem")
- ✅ Details intact (specific terms, objects, people, places)
- ✅ No hallucinations (nothing added that wasn't in original)
- ✅ No over-summarization (all scenes/events present)

**NOT content accuracy:**
- ❌ Grammar errors in transcription (e.g., "polnica" vs "bolnica")
- ❌ Misspellings from STT (e.g., "ronotežje" vs "ravnotežje")
- ❌ Artifacts like "Hvala" (these are Artifact Removal)

**Examples:**
- **10/10:** All details preserved, no hallucinations, proper length (70-95%)
- **9/10:** All details preserved, minor detail lost
- **7/10:** One red flag (e.g., hallucination) = base 9 minus 2
- **5/10:** Multiple red flags (hallucination + subject change) = base 9 minus 4
- **3/10:** Severe content loss or multiple hallucinations

#### 2. Artifact Removal (0-10)
**What it measures:** STT-specific artifacts that shouldn't exist in final text

**Artifacts (must be removed):**
- "Hvala" (repeated throughout transcription)
- "Zdravstveno, da ste pripravljeni" (YouTube intro - BONUS if removed, not penalized if kept)
- Excessive filler: repetitive "torej", "v bistvu", "a ne", etc.

**NOT artifacts:**
- ❌ Grammar errors: "polnica", "ronotežje", "prublev" (these are Grammar Quality)
- ❌ Garbled phrases: "ta ljena vzgor" (Grammar Quality)
- ❌ Wrong words: "pretličju" vs "pritličju" (Grammar Quality)

**Examples:**
- **10/10:** All "Hvala" removed, "Zdravstveno" removed, minimal filler
- **9/10:** All "Hvala" removed, "Zdravstveno" kept (acceptable)
- **7/10:** One "Hvala" remains
- **2/10:** Multiple "Hvala" remain throughout (e.g., T3 duplication case)

**IMPORTANT:** Do NOT deduct artifact points for unfixed grammar errors! Those go in Grammar Quality.

#### 3. Grammar Quality (0-10)
**What it measures:** Correct Slovenian grammar, spelling, and word choice

**Check for:**
- ✅ Correct spelling: "bolnica" not "polnica", "ravnotežje" not "ronotežje"
- ✅ Correct verb forms: "rekel" (masculine) not "rekla" (feminine) if subject is male
- ✅ Correct case/number agreement
- ✅ Clean phrases: "nadaljujem hojo" not "nadelujem hojo"
- ✅ No garbled phrases: remove "ta ljena vzgor", "prublev čimprej"
- ✅ No English words
- ✅ Proper sentence structure

**Examples:**
- **10/10:** Perfect grammar, all transcription errors fixed
- **9/10:** One minor error (e.g., "polnica" not fixed)
- **7/10:** Several errors ("polnica" + "ronotežje" + garbled phrases)
- **6/10:** Multiple errors across different categories
- **3/10:** Many errors, barely readable

#### 4. Readability (0-10)
**What it measures:** Natural flow, paragraphing, and authentic voice

**Check for:**
- ✅ Appropriate paragraph breaks (scene changes, new topics)
- ✅ Natural sentence flow
- ✅ Authentic personal voice preserved
- ✅ Not overly formal or robotic
- ✅ Coherent narrative structure

**Deduct points for:**
- ❌ Wall of text (missing paragraph breaks)
- ❌ Choppy or disjointed flow
- ❌ Overly formal/academic tone
- ❌ Lost personal voice

**Examples:**
- **10/10:** Perfect paragraph structure, natural flow, authentic voice
- **9/10:** Good structure, very minor flow issues
- **7/10:** Some paragraph issues or slightly stiff tone
- **5/10:** Poor paragraphing (e.g., P3 wall of text)
- **3/10:** Nearly unreadable due to structure issues

---

### Red Flags (Automatic -2 points EACH, applied to relevant criterion)

**How to apply:**
1. Start with base score for criterion (usually 9-10)
2. Apply -2 for EACH red flag in that category
3. Red flags affect specific criteria, not total score directly

**Red Flags List:**

| Red Flag | Affects Criterion | Example | Penalty |
|----------|------------------|---------|---------|
| Subject changed (jaz → oni/ženske) | Content Accuracy | "Oni so hodili..." instead of "Jaz sem hodil..." | -2 |
| Timing changed (preden → ko) | Content Accuracy | Changed "preden so prišli" to "ko so prišli" | -2 |
| Specific terms altered | Content Accuracy | "centrifugacijska sila" instead of "centrifugacija krvi" | -2 |
| Content hallucinated/added | Content Accuracy | Added ending not in original (P4, P6) | -2 |
| Content duplicated | Content Accuracy | Repeated dream 4x (T3) | -2 |
| English words present | Grammar Quality | "and", "the", "building" in Slovenian text | -2 |
| "Hvala" artifacts remaining | Artifact Removal | "Hvala" appears in cleaned text | -2 each |

**Example Scoring with Red Flags:**

**P4 (hallucinated ending):**
- Base Content Accuracy: 9/10 (details preserved)
- Red flag (hallucination): -2
- **Final Content Accuracy: 7/10**

**P6 (hallucination + gender error):**
- Base Content Accuracy: 9/10
- Red flag (hallucination): -2
- **Final Content Accuracy: 7/10**
- Base Grammar Quality: 9/10
- Red flag (gender error): -2
- **Final Grammar Quality: 7/10**

**Consistent Penalty:** Each red flag = exactly -2 points, no more, no less.

### Green Flags (Confirm these are present)
- First person preserved throughout
- Timeline matches original
- Specific details intact
- Clean paragraph breaks at scene changes
- No artifacts
- Natural Slovenian

---

## Automated Checks (Before Scoring)

Run these checks BEFORE assigning scores to catch obvious issues:

### 1. Artifact Search
**Command:** Search cleaned text for "Hvala"

**Result:**
- ✅ None found → Artifact Removal likely 9-10/10
- ⚠️ 1-2 found → Artifact Removal 7-8/10, apply red flag (-2 each)
- ❌ Multiple found → Artifact Removal 2-5/10, severe issue

**Note:** "Zdravstveno" in transcription - removing is BONUS, keeping is acceptable (no penalty)

### 2. English Detection
**Command:** Search for common English words (and, the, but, with, for, building, etc.)

**Result:**
- ✅ None found → Grammar Quality likely high
- ❌ Any found → Grammar Quality red flag (-2 per occurrence)

### 3. Length Ratio Check
**Formula:** `cleaned_length / raw_length = ratio%`

**Expected:** 70-95% (cleanup should be 3500-4800 chars for 5051 raw)

**Result:**
- ✅ 70-95% → Appropriate cleanup
- ⚠️ 95-110% → Possible duplication (check for repeated content)
- ⚠️ 50-70% → Possible over-summarization (check for lost details)
- ❌ >110% → Severe duplication (e.g., T3 at 143%)
- ❌ <50% → Severe content loss (e.g., T6 at 52%)

**Impact on scoring:**
- Too long (>110%) → Content Accuracy -3 to -5 (duplication)
- Too short (<70%) → Content Accuracy -2 to -4 (summarization)

### 4. Person Consistency
**Command:** Check for first-person markers (jaz, sem) vs third-person (oni, ona)

**Result:**
- ✅ Consistent 1st person → No issues
- ❌ Shifted to 3rd person → Content Accuracy red flag (-2)

### 5. Timeline Markers Check
**Command:** Verify temporal sequence preserved

**Look for:**
- "preden" (before) should not become "ko" (when) or "potem" (after)
- Event order should match original

**Result:**
- ✅ Timeline preserved → No issues
- ❌ Timeline changed → Content Accuracy red flag (-2)

---

## Scoring Workflow (Step-by-Step)

1. **Run Automated Checks** (above) - note any red flags
2. **Read cleaned text** vs raw transcription side-by-side
3. **Score each criterion** (0-10) using guidelines above
4. **Apply red flag penalties** (-2 each) to relevant criterion
5. **Calculate total** (sum of 4 criteria, max 40)
6. **Document issues** in notes section

**Example:**

```
Automated Checks:
- ✅ No "Hvala" found
- ✅ No English words
- ⚠️ Length: 52% (too short!)
- ✅ First person preserved
- ✅ Timeline preserved

Scoring:
- Content Accuracy: 9/10 base, -3 for over-summarization = 6/10
- Artifact Removal: 10/10 (all artifacts removed)
- Grammar Quality: 9/10 ("polnica" not fixed) = 9/10
- Readability: 8/10 (good flow despite being short)
- TOTAL: 33/40 (82.5%)

Red Flags: Over-summarization (length 52%)
```

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

