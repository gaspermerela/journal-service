# Dream Cleanup Testing

## Purpose
The purpose of this "subproject" is to document and implement 
a **deterministic** and **automatic** way to test the success of different prompts 
and parameters (`temperature`, `p_top`) for transcription cleanup using LLMs. 
I use `claude-code` to execute batch cleanups with different parameters for specific 
transcription and evaluate their success based on pre-determined scoring criteria (see [CLAUDE_CODE_INSTRUCTIONS.md](CLAUDE_CODE_INSTRUCTIONS.md)). 

With this approach I hope to understand how different prompts and parameters behave in regards to cleanup quality and hopefully get the optimal configuration for production.

**NOTE:** Keep in mind that raw transcription and cleanup data is not persisted in git versioning.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Workflow](#core-workflow)
- [Test Target](#test-target)
- [Scoring](#scoring-0-40-total)
- [Scripts](#scripts)
- [Cache Strategy](#cache-strategy)
- [Re-running Configs](#re-running-configs)
- [Results](#results)
- [Current Status](#current-status-see-planmd)
- [Environment Setup](#environment-setup)
- [Key Files](#key-files)

## Quick Start

```bash
# 1. Fetch transcription + prompt from database
python fetch_data.py

# 2. Run parameter tests (saves to DB + cache)
python run_cleanups_api.py

# 3. Score results manually using criteria in CLAUDE_CODE_INSTRUCTIONS.md
# Results saved to: results/cleanup_{transcription_id}_{date}.md
```

## Core Workflow

**Phase 1: Parameter Optimization**
1. Test temperature-only configs (T1-T7)
2. Test top-p-only configs (P1-P6)
3. Compare winners, identify best parameters

**Phase 2: Prompt Optimization**
1. Analyze issues from best parameters
2. Modify prompt, test improvements
3. Iterate until target score reached

**Phase 3: Model Comparison** (optional)
1. Test different models with best params/prompt
2. Select production configuration

## Test Target

**Transcription ID:** `5beeaea1-967a-4569-9c84-eccad8797b95`

All tests use this single transcription for consistency. Raw text cached in `cache/fetched_data.json`.

## Scoring (0-40 total)

- **Content Accuracy** (0-10): Dream details preserved, no hallucinations
- **Artifact Removal** (0-10): "Hvala", fillers, intro removed
- **Grammar Quality** (0-10): Correct Slovenian spelling/grammar
- **Readability** (0-10): Natural flow, paragraphing, authentic voice

**Target:** ≥36/40 (90%) for parameters, ≥38/40 (95%) for final

**Red flags:** -2 points each (subject changes, hallucinations, English words, etc.)

Full criteria: `CLAUDE_CODE_INSTRUCTIONS.md`

## Scripts

| Script | Purpose | DB Persistence |
|--------|---------|----------------|
| `fetch_data.py` | Get transcription + prompt from DB | Read-only |
| `run_cleanups_api.py` | Run batch tests via backend API | ✅ Yes |
| `run_cleanups.py` | Run batch tests directly with Groq | ❌ No |
| `rerun_one_config.py` | Re-run or re-evaluate single config | ✅ Yes |

**Recommended:** Use `run_cleanups_api.py` for all testing (results visible in frontend).

## Cache Strategy

**Why cache?** Protects expensive Groq API calls from being lost if session ends.

**Structure:**
```
cache/
├── fetched_data.json              # Raw transcription + prompt
└── 5beeaea1-967a-4569-9c84.../
    ├── T1.json                    # First run
    ├── T3.json                    # Original T3 run
    ├── T3_v2.json                 # Re-run (preserves history)
    └── _summary.json              # Batch test metadata
```

**Versioning:** Re-running a config creates new version (T3_v2.json), never overwrites.

## Re-running Configs

```bash
# Re-execute T3 (fresh API call, creates T3_v2.json)
python rerun_one_config.py T3

# Re-evaluate T3 (load cached result, no API call)
python rerun_one_config.py T3 --evaluate

# List all versions
python rerun_one_config.py T3 --list-versions
```

**Use case:** T3 showed catastrophic duplication (temp=0.5 anomaly) - re-run to verify reproducibility.

## Results

**Location:** `results/cleanup_{transcription_id}_{date}.md`

**Format:** Uses template from `templates/RESULT_TEMPLATE.md`

**Contents:**
- Raw transcription
- Prompt version used
- Each cleanup attempt with scores, issues, cleaned text
- Best result summary at top

**Reference:** `reference/reference-cleanup-example.md` shows target quality level.

## Current Status (see PLAN.md)

✅ **Phase 1 Complete**
- Case 1 (Temperature): Winner = T1 (temp=0.0, 37/40)
- Case 2 (Top-p): Winner = P2 (top_p=0.3, 36/40)
- **Production config:** temp=0.0, top_p=null

🔒 **Phase 2 Pending:** Prompt optimization to reach ≥38/40

## Environment Setup

```bash
# Required in .env:
TEST_USER_EMAIL=your-email@example.com
TEST_USER_PASSWORD=your-password
GROQ_API_KEY=gsk_xxxxx
```

## Key Files

- **CLAUDE_CODE_INSTRUCTIONS.md** - Complete testing instructions + scoring criteria
- **PLAN.md** - Current status, results summary, next actions
- **templates/RESULT_TEMPLATE.md** - Results file format
- **reference/reference-cleanup-example.md** - Example of target quality
