# openai/gpt-oss-120b on dream_v8

**Best:** T1 | Score: 28/40 | Status: ITERATE

---

## All Configs

### Temperature Tests (Case 1)

| Config | Params | Len% | G | C | A | R | Total | Status | Key Failures |
|--------|--------|------|---|---|---|---|-------|--------|--------------|
| T1 | t=0.0 | 58% | 7 | 5 | 8 | 8 | 28 | ITERATE | C+++ (over-summarized); C++ hallucination; A2 kept; G2 |
| T2 | t=0.3 | - | - | - | - | - | - | SKIP | Not in cache |
| T3 | t=0.5 | 49% | 7 | 4 | 10 | 8 | 29 | ITERATE | C+++ (severely over-summarized <50%); many C failures |
| T4 | t=0.8 | - | - | - | - | - | - | SKIP | Not in cache |
| T5 | t=1.0 | - | - | - | - | - | - | SKIP | Not in cache |
| T6 | t=1.5 | - | - | - | - | - | - | SKIP | Not in cache |
| T7 | t=2.0 | 58% | 5 | 4 | 10 | 6 | 25 | ITERATE | C++ hallucinations; garbled phrases; C+++ |

### Top-p Tests (Case 2)

| Config | Params | Len% | G | C | A | R | Total | Status | Key Failures |
|--------|--------|------|---|---|---|---|-------|--------|--------------|
| P1 | p=0.1 | 52% | 7 | 5 | 10 | 8 | 30 | ITERATE | C+++ (over-summarized); many C details lost |
| P2 | p=0.3 | - | - | - | - | - | - | SKIP | Not in cache |
| P3 | p=0.5 | - | - | - | - | - | - | SKIP | Not in cache |
| P4 | p=0.7 | - | - | - | - | - | - | SKIP | Not in cache |
| P5 | p=0.9 | - | - | - | - | - | - | SKIP | Not in cache |
| P6 | p=1.0 | - | - | - | - | - | - | SKIP | Not in cache |

---

## Scoring Details

### Automated Checks

| Check | T1 | T3 | P1 |
|-------|----|----|-----|
| No "Hvala" | ✅ | ✅ | ✅ |
| No English | ✅ | ✅ | ✅ |
| No Russian | ✅ | ✅ | ✅ |
| Length 70-95% | ❌ 58% | ❌ 49% | ❌ 52% |
| First person | ⚠️ shifts | ✅ | ✅ |
| Present tense | ✅ | ✅ | ✅ |

### Grammar Analysis

**Best grammar fixes of all models:**
- G1: ✅ Fixed "polnica" → "bolnica" (T1, P1)
- G2: ❌ "pretličju" sometimes kept
- G6: ✅ "praktično" correct
- G13: ✅ Direction words often correct ("navzdol")
- G25: ✅ Often fixes garbled phrases

**Grammar score higher due to:**
- Better spelling corrections overall
- More consistent tense usage
- Cleaner sentence structure

### Content Analysis

**CRITICAL ISSUE: Over-summarization (C+++)**

All configs fail the 70-95% length requirement:
- T1: 58% (lost 42% of content)
- T3: 49% (lost 51% of content)
- P1: 52% (lost 48% of content)

**Content lost:**
- C6: Spray detail often simplified
- C7: Sound description reduced
- C22: Stair descriptions shortened
- C23: Flat areas + corridors detail lost
- C26: Movement detail reduced
- C34: 10 meters width sometimes kept
- Many scene transitions compressed

**Hallucination detected (C++):**
- T1: "Zdravstveno, da sem pripravljen" added at start (NOT in original)
- T7: "polna svetlobe" (full of light) - original says DARK
- T7: Various invented phrases

### Readability Analysis

**Best paragraph structure of all models:**
- R1: ✅ Excellent paragraph breaks with "\n\n"
- R2: ✅ Good sentence flow
- R3: ⚠️ Sometimes shifts to third person
- R4: ✅ Dream logic maintained

---

## Key Findings

1. **Severe over-summarization** - All configs under 60% length (C+++ violation)
2. **Best grammar fixes** - G1 "polnica→bolnica" FIXED (only model to do this consistently)
3. **Hallucinations present** - Adds content not in original (C++ violation)
4. **Excellent paragraph structure** - Best R1 scores
5. **Best for structure, worst for content** - Opposite trade-off from other models
6. **A2 sometimes kept** - "Zdravstveno" intro preserved in T1

---

## Comparison with Other Models

| Aspect | llama-3.3 | maverick | gpt-oss | Winner |
|--------|-----------|----------|---------|--------|
| Best Score | 30.5/40 | 32/40 | 30/40 | **maverick** |
| G1 fix | Rarely | Never | **Yes** | gpt-oss |
| Content preservation | **Good** | **Good** | Poor | llama/maverick |
| Over-summarization | No | No | **Yes** | llama/maverick |
| Paragraphs | Never | Partial | **Full** | gpt-oss |
| Hallucinations | No | No | **Yes** | llama/maverick |

---

## Recommendation

**Not recommended for production.**

**Major issues:**
1. Over-summarization loses 40-50% of dream content
2. Hallucinations add incorrect information
3. Trade-off not acceptable: good structure but poor content

**Potential use case:**
- Could be used as a second-pass "formatter" after content is cleaned by another model
- Best for paragraph structure learning/reference

**Do NOT use for:**
- Primary dream cleanup
- Content that needs detail preservation
- Any task where hallucinations are unacceptable

---

## Suggested Next Steps

1. Do NOT prioritize further testing with gpt-oss-120b
2. Focus on maverick T3/T5 for best results
3. Consider hybrid approach: maverick for content + gpt-oss structure guidance
