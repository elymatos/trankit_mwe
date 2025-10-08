#!/usr/bin/env python3
"""
Interactive MWE Recognition Tool

This script allows you to test MWE recognition with your own sentences.
You can input sentences interactively and see MWE annotations in real-time.

Prerequisites:
    Run the database extraction script first:
    python scripts/extract_dictionaries_from_db.py
"""

import sys
import os
from trankit import Pipeline

def print_header():
    """Print welcome header."""
    print("\n" + "=" * 80)
    print("Interactive MWE Recognition Tool for Portuguese")
    print("=" * 80)
    print("\nThis tool will analyze your sentences and identify multiword expressions.")
    print("Type 'quit' or 'exit' to stop.\n")


def print_analysis(result):
    """Print detailed analysis of the sentence."""
    print("\n" + "-" * 80)
    print("Analysis:")
    print("-" * 80)

    for sent in result['sentences']:
        print(f"\n{'ID':<6} {'Token':<20} {'Lemma':<20} {'POS':<8} {'MWE Info'}")
        print("-" * 80)

        for token in sent['tokens']:
            token_id = token['id']
            text = token['text']
            lemma = token.get('lemma', '-')
            pos = token.get('upos', '-')

            # Format token ID (handle both int and tuple for MWT)
            if isinstance(token_id, tuple):
                id_str = f"{token_id[0]}-{token_id[1]}"
            else:
                id_str = str(token_id)

            # Check for MWE annotation
            mwe_info = ""
            if 'mwe_span' in token:
                span = token['mwe_span']
                mwe_lemma = token.get('mwe_lemma', '-')
                mwe_type = token.get('mwe_type', 'unknown')
                mwe_pos = token.get('mwe_pos', '-')
                mwe_info = f"✓ MWE: '{mwe_lemma}' [{mwe_type}, {mwe_pos}]"

            print(f"{id_str:<6} {text:<20} {lemma:<20} {pos:<8} {mwe_info}")

    # Count MWEs detected
    mwe_count = sum(1 for token in result['sentences'][0]['tokens'] if 'mwe_span' in token)

    print("-" * 80)
    if mwe_count > 0:
        print(f"✓ Found {mwe_count} token(s) that are part of multiword expressions.")
    else:
        print("No multiword expressions detected in this sentence.")
    print("-" * 80)


def main():
    # Check for dictionary files
    mwe_database_path = 'data/portuguese/mwe_database.json'
    lemma_dict_path = 'data/portuguese/lemma_dict.json'

    if not os.path.exists(mwe_database_path) or not os.path.exists(lemma_dict_path):
        print("\n❌ ERROR: Dictionary files not found!")
        print("\nPlease run the database extraction script first:")
        print("    python scripts/extract_dictionaries_from_db.py")
        print("\nThis will create:")
        print(f"    - {mwe_database_path}")
        print(f"    - {lemma_dict_path}")
        sys.exit(1)

    print_header()

    # Initialize pipeline
    print("Loading Trankit pipeline with MWE recognition...")
    print("(This may take a minute on first run to download models...)\n")

    try:
        p = Pipeline('portuguese',
                     gpu=False,
                     mwe_database=mwe_database_path,
                     lemma_dict=lemma_dict_path)
        print("✓ Pipeline loaded successfully!")

        # Show statistics
        mwe_recognizer = p._mwe_recognizer.get('portuguese')
        if mwe_recognizer:
            stats = mwe_recognizer.get_statistics()
            print(f"✓ Loaded {stats['total_mwes']} MWE expressions")
            print(f"✓ Loaded {len(mwe_recognizer.lemma_dict)} lemma mappings")
    except Exception as e:
        print(f"\n❌ Error loading pipeline: {e}")
        sys.exit(1)

    # Interactive loop
    print("\n" + "=" * 80)
    print("Ready! Enter sentences to analyze:")
    print("=" * 80)

    while True:
        try:
            # Get input from user
            print("\n")
            sentence = input("Enter sentence (or 'quit' to exit): ").strip()

            # Check for exit commands
            if sentence.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            # Skip empty input
            if not sentence:
                continue

            # Process the sentence
            print(f"\nProcessing: {sentence}")
            result = p(sentence)

            # Display analysis
            print_analysis(result)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error processing sentence: {e}")
            import traceback
            traceback.print_exc()
            continue


if __name__ == "__main__":
    main()
