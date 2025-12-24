# Diarization Journey

This document chronicles the iterative development of word-level timestamps (NFA) for the Slovenian ASR diarization pipeline.

---

## Introduction: Key Concepts

### What is Forced Alignment (NFA)?

**Problem**: ASR gives you WHAT was said, diarization gives you WHO spoke WHEN. But how do you know which WORD belongs to which SPEAKER?

**Solution**: Forced Alignment finds the precise timestamp (start/end) for each word in the transcript.

```
Without alignment:  "Hello how are you" + Speaker changes at 2.5s → ???
With alignment:     "Hello"[0.1-0.5s] "how"[0.6-0.9s] "are"[1.0-1.2s] "you"[2.6-2.9s]
                    → "Hello how are" = Speaker 1, "you" = Speaker 2
```

### CTC and Viterbi: How Alignment Works

**CTC (Connectionist Temporal Classification)**: Neural network output format that produces frame-level character probabilities (~20ms per frame).

```
Frame 1:  80% "h", 10% "a", 10% blank
Frame 2:  70% "e", 20% "h", 10% blank
Frame 3:  90% "l", 5% "e", 5% blank
...
```

**Viterbi Algorithm**: Dynamic programming algorithm that finds the optimal path through CTC probabilities given a known transcript. It answers: "Given we KNOW the word is 'hello', which frames most likely correspond to h-e-l-l-o?"

**Why CTC models struggle with short segments**: CTC needs many more audio frames than output tokens. When segment duration approaches token count (e.g., 2 seconds for 10 words), alignment fails because there aren't enough frames to distinguish between tokens.

### Why Not Use PROTOVERB for Alignment?

| Aspect | PROTOVERB | ctc-forced-aligner (MMS) |
|--------|-----------|--------------------------|
| Primary purpose | ASR (discover WHAT) | Alignment (find WHEN) |
| API | `transcribe()` only | Full alignment pipeline |
| Frame probabilities | Not exposed | Accessible |
| Pre-built solution | Would need custom Viterbi | Ready to use |

PROTOVERB is optimized for transcription, not alignment. Implementing a custom Viterbi decoder for PROTOVERB's CTC output would require significant engineering effort vs. using a library purpose-built for alignment.

### Performance Expectations

| Metric | Value | Notes |
|--------|-------|-------|
| **RTF (Real-Time Factor)** | ~5-7% | ~3-4 min processing per hour of audio |
| **Memory (GPU)** | ~10GB total | PROTOVERB 4GB + TitaNet 3GB + VAD 1GB (Phase 7: no separate MMS) |
| **Memory (CPU)** | ~6GB | Models run slower but fit in less memory |
| **Alignment accuracy** | ~95% | Word-to-speaker attribution (Viterbi via PROTOVERB) |
| **WER baseline** | 6.4-9.8% | PROTOVERB on ARTUR/SloBENCH test sets |

### Glossary

| Term | Meaning |
|------|---------|
| **NFA** | NeMo Forced Aligner (or generic "forced alignment") |
| **CTC** | Connectionist Temporal Classification - neural network output format |
| **WER** | Word Error Rate - (substitutions + insertions + deletions) / total words |
| **DER** | Diarization Error Rate - speaker attribution errors |
| **RTF** | Real-Time Factor - processing time / audio duration |
| **MMS** | Massively Multilingual Speech - Meta's 1100+ language model |
| **VAD** | Voice Activity Detection - finds speech vs silence |
| **OOV** | Out-of-Vocabulary - words not in training data |

---

## Phase 1: Initial Problem (NeMo CLI Approach)

**Commit**: Initial implementation attempt

**Problem**: The original NFA implementation called `ASR_MODEL.transcribe()` expecting forced alignment, but this just runs ASR again - no CTM files were generated.

**Root Cause**: NeMo Forced Aligner is a CLI tool (`tools/nemo_forced_aligner/align.py`), not a Python API. There is no `model.align()` or `model.forced_align()` method.

**Decision**: Abandon NeMo CLI subprocess approach due to complexity (manifest files, CTM parsing, subprocess management).

---

## Phase 2: Switch to ctc-forced-aligner

**Commit**: `d94ac68b feat(runpod): use ctc-forced-aligner library instead of NeMo CLI subprocess`

**Solution**: Use `ctc-forced-aligner` library which provides a clean Python API.

**Why ctc-forced-aligner?**
- Python functions (not CLI)
- 5X less memory than TorchAudio
- 1100+ languages via MMS model
- Simple `pip install`

**Trade-off**: Uses separate Wav2Vec2/MMS model instead of PROTOVERB (adds ~2-3GB GPU RAM).

**Initial Architecture** (ASR-first):
```
Audio → ASR (full audio) → NFA alignment → Diarization → Merge
```

**Result**: Basic word-level timestamps working.

---

## Phase 3: Critical Bug Discovery

**Problem**: On a 3-minute phone call test, Speaker 2's response "Ja, super super" **(plus more words following this section!)** was completely missing from the transcript.

**Investigation**:
1. Checked diarization output - segment existed at correct timestamp (71.90s-79.39s)
2. Checked raw ASR output - phrase was NOT in transcript
3. **Hypothesis**: ASR on long audio drops words during speaker transitions

**Breakthrough Test**: Extracted 25-second segment (65-90s) and ran ASR on just that segment.

**Result**: "Ja super super" WAS transcribed correctly!

**Root Cause Confirmed**: PROTOVERB's CTC decoding struggles with long audio (3-5 min) containing multiple speakers. Words at speaker transition boundaries get dropped.

**This was also tested manually on https://slovenscina.eu/razpoznavalnik. Transcription of preprocessed AND not preprocessed 3min phone call audio was missing large parts of male speaking voice!**

---

## Phase 4: Diarize-First Architecture

**Commit**: `feat(diarization): implement diarize-first architecture for ASR`

**Solution**: Flip the pipeline - run diarization FIRST, then ASR per segment.

**New Architecture**:
```
Audio → Diarization → Split by speaker → [ASR + NFA per segment] → Merge
```

**Implementation**:
- `extract_audio_segment()` - slice audio using soundfile
- `process_diarization_segment()` - ASR + NFA on single segment
- `process_segments_parallel()` - ThreadPoolExecutor with 4 workers
- `merge_consecutive_speaker_segments()` - combine same-speaker turns

**Result**: "Ja, super super" now captured! Processing time also improved (281s vs 666s due to parallel processing).

---

## Phase 5: ASR Quality Degradation

**New Problem**: ASR quality degraded on very short segments (1-2 seconds). PROTOVERB needs acoustic context to produce quality transcriptions.

**Example Errors**:
- "tore" instead of "torej"
- Missing words at segment boundaries

**Solution**: Quality refinements with three new configuration constants.

### 5a: Pre-merge Short Segments

**Constant**: `MIN_SEGMENT_FOR_ASR = 3.0s`

Added `merge_short_segments_for_asr()` to combine adjacent same-speaker segments shorter than 3 seconds BEFORE running ASR.

**Result**: 106 raw diarization segments → 9 segments for ASR (97 merged) (3 min phone call).

### 5b: Context Padding

**Constant**: `CONTEXT_PADDING = 0.5s`

Updated `extract_audio_segment()` to add 0.5s of audio before and after each segment boundary, giving PROTOVERB more acoustic context.

**Result**: "tore" → "torej" (correct), recovered missing "v bistvu".

### 5c: Skip NFA on Tiny Segments

**Constant**: `MIN_SEGMENT_FOR_NFA = 2.0s`

For segments shorter than 2 seconds, skip NFA (overhead not worth it, just return text without word timestamps).

---

## Phase 6: Performance Optimization

**New Problem**: NFA model was being loaded 9 times (once per segment), adding ~2s overhead per segment on CPU.

**Solution**: Cache NFA model globally like other models.

### 6a: Global NFA Model Caching

- Added `NFA_MODEL` and `NFA_TOKENIZER` global variables
- Added `load_nfa_model()` function
- Updated `load_models_parallel()` with Phase 4 for NFA loading
- Updated `run_forced_alignment()` to use cached model

**Result**: Model loaded once at startup, reused for all segments.

### 6b: Max Segment Length Cap

**Constant**: `MAX_SEGMENT_FOR_ASR = 30.0s`

Updated `merge_short_segments_for_asr()` to never create segments longer than 30 seconds (prevents NFA slowdown on very long segments).

**Result**: 9 → 11 segments (two segments split due to 30s cap).

---

## Final Pipeline

```
Phase 1:   Diarization (full audio) - TitaNet + clustering
Phase 1.5: Pre-merge short segments (<3s same-speaker)
Phase 2:   Process in parallel (ASR with 0.5s padding + NFA if >2s)
Phase 3:   Merge consecutive same-speaker turns
Phase 4:   Punctuation + Denormalization per segment
```

**Configuration Constants** (in `handler.py`):
```
MIN_SEGMENT_FOR_ASR = 3.0   # Pre-merge threshold
MAX_SEGMENT_FOR_ASR = 30.0  # Max merged segment length
CONTEXT_PADDING = 0.5       # Audio padding before/after
MIN_SEGMENT_FOR_NFA = 2.0   # Skip NFA below this
```

---

## Performance Results

| Metric | ASR-First (v2) | Diarize-First (v4) | + Optimizations (v6) |
|--------|----------------|--------------------|-----------------------|
| "Ja, super super" | ❌ Missing | ✅ Captured | ✅ Captured |
| Processing time | 666s | 281s | 315s |
| NFA model loads | 1x | 9x | 1x |
| Segments processed | N/A | 9 | 11 |

---

## Known Limitations

### ~~1. MMS Forced Aligner Licensing~~ ✅ RESOLVED (Phase 7)

**Problem**: The MMS model used by ctc-forced-aligner had **CC-BY-NC 4.0** license.

**Solution**: Switched to NeMo Forced Aligner (Apache 2.0) in December 2025 - see Phase 7.

### 2. Short Segment CTC Degradation

**Problem**: CTC models require many more frames than tokens. When segment <3s, frames ≈ tokens → alignment fails.

**Impact**: Empty or garbled transcriptions on short segments.

**Mitigation**: Pre-merge segments <3s with neighbors (implemented in Phase 5a).

### 3. Separate Model Overhead

**Problem**: Running 3 separate models (PROTOVERB + TitaNet + MarbleNet).

**Impact**: ~10GB VRAM total, multiple loading phases.

**Improvement (Phase 7)**: Removed MMS model (~2GB), NFA now reuses PROTOVERB.

**Future**: End-to-end ASR+diarization models eliminate this, but not ready for Slovenian.

### 4. No Overlap Handling

**Problem**: Current pipeline doesn't separate overlapping speakers.

**Impact**: Overlapping regions produce garbled text or dropped words.

**Solution**: pyannote has better overlap detection; could route overlaps to speech separation model.

---

## Alternatives Analysis

### Is This an ASR Problem or Diarization Problem?

**Answer: Primarily ASR, with diarization contributing.**

| Factor | Contribution to WER Gap | Fix |
|--------|------------------------|-----|
| Medical domain mismatch | ~16% | Fine-tune PROTOVERB |
| Short segment degradation | ~3-5% | Better diarization (longer segments) |
| Pipeline reconciliation | ~2-4% | Boundary padding, overlap handling |

Better diarization (pyannote) helps ~3-5%, but won't fix the 16% medical vocabulary gap.

### Diarization Alternatives

#### pyannote-audio 3.1 (Recommended)

| Aspect | pyannote | NeMo ClusteringDiarizer |
|--------|----------|------------------------|
| Segment count (30-min) | 126 | 1209 |
| Overlap detection | ✅ Superior | ⚠️ Basic |
| License | MIT | Apache 2.0 |
| Speed (RTF) | ~2.5% | ~0.03-0.05% |
| Max speakers | 3 per 10s chunk | Unlimited |

**Verdict**: pyannote produces fewer, longer segments → reduces short segment problem. **Recommended for medical phone calls** (typically 2-3 speakers).

#### NeMo Sortformer (Not Recommended)

- **Fastest** diarization (RTF ~1%)
- End-to-end single-pass
- **BLOCKER**: CC-BY-NC-4.0 license (non-commercial only)
- Max 4 speakers only

### ASR Alternatives

#### Whisper large-v3 + WhisperX

| Aspect | Whisper | PROTOVERB |
|--------|---------|-----------|
| Training data | 5M+ hours | ~1,000 hours |
| Slovenian WER | ~10-12% | 6.4% |
| Medical coverage | Broader | None |
| Hallucinations | Common (WhisperX fixes) | Rare |

**Verdict**: Test on medical calls - broader training may handle jargon better despite higher baseline WER.

#### Domain-Adapted PROTOVERB (Best Long-term)

- Fine-tune on 100-200 hours Slovenian medical data
- Cost: ~$5,000-10,000 (data labeling + compute)

### End-to-End Models (Wait 6-12 months)

| Model | Status | Slovenian Support |
|-------|--------|-------------------|
| SLIDAR | Research | ❌ |
| UME (ICLR 2025) | Research | ❌ |
| JEDIS-LLM | Research | ❌ |
| Sortformer+ASR | Research | ❌ |

**Verdict**: Promising but not production-ready for Slovenian. Wait 6-12 months.

---

## Lessons Learned

1. **Test with real data early** - The ASR word-dropping bug only appeared on 3+ minute multi-speaker audio
2. **Isolate components for debugging** - Testing ASR on extracted segment proved the words were audible
3. **Architecture matters more than tuning** - Diarize-first was the breakthrough, not parameter tweaking
4. **Trade-offs are inevitable** - Pre-merging helps ASR quality but creates longer segments for NFA
5. **Cache expensive operations** - Loading the NFA model per-segment was a 9x overhead

---

## Phase 7: MMS → NeMo NFA Migration (Licensing Fix)

**Date**: December 2025

**Problem**: ctc-forced-aligner uses MMS model with **CC-BY-NC 4.0** license - blocking commercial deployment. We also want to test different, possibly more accurate approaches.

**Research**: Explored multiple approaches:

| Approach | Verdict | Reason |
|----------|---------|--------|
| NeMo 2.x `aligner_utils.py` | ✅ **CHOSEN** | Viterbi-optimal (~95%), Apache 2.0, reuses PROTOVERB |
| Greedy CTC timestamp extraction | ❌ Rejected | Only ~70-80% accuracy (local decisions only) |
| ASRDecoderTimeStamps | ❌ Rejected | Complex API, requires manifest files |
| NeMo CLI subprocess | ❌ Rejected | Fragile, manifest parsing overhead |

**Solution**: Copy `aligner_utils.py` from NeMo 2.x main branch to `nemo_compat/` directory.

**Key Discovery**: `aligner_utils.py` does NOT exist in NeMo 1.21.0 (only in NeMo 2.x), but its dependencies (`ASRModel`, `Hypothesis`) DO exist in 1.21.0 - making the backport possible.

### Implementation Details

**New files created**:
```
nemo_compat/
├── __init__.py           # Module marker with documentation
└── aligner_utils.py      # Copied from NeMo 2.x (Apache 2.0)
```

**API usage** (critical gotchas discovered through testing):

```python
from nemo_compat.aligner_utils import (
    get_batch_variables,
    viterbi_decoding,
    add_t_start_end_to_utt_obj,
    Segment,
    Word,
)

# CRITICAL: Both audio and gt_text_batch MUST be lists of same length
log_probs, y, T, U, utt_objs, timestep_duration = get_batch_variables(
    audio=[audio_path],           # LIST, not string!
    model=ASR_MODEL,
    gt_text_batch=[transcript],   # LIST of same length
    output_timestep_duration=OUTPUT_TIMESTEP_DURATION,
)

# Viterbi alignment
alignments = viterbi_decoding(log_probs, y, T, U, viterbi_device=device)

# Add timestamps to utterance object
utt_obj = add_t_start_end_to_utt_obj(
    utt_obj=utt_objs[0],
    alignment_utt=alignments[0],
    output_timestep_duration=timestep_duration,
)

# CRITICAL: Navigate data structure correctly
# NOT: utt_obj.segments (doesn't exist!)
# YES: utt_obj.segments_and_tokens → filter for Segment → segment.words_and_tokens → filter for Word
words = []
for item in utt_obj.segments_and_tokens:
    if isinstance(item, Segment):
        for word_item in item.words_and_tokens:
            if isinstance(word_item, Word) and word_item.t_start is not None:
                words.append({
                    "word": word_item.text,
                    "start": round(word_item.t_start + segment_start, 3),
                    "end": round(word_item.t_end + segment_start, 3),
                })
```

**Data structures** (from aligner_utils.py):
```
Utterance
├── text: str
├── segments_and_tokens: List[Token | Segment]
│   ├── Token (for punctuation/spaces between segments)
│   └── Segment
│       ├── text: str
│       ├── t_start: float (after alignment)
│       ├── t_end: float (after alignment)
│       └── words_and_tokens: List[Token | Word]
│           ├── Token (for spaces between words)
│           └── Word
│               ├── text: str
│               ├── t_start: float
│               └── t_end: float
```

**Result**:
- ✅ Commercial deployment unblocked (Apache 2.0)
- ✅ ~2GB less memory (no separate MMS model)
- ✅ Faster cold starts
- ✅ Same ~95% accuracy (Viterbi algorithm)
- ✅ No romanization needed (MMS required č→c conversion)

---

## Future Improvements

### Completed
1. ~~Bake NFA model into Docker~~ ✅ (pre-downloaded in Dockerfile)
2. ~~Cache NFA model globally~~ ✅
3. ~~Switch MMS → NeMo NFA~~ ✅ (Phase 7 - December 2025)

### Recommended Roadmap

| Action | Priority | Expected WER Improvement |
|--------|----------|-------------------------|
| Benchmark pyannote 3.1 | HIGH | +3-5% |
| Test Whisper large-v3 for medical calls | MEDIUM | Unknown (broader training) |

---

## References

- **ctc-forced-aligner**: https://github.com/MahmoudAshraf97/ctc-forced-aligner
- **NeMo Forced Aligner**: https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/tools/nemo_forced_aligner.html
- **pyannote-audio 3.1**: https://huggingface.co/pyannote/speaker-diarization-3.1
- **PROTOVERB ASR**: https://clarin.si/repository/xmlui/handle/11356/2024
- **ARTUR Corpus**: https://www.clarin.si/repository/xmlui/handle/11356/1772
- **Sortformer**: https://arxiv.org/abs/2409.06656
- **WhisperX**: https://github.com/m-bain/whisperX
- **pyannote vs NeMo comparison**: https://lajavaness.medium.com/comparing-state-of-the-art-speaker-diarization-frameworks-pyannote-vs-nemo-31a191c6300

---

## License Summary

### Current Stack (Phase 7+)

| Component | License | Commercial Use |
|-----------|---------|----------------|
| NeMo NFA (aligner_utils) | Apache 2.0 | ✅ OK |
| NeMo ClusteringDiarizer | Apache 2.0 | ✅ OK |
| PROTOVERB | CC-BY-SA 4.0 | ✅ OK (with attribution) |
| pyannote-audio | MIT | ✅ OK |

### Historical / Not Used

| Component | License | Commercial Use | Status |
|-----------|---------|----------------|--------|
| ctc-forced-aligner library | BSD | ✅ OK | Removed in Phase 7 |
| MMS alignment model | CC-BY-NC 4.0 | ❌ **NO** | Removed in Phase 7 |
| Sortformer | CC-BY-NC 4.0 | ❌ **NO** | Not recommended |