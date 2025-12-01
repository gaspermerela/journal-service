# Source Data

← [Back to Index](./README.md)

---

## Transcription Info

| Field | Value |
|-------|-------|
| **Transcription ID** | 5beeaea1-967a-4569-9c84-eccad8797b95 |
| **Transcription Model** | groq-whisper-large-v3 |
| **Language** | sl (Slovenian) |
| **Raw Length** | 5,051 characters |

---

## Major Artifacts in Raw Transcription

| Artifact | Type | Notes |
|----------|------|-------|
| "Zdravstveno, da ste pripravljeni" | YouTube intro hallucination | Should be removed completely |
| "Hvala" (6+ occurrences) | Audio artifact | Should be removed |
| "polnica" | Mishearing | Should be "bolnica" (hospital) |
| "ronotežje" | Mishearing | Should be "ravnotežje" (balance) |
| Filler words | STT artifacts | "v bistvu", "torej", etc. |

---

## Scoring Criteria

| Criterion | Max Score | Description |
|-----------|-----------|-------------|
| Content Accuracy | 10 | Details preserved, no hallucinations, 70-95% length ratio |
| Artifact Removal | 10 | "Hvala", "Zdravstveno" removed, fillers cleaned |
| Grammar Quality | 10 | Proper Slovenian, errors corrected |
| Readability | 10 | Paragraph structure, natural flow |
| **Total** | **40** | ≥36/40 (90%) = threshold |

---

## Cache Location

JSON results cached at: `cache/prompt_{name}/{transcription_id}_{model}/T*.json`
