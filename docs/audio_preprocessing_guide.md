# 📘 **Audio Preprocessing & Recording Best Practices Guide**

### *For Whisper / FasterWhisper transcription quality*

This document explains:

1.  **Why audio preprocessing is required**
2.  **How to preprocess recordings step-by-step**
3.  **How to fix AAC lossy compression problems**
4.  **How to configure iPhones to use lossless recording (best
    option)**
5.  **What Claude must ALWAYS do when handling your dream journal
    audio**

### Summary
> Dream journal recordings must be preprocessed because AAC is lossy and
> degrades Whisper accuracy. Preprocessing stabilizes transcription, but
> enabling iPhone LOSSLESS mode is the best long‑term solution.

------------------------------------------------------------------------

# 🧠 1. Why Preprocessing Is Required

Most mobile devices - including iPhones - record audio in **AAC lossy
format** by default:

    AAC, 44.1kHz, stereo, ~100kbps

AAC compression introduces:

-   high-frequency smearing
-   pre-echo artifacts
-   stereo phase noise
-   inconsistent loudness
-   muffled consonants
-   background hiss
-   random micro-reverberation
-   unstable low-volume regions

These issues **severely degrade accuracy** of Whisper, especially in:

-   Slavic languages
-   fast speech
-   whispered speech
-   dream-state unclear articulation
-   long continuous recordings (15--30+ minutes)

Whisper's hallucinations (mixing different Slavic languages, repeating
words, inventing phrases) become MUCH more common with lossy input.

**Therefore, preprocessing IS REQUIRED** for stable results.

------------------------------------------------------------------------

# 🎚️ 2. Required Audio Preprocessing Steps

## **Step 1 - Convert AAC/MP3 to WAV**

    ffmpeg -i input.m4a -ac 1 -ar 16000 output.wav

## **Step 2 - High-Pass Filter**

    -af "highpass=f=60"

## **Step 3 - Normalize Loudness (EBU R128)**

    -af loudnorm=I=-16:TP=-1.5:LRA=11

## **Step 4 - Trim Silence**

    -af "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-40dB:stop_periods=1:stop_silence=0.5:stop_threshold=-40dB"

## **Step 5 - Full Pipeline**

    ffmpeg -i input.m4a   -ac 1 -ar 16000   -af "highpass=f=60,loudnorm=I=-16:TP=-1.5:LRA=11,       silenceremove=start_periods=1:start_silence=0.5:start_threshold=-40dB:       stop_periods=1:stop_silence=0.5:stop_threshold=-40dB"   output_preprocessed.wav

------------------------------------------------------------------------

# ⚠️ 3. AAC Is Lossy - It Cannot Be Reversed

-   AAC permanently removes information.
-   Converting to WAV does **not** restore it.
-   Preprocessing improves quality but **cannot recover** lost clarity.

------------------------------------------------------------------------

# 📱 4. Best Fix: Use Lossless Recording on iPhone

**Settings → Voice Memos → Audio Quality → LOSSLESS**

This switches from:

    AAC (lossy)

to:

    ALAC (Apple Lossless)

Benefits:

-   No artifacts
-   Much clearer consonants
-   Better language detection
-   Drastically fewer hallucinations

------------------------------------------------------------------------

# 🚀 5. Whisper Model Recommendations

### CPU-only:

-   **large-v3 int8** (best)
-   **medium** (acceptable, worse for Slavic)

### GPU:

-   **large-v3 FP16** (best accuracy)

------------------------------------------------------------------------

# 📜 6. Claude's Required Behavior

Claude must:

-   Apply preprocessing
-   Warn about AAC issues
-   Recommend iPhone lossless mode
-   Normalize, resample, convert to mono
-   Avoid hallucinations
-   Explain decisions in comments