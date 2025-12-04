# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v8

**Best:** T5 | Score: 87/100 | Status: PASS

**Criteria:** G=28, C=44

---

## All Configs

### Temperature Tests (Case 1)

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| T1 | t=0.0 | 79% | 12 | 39 | 11 | 10 | 5 | 77 | REVIEW |
| T2 | t=0.3 | 77% | 12 | 39 | 11 | 10 | 5 | 77 | REVIEW |
| T3 | t=0.5 | 71% | 17 | 39 | 11 | 10 | 5 | 82 | PASS |
| T4 | t=0.8 | 69% | 16 | 37 | 11 | 10 | 3 | 77 | REVIEW |
| T5 | t=1.0 | 81% | 20 | 41 | 11 | 10 | 5 | 87 | PASS |
| T6 | t=1.5 | 55% | 17 | 30 | 11 | 10 | 1 | 69 | ITERATE |
| T7 | t=2.0 | 54% | 12 | 30 | 8 | 8 | 1 | 59 | FAIL |

### Top-p Tests (Case 2)

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| P1 | p=0.1 | 82% | 12 | 39 | 11 | 10 | 5 | 77 | REVIEW |
| P2 | p=0.3 | 80% | 12 | 39 | 11 | 10 | 5 | 77 | REVIEW |
| P3 | p=0.5 | 80% | 12 | 39 | 11 | 10 | 5 | 77 | REVIEW |
| P4 | p=0.7 | 53% | 12 | 30 | 11 | 10 | 1 | 64 | ITERATE |
| P5 | p=0.9 | 76% | 18 | 37 | 11 | 10 | 5 | 81 | PASS |
| P6 | p=1.0 | 74% | 17 | 37 | 11 | 10 | 5 | 80 | PASS |

---

## Score Calculations

### Best Config: T5 (t=1.0)

```
G_total: 28 | G_failed: 6 | G_passed: 22
C_total: 44 | C_failed: 4 | C_passed: 40
H_count: 0
R_score: 3/4 (R1 partial paragraphs)
Voice: OK (no penalty)
Language: OK (no G++, clean)

Content:       45 × (40/44) - 0 = 40.9 → 41
Grammar:       25 × (22/28) - 0 = 19.6 → 20
Readability:   15 × (3/4)       = 11.25 → 11
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (81% optimal)  = 5
───────────────────────────────────────
TOTAL:                          87/100 (PASS)
```

### T1 with Russian Leak (G++)

```
G_total: 28 | G_failed: 6 | G_passed: 22
C_total: 44 | C_failed: 4 | C_passed: 40
H_count: 0
R_score: 3/4
Voice: OK
Language: G++ Russian "приходят" = -5

Content:       45 × (40/44) - 0 = 40.9 → 41
Grammar:       25 × (22/28) - 5 = 14.6 → 15
Readability:   15 × (3/4)       = 11.25 → 11
Hallucinations: 10 - (0 × 2)    = 10
Length:        5 (79% optimal)  = 5
───────────────────────────────────────
TOTAL:                          82/100 (PASS, but penalized)
```

### T7: Degraded Output

```
G_total: 28 | G_failed: 10 | G_passed: 18
C_total: 44 | C_failed: 14 | C_passed: 30 (over-summarized + garbled ending)
H_count: 1 (garbled text counts as hallucination)
R_score: 2/4 (partial paragraphs, incoherent ending)
Voice: Minor issues = -3

Content:       45 × (30/44) - 3 = 27.7 → 28
Grammar:       25 × (18/28) - 0 = 16.1 → 16
Readability:   15 × (2/4)       = 7.5 → 8
Hallucinations: 10 - (1 × 2)    = 8
Length:        1 (54% problematic) = 1
───────────────────────────────────────
TOTAL:                          61/100 (ITERATE)
```

---

## Grammar Failures

**G1 Status:**

| ID | Raw → Expected | Status |
|----|----------------|--------|
| G1 | polnica → bolnica | ✅ Fixed in P5! ❌ Unfixed in others |
| G13 | nazdolj → navzdol | ⚠️ Sometimes fixed |
| G16 | kmalo → kmalu | ⚠️ Sometimes fixed |
| G17 | mogo → moral | ❌ Rarely fixed |

**Better than llama-3.3:**

| ID | Raw → Expected | Status |
|----|----------------|--------|
| G25 | hori ta ljena vzgor | ✅ Often fixed to "hodita vzgor" |
| G27 | nadreval → nadaljeval | ⚠️ Sometimes fixed |
| G28 | notakrat → nato | ⚠️ Sometimes fixed |

**Language checks:**

| Config | G+ (English) | G++ (Russian) |
|--------|--------------|---------------|
| T1 | Clean | ❌ "приходят" present |
| T2 | Clean | ❌ "приходят" present |
| T3 | Clean | ✅ Clean |
| T4 | Clean | ✅ Clean |
| T5 | Clean | ✅ Clean |
| P1 | Clean | ❌ "приходят" present |
| P2 | Clean | ❌ "приходят" present |
| P3 | Clean | ❌ "приходят" present |
| P4 | Clean | ❌ "приходят" present |
| P5 | Clean | ✅ Clean |
| P6 | Clean | ✅ Clean |

---

## Content Failures

### T5 (Best - 81%, C=41)

**Failed (4 checkpoints):**

| ID | Detail | Issue |
|----|--------|-------|
| C3 | "preden" timeline (before work) | Present but slightly reworded |
| C8 | "hodim naprej in naprej" repetition | Preserved ✅ |
| C23 | Flat areas + corridors between stairs | Simplified to just "stopnice" |
| C42 | Wet ground specific detail | "vljudno nekakšna zemlja" slightly vague |

---

## Readability Analysis

| Check | T1-T5 | T7 |
|-------|-------|-----|
| R1: Paragraphs | ⚠️ Partial | ⚠️ Partial |
| R2: Flow | ✅ Good | ❌ Broken at end |
| R3: Voice | ✅ jaz preserved | ⚠️ Shifts |
| R4: Coherence | ✅ Good | ❌ Incoherent ending |

**R_score:** 3/4 for T1-T5, 2/4 for T7

---

## Hallucinations

| Config | H_count | Details |
|--------|---------|---------|
| T1-T5 | 0 | None detected |
| T7 | 1 | Garbled ending constitutes hallucination |

---

## Key Findings

1. **Russian leak in T1, T2, P1-P4** - "приходят" (Cyrillic) costs -5 points
2. **T5 is best overall** - No Russian, good grammar, 87/100
3. **P5 fixes G1 "polnica→bolnica"** - Only maverick config to fix this!
4. **P5 and P6 are clean** - No Russian, no G++ penalty
5. **P4 severely over-summarizes** - 53% length, loses too much content
6. **Better garbled phrase handling** - G25, G27, G28 often fixed
7. **Partial paragraph structure** - Better than llama-3.3
8. **T7 degrades significantly** - 54% length, garbled ending
9. **No hallucinations** (except T7 degradation)

---

## Comparison with llama-3.3-70b

| Metric | llama-3.3 | maverick | Winner |
|--------|-----------|----------|--------|
| Best Score | 83/100 | 87/100 | **maverick** |
| Russian leak | Never | T1,T2,P1 | llama-3.3 |
| G25 fix | Never | Often | **maverick** |
| Paragraphs | Never | Partial | **maverick** |
| Best config | P4 | T5 | - |

---

## Recommendation

**Status: PASS** - Best model for dream_v8.

**Best configs:**
- **T5** (87/100) - Best overall, good grammar + content
- **P5** (81/100) - Fixes G1! Only config to fix "polnica→bolnica"
- **P6** (80/100) - Clean, no Russian
- **T3** (82/100) - Good alternative

**Avoid:** T1, T2, P1-P4 (Russian contamination), T7 (degraded), P4 (over-summarized)

**Remaining issues:**
- Paragraph structure incomplete (R1 partial)
- G1 only fixed in P5
