# openai/gpt-oss-120b on dream_v9_slo

← [Back to dream_v9_slo](./README.md) | [Back to Index](../README.md)

---

**Status:** FAIL | **Best Score:** 51/100 (P1)
**Cache:** `cache/5beeaea1-967a-4569-9c84-eccad8797b95/dream_v9_slo/openai-gpt-oss-120b/`
**Test Date:** 2025-12-04
**Raw Length:** 5,051 characters

---

## CASE 1: Temperature Only (top_p = null)

**Winner:** T3 (temp=0.5) - 50/100

### Summary Table

| Config | Temp | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|------|------|------|------|------|------|-----|-------|--------|
| T1 | 0.0 | 39% | 16 | 24 | 11 | 6 | 0 | **49** | FAIL |
| T2 | 0.3 | 42% | 16 | 25 | 11 | 6 | 0 | **50** | FAIL |
| **T3** | 0.5 | 45% | 16 | 26 | 11 | 6 | 0 | **50** | FAIL |
| T4 | 0.8 | 48% | 15 | 26 | 11 | 6 | 0 | **50** | FAIL |
| T5 | 1.0 | 51% | 15 | 26 | 11 | 6 | 1 | **51** | FAIL |
| T6 | 1.5 | 49% | 14 | 25 | 11 | 6 | 0 | **48** | FAIL |
| T7 | 2.0 | 56% | 12 | 22 | 8 | 4 | 1 | **43** | FAIL |

### Config Analysis

#### T1 (temp=0.0) - 49/100
- **Length:** 1984 chars (39%) - SEVERE under-generation
- **Content:** Massive content loss, many checkpoints missing
- **Grammar:** G1 fail (polnica), some cleanup applied
- **Readability:** Good paragraph breaks
- **Hallucination:** "jaz skočim in ji pomagam" (H1 fail - NOT in original)
- **Artifacts:** KEEPS "Zdravstveno sem pripravljen" (A2 fail)

#### T3 (temp=0.5) - 50/100
- **Length:** 2261 chars (45%) - SEVERE under-generation
- **Content:** Better than T1 but still significant loss
- **Grammar:** G1 fail (polnica)
- **Hallucination:** "jaz pa skočim in ji pomagam" (H1 fail)
- **Artifacts:** A2 fail

#### T7 (temp=2.0) - 43/100
- **Length:** 2831 chars (56%) - borderline severe
- **Content:** Worst due to randomness
- **Grammar:** Many issues
- **Hallucination:** Multiple invented transitions
- **Incoherent:** High temperature degrades quality

---

## CASE 2: Top-p Only (temperature = null)

**Winner:** P1 (top_p=0.1) - 51/100

### Summary Table

| Config | top_p | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|-------|------|------|------|------|------|-----|-------|--------|
| **P1** | 0.1 | 51% | 16 | 25 | 11 | 6 | 1 | **51** | FAIL |
| P2 | 0.3 | 50% | 16 | 25 | 11 | 6 | 1 | **51** | FAIL |
| P3 | 0.5 | 49% | 16 | 25 | 11 | 6 | 0 | **50** | FAIL |
| P4 | 0.7 | 47% | 15 | 24 | 11 | 6 | 0 | **48** | FAIL |
| P5 | 0.9 | 45% | 14 | 23 | 11 | 6 | 0 | **46** | FAIL |
| P6 | 1.0 | 42% | 13 | 22 | 11 | 6 | 0 | **44** | FAIL |

### Config Analysis

#### P1 (top_p=0.1) - 51/100 BEST
- **Length:** 2561 chars (51%) - borderline severe
- **Content:** Significant loss but preserves main storyline
- **Grammar:** G1 fail (polnica), cleaner output overall
- **Readability:** Excellent paragraph structure
- **Hallucination:** "jaz pa skočim in je bilo vse v redu" - implies helping (H1 fail)
- **Artifacts:** "Zdravstveno sem pripravljen" retained (A2 fail)

#### P3 (top_p=0.5) - 50/100
- **Length:** 2475 chars (49%) - severe
- **Content:** Similar to P1
- **Note:** "jaz skočim namesto nje" - explicitly says he jumped FOR her (H1 fail)

---

## Failures Summary (P1 - Best Config)

### Grammar (G) - 9 failures = 16/25
- **G1:** "polnica" NOT fixed to "bolnica"
- **G2:** "pretličju" NOT fixed to "pritličju"
- Most garbled phrases removed due to over-summarization (not a positive)

### Content (C) - 20 failures = 25/45
- **C3:** "okoli četrte ali pete ure" → over-simplified to generic time
- **C7:** "zvok, ki mi vzpodbuja in govori" detail simplified
- **C10:** Cabinet big-doors-vs-small detail lost
- **C12:** "vidim seveda veliko manj podrobnosti" → LOST
- **C16:** "v začetku mislim" internal thought → LOST
- **C21:** "tako kot že velik razdelek" → LOST
- **C23:** Flat areas mixed with stairs detail → LOST
- **C26:** "napol tek" (half-running) detail → LOST
- **C28:** Falling detail simplified
- **C29:** "nisem mogel stopnic držati" → LOST
- **C30:** "hodnik levo-desno" corridor detail → LOST
- **C33:** Stairs description simplified
- **C36:** Women unbothered detail simplified
- **C39:** "odmaknem se nekaj metrov stran" → LOST
- **C40:** Ground/grass transition detail lost

### Hallucinations (H) - 2 failures = 6/10
- **H1:** "jaz pa skočim in je v redu" - implies he jumped WITH/FOR her
  - Original: "Jaz sem takoj skočil in je bilo vse v redu" (he jumped first, alone)
  - Model changes meaning: adds "helping" action NOT in original
- **H2:** Lost ending "in nato naprej se ne spomnim več veliko od tega dela"

### Readability (R) - 1 failure = 11/15
- **R1:** Has paragraph breaks (PASS)
- **R2:** Sentence flow good (PASS)
- **R3:** Personal voice preserved (PASS)
- **R4:** Dream logic altered by summarization

### Artifacts (A)
- **A2 FAIL:** "Zdravstveno sem pripravljen" retained

### Length (L) - 1/5
- 51% length is borderline severe (should be 70-95%)

---

## Key Finding

**gpt-oss-120b completely ignores the Slovenian prompt instruction "NE povzemaj" (DO NOT summarize).**

Critical issues:
1. **Severe over-summarization:** 39-51% length (should be 60-95%)
2. **Hallucination:** Invents "helping" action that changes dream meaning
3. **Artifact retention:** Keeps "Zdravstveno sem pripravljen" noise
4. **Content loss:** Multiple specific details lost due to aggressive summarization

The model appears to treat Slovenian prompts as suggestions rather than rules. It applies English-language summarization behavior regardless of explicit instructions in Slovenian.

---

## Production Recommendation

**gpt-oss-120b is NOT recommended for dream_v9_slo prompt.**

- Best score: **51/100** (FAIL threshold: <80)
- All configs FAIL
- Severe hallucination (changes dream meaning)
- Ignores "NE povzemaj" instruction

This model should NOT be used with Slovenian prompts for dream cleanup. The combination of over-summarization and meaning-changing hallucinations makes it unsuitable for this task.

---

## Detailed Example (P1 vs Original)

**Original ending:**
> "Spomnim se, da smo prišli do enega dela, kjer je bilo treba malo skočiti čez nek predel, kjer ni bilo stopnic, torej vljudno nekakšna zemlja in mokro je bilo, ampak ona si ni upala skočiti. Jaz sem takoj skočil in je bilo vse v redu in nato naprej se ne spomnim več veliko od tega dela."

**P1 output:**
> "Prišla je do dela, kjer je treba skočiti čez mokro zemljo; ni se upala, jaz pa skočim in je v redu."

**Problems:**
1. Lost: "torej vljudno nekakšna zemlja" detail
2. Lost: "in nato naprej se ne spomnim več veliko od tega dela"
3. Changed meaning: implies he helped her (original: he jumped, she stayed)
