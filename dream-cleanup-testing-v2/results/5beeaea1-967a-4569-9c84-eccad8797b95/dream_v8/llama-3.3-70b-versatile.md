# llama-3.3-70b-versatile on dream_v8

**Best:** P4 | Score: 87/100 | Status: PASS

**Criteria:** G=28, C=44

---

## All Configs

### Temperature Tests (Case 1)

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| T1 | t=0.0 | 88% | 16 | 39 | 11 | 10 | 5 | 81 | PASS |
| T2 | t=0.3 | 82% | 17 | 39 | 11 | 10 | 5 | 82 | PASS |
| T3 | t=0.5 | 88% | 16 | 39 | 11 | 10 | 5 | 81 | PASS |
| T4 | t=0.8 | 84% | 15 | 37 | 11 | 10 | 5 | 78 | REVIEW |
| T5 | t=1.0 | 78% | 17 | 37 | 11 | 10 | 5 | 80 | PASS |
| T6 | t=1.5 | 41% | 18 | 25 | 11 | 10 | 0 | 64 | ITERATE |
| T7 | t=2.0 | 41% | 0 | 0 | 0 | 0 | 0 | 0 | FAIL |

### Top-p Tests (Case 2)

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| P1 | p=0.1 | 76% | 15 | 37 | 11 | 10 | 5 | 78 | REVIEW |
| P2 | p=0.3 | 78% | 15 | 37 | 11 | 10 | 5 | 78 | REVIEW |
| P3 | p=0.5 | 88% | 16 | 37 | 11 | 10 | 5 | 79 | REVIEW |
| P4 | p=0.7 | 82% | 18 | 43 | 11 | 10 | 5 | 87 | PASS |
| P5 | p=0.9 | 74% | 15 | 37 | 11 | 10 | 5 | 78 | REVIEW |
| P6 | p=1.0 | 70% | 15 | 36 | 11 | 10 | 5 | 77 | REVIEW |

---

## Score Calculations

### Best Config: P4 (p=0.7)

```
G_total: 28 | G_failed: 8 | G_passed: 20
C_total: 44 | C_failed: 2 | C_passed: 42
H_count: 0
R_score: 3/4 (R1 failed - no paragraphs)
Voice: OK (no penalty)
Language: OK (no penalty)

Content:       45 × (42/44) - 0 = 42.95 → 43
Grammar:       25 × (20/28) - 0 = 17.9 → 18
Readability:   15 × (3/4)       = 11.25 → 11
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (82% optimal)  = 5
───────────────────────────────────────
TOTAL:                          87/100 (PASS)
```

### Worst Usable: T6 (t=1.5)

```
G_total: 28 | G_failed: 8 | G_passed: 20
C_total: 44 | C_failed: 19 | C_passed: 25 (over-summarized)
H_count: 0
R_score: 3/4
Voice: OK
Language: OK

Content:       45 × (25/44) - 0 = 25.6 → 26
Grammar:       25 × (20/28) - 0 = 17.9 → 18
Readability:   15 × (3/4)       = 11.25 → 11
Hallucinations: 10 - (0 × 2)    = 10
Length:        0 (41% severe)   = 0
───────────────────────────────────────
TOTAL:                          65/100 (ITERATE)
```

### T7: FAIL (Gibberish)

Output is garbled Slovenian, completely unusable. Score: 0/100

---

## Grammar Failures

**Consistently UNFIXED (all configs):**

| ID | Raw → Expected | Status |
|----|----------------|--------|
| G1 | polnica → bolnica | ✅ Fixed in P4! ❌ Unfixed in others |
| G3 | uspodbudo → spodbudo | ❌ Never fixed |
| G13 | nazdolj → navzdol | ⚠️ Inconsistent |
| G16 | kmalo → kmalu | ❌ Rarely fixed |
| G17 | mogo → moral | ❌ Never fixed |
| G23 | prublev čimprej | ❌ Never fixed |
| G25 | hori ta ljena vzgor | ❌ Never fixed |
| G27 | nadreval → nadaljeval | ❌ Never fixed |
| G28 | notakrat → nato | ❌ Never fixed |

**Language checks:** No G+ or G++ violations in any config.

---

## Content Failures

### P4 (Best - 82%, C=43)

**Failed (2 checkpoints):**

| ID | Detail | Issue |
|----|--------|-------|
| C34 | "deset metrov široke" (10m width) | ❌ MISSING - no width mentioned at all |
| C35 | Two women walking UP | ⚠️ "hodi ta ženska vzgor" - uses singular instead of both |

---

## Readability Analysis

| Check | Score | Notes |
|-------|-------|-------|
| R1: Paragraphs | 0 | Wall of text in ALL configs |
| R2: Flow | 1 | Sentences connect well |
| R3: Voice | 1 | "jaz" preserved |
| R4: Coherence | 1 | Dream logic maintained |

**R_score: 3/4** (consistently loses 3.75 points)

---

## Hallucinations

**None detected** in any config (except T7 which is gibberish).

---

## Key Findings

1. **G1 "polnica→bolnica" fixed in P4!** - only config to fix this
2. **Garbled phrases preserved** - G23, G25, G27, G28 never cleaned
3. **No paragraph structure** - consistent R1 failure (wall of text)
4. **T7 completely unusable** - produces gibberish at temp=2.0
5. **T6 over-summarizes** - only 41% length
6. **No hallucinations** - content is faithful when preserved
7. **P4 is best** - 87/100, fixes G1, excellent content preservation

---

## Recommendation

**Status: PASS** - P4 achieves 87/100.

**Use P4** for best results (87/100) - fixes G1, preserves 42/44 content checkpoints.

**Remaining issues:**
- R1: No paragraphs (need prompt change)
- G25, G27, G28: Garbled phrases not fixed (need examples in prompt)
