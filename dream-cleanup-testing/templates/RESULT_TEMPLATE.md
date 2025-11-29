# Cleanup Analysis: [Transcription ID]
**Date:** [Date]
**Status:** [In Progress / Complete]

---

## Best Result Summary
| Field | Value |
|-------|-------|
| Best Model | [model name] |
| Best Temperature | [value] |
| Best Top-p | [value] |
| Best Prompt Version | [version] |
| Final Score | [XX/40] |

---

## Raw Transcription
**Source:** Whisper large-v3
**Whisper Temperature:** [value]
**Language:** sl
```
[Raw transcription text from database]
```

---

## Prompt v[X] (Active: [Yes/No])
**Prompt ID:** [from database]
**Created:** [date]
```
[Full prompt text fetched from database]
```

### Test Results for Prompt v[X]

#### [Model Name] - Temp: [X], Top-p: [Y]
**Scores:**

| Criterion | Score |
|-----------|-------|
| Content Accuracy | X/10 |
| Artifact Removal | X/10 |
| Grammar Quality | X/10 |
| Readability | X/10 |
| **Total** | **XX/40** |

**Red Flags Found:**
- [ ] Subject changed
- [ ] Timing changed
- [ ] Terms altered
- [ ] Content added
- [ ] Content duplicated
- [ ] Artifacts remaining
- [ ] English words
- [ ] Nonsense phrases

**Notes:**
[Specific observations about this cleanup]

**Cleanup Text:**
```
[The actual cleaned text]
```

---

#### [Model Name] - Temp: [X], Top-p: [Y]
[Repeat structure for each test...]

---

## Prompt v[X+1] (Active: [Yes/No])
[Repeat structure for each prompt version...]

---

## Analysis & Recommendations

### Issues Identified Across Tests
1. [Issue 1]
2. [Issue 2]

### Suggested Prompt Changes
1. [Change 1]
2. [Change 2]

### Recommended Production Settings
- **Model:** [recommendation]
- **Temperature:** [value]
- **Top-p:** [value]
- **Prompt Version:** [version]