# Dream Cleanup Testing v2

## Purpose

Deterministic testing framework for optimizing Slovenian dream transcription cleanup using LLMs. 

The process described below is meant to be done on a regular basis for different transcriptions to identify the strengths/weaknesses of different models, prompts and their configurations. 

**Key improvements in v2:**
- **Checklist-based scoring** - Per-transcription criteria files with specific checkpoints (G1-G28, C1-C44)
- **Faster iteration** - Score by checking boxes, not re-reading entire text
- **Cleaner cache structure** - `cache/{transcription_id}/{prompt_name}/{model_name}/`
- **Privacy-aware** - Criteria files contain dream content but are gitignored; results only reference checkpoint IDs

## Quick Start

```bash
# 1. Fetch transcription + prompt from database
cd dream-cleanup-testing-v2
set -a && source ../.env && set +a
python fetch_data.py

# 2. Run parameter tests (results saved to DB + cache)
python run_cleanups_api.py llama-3.3-70b-versatile --prompt dream_v8 --case 1

# 3. Score using checklist in criteria/{transcription_id}.md
# Results saved to: results/{transcription_id}/{prompt_name}/{model}.md
```

## Directory Structure

```
dream-cleanup-testing-v2/
├── cache/                          # Cached API results (gitignored)
│   └── {transcription_id}/
│       ├── fetched_data.json       # Raw transcription + prompt
│       └── {prompt_name}/
│           └── {model_name}/
│               ├── T1.json ... T7.json
│               ├── P1.json ... P6.json
│               └── _summary.json
│
├── criteria/                       # Scoring criteria (gitignored - contains dream content)
│   └── {transcription_id}.md       # G1-G28, C1-C44, A1-A3, R1-R4 checkpoints
│
├── results/                        # Scored results (committed - no dream content)
│   └── {transcription_id}/
│       ├── README.md               # Best result summary
│       └── {prompt_name}/
│           └── {model}.md          # Checklist scores per config
│
├── fetch_data.py                   # Fetch transcription from DB
├── run_cleanups_api.py             # Run batch tests via API
├── run_cleanups.py                 # Run batch tests via Groq (legacy)
├── rerun_one_config.py             # Re-run single config
└── CLAUDE_CODE_INSTRUCTIONS.md     # Full testing guide
```

## Scoring System

### Four Criteria (10 points each, 40 total)

| Criterion | Checkpoints | What it measures |
|-----------|-------------|------------------|
| **Grammar** | G1-G28, G+, G++ | Spelling fixes, garbled phrases, no English/Russian |
| **Content** | C1-C44, C+/++/+++ | Scene details preserved, narrative voice, no hallucinations |
| **Artifacts** | A1-A3 | "Hvala" removed, fillers reduced |
| **Readability** | R1-R4 | Paragraph breaks, flow, personal voice |

### How Scoring Works

1. **Before testing:** Create criteria file for the transcriptio with manual interventionn (one-time setup)
2. **After each cleanup:** Check boxes against criteria, count failures
3. **Record results:** `G: 8 | C: 9 | A: 10 | R: 9 | Total: 36/40 | Failed: G1, G5, C3`

## Scripts

| Script | Purpose | DB Persistence |
|--------|---------|----------------|
| `fetch_data.py` | Fetch transcription + prompt | Read-only |
| `run_cleanups_api.py` | Batch tests via backend API | Yes |
| `run_cleanups.py` | Batch tests via Groq directly | No |
| `rerun_one_config.py` | Re-run or re-evaluate single config | Yes |

### Usage Examples

```bash
# Run temperature tests (T1-T7)
python run_cleanups_api.py llama-3.3-70b-versatile --prompt dream_v8 --case 1

# Run top-p tests (P1-P6)
python run_cleanups_api.py llama-3.3-70b-versatile --prompt dream_v8 --case 2

# Re-run single config
python rerun_one_config.py T3 llama-3.3-70b-versatile --prompt dream_v8

# Re-evaluate without API call
python rerun_one_config.py T3 llama-3.3-70b-versatile --prompt dream_v8 --evaluate
```

## Test Configurations

### Case 1: Temperature Only (top_p = null)

| Config | Temperature | Expected |
|--------|-------------|----------|
| T1 | 0.0 | Most deterministic |
| T2 | 0.3 | Conservative |
| T3 | 0.5 | Balanced |
| T4 | 0.8 | Slightly creative |
| T5 | 1.0 | Default |
| T6 | 1.5 | More random |
| T7 | 2.0 | Maximum randomness |

### Case 2: Top-p Only (temperature = null)

| Config | Top-p | Expected |
|--------|-------|----------|
| P1 | 0.1 | Very narrow |
| P2 | 0.3 | Narrow |
| P3 | 0.5 | Moderate |
| P4 | 0.7 | Slight restriction |
| P5 | 0.9 | Minimal restriction |
| P6 | 1.0 | No restriction |

## Workflow

### Phase 1: Parameter Optimization
1. Test Case 1 (T1-T7) - find best temperature
2. Test Case 2 (P1-P6) - find best top-p
3. Compare winners
4. Optionally mix temperature with top-p parameters and re-evaluate

### Phase 2: Prompt Optimization
1. Analyze failures from best config
2. Modify prompt to fix issues
3. Re-test

### Phase 3: Model Comparison
1. Test different models with different prompt and params
2. Select production configuration

## Environment Setup

Required in `.env`:
```bash
TEST_USER_EMAIL=your-email@example.com
TEST_USER_PASSWORD=your-password
GROQ_API_KEY=gsk_xxxxx
```

## Key Files

| File | Purpose |
|------|---------|
| `CLAUDE_CODE_INSTRUCTIONS.md` | Complete testing guide |
| `criteria/{id}.md` | Per-transcription scoring checklist (gitignored) |
| `reference/reference-cleanup-example.md` | Example of target quality |
