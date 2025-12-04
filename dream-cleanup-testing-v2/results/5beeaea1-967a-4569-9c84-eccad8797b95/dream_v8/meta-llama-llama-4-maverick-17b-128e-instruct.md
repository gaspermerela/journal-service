# meta-llama/llama-4-maverick-17b-128e-instruct on dream_v8

**Best:** T5 | Score: 32/40 | Status: ITERATE

---

## All Configs

### Temperature Tests (Case 1)

| Config | Params | Len% | G | C | A | R | Total | Status | Key Failures |
|--------|--------|------|---|---|---|---|-------|--------|--------------|
| T1 | t=0.0 | 79% | 4 | 8.5 | 10 | 7 | 29.5 | ITERATE | G1, G++Russian("приходят"), G13, G16, G17, G25; R1 partial |
| T2 | t=0.3 | 77% | 4 | 8.5 | 10 | 7 | 29.5 | ITERATE | G1, G++Russian("приходят"), G13, G16, G17, G25; R1 partial |
| T3 | t=0.5 | 71% | 6.5 | 8.5 | 10 | 7 | 32 | ITERATE | G1, G13, G16, G17, G25; R1 partial |
| T4 | t=0.8 | 69% | 6 | 8 | 10 | 7 | 31 | ITERATE | G1, G5, G13, G16, G24; C34 missing width; R1 partial |
| T5 | t=1.0 | 81% | 6.5 | 8.5 | 10 | 7 | 32 | ITERATE | G1, G13, G16, G17; R1 partial |
| T6 | t=1.5 | - | - | - | - | - | - | SKIP | Not in cache |
| T7 | t=2.0 | 54% | 3 | 6 | 10 | 5 | 24 | ITERATE | Degraded text quality; garbled ending; C+++ |

### Top-p Tests (Case 2)

| Config | Params | Len% | G | C | A | R | Total | Status | Key Failures |
|--------|--------|------|---|---|---|---|-------|--------|--------------|
| P1 | p=0.1 | 82% | 4 | 8.5 | 10 | 7 | 29.5 | ITERATE | G1, G++Russian("приходят"), G13, G16, G17, G25; R1 partial |
| P2 | p=0.3 | - | - | - | - | - | - | SKIP | Not in cache |
| P3 | p=0.5 | - | - | - | - | - | - | SKIP | Not in cache |
| P4 | p=0.7 | - | - | - | - | - | - | SKIP | Not in cache |
| P5 | p=0.9 | - | - | - | - | - | - | SKIP | Not in cache |
| P6 | p=1.0 | - | - | - | - | - | - | SKIP | Not in cache |

---

## Scoring Details

### Automated Checks

| Check | T1 | T3 | T5 (best) |
|-------|----|----|-----------|
| No "Hvala" | ✅ | ✅ | ✅ |
| No English | ✅ | ✅ | ✅ |
| No Russian | ❌ "приходят" | ✅ | ✅ |
| Length 70-95% | ✅ 79% | ✅ 71% | ✅ 81% |
| First person | ✅ | ✅ | ✅ |
| Present tense | ✅ | ✅ | ✅ |

### Grammar Analysis

**Critical issue: Russian word leak (G++)**
- T1, T2, P1 contain "приходят" (Russian for "come/arrive")
- This is a -2 penalty each time
- T3, T5 do NOT have this issue

**Consistently UNFIXED:**
- G1: "polnica" → "bolnica" (never fixed, keeps "polnica")
- G13: direction words inconsistent
- G16: "kmalo" → "kmalu" (sometimes fixed)
- G17: "mogo" → "moral" (rarely fixed)

**Better than llama-3.3:**
- G25: "hori ta ljena vzgor" → properly fixed to "hodita vzgor" in most configs ✅
- G27, G28: Better handling of garbled phrases
- Better tense consistency (present tense maintained)

### Content Analysis

**Well preserved:**
- C1-C10: Hospital and cabinet scenes ✅
- C11-C14: Gyroscope discovery ✅
- C15-C20: Hiding from people ✅
- C21-C30: Stair descent ✅
- C31-C36: Different environment ✅
- C37-C44: Giant gyroscope and young woman ✅

**Sometimes lost:**
- C34: 10 meters width - sometimes omitted or different number
- C3: Timeline "preden" sometimes changed

### Readability Analysis

**Better than llama-3.3:**
- R1: ⚠️ Partial paragraph structure (some breaks, not complete)
- R2: ✅ Good sentence flow
- R3: ✅ Personal voice well preserved
- R4: ✅ Dream logic maintained

---

## Key Findings

1. **Russian word contamination in T1, T2, P1** - "приходят" appears (G++ -2 penalty)
2. **T3 and T5 are cleanest** - No Russian, good grammar fixes
3. **G1 "polnica" NEVER fixed** - Same issue as llama-3.3
4. **Better garbled phrase handling** - G25, G27, G28 often fixed correctly
5. **Partial paragraph structure** - Some "\n\n" breaks, better than llama-3.3
6. **T7 degrades significantly** - Garbled ending, loses coherence
7. **Content preservation excellent** - All major scenes preserved

---

## Comparison with llama-3.3-70b

| Aspect | llama-3.3 | maverick | Winner |
|--------|-----------|----------|--------|
| Best Score | 30.5/40 | 32/40 | **maverick** |
| Russian leak | Never | T1,T2,P1 | llama-3.3 |
| G25 fix | Never | Often | **maverick** |
| Paragraphs | Never | Partial | **maverick** |
| Tense consistency | Mixed | Good | **maverick** |
| Content preservation | Good | Good | Tie |

---

## Recommendation

**Better than llama-3.3 but not production ready.**

**Use T3 or T5** - avoid T1, T2, P1 due to Russian contamination.

**Issues to address:**
1. G1 "polnica→bolnica" still not fixed
2. Paragraph structure incomplete
3. Some configs have Russian word leaks

**Suggested prompt changes:**
1. Explicitly mention Slovenian-only output (no Russian/Cyrillic)
2. Add G1 example in prompt
3. Require complete paragraph separation with blank lines
