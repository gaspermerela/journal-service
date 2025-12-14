# Slovenian STT Cleanup with LLMs: A Comprehensive Guide

**For Slovenian dream journal transcriptions from Whisper, the most effective approach combines GaMS-9B (a Slovenian-specific LLM) with carefully structured prompts using explicit anti-transformation rules, few-shot examples, and chunked processing.** The key problems—person changes (jaz→oni), length variance, and diacritic loss—stem from LLMs defaulting to "interpretation" rather than "editing" behavior, which can be corrected through specific prompting techniques and constrained decoding. GDPR-compliant deployment is achievable via Mistral AI's EU-hosted API or self-hosted solutions using vLLM on EU cloud infrastructure.

---

## Table of Contents

1. [Why LLMs Transform Instead of Edit](#why-llms-transform-instead-of-edit-your-transcripts)
2. [Prompt Engineering Techniques](#prompt-engineering-techniques-that-actually-work)
3. [Diacritic Restoration Strategies](#diacritic-restoration-strategies)
4. [Best Models for Slovenian](#best-models-for-slovenian-text-cleanup)
5. [GDPR-Compliant Deployment](#gdpr-compliant-deployment-options)
6. [CLASSLA Preprocessing Pipeline](#classla-essential-preprocessing-pipeline)
7. [Production Pipeline](#recommended-production-pipeline)
8. [Constrained Decoding](#preventing-hallucination-through-constrained-decoding)
9. [Academic Resources](#academic-resources-for-further-development)
10. [Source Links](#source-links)

---

## Why LLMs Transform Instead of Edit Your Transcripts

The core issue isn't model capability but **task framing**. When LLMs receive text for "cleanup," they often interpret this as permission to improve, paraphrase, or summarize—behaviors trained into them during instruction tuning. Your observed problems have specific causes:

**Person changes** (jaz→oni) occur because LLMs trained predominantly on third-person narrative text default to that style. The model sees first-person text and "normalizes" it to its training distribution, especially when processing dream content that could be interpreted as either personal narrative or story.

**Length variance at temperature=0** (55-78%) happens despite greedy decoding because of floating-point non-determinism in GPU operations, Mixture-of-Experts routing variability, and hardware differences when using API providers. [Research shows](https://www.vincentschmalbach.com/does-temperature-0-guarantee-deterministic-llm-outputs/) even fixed seeds produce "alarming degrees of variation" across identical runs. See also: [Non-Determinism of "Deterministic" LLM Settings (arXiv)](https://arxiv.org/html/2408.04667v5).

**Diacritic loss** stems from two sources: Whisper sometimes strips diacritics during transcription (outputting "cas" instead of "čas"), and LLMs may fail to restore them or introduce encoding errors during processing.

---

## Prompt Engineering Techniques That Actually Work

### Explicit Anti-Transformation Rules

The most effective approach frames the LLM as an **editor, not an author**. This tested system prompt from [transcript cleanup practitioners](https://den.dev/blog/how-i-automated-podcast-transcription-with-local-ai/) consistently prevents unwanted transformations:

```
You are an experienced editor specializing in cleaning up transcripts, but you 
NEVER add your own text. You are an EDITOR, not an AUTHOR—this transcript may 
be quoted later.

CRITICAL RULES:
- NEVER change grammatical person. If speaker says "jaz" (I), keep "jaz"
- NEVER change subject pronouns (jaz→oni is FORBIDDEN)
- This is a FIRST-PERSON journal entry—maintain first-person throughout
- Preserve speaker's perspective exactly as spoken
- Output must be 90-110% of input length—this is CLEANUP, not SUMMARIZATION
```

For Slovenian specifically, add native-language constraints:

```
Ta je prepis dnevnika sanj v slovenščini, zapisan v PRVI OSEBI.
Ohrani prvo osebo (jaz, sem, imam) - NIKOLI ne spreminjaj v tretjo osebo.
```

### Length Preservation Through Structured Output

Force consistent output by requiring JSON with validation fields:

```json
{
  "cleaned_text": "...",
  "input_word_count": 150,
  "output_word_count": 147,
  "length_ratio": 0.98,
  "person_check": "first_person_maintained"
}
```

This approach makes length violations explicit and detectable. If `length_ratio` falls below **0.75**, reject the output and retry with stricter instructions or fall back to punctuation-only fixes.

### Few-Shot Examples for Slovenian

Few-shot prompting outperforms zero-shot for transcript cleanup because it demonstrates exactly what "cleanup" means versus "rewriting." **Two to five examples** is optimal—more wastes tokens without improving results.

```
Example 1:
INPUT: "jaz sem sanjal da sem letel nad gozdom bilo je cudovito"
OUTPUT: "Jaz sem sanjal, da sem letel nad gozdom. Bilo je čudovito."

Example 2:
INPUT: "potem sem se zbudil in videl sem da je se temno"
OUTPUT: "Potem sem se zbudil in videl sem, da je še temno."

Example 3:
INPUT: "v sanjah sem bil na plazi morje je bilo zelo mirno jaz sem plaval"
OUTPUT: "V sanjah sem bil na plaži. Morje je bilo zelo mirno. Jaz sem plaval."

Now clean this transcript following the same pattern:
INPUT: [actual transcript]
OUTPUT:
```

Notice how examples demonstrate: diacritic restoration (cudovito→čudovito), punctuation addition, capitalization, and **consistent first-person preservation**.

### Chunk Processing Prevents Hallucination

Research consistently shows that processing **chunks under 500 words** dramatically reduces hallucinations and unwanted transformations. Longer inputs trigger the model's summarization tendencies. For dream journals, chunk by natural paragraph breaks or timestamp segments from Whisper.

---

## Diacritic Restoration Strategies

Slovenian diacritics (č, š, ž) require explicit handling because Whisper sometimes strips them and LLMs may not reliably restore them.

### Prompt-Based Restoration

Include explicit restoration rules with common patterns:

```
DIACRITIC RESTORATION (Slovenian č, š, ž):
- "cas" → "čas" (time)
- "cez" → "čez" (across)
- "zivljenje" → "življenje" (life)
- "clovek" → "človek" (person)
- "zelel" → "želel" (wanted)
- "vec" → "več" (more)
- "ze" → "že" (already)
- "se" → "še" when meaning "still/yet"

When uncertain, preserve original form rather than guessing.
```

### Dedicated Restoration Models

For highest accuracy, use a **separate diacritic restoration step**. Academic research shows transformer-based approaches achieve **98%+ accuracy** on South Slavic languages. Available tools include:

- **REDI** (`clarinsi/redi`): Specialized for Croatian, Serbian, Slovenian diacritic restoration
- **ReLDIanno**: [Web service at CLARIN Slovenia](https://www.clarin.si/info/k-centre/web-services-documentation/) for Slovenian text processing
- **BERT-based restoration**: Following [Czech methodology from UFAL Prague](https://ar5iv.labs.arxiv.org/html/2105.11408) achieves state-of-the-art results

The [LREC 2016 paper](https://aclanthology.org/L16-1573/) by Ljubešić et al. specifically addresses corpus-based diacritic restoration for Slovenian, Croatian, and Serbian, with freely available systems.

### Research on Diacritics

- [Automatic Diacritic Restoration With Transformer Model Based Neural Machine Translation for East-Central European Languages](https://www.researchgate.net/publication/349645838_Automatic_Diacritic_Restoration_With_Transformer_Model_Based_Neural_Machine_Translation_for_East-Central_European_Languages)
- [Corpus-Based Diacritic Restoration for South Slavic Languages (ACL Anthology)](https://aclanthology.org/L16-1573/)

---

## Best Models for Slovenian Text Cleanup

### GaMS-9B-Instruct: Purpose-Built for Slovenian

The **GaMS (Generative Model for Slovene)** family, developed by University of Ljubljana's CJVT, represents the state-of-the-art for Slovenian. Trained on **47 billion tokens** of Slovenian, English, and Croatian-Bosnian-Serbian text, GaMS-9B-Instruct outperforms base Gemma 2 and other models on Slovenian benchmarks.

- **HuggingFace**: [cjvt/GaMS-9B-Instruct](https://huggingface.co/cjvt/GaMS-9B-Instruct) (also see [cjvt/OPT_GaMS-1B](https://huggingface.co/cjvt/OPT_GaMS-1B) for smaller variant)
- **Memory**: ~10GB with 4-bit quantization
- **Test interface**: [povejmo.si/klepet](https://povejmo.si/klepet)
- **Advantage**: Native tokenizer handles Slovenian morphology correctly
- **Overview**: [Slovenian Language Technologies Overview (GitHub)](https://github.com/clarinsi/Slovenian-Language-Technologies-Overview)

### Gemma 2: Best General-Purpose Option

If you need multilingual support or GaMS isn't suitable, **Gemma 2 27B** achieves the highest accuracy among major open-source models for Slavic languages (**0.694 average accuracy**) with remarkably consistent performance across different Slavic languages. The 9B variant is "coherent enough to use" for most tasks and runs on consumer hardware.

Gemma's superior tokenizer handles Slavic scripts efficiently rather than degrading to character-level tokenization like Llama models.

**Resources:**
- [Google Open Sources 27B Parameter Gemma 2 Language Model (InfoQ)](https://www.infoq.com/news/2024/07/google-gemma-2/)
- [LLM Practitioner's Guide: Gemma, a Game-Changing Multilingual LLM](https://www.shelpuk.com/post/llm-practitioner-s-guide-gemma-a-game-changing-multilingual-llm)
- [Towards Multilingual LLM Evaluation for European Languages (arXiv)](https://arxiv.org/html/2410.08928v2)

### Model Comparison for Slavic Languages

| Model | Slavic Performance | Slovenian-Specific | Self-Hostable |
|-------|-------------------|-------------------|---------------|
| **GaMS-9B** | Excellent | Yes (native) | Yes |
| **Gemma 2 27B** | Excellent | Good | Yes |
| **Mistral/Mixtral** | Good | Good | Yes |
| **Llama 3.1 70B** | Moderate | Moderate | Yes |
| **Qwen 2.5** | Limited | Limited | Yes |

For comparison: Llama 3.1-70B achieves **0.680 on Slavic vs 0.745 on Germanic** languages—a notable performance gap. Smaller Llama models struggle significantly with low-resource Slavic languages.

---

## GDPR-Compliant Deployment Options

### Mistral AI: Recommended EU-Hosted API

**[Mistral AI](https://mistral.ai/)** (Paris, France) offers the strongest GDPR compliance among commercial LLM providers:

- Fully EU-based, **not subject to US CLOUD Act**
- All services hosted exclusively in EU data centers
- Data Processing Agreements available
- Zero Data Retention option for Enterprise tier
- Pricing: Mixtral 8x7B at **$0.70/1M tokens** (excellent for Slovenian cleanup)

For your use case, **Mistral Small** ($1.00/$3.00 per million input/output tokens) provides good multilingual support at reasonable cost.

**Resources:**
- [Mistral AI Solution Overview: Models, Pricing, and API](https://obot.ai/resources/learning-center/mistral-ai/)
- [Mistral AI Pricing: Comprehensive Guide to Models and Costs](https://merlio.app/blog/mistral-ai-pricing-guide)

### Self-Hosted Production Deployment

For maximum data control, self-host using **vLLM** on EU cloud infrastructure:

**vLLM advantages**:
- PagedAttention for efficient memory management
- **793 tokens/second** throughput (vs Ollama's 41 TPS)
- 80ms P99 latency at peak load
- OpenAI-compatible API

```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --model cjvt/GaMS-9B-Instruct \
  --port 8000
```

**Resources:**
- [TGI vs. vLLM: Making Informed Choices for LLM Deployment (Medium)](https://medium.com/@rohit.k/tgi-vs-vllm-making-informed-choices-for-llm-deployment-37c56d7ff705)
- [Ollama vs. vLLM: A deep dive into performance benchmarking (Red Hat)](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)
- [Best GPU for Local LLM: Complete Hardware Guide](https://nutstudio.imyfone.com/llm-tips/best-gpu-for-local-llm/)

**EU Cloud Options:**
- **[Scaleway](https://www.scaleway.com/en/generative-apis/)** (France): L40S GPUs, €0.20-0.90/1M tokens for hosted APIs
- **OVHcloud** (France): H100 instances, AI Endpoints with 40+ open-source models
- **AWS Frankfurt** (eu-central-1): A100/H100 instances with spot pricing

**Hardware requirements** for GaMS-9B or similar 7-9B models: **12-16GB VRAM** at 4-bit quantization (RTX 4070 or better).

### Avoid for GDPR Compliance

- **Groq**: US-based, Norway data center not yet operational
- **OpenAI direct API**: US company, CLOUD Act concerns
- **Azure OpenAI**: Requires specific "Data Zone Standard (EUR)" configuration—"Worldwide Standard" does NOT guarantee EU residency

---

## CLASSLA: Essential Preprocessing Pipeline

Before LLM cleanup, process transcripts through **[CLASSLA](https://github.com/clarinsi/classla)**, a specialized NLP pipeline for South Slavic languages with a **spoken text mode** designed for transcriptions:

```python
import classla

# Download Slovenian spoken model (ideal for STT output)
classla.download('sl', type='spoken')
nlp = classla.Pipeline('sl', type='spoken')

# Process transcript with disfluencies like "eee"
doc = nlp("to je igra, ki jo igrajo, eee, ti, eee, člani družine.")
```

CLASSLA provides:
- **94% morphosyntactic tagging accuracy**, 99% lemmatization
- Handling of disfluencies (um, uh, eee)
- Non-standard text mode for colloquial speech
- Tokenization, POS tagging, NER, dependency parsing

This preprocessing normalizes text structure before LLM cleanup, reducing the chances of unwanted transformations.

**Resources:**
- [CLASSLA GitHub Repository](https://github.com/clarinsi/classla)
- [ReLDIanno Web Services Documentation (CLARIN Slovenia)](https://www.clarin.si/info/k-centre/web-services-documentation/)

---

## Recommended Production Pipeline

Based on research and practitioner experience, here's the optimal workflow for Slovenian dream journal cleanup:

```
Audio
  ↓
Whisper large-v3 (language="sl")
  ↓
Chunk into ≤500 word segments
  ↓
CLASSLA (type='spoken') preprocessing
  ↓
GaMS-9B-Instruct cleanup
  • Few-shot examples
  • JSON output with length validation
  • Explicit anti-transformation rules
  ↓
Diacritic restoration (REDI or prompt-based)
  ↓
Length validation (reject if <75%)
  ↓
Final transcript
```

### Key Parameters

```python
# LLM settings for maximum consistency
temperature = 0
top_p = 1.0  # Disable nucleus sampling
max_tokens = input_length * 1.2  # Allow slight expansion only

# Validation thresholds
min_length_ratio = 0.75
max_length_ratio = 1.15
required_person = "first"  # Check for "jaz", "sem", "moj"
```

---

## Preventing Hallucination Through Constrained Decoding

Academic research on reducing LLM hallucinations in text cleanup offers a powerful technique: **N-best constrained decoding**. The [N-best T5 approach](https://arxiv.org/html/2303.00456) constrains LLM output to tokens present in Whisper's N-best hypotheses list or ASR lattice, achieving **12% additional WER reduction** while preventing acoustically-implausible outputs.

For implementation:
1. Configure Whisper to output N-best hypotheses (typically 5-10)
2. Extract unique tokens from all hypotheses
3. Constrain LLM decoding to only these tokens plus punctuation
4. This prevents the LLM from generating words that weren't actually spoken

This approach directly addresses your "jaz→oni" problem—if "oni" never appeared in any Whisper hypothesis, it cannot appear in the output.

**Resources:**
- [ASR Error Correction using Large Language Models (arXiv)](https://arxiv.org/html/2409.09554v2)
- [N-best T5: Robust ASR Error Correction using Multiple Input Hypotheses and Constrained Decoding Space (arXiv)](https://arxiv.org/html/2303.00456)
- [Enhancing Speech Recognition (OpenReview)](https://openreview.net/pdf/7ca9a69e2094fe214442250fb19b171a57fe882f.pdf)

---

## Academic Resources for Further Development

The most relevant papers for your use case:

| Paper | Description | Link |
|-------|-------------|------|
| **HyPoradise** (Chen et al., NeurIPS 2023) | Open benchmark for LLM-based ASR correction with 334K hypothesis-transcription pairs. Fine-tuned LLaMA-13B achieves 86% WER reduction. | [Paper](https://arxiv.org/abs/2309.15701) |
| **Corpus-Based Diacritic Restoration for South Slavic** (Ljubešić et al., LREC 2016) | Direct methodology for Slovenian diacritics with freely available systems. | [ACL Anthology](https://aclanthology.org/L16-1573/) |
| **N-best T5** (2023) | Constrained decoding approach preventing hallucinations by limiting output vocabulary to acoustically-plausible alternatives. | [arXiv](https://arxiv.org/html/2303.00456) |
| **GaMS Models** (Vreš et al., 2024) | Technical documentation for Slovenian-specific LLMs from the POVEJMO project. | [GitHub Overview](https://github.com/clarinsi/Slovenian-Language-Technologies-Overview) |
| **Diacritics Restoration using BERT** | Analysis on Czech language, applicable to Slovenian. | [arXiv](https://ar5iv.labs.arxiv.org/html/2105.11408) |
| **Multilingual LLM Evaluation for European Languages** | Comprehensive benchmarks including Slavic languages. | [arXiv](https://arxiv.org/html/2410.08928v2) |

The Slovenian NLP ecosystem through **[CLARIN.SI](https://www.clarin.si/)** provides extensive resources including the RSDO-DS2-ASR-E2E 2.0 model (5.58% WER Conformer-CTC ASR), CLASSLA pipeline, and comprehensive corpora for further fine-tuning.

---

## Source Links

### LLM Temperature and Determinism
- [Does Temperature 0 Guarantee Deterministic LLM Outputs?](https://www.vincentschmalbach.com/does-temperature-0-guarantee-deterministic-llm-outputs/)
- [Non-Determinism of "Deterministic" LLM Settings (arXiv)](https://arxiv.org/html/2408.04667v5)

### Transcript Cleanup Techniques
- [How I Automated My Podcast Transcript Production With Local AI](https://den.dev/blog/how-i-automated-podcast-transcription-with-local-ai/)

### Diacritic Restoration
- [Automatic Diacritic Restoration With Transformer Model (ResearchGate)](https://www.researchgate.net/publication/349645838_Automatic_Diacritic_Restoration_With_Transformer_Model_Based_Neural_Machine_Translation_for_East-Central_European_Languages)
- [Corpus-Based Diacritic Restoration for South Slavic Languages (ACL)](https://aclanthology.org/L16-1573/)
- [Diacritics Restoration using BERT with Analysis on Czech (arXiv)](https://ar5iv.labs.arxiv.org/html/2105.11408)
- [ReLDIanno Web Services (CLARIN Slovenia)](https://www.clarin.si/info/k-centre/web-services-documentation/)

### Slovenian Language Models
- [Slovenian Language Technologies Overview (GitHub)](https://github.com/clarinsi/Slovenian-Language-Technologies-Overview)
- [GaMS-1B (HuggingFace)](https://huggingface.co/cjvt/OPT_GaMS-1B)
- [CLASSLA NLP Pipeline (GitHub)](https://github.com/clarinsi/classla)

### Multilingual LLM Benchmarks
- [Towards Multilingual LLM Evaluation for European Languages (arXiv)](https://arxiv.org/html/2410.08928v2)
- [Gemma 2 Launch (InfoQ)](https://www.infoq.com/news/2024/07/google-gemma-2/)
- [LLM Practitioner's Guide: Gemma Multilingual](https://www.shelpuk.com/post/llm-practitioner-s-guide-gemma-a-game-changing-multilingual-llm)

### GDPR-Compliant Deployment
- [Mistral AI Solution Overview](https://obot.ai/resources/learning-center/mistral-ai/)
- [Mistral AI Pricing Guide](https://merlio.app/blog/mistral-ai-pricing-guide)
- [Scaleway Generative APIs](https://www.scaleway.com/en/generative-apis/)

### Self-Hosting LLMs
- [TGI vs. vLLM Comparison (Medium)](https://medium.com/@rohit.k/tgi-vs-vllm-making-informed-choices-for-llm-deployment-37c56d7ff705)
- [Ollama vs. vLLM Benchmarking (Red Hat)](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking)
- [Best GPU for Local LLM Guide](https://nutstudio.imyfone.com/llm-tips/best-gpu-for-local-llm/)

### ASR Error Correction Research
- [ASR Error Correction using Large Language Models (arXiv)](https://arxiv.org/html/2409.09554v2)
- [N-best T5: Robust ASR Error Correction (arXiv)](https://arxiv.org/html/2303.00456)
- [Enhancing Speech Recognition (OpenReview)](https://openreview.net/pdf/7ca9a69e2094fe214442250fb19b171a57fe882f.pdf)

---

## Conclusion

Solving your Slovenian dream journal cleanup challenges requires addressing each problem with targeted techniques. **Person preservation** needs explicit anti-transformation prompting and few-shot examples demonstrating correct behavior. **Length variance** requires structured JSON output with validation, chunked processing under 500 words, and rejection/retry logic for outputs below 75% length. **Diacritic restoration** benefits from dedicated models (REDI) or explicit restoration rules in prompts.

The **GaMS-9B-Instruct** model offers the best Slovenian-specific performance, deployable via self-hosted vLLM on EU infrastructure for full GDPR compliance. Alternatively, **Mistral AI's API** provides compliant hosted inference without infrastructure management.

For production deployment, the combination of CLASSLA preprocessing, few-shot prompted GaMS cleanup, and N-best constrained decoding offers the most robust solution—addressing not just your current problems but providing a foundation that prevents future issues as you scale.

---

*Document generated: December 2025*
*Last updated: Based on research from academic papers, GitHub repositories, and practitioner resources*