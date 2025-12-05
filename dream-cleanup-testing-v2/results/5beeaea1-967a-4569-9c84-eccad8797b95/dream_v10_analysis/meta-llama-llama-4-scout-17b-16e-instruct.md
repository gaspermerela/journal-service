# scout-17b on dream_v10_analysis

**Best:** T5 | Score: **83/100** | Status: **PASS**

---

## All Configs (Case 1: Temperature)

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| **T5** | temp=1.0 | 94% | 18 | 42 | 8 | 10 | 5 | **83** | **PASS** |
| T1 | temp=0.0 | 97% | 18 | 42 | 4 | 10 | 3 | 77 | REVIEW |
| T2 | temp=0.3 | 98% | 18 | 42 | 4 | 10 | 3 | 77 | REVIEW |
| T3 | temp=0.5 | 99% | 18 | 42 | 4 | 10 | 3 | 77 | REVIEW |
| T4 | temp=0.8 | 98% | 18 | 42 | 4 | 10 | 3 | 77 | REVIEW |
| T7 | temp=2.0 | 74% | 14 | 32 | 4 | 0 | 5 | 55 | FAIL |
| T6 | temp=1.5 | - | - | - | - | - | - | FAIL | JSON error |

**JSON Success Rate:** 6/7 (86%)

---

## Config-Specific Notes

### T5 (temp=1.0) - BEST
- Only config that adds paragraph breaks (but with the wrong pattern: `\n\n<break>\n\n` instead of `<break>`)
- Length in optimal range (94%)
- Still keeps many filler words but readable

### T1-T4 (temp=0.0-0.8) - NO CLEANUP
- All produce nearly identical output (97-99% of original)
- No paragraph breaks added
- No filler words removed
- Grammar errors NOT fixed
- Perfect content but unusable readability

### T7 (temp=2.0) - CORRUPTED OUTPUT
- **SEVERE:** Output becomes garbled gibberish at the end
- Last ~300 chars are nonsense: "Tu v mes sprajuje čečnja kam gredo..."
- Loses significant content in corruption
- Scores 0/10 hallucinations due to corrupted content

### T6 (temp=1.5) - JSON ERROR
- Model added preamble text before JSON
- Parser expects JSON at start of response

---

## T5 vs T1 Comparison

| Metric | T5 (temp=1.0) | T1 (temp=0.0) |
|--------|---------------|---------------|
| Length | 94% | 97% |
| Paragraph breaks | YES | NO |
| Readability | 8/15 | 4/15 |
| Length points | 5 | 3 |
| **Total** | **83** | 77 |

T5 is better because it actually adds some structure (paragraph breaks), though it still keeps most filler words and doesn't fix grammar.

---

## Failures Summary (Best Config: T5)

### Grammar (G) - 8 failures

Same as T1 - Scout doesn't clean grammar at any temperature:
- **G7:** "vzpodguja" NOT fixed
- **G15:** "zdrževanju" NOT fixed
- **G20:** "predem" NOT fixed
- **G22:** "Vzpomnim" NOT fixed
- **G23:** "prubleval" NOT fixed
- **G24/G27:** "nadreval" NOT fixed
- **G25:** "ta ljena vzgor" NOT fixed (garbled)

### Content (C) - 0 failures

All 44 content checkpoints preserved (because minimal cleanup performed).

### Hallucinations (H) - None in T5

### Readability (R) - 2/4 in T5

- **R1:** Paragraph breaks present ✅
- R2: Sentences still messy ❌
- **R3:** "jaz" voice preserved ✅
- R4: Hard to follow ❌

---

## Scoring Details (T5)

```
AUTOMATED CHECKS:
[!] "Zdravstveno..." NOT removed (A2)
[!] "v bistvu" appears 8+ times (A3)
[x] No English (G+)
[x] No Russian (G++)
[x] Length: 94% → 5 points (70-95% optimal)

COUNTS:
G_total: 28 | G_failed: 8 | G_passed: 20
C_total: 44 | C_failed: 0 | C_passed: 44
H_count: 0
R_score: 2/4

CALCULATION:
Content:       45 × (44/44) - 3 = 42
Grammar:       25 × (20/28) - 0 = 18
Readability:   15 × (2/4)       = 8 (rounded)
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (94%)          = 5
───────────────────────────────────────
TOTAL:                          83/100
```

---

## Key Findings

### 1. Scout doesn't clean with this prompt (except T5)
- T1-T4 produce 97-99% of original length
- Almost no grammar fixes, no filler removal
- Analysis prompt seems to override cleanup instructions

### 2. T5 is the sweet spot
- temp=1.0 triggers paragraph break behavior
- Still in optimal length range
- Only scout config that passes (83/100)

### 3. High temperature is dangerous
- T6 (temp=1.5): JSON formatting errors
- T7 (temp=2.0): Complete gibberish

### Recommendation
**Use T5 (temp=1.0)** if you must use scout with this prompt.

But overall, **prefer maverick** for dream_v10_analysis - it actually cleans the text (87/100 vs 83/100).