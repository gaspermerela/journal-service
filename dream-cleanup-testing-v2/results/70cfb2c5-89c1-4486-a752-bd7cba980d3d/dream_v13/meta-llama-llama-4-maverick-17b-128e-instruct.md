# maverick on dream_v13

**Transcription ID:** 70cfb2c5-89c1-4486-a752-bd7cba980d3d
**Model:** groq-meta-llama/llama-4-maverick-17b-128e-instruct

**Best:** T1_v1/v2 | Score: 91/100 | Status: EXCELLENT

---

## Prompt Changes from v12

Key improvements in v13:
1. Added present tense instruction in CRITICAL section: `⚠️ DO write in present tense, first person singular ("jaz")`
2. Added `OUTPUT FORMAT: Respond ONLY with the cleaned text.` to prevent header artifacts
3. Reorganized REMOVE section for clarity

---

## Variance Testing (T1 × 4 runs)

**Key finding:** Much tighter variance than v12, and all scores in EXCELLENT range (90-91).

| Run | Chars | Ratio | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|-----|-------|-------|------|------|------|------|-----|-------|--------|
| T1_v1 | 3740 | 74.6% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v2 | 3806 | 75.9% | 23 | 40 | 15 | 8 | 5 | **91** | EXCELLENT |
| T1_v3 | 3796 | 75.7% | 23 | 39 | 15 | 8 | 5 | **90** | EXCELLENT |
| T1_v4 | 3695 | 73.7% | 22 | 40 | 15 | 8 | 5 | **90** | EXCELLENT |

### Variance Summary

| Metric | Min | Max | Range |
|--------|-----|-----|-------|
| Length | 73.7% | 75.9% | 2.2% |
| Score | 90 | 91 | 1 pt |

**Improvement from v12:** Length variance reduced from 7.5% to 2.2%, score variance from 3pts to 1pt.

---

## Comparison: v12 vs v13

| Metric | v12 (best) | v12 (avg) | v13 (best) | v13 (avg) | Delta |
|--------|------------|-----------|------------|-----------|-------|
| **Total** | 85 | 83 | 91 | 90.5 | **+6 to +7.5** |
| Content | 37 | 35 | 40 | 40 | **+3 to +5** |
| Grammar | 22 | 22 | 23 | 23 | +1 |
| Readability | 15 | 12 | 15 | 15 | 0 to +3 |
| Hallucinations | 6 | 9 | 8 | 8 | +2 to -1 |
| Length | 5 | 5 | 5 | 5 | 0 |
| Voice penalty | -7 | -7 | -3 | -3 | **+4** |

**Key improvements:**
- Voice penalty reduced from -7 to -3 (past → present tense)
- No header artifact ("Here is the cleaned...")
- Tighter length variance (2.2% vs 7.5%)

---

## Failures Summary (Common across runs)

### Grammar (G) - 2-3 failures

Common failures:
- **G13:** "nazdolj" ❌ (should be "navzdol")
- **G20/G21:** "obhodnikov" ❌ (should be "hodnikov")

Additional in T1_v4:
- **G?:** "velikih stavbi" ❌ (should be "veliki stavbi")

### Content (C) - 2-3 failures per run

**Always missing:**
- **C23:** Flat areas + corridors mixed with stairs

**Variable across runs:**
| Checkpoint | T1_v1 | T1_v2 | T1_v3 | T1_v4 |
|------------|-------|-------|-------|-------|
| C30 (hodnik levo-desno) | ✅ | ✅ | ❌ | ❌ |
| C34 (10m width) | ✅ | ❌ | ❌ | ✅ |
| C36 (women unbothered) | ❌ | ✅ | ✅ | ✅ |

**Voice penalty (-3):** Minor past tense shifts in natural contexts (feelings, specific past events). Core narrative uses present tense consistently ("Hodim", "Vidim", "sprašujem se").

### Hallucinations (H) - 1 per run

- **H1:** "Skupaj pridemo" / "smo prišli" - implies they walked together (original says he met her on the way)

### Readability (R) - 4/4 all runs

- R1: Paragraph breaks via `\n` ✓
- R2: Sentences flow logically ✓
- R3: "jaz" voice preserved ✓
- R4: Dream coherence maintained ✓

### Artifacts

- ✅ No header artifact (fixed by `OUTPUT FORMAT` instruction)
- ✅ All "Hvala" removed
- ⚠️ "v bistvu" appears once in T1_v3

---

## Detailed Scoring Breakdown

### T1_v1 (Best)
```
Content:       45 × (42/44) - 3 = 40
Grammar:       25 × (26/28) - 0 = 23
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (1 × 2)    = 8
Length:        5 (74.6% optimal)= 5
─────────────────────────────────────
TOTAL:                          91/100
```

### T1_v2
```
Content:       45 × (42/44) - 3 = 40
Grammar:       25 × (26/28) - 0 = 23
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (1 × 2)    = 8
Length:        5 (75.9% optimal)= 5
─────────────────────────────────────
TOTAL:                          91/100
```

### T1_v3
```
Content:       45 × (41/44) - 3 = 39
Grammar:       25 × (26/28) - 0 = 23
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (1 × 2)    = 8
Length:        5 (75.7% optimal)= 5
─────────────────────────────────────
TOTAL:                          90/100
```

### T1_v4
```
Content:       45 × (42/44) - 3 = 40
Grammar:       25 × (25/28) - 0 = 22
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (1 × 2)    = 8
Length:        5 (73.7% optimal)= 5
─────────────────────────────────────
TOTAL:                          90/100
```

---

## Recommendations

1. **Fix G13 (nazdolj→navzdol):** Add to STT mishearings list in prompt
2. **Fix G20/G21 (obhodnikov→hodnikov):** Add to STT mishearings list
3. **Fix H1 ("smo prišli"):** Add instruction to preserve individual agency
4. **Production ready:** All runs score ≥90 (EXCELLENT threshold)
