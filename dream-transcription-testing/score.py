"""
Compare transcription results between providers.

Usage:
    python score.py <audio_id> compare [--temp 0.0]
    python score.py <audio_id> stats <provider> [--temp 0.0]

Examples:
    python score.py dream1 compare                    # Compare at temp=0.0
    python score.py dream1 compare --temp 0.5         # Compare at temp=0.5
    python score.py dream1 stats groq                 # Stats for groq temp=0.0
    python score.py dream1 stats groq --temp 0.5      # Stats for groq temp=0.5
"""
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional


def count_diacritics(text: str) -> dict:
    """Count Slovenian diacritics in text."""
    return {
        "č": text.lower().count("č"),
        "š": text.lower().count("š"),
        "ž": text.lower().count("ž"),
        "total": text.lower().count("č") + text.lower().count("š") + text.lower().count("ž"),
    }


def get_cache_path(audio_id: str, provider: str, temperature: Optional[float]) -> Path:
    """Get cache file path."""
    cache_dir = Path(__file__).parent / "cache" / audio_id / provider

    if temperature is not None:
        filename = f"temp_{temperature}.json"
    else:
        filename = "result.json"

    return cache_dir / filename


def load_transcription(audio_id: str, provider: str, temperature: Optional[float]) -> Optional[Dict[str, Any]]:
    """Load transcription result from cache."""
    cache_path = get_cache_path(audio_id, provider, temperature)

    if not cache_path.exists():
        return None

    with open(cache_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def show_stats(audio_id: str, provider: str, temperature: Optional[float]):
    """Show stats for a single transcription."""
    data = load_transcription(audio_id, provider, temperature)

    if not data:
        cache_path = get_cache_path(audio_id, provider, temperature)
        print(f"[ERROR] No data found: {cache_path}")
        return

    text = data.get("transcribed_text", "")
    diacritics = count_diacritics(text)

    print(f"\n{'=' * 60}")
    print(f"  {audio_id} / {provider} / temp={temperature}")
    print(f"{'=' * 60}")
    print(f"  Status: {data.get('status')}")
    print(f"  Model: {data.get('model_used', 'N/A')}")
    print(f"  Text length: {len(text)} chars")
    print(f"  Word count: {len(text.split())}")
    print(f"\n  Diacritics:")
    print(f"    č: {diacritics['č']}")
    print(f"    š: {diacritics['š']}")
    print(f"    ž: {diacritics['ž']}")
    print(f"    Total: {diacritics['total']}")
    print(f"\n{'=' * 60}")
    print(f"\nText:\n{text[:500]}{'...' if len(text) > 500 else ''}")


def compare_providers(audio_id: str, temperature: float):
    """Compare groq vs assemblyai."""
    groq = load_transcription(audio_id, "groq", temperature)
    assemblyai = load_transcription(audio_id, "assemblyai", None)  # AssemblyAI has no temp

    if not groq and not assemblyai:
        print(f"[ERROR] No data for {audio_id}")
        print("  Run transcriptions first")
        return

    print(f"\n{'=' * 70}")
    print(f"  COMPARISON: {audio_id} (groq temp={temperature} vs assemblyai)")
    print(f"{'=' * 70}")

    groq_text = groq.get("transcribed_text", "") if groq else ""
    asm_text = assemblyai.get("transcribed_text", "") if assemblyai else ""

    groq_dc = count_diacritics(groq_text)
    asm_dc = count_diacritics(asm_text)

    rows = [
        ("Status",
         groq.get("status") if groq else "N/A",
         assemblyai.get("status") if assemblyai else "N/A"),
        ("Model",
         groq.get("model_used", "N/A") if groq else "N/A",
         assemblyai.get("model_used", "N/A") if assemblyai else "N/A"),
        ("Text length",
         f"{len(groq_text)} chars",
         f"{len(asm_text)} chars"),
        ("Word count",
         str(len(groq_text.split())),
         str(len(asm_text.split()))),
        ("č count", str(groq_dc["č"]), str(asm_dc["č"])),
        ("š count", str(groq_dc["š"]), str(asm_dc["š"])),
        ("ž count", str(groq_dc["ž"]), str(asm_dc["ž"])),
        ("Total diacritics", str(groq_dc["total"]), str(asm_dc["total"])),
    ]

    print(f"\n  {'Metric':<20} {'Groq':<20} {'AssemblyAI':<20}")
    print(f"  {'-'*20} {'-'*20} {'-'*20}")
    for label, g, a in rows:
        marker = " *" if g != a else ""
        print(f"  {label:<20} {g:<20} {a:<20}{marker}")

    # Diacritic comparison
    print(f"\n  Diacritic comparison:")
    if groq_dc["total"] > asm_dc["total"]:
        print(f"    Groq has MORE diacritics ({groq_dc['total']} vs {asm_dc['total']})")
    elif asm_dc["total"] > groq_dc["total"]:
        print(f"    AssemblyAI has MORE diacritics ({asm_dc['total']} vs {groq_dc['total']})")
    else:
        print(f"    Same diacritic count ({groq_dc['total']})")

    # Save comparison
    results_dir = Path(__file__).parent / "results" / audio_id
    results_dir.mkdir(parents=True, exist_ok=True)

    comparison_file = results_dir / f"compare_temp_{temperature}.md"
    md = generate_comparison_md(audio_id, temperature, groq, assemblyai, groq_dc, asm_dc)
    comparison_file.write_text(md, encoding='utf-8')

    print(f"\n{'=' * 70}")
    print(f"  Saved: {comparison_file}")
    print(f"{'=' * 70}\n")


def generate_comparison_md(
    audio_id: str,
    temperature: float,
    groq: Optional[dict],
    assemblyai: Optional[dict],
    groq_dc: dict,
    asm_dc: dict
) -> str:
    """Generate comparison markdown (metrics only, no transcription text)."""
    groq_text = groq.get("transcribed_text", "") if groq else ""
    asm_text = assemblyai.get("transcribed_text", "") if assemblyai else ""

    return f"""# Comparison: {audio_id}

Groq (temp={temperature}) vs AssemblyAI

## Summary

| Metric | Groq | AssemblyAI |
|--------|------|------------|
| Status | {groq.get('status') if groq else 'N/A'} | {assemblyai.get('status') if assemblyai else 'N/A'} |
| Model | {groq.get('model_used', 'N/A') if groq else 'N/A'} | {assemblyai.get('model_used', 'N/A') if assemblyai else 'N/A'} |
| Text length | {len(groq_text)} chars | {len(asm_text)} chars |
| Word count | {len(groq_text.split())} | {len(asm_text.split())} |
| č count | {groq_dc['č']} | {asm_dc['č']} |
| š count | {groq_dc['š']} | {asm_dc['š']} |
| ž count | {groq_dc['ž']} | {asm_dc['ž']} |
| **Total diacritics** | **{groq_dc['total']}** | **{asm_dc['total']}** |

## Full Transcriptions

Full text is in cache (gitignored):
- Groq: `cache/{audio_id}/groq/temp_{temperature}.json`
- AssemblyAI: `cache/{audio_id}/assemblyai/result.json`
"""


def main():
    parser = argparse.ArgumentParser(
        description="Compare transcription results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python score.py dream1 compare
    python score.py dream1 compare --temp 0.5
    python score.py dream1 stats groq
        """
    )
    parser.add_argument("audio_id", help="Audio ID")
    parser.add_argument("command", choices=["compare", "stats"])
    parser.add_argument("provider", nargs="?", help="Provider (for stats command)")
    parser.add_argument("--temp", "-t", type=float, default=0.0, help="Temperature (default: 0.0)")

    args = parser.parse_args()

    if args.command == "compare":
        compare_providers(args.audio_id, args.temp)
    elif args.command == "stats":
        if not args.provider:
            parser.error("stats requires provider (groq or assemblyai)")
        temp = args.temp if args.provider == "groq" else None
        show_stats(args.audio_id, args.provider, temp)


if __name__ == "__main__":
    main()
