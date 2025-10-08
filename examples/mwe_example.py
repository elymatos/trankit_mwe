"""
Example of using Trankit with MWE (Multiword Expression) recognition.

This example demonstrates how to:
1. Load MWE database and lemma dictionary from JSON files (extracted from database)
2. Initialize a Pipeline with external dictionary files
3. Process text containing MWEs
4. Inspect the output to see MWE annotations

Prerequisites:
    1. Run the database extraction script first:
       python scripts/extract_dictionaries_from_db.py

    2. This will create:
       - data/portuguese/mwe_database.json
       - data/portuguese/lemma_dict.json
"""

import os
import json
from trankit import Pipeline

def load_json_file(filepath):
    """Load JSON file if it exists."""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def main():
    print("=" * 80)
    print("Trankit MWE Recognition Example")
    print("=" * 80)

    # Paths to extracted dictionary files
    mwe_database_path = 'data/portuguese/mwe_database.json'
    lemma_dict_path = 'data/portuguese/lemma_dict.json'

    # Check if files exist
    print("\n1. Checking for extracted dictionary files...")
    mwe_db_exists = os.path.exists(mwe_database_path)
    lemma_dict_exists = os.path.exists(lemma_dict_path)

    if not mwe_db_exists or not lemma_dict_exists:
        print("\n⚠️  WARNING: Dictionary files not found!")
        print("\nPlease run the database extraction script first:")
        print("    python scripts/extract_dictionaries_from_db.py")
        print("\nThis will create:")
        print(f"    - {mwe_database_path}")
        print(f"    - {lemma_dict_path}")
        print("\nFor now, using fallback hardcoded dictionaries...\n")

        # Fallback: use small hardcoded dictionaries
        mwe_database = {
            "café da manhã": {"lemma": "café da manhã", "pos": "NOUN", "type": "fixed"},
            "de acordo com": {"lemma": "de acordo com", "pos": "ADP", "type": "fixed"},
            "por favor": {"lemma": "por favor", "pos": "ADV", "type": "fixed"}
        }
        lemma_dict = {
            "cafés": "café",
            "tomei": "tomar",
            "foram": "ser"
        }
    else:
        print(f"   ✓ Found: {mwe_database_path}")
        print(f"   ✓ Found: {lemma_dict_path}")

        # Load dictionaries from files
        print("\n2. Loading dictionaries from JSON files...")
        mwe_database = load_json_file(mwe_database_path)
        lemma_dict = load_json_file(lemma_dict_path)

        if mwe_database:
            print(f"   ✓ Loaded {len(mwe_database)} MWE expressions")
        if lemma_dict:
            print(f"   ✓ Loaded {len(lemma_dict)} lemma mappings")

    # Example 1: Initialize pipeline with MWE database only
    print("\n3. Initializing Trankit pipeline with MWE database...")
    p = Pipeline('portuguese', gpu=False, mwe_database=mwe_database)
    print("   ✓ Pipeline initialized successfully")

    # Example 2: Initialize pipeline with both MWE database and lemma dictionary
    print("\n4. Initializing pipeline with MWE database + lemma dictionary...")
    p_with_dict = Pipeline('portuguese', gpu=False,
                          mwe_database=mwe_database,
                          lemma_dict=lemma_dict)
    print("   ✓ Pipeline with lemma dictionary initialized successfully")

    # Example texts containing MWEs
    texts = [
        "Tomei café da manhã antes de sair.",
        "Lemos os emails uma a uma.",
        "De acordo com o relatório, tudo está correto.",
        "Café da manhã é a refeição mais importante.",
        "Por favor, venha de manhã."
    ]

    print("\n5. Processing texts containing MWEs...")
    print("-" * 80)

    for idx, text in enumerate(texts, 1):
        print(f"\nText {idx}: {text}")
        print("-" * 80)

        # Process the text
        result = p(text)

        # Display results
        for sent in result['sentences']:
            print("\nTokens and annotations:")
            print(f"{'ID':<4} {'Text':<15} {'Lemma':<20} {'POS':<8} {'Head':<6} {'DepRel':<12} {'MWE'}")
            print("-" * 95)

            for token in sent['tokens']:
                token_id = token['id']
                text = token['text']
                lemma = token.get('lemma', '-')
                pos = token.get('upos', '-')
                head = token.get('head', '-')
                deprel = token.get('deprel', '-')

                # Format token ID (handle both int and tuple for MWT)
                if isinstance(token_id, tuple):
                    id_str = f"{token_id[0]}-{token_id[1]}"
                else:
                    id_str = str(token_id)

                # Check for MWE annotation
                mwe_info = ""
                if 'mwe_span' in token:
                    span = token['mwe_span']
                    mwe_type = token.get('mwe_type', 'unknown')
                    mwe_info = f"✓ MWE[{span[0]}-{span[1]}]:{mwe_type}"

                print(f"{id_str:<4} {text:<15} {lemma:<20} {pos:<8} {head:<6} {deprel:<12} {mwe_info}")

        print("\n" + "=" * 80)

    # Show MWE statistics
    print("\n6. MWE Database Statistics:")
    print("-" * 80)
    mwe_recognizer = p._mwe_recognizer.get('portuguese')
    if mwe_recognizer:
        stats = mwe_recognizer.get_statistics()
        print(f"Total MWEs loaded: {stats['total_mwes']}")
        print(f"Length distribution: {stats['length_distribution']}")
        print(f"POS distribution: {stats['pos_distribution']}")
        print(f"Type distribution: {stats['type_distribution']}")

    # Show lemma dictionary info for pipeline with dict
    mwe_recognizer_dict = p_with_dict._mwe_recognizer.get('portuguese')
    if mwe_recognizer_dict:
        print(f"\nPipeline with lemma_dict has {len(mwe_recognizer_dict.lemma_dict)} wordform mappings")
    print("=" * 80)

    # Example: Adding MWEs at runtime
    print("\n7. Adding MWEs dynamically:")
    print("-" * 80)
    if mwe_recognizer:
        mwe_recognizer.add_mwe(
            "ponto de vista",
            lemma="ponto de vista",
            pos="NOUN",
            mwe_type="fixed"
        )
        print("   ✓ Added 'ponto de vista' to MWE database")

        # Test the newly added MWE
        test_text = "Do meu ponto de vista, isso está correto."
        print(f"\n   Testing: {test_text}")
        result = p(test_text)

        for sent in result['sentences']:
            for token in sent['tokens']:
                if 'mwe_span' in token:
                    print(f"   ✓ Detected MWE: '{token['text']}' (lemma: {token.get('mwe_lemma', 'N/A')})")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
