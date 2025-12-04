# openai/gpt-oss-120b on dream_v8

**Best:** P1 | Score: 73/100 | Status: REVIEW

**Criteria:** G=28, C=44

---

## All Configs

### Temperature Tests (Case 1)

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| T1 | t=0.0 | 58% | 19 | 27 | 13 | 6 | 1 | 66 | ITERATE |
| T2 | t=0.3 | 51% | 19 | 27 | 15 | 10 | 1 | 72 | REVIEW |
| T3 | t=0.5 | 49% | 19 | 22 | 13 | 10 | 0 | 64 | ITERATE |
| T4 | t=0.8 | 46% | 19 | 25 | 15 | 10 | 0 | 69 | ITERATE |
| T5 | t=1.0 | 51% | 19 | 27 | 15 | 8 | 1 | 70 | REVIEW |
| T6 | t=1.5 | 49% | 19 | 26 | 15 | 10 | 0 | 70 | REVIEW |
| T7 | t=2.0 | 58% | 15 | 22 | 11 | 4 | 1 | 53 | FAIL |

### Top-p Tests (Case 2)

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| P1 | p=0.1 | 52% | 20 | 27 | 15 | 10 | 1 | 73 | REVIEW |
| P2 | p=0.3 | 55% | 19 | 28 | 15 | 10 | 1 | 73 | REVIEW |
| P3 | p=0.5 | 56% | 19 | 28 | 15 | 10 | 1 | 73 | REVIEW |
| P4 | p=0.7 | 50% | 19 | 26 | 15 | 8 | 1 | 69 | ITERATE |
| P5 | p=0.9 | 52% | 19 | 27 | 15 | 8 | 1 | 70 | REVIEW |
| P6 | p=1.0 | 54% | 19 | 27 | 15 | 10 | 1 | 72 | REVIEW |

---

## Score Calculations

### Best Config: P1 (p=0.1)

```
G_total: 28 | G_failed: 6 | G_passed: 22
C_total: 44 | C_failed: 18 | C_passed: 26 (over-summarized)
H_count: 0
R_score: 4/4 (excellent paragraphs!)
Voice: OK (no penalty)
Language: OK (no penalty)

Content:       45 × (26/44) - 0 = 26.6 → 27
Grammar:       25 × (22/28) - 0 = 19.6 → 20
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (0 × 2)    = 10
Length:        1 (52% problematic) = 1
───────────────────────────────────────
TOTAL:                          73/100 (REVIEW)
```

### T1 with Hallucinations

```
G_total: 28 | G_failed: 6 | G_passed: 22
C_total: 44 | C_failed: 18 | C_passed: 26
H_count: 2 (added intro + light description)
R_score: 3.5/4
Voice: OK
Language: OK

Content:       45 × (26/44) - 0 = 26.6 → 27
Grammar:       25 × (22/28) - 0 = 19.6 → 20
Readability:   15 × (3.5/4)     = 13.1 → 13
Hallucinations: 10 - (2 × 2)    = 6
Length:        1 (58% problematic) = 1
───────────────────────────────────────
TOTAL:                          67/100 (ITERATE)
```

### T7 with Multiple Issues

```
G_total: 28 | G_failed: 10 | G_passed: 18
C_total: 44 | C_failed: 22 | C_passed: 22
H_count: 3 (multiple invented details)
R_score: 3/4
Voice: OK
Language: OK

Content:       45 × (22/44) - 0 = 22.5 → 23
Grammar:       25 × (18/28) - 0 = 16.1 → 16
Readability:   15 × (3/4)       = 11.25 → 11
Hallucinations: 10 - (3 × 2)    = 4
Length:        1 (58% problematic) = 1
───────────────────────────────────────
TOTAL:                          55/100 (FAIL)
```

---

## Grammar Analysis

**Best grammar fixes of all models:**

| ID | Raw → Expected | Status |
|----|----------------|--------|
| G1 | polnica → bolnica | ✅ **FIXED** (only model to fix!) |
| G13 | nazdolj → navzdol | ✅ Often fixed |
| G25 | hori ta ljena vzgor | ✅ Often fixed |
| G27 | nadreval → nadaljeval | ✅ Often fixed |
| G28 | notakrat → nato | ✅ Often fixed |

**Still problematic:**

| ID | Raw → Expected | Status |
|----|----------------|--------|
| G2 | pretličju → pritličju | ⚠️ Sometimes kept |

**Language checks:** No G+ or G++ violations.

---

## Content Analysis

**CRITICAL ISSUE: Severe Over-summarization**

| Config | Length | Ratio | Content Lost |
|--------|--------|-------|--------------|
| T1 | 2925 | 58% | ~42% |
| T3 | 2466 | 49% | ~51% |
| P1 | 2650 | 52% | ~48% |
| T7 | 2940 | 58% | ~42% |

All configs fail the 70-95% length requirement.

**Details commonly lost:**
- C6: Spray detail simplified
- C7: Sound description reduced
- C22: Stair descriptions shortened
- C23: Flat areas + corridors detail lost
- C26: Movement detail reduced
- C34: 10m width sometimes kept, sometimes lost

---

## Hallucinations Detected

| Config | H_count | Details |
|--------|---------|---------|
| T1 | 2 | H1: "Zdravstveno..." added; H2: changed details |
| T2 | 0 | Clean but shortened |
| T3 | 0 | Clean but shortened |
| T4 | 0 | Clean but shortened |
| T5 | 1 | H1: "Zdravstveno, da sem pripravljen" added at start |
| T6 | 0 | Clean but shortened |
| T7 | 3 | Multiple invented phrases |
| P1 | 0 | Clean but shortened |
| P2 | 0 | Clean but shortened |
| P3 | 0 | Clean but shortened |
| P4 | 1 | H1: "Zdravstveno, da sem pripravljen" added at start |
| P5 | 1 | H1: "Zdravstveno sem pripravljen" added at start |
| P6 | 0 | Clean but shortened |

---

## Readability Analysis

**Best paragraph structure of all models!**

| Check | T1 | T3 | P1 | T7 |
|-------|----|----|----|----|
| R1: Paragraphs | ✅ Excellent | ✅ Excellent | ✅ Excellent | ⚠️ Good |
| R2: Flow | ✅ Good | ✅ Good | ✅ Good | ⚠️ OK |
| R3: Voice | ⚠️ Sometimes shifts | ✅ Good | ✅ Good | ⚠️ Shifts |
| R4: Coherence | ✅ Good | ✅ Good | ✅ Good | ⚠️ OK |

**R_score:** 3.5-4/4 (excellent, best of all models)

---

## Key Findings

1. **Severe over-summarization** - All configs 49-58% length (loses 40-50% content)
2. **Best grammar fixes** - G1 "polnica→bolnica" FIXED (only model!)
3. **Best paragraph structure** - R1 excellent, R_score 4/4
4. **Hallucinations present** - T1, T7 add invented content
5. **Length penalty hurts score** - Only gets 0-1 points for Length
6. **Content vs Structure trade-off** - Best R, worst C

---

## Comparison with Other Models

| Metric | llama-3.3 | maverick | gpt-oss | Winner |
|--------|-----------|----------|---------|--------|
| Best Score | 83/100 | 87/100 | 73/100 | **maverick** |
| G1 fix | Never | Never | **Yes** | gpt-oss |
| Content preservation | Good | Good | **Poor** | llama/maverick |
| Length ratio | 70-88% | 69-82% | **49-58%** | llama/maverick |
| Paragraphs | None | Partial | **Full** | gpt-oss |
| Hallucinations | None | None | **Yes** | llama/maverick |

---

## Recommendation

**Status: ITERATE** - Not recommended for production.

**Do NOT use** - Over-summarization loses too much dream content.

**Potential use case:**
- Could study its paragraph structure for prompt engineering
- Reference for how to format output

**Why it fails:**
1. Loses 40-50% of content (unacceptable)
2. Hallucinations in some configs
3. Only gets 1 point for Length in all configs

**If you must use:** P1 is cleanest (no hallucinations, 73/100)
