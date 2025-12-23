#!/usr/bin/env python3
"""
Generate Slovenian word list from Sloleks 3.0 morphological lexicon.

Sloleks is the official Slovenian morphological lexicon maintained by CJVT
(Center for Language Resources and Technologies). It contains ~365,000 lemmas
with ALL inflected word forms.

This script extracts all unique word forms into a simple text file for
use in spell-checking with SymSpellPy.

Requirements:
    pip install datasets

Usage:
    python scripts/generate_slovenian_wordlist.py
    python scripts/generate_slovenian_wordlist.py --output /path/to/sl-words.txt

Output:
    sl-words.txt (~2-3 million unique word forms, one per line)
"""

import argparse
import sys
from pathlib import Path


def main():
    """Generate Slovenian word list from Sloleks dataset."""
    parser = argparse.ArgumentParser(
        description="Generate Slovenian word list from Sloleks 3.0 dataset"
    )
    parser.add_argument(
        "--output", "-o",
        default="sl-words.txt",
        help="Output file path (default: sl-words.txt)"
    )
    args = parser.parse_args()

    # Import datasets here to give better error message if not installed
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: 'datasets' package not installed.")
        print("Install it with: pip install datasets")
        sys.exit(1)

    print("Loading Sloleks dataset from HuggingFace...")
    print("(This may take a few minutes on first run)")

    # Load the Sloleks dataset
    dataset = load_dataset("cjvt/sloleks", split="train")

    print(f"Loaded {len(dataset)} entries")
    print("Extracting word forms...")

    words = set()

    # Process each entry
    for i, entry in enumerate(dataset):
        # Add the headword/lemma
        if 'headword_lemma' in entry and entry['headword_lemma']:
            words.add(entry['headword_lemma'].lower())

        # Add all word forms
        if 'word_forms' in entry and entry['word_forms']:
            for wf in entry['word_forms']:
                if 'forms' in wf and wf['forms']:
                    for form in wf['forms']:
                        if form:
                            words.add(form.lower())

        # Progress indicator
        if (i + 1) % 50000 == 0:
            print(f"  Processed {i + 1:,} entries, {len(words):,} unique words so far...")

    print(f"\nTotal unique word forms: {len(words):,}")

    # Sort words for consistent output
    sorted_words = sorted(words)

    # Ensure output directory exists
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted_words))

    # Calculate file size
    file_size = output_file.stat().st_size
    size_mb = file_size / (1024 * 1024)

    print(f"\nDone! Generated {len(sorted_words):,} unique word forms")
    print(f"File size: {size_mb:.2f} MB")
    print(f"Output: {output_file}")

    # Verify some known words are present
    test_words = ['ja', 'okej', 'izgleda', 'probam', 'probal', 'odpiral']
    print("\nVerifying test words:")
    for word in test_words:
        status = "✓" if word in words else "✗"
        print(f"  {status} {word}")


if __name__ == "__main__":
    main()
