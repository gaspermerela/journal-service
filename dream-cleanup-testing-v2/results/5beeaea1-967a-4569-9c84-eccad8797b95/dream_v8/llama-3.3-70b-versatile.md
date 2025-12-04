# llama-3.3-70b-versatile on dream_v8

**Best:** T2 | Score: 30/40 | Status: ITERATE

---

## All Configs

### Temperature Tests (Case 1)

| Config | Params | Len% | G | C | A | R | Total | Status | Key Failures |
|--------|--------|------|---|---|---|---|-------|--------|--------------|
| T1 | t=0.0 | 88% | 5 | 8.5 | 10 | 6 | 29.5 | ITERATE | G1, G3, G13, G16, G17, G18, G19, G20, G21, G23, G25, G27, G28; R1 (no paragraphs) |
| T2 | t=0.3 | 82% | 5.5 | 8.5 | 10 | 6 | 30 | ITERATE | G1, G3, G13, G16, G17, G23, G25, G27, G28; R1 |
| T3 | t=0.5 | 88% | 5 | 8.5 | 10 | 6 | 29.5 | ITERATE | G1, G3, G13, G16, G17, G18, G20, G22, G23, G25, G27, G28; R1 |
| T4 | t=0.8 | 84% | 4.5 | 7.5 | 10 | 6 | 28 | ITERATE | G1, G3, G13, G20, G22, G23, G25, G27; C26 (wrong direction "navzgor"); R1 |
| T5 | t=1.0 | 78% | 5.5 | 7.5 | 9 | 6 | 28 | ITERATE | G1, G3, G13, G22, G23, G25, G27; C6 (missing spray detail); A2 kept; R1 |
| T6 | t=1.5 | 41% | 6 | 4 | 10 | 5 | 25 | ITERATE | G2; C+++ (over-summarized <70%); Many C failures |
| T7 | t=2.0 | 41% | 0 | 0 | 10 | 0 | 10 | ITERATE | **GIBBERISH** - Unusable output |

### Top-p Tests (Case 2)

| Config | Params | Len% | G | C | A | R | Total | Status | Key Failures |
|--------|--------|------|---|---|---|---|-------|--------|--------------|
| P1 | p=0.1 | 76% | 5 | 8 | 10 | 6 | 29 | ITERATE | G1, G3, G9, G13, G16, G17, G22, G23, G25, G27, G28; R1 |
| P2 | p=0.3 | 78% | 5 | 8 | 10 | 6 | 29 | ITERATE | G1, G3, G9, G13, G16, G17, G22, G23, G25, G27, G28; R1 |
| P3 | p=0.5 | 88% | 5 | 8 | 9 | 6 | 28 | ITERATE | G1, G3, G13, G16, G17, G22, G23, G25, G28; A2 kept; R1 |
| P4 | p=0.7 | 82% | 6 | 8.5 | 10 | 6 | 30.5 | ITERATE | G1, G3, G13, G16, G17, G23, G27, G28; R1 |
| P5 | p=0.9 | 74% | 5 | 8 | 10 | 6 | 29 | ITERATE | G1, G3, G9, G13, G16, G17, G22, G24, G25, G27; R1 |
| P6 | p=1.0 | 70% | 5 | 7.5 | 10 | 6 | 28.5 | ITERATE | G1, G2, G3, G13, G16, G17, G22, G24, G25, G27; C34 missing; R1 |

---

## Scoring Details

### Automated Checks

| Check | T1 | T2 | T3 | P4 (best) |
|-------|----|----|----|----|
| No "Hvala" | ✅ | ✅ | ✅ | ✅ |
| No English | ✅ | ✅ | ✅ | ✅ |
| No Russian | ✅ | ✅ | ✅ | ✅ |
| Length 70-95% | ✅ 88% | ✅ 82% | ✅ 88% | ✅ 82% |
| First person | ✅ | ✅ | ✅ | ✅ |
| Present tense | ⚠️ Mixed | ⚠️ Mixed | ⚠️ Mixed | ⚠️ Mixed |

### Grammar Analysis

**Consistently UNFIXED across all configs:**
- G1: "polnica" → should be "bolnica" (NEVER fixed)
- G3: "uspodbudo" → should be "spodbudo/vzpodbudo" (rarely fixed)
- G13: direction words inconsistent
- G16: "kmalo" → should be "kmalu" (rarely fixed)
- G17: "mogo" → should be "moral" (rarely fixed)
- G23: "prublev čimprej" garbled phrase (rarely fixed)
- G25: "hori ta ljena vzgor" → "hodita navzgor" (NEVER fixed properly)
- G27: "nadreval" → "nadaljeval" (NEVER fixed)
- G28: "notakrat" → "nato/potem" (NEVER fixed)

**P4 fixed but others didn't:**
- G1 fixed to "bolnica" ✅

### Content Analysis

**Well preserved:**
- C1-C8: Hospital entrance and cabinet scenes
- C11-C14: Gyroscope discovery
- C21-C30: Stair descent details
- C37-C40: Deteriorating stairs

**Sometimes lost:**
- C34: 10 meters wide stairs (specific number)
- C6: Spray detail at cabinets

### Readability Analysis

**Major issue:** No paragraph breaks (wall of text) in ALL configs
- R1: ❌ No paragraph breaks
- R2: ✅ Sentence flow OK
- R3: ✅ Personal voice preserved
- R4: ✅ Dream logic maintained

---

## Key Findings

1. **G1 "polnica→bolnica" only fixed in P4** - the model doesn't recognize this as a spelling error
2. **G25, G27, G28 NEVER fixed** - garbled phrases preserved verbatim
3. **No paragraph structure** - consistently outputs wall of text (R1 failure)
4. **T7 produces gibberish** - completely unusable at temperature 2.0
5. **T6 over-summarizes** - loses too much content (<50% retention)
6. **Best configs: T2, P4** - similar scores around 30/40
7. **Filler words retained** - "v bistvu" often kept despite instructions

---

## Recommendation

**Not production ready.** Major issues:
- Critical G checkpoints never fixed (G25, G27, G28)
- No paragraph structure
- Best score only 30.5/40

**Suggested prompt changes:**
1. Add explicit examples for G1 (polnica→bolnica)
2. Add explicit instruction to fix garbled Slovenian phrases
3. Require paragraph breaks with "\n\n" between scenes
