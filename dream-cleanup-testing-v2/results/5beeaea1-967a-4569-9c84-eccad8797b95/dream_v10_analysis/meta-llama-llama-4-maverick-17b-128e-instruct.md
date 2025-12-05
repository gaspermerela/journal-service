# maverick-17b on dream_v10_analysis

**Best:** T1 | Score: **87/100** | Status: **PASS**

---

## All Configs (Case 1: Temperature)

| Config | Params | Len% | G/25 | C/45 | R/15 | H/10 | L/5 | Total | Status |
|--------|--------|------|------|------|------|------|-----|-------|--------|
| **T1** | temp=0.0 | 51% | 24 | 37 | 15 | 10 | 1 | **87** | **PASS** |
| T6 | temp=1.5 | 47% | 24 | 38 | 15 | 10 | 0 | 87 | PASS |
| T4 | temp=0.8 | 46% | 24 | 36 | 15 | 10 | 0 | 85 | PASS |
| T5 | temp=1.0 | 36% | 23 | 37 | 15 | 10 | 0 | 85 | PASS |
| T2 | temp=0.3 | 43% | 23 | 34 | 15 | 10 | 0 | 82 | PASS |
| T7 | temp=2.0 | 41% | 19 | 35 | 15 | 10 | 0 | 79 | REVIEW |
| T3 | temp=0.5 | 34% | 22 | 30 | 15 | 8 | 0 | 75 | REVIEW |

**JSON Success Rate:** 7/7 (100%)

---

## Config-Specific Notes

### T1 (temp=0.0) - BEST
- Most deterministic output
- Only config in optimal length range (51% → L=1)
- Good balance of cleanup vs content preservation

### T6 (temp=1.5) - TIED FOR BEST
- Preserves C32: "pet, šest ali sedem" (specific people count)
- Preserves C26: "napol tek nazdolj" (movement description)
- Loses length points (47% < 50%)

### T5 (temp=1.0)
- Preserves C34: "deset metrov" (10m width detail)
- Very aggressive summarization (36%)

### T7 (temp=2.0) - RUSSIAN LEAK
- **G++ penalty:** Contains Russian word "смrдел" (-5 points)
- High temperature causes language mixing

### T3 (temp=0.5) - HALLUCINATION
- **H penalty:** Invents "Ona se ne uspe odrezati" (she fails to cut herself off)
- Original says "si ni upala skočiti" (she didn't dare to jump)
- Severe over-summarization (34%)

---

## Failures Summary (Best Config: T1)

### Grammar (G) - 1 failure

- **G13:** "nazaj dol" NOT fixed to "navzdol"

### Content (C) - 5 failures

- **C21:** "zelo globoko pod stavbo" - MISSING
- **C23:** Flat areas + corridors mixed with stairs - MISSING
- **C30:** "hodnik levo-desno" at landing - MISSING
- **C32:** "5-7 people" - simplified to "nekaj ljudi"
- **C34:** "deset metrov široke" - MISSING

### Hallucinations (H) - None in T1

### Readability (R) - All passed

---

## Scoring Details (T1)

```
AUTOMATED CHECKS:
[x] No "Hvala" (A1)
[x] No English (G+)
[x] No Russian (G++)
[x] Length: 51% → 1 point

COUNTS:
G_total: 28 | G_failed: 1 | G_passed: 27
C_total: 44 | C_failed: 5 | C_passed: 39
H_count: 0
R_score: 4/4

CALCULATION:
Content:       45 × (39/44) - 3 = 37
Grammar:       25 × (27/28) - 0 = 24
Readability:   15 × (4/4)       = 15
Hallucinations: 10 - (0 × 2)    = 10
Length:        1 (51%)          = 1
───────────────────────────────────────
TOTAL:                          87/100
```

---

## Key Findings

### 1. All configs over-summarize
- Every config is below 70% optimal length
- Only T1 reaches 51% (gets 1 length point)
- Analysis prompt causes aggressive summarization

### 2. Higher temperature preserves more specific details
- T5 (temp=1.0): Preserves C34 (10m width)
- T6 (temp=1.5): Preserves C32 (people count) + C26 (movement)
- But also introduces risks (T7 Russian, T3 hallucination)

### 3. Temp=0.0 is safest but loses details
- Most consistent output
- No language leaks or hallucinations
- But misses some specific details

### Recommendation
**Use T1 (temp=0.0)** for production - safest and achieves highest score.

T6 ties for score but higher temperature introduces risk of language mixing or hallucinations in other prompts/transcriptions.