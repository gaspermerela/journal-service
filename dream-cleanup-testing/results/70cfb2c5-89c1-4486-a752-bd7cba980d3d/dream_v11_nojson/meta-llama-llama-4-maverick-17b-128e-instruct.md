# maverick on dream_v11_nojson

**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Model:** groq-meta-llama/llama-4-maverick-17b-128e-instruct

**Best:** T1 | Score: 86/100 | Status: PASS

---

## Raw Transcription Comparison

### Old vs New Transcription

| Metric | Old (5beeaea1) | New (70cfb2c5) |
|--------|----------------|----------------|
| Length | 5,051 chars | 5,013 chars |
| Model | groq-whisper-large-v3 | groq-whisper-large-v3 |
| Date | 2025-11-29 | 2025-12-08 |

### Transcription Quality

Both transcriptions capture all criteria details - **no transcription-level failures**.

| Detail | Present in New? |
|--------|-----------------|
| C23: flat areas + corridors | Yes - "niso bile tako samo stopnice ampak le so neki čas stopnice pa je bilo malo spet ravnine, pa spet na stopnic, pa v mestu odhodniki" |
| C30: "hodnik, levo-desno" | Yes - "je bil tudi hodnik, levo-desno" |
| All other C1-C44 details | Yes |

**Conclusion:** All content failures are **cleanup failures**, not transcription issues.

---

## T1 Score Comparison

| Metric | Old T1 (5beeaea1) | New T1 (70cfb2c5) | Delta |
|--------|-------------------|-------------------|-------|
| **Total Score** | 94/100* | 86/100 | -8 |
| Content | 42/45 | 41/45 | -1 |
| Grammar | 23/25 | 23/25 | 0 |
| Readability | 15/15 | 15/15 | 0 |
| Hallucinations | 10/10 | 6/10 | -4 |
| Length | 4/5 (72%) | 1/5 (58%) | -3 |

*Old T1 status was "failed" but raw_response contained cleaned text - score estimated from that output.

### Why New Score is Lower

1. **Over-compression (58% vs 72%):** New output is 2,915 chars vs ~3,640 chars expected
2. **More hallucinations:**
   - "Skupaj pridemo" (implies joint arrival - not in original)
   - Direction change "nazaj" instead of "navzdol"
3. **Content losses:**
   - C10: Cabinet misunderstanding detail missing
   - C23: Flat areas + corridors detail missing
   - C26: "napol tek navzdol" became "nazaj"
   - C30: "hodnik levo-desno" missing

---

## All Configs

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| T1 | t=0.0 | 58% | 23 | 41 | 15 | 6 | 1 | 86 | PASS |

---

## Failures Summary (T1)

### Grammar (G) - 2 failures

- **G13:** "navzdol" incorrectly became "nazaj" (back instead of down)
- **G21:** "obhodnikov" still used instead of "hodnikov"

### Content (C) - 4 failures

- **C10:** Cabinet misunderstanding detail MISSING
  - Original: "v začetku mislim, da je omara kot recimo za velikimi vrati... ampak v resnici je bila omara za večmi, manjšimi vrati"
  - Output: Just "za manjšimi vrati" - no misunderstanding contrast

- **C23:** Flat areas + corridors mixed with stairs MISSING
  - Original: "niso bile tako samo stopnice ampak le so neki čas stopnice pa je bilo malo spet ravnine, pa spet na stopnic, pa v mestu odhodniki"
  - Output: Only describes stair variation, not the flat areas/corridors

- **C26:** "napol tek navzdol" (half-running down) MISSING
  - Original: "nadelujem hojo oziroma napol tek nazdolj in nazdolj"
  - Output: "Nadaljujem hojo, oziroma napol tek, nazaj po stopnicah" - says "back" not "down"

- **C30:** "hodnik levo-desno" at landing MISSING
  - Original: "je bil tudi hodnik, levo-desno"
  - Output: Not mentioned at all

### Hallucinations (H) - 2 found

- **H1:** "Skupaj pridemo" - implies they arrive together, but original says he meets her separately and they don't walk together
- **H2:** "nazaj po stopnicah" - says going BACK, but original is going DOWN continuously

### Readability (R) - 0 failures

All 4 readability checks passed.

---

## Recommendations

1. **Re-transcribe:** The new transcription may have lost some detail - consider re-recording or using different STT settings
2. **Test more configs:** T2-T7 might produce better results with less compression
3. **Prompt adjustment:** Consider adding explicit instruction to preserve percentage of content (target 70-95%)
