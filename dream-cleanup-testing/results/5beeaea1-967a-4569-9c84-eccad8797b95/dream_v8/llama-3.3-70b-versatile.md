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

## Failures Summary (P4 - Best Config)

### Grammar (G) - 8 failures = 18/25
- **G1:** "polnica" → "bolnica" ✅ FIXED in P4 (unique!)
- **G3:** "uspodbudo" NOT fixed to "spodbudo"
- **G17:** "mogo" NOT fixed to "moral"
- **G21:** "obhodnikov" NOT fixed to "hodnikov"
- **G23:** "prubel čimprej" garbled phrase remains
- **G25:** "hodi ta ženska vzgor" garbled remains (singular instead of plural)
- **G27:** "nadreval" NOT fixed to "nadaljeval"
- **G28:** "notakrat" NOT fixed to "nato"

### Content (C) - 2 failures = 43/45
- **C34:** "deset metrov široke" (10m width) - MISSING
- **C35:** Two women walking up - uses singular "ta ženska" instead of "dve ženski"

### Hallucinations (H) - 0 failures = 10/10
- None detected in P4

### Readability (R) - 1 failure = 11/15
- **R1:** No paragraph breaks - wall of text
- **R2:** Sentence flow good (PASS)
- **R3:** Personal voice "jaz" preserved (PASS)
- **R4:** Dream coherence maintained (PASS)

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
