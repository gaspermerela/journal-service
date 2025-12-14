# Dream Transcription Testing

Compare Groq vs AssemblyAI on Slovenian dream recordings.

## Prerequisites

- PostgreSQL running (e.g., via `docker compose -f docker-compose.dev.yml up -d postgres`)
- `.env` file in project root with API keys and test credentials

**Required Environment Variables**

```bash
TEST_USER_EMAIL=your@email.com
TEST_USER_PASSWORD=yourpassword
GROQ_API_KEY=gsk_xxx
ASSEMBLYAI_API_KEY=xxx
```

## Quick Start

```bash
cd dream-transcription-testing
set -a && source ../.env && set +a

# 1. Test Groq
python switch_provider.py groq
python run_transcriptions.py db1b48a1-59be-49be-bac4-3da3bf8f82cd --provider groq

# 2. Test AssemblyAI
python switch_provider.py assemblyai
python run_transcriptions.py db1b48a1-59be-49be-bac4-3da3bf8f82cd --provider assemblyai

# 3. Compare
python score.py db1b48a1 compare
```

## How It Works

1. `switch_provider.py` - Kills app, updates `.env`, restarts app, waits for health
2. `run_transcriptions.py` - Triggers `/entries/{entry_id}/transcribe` on existing entry
3. `score.py` - Compares cached transcription results (uses first 8 chars of entry_id)

## Directory Structure

```
cache/db1b48a1/
├── groq/
│   ├── temp_0.0.json
│   └── temp_0.5.json
└── assemblyai/
    └── result.json
```

## Scripts

```bash
# Switch provider (kills app, updates .env, restarts app)
python switch_provider.py groq
python switch_provider.py assemblyai

# Run transcription on existing entry (never overwrites - auto-versions)
python run_transcriptions.py <entry_id> --provider groq
python run_transcriptions.py <entry_id> --provider groq --temp 0.5
python run_transcriptions.py <entry_id> --provider assemblyai

# Compare results (uses first 8 chars of entry_id)
python score.py <audio_id> compare
python score.py <audio_id> compare --temp 0.5
python score.py <audio_id> stats groq
```

## Provider Differences

| Feature | Groq | AssemblyAI |
|---------|------|------------|
| Temperature | 0.0-1.0 | Not supported |
| Language auto | Supported | Defaults to en_us |
| Model | whisper-large-v3 | universal |

## Qualitative Analysis with Claude

After `score.py compare` generates automated metrics, ask Claude to analyze the transcriptions:

```
Read cache/db1b48a1/groq/temp_0.0.json and cache/db1b48a1/assemblyai/result.json, then score both transcriptions
```

Claude can help with:
- Comparing transcription accuracy between providers
- Evaluating Slovenian diacritic usage (č, š, ž)
- Identifying errors, hallucinations, or missing words
- Recommending which provider performed better

See `CLAUDE.md` for detailed scoring criteria and output format.
