#!/usr/bin/env python3
"""
Simple example of using Trankit with MWE recognition from database-extracted files.

This is a minimal example showing how to:
1. Load MWE database from JSON file
2. Load lemma dictionary from JSON file
3. Initialize Pipeline with the files
4. Process text and see MWE annotations

Prerequisites:
    Run the database extraction script first:
    python scripts/extract_dictionaries_from_db.py
"""

from trankit import Pipeline

def main():
    print("Simple MWE Recognition Example\n")
    print("=" * 70)

    # Initialize pipeline with extracted dictionary files
    print("Loading dictionaries from JSON files...")
    p = Pipeline('portuguese',
                 gpu=False,
                 mwe_database='data/portuguese/mwe_database.json',
                 lemma_dict='data/portuguese/lemma_dict.json')

    print("✓ Pipeline initialized with MWE recognition\n")

    # Test sentences
    sentences = [
        "Tomei café da manhã cedo.",
        "De acordo com o relatório, tudo está correto.",
        "Por favor, venha amanhã."
    ]

    # Process each sentence
    for sentence in sentences:
        print(f"Input:  {sentence}")

        result = p(sentence)

        # Show tokens with MWE annotations
        print("Output: ", end="")
        for token in result['sentences'][0]['tokens']:
            text = token['text']
            if 'mwe_span' in token:
                mwe_lemma = token.get('mwe_lemma', '')
                print(f"[{text}→{mwe_lemma}]", end=" ")
            else:
                print(text, end=" ")
        print("\n")

    print("=" * 70)
    print("✓ Example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print("\n❌ Error: Dictionary files not found!")
        print("\nPlease run the database extraction script first:")
        print("    python scripts/extract_dictionaries_from_db.py")
        print("\nThis will create the required JSON files.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
