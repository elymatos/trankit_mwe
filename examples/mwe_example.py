"""
Example of using Trankit with MWE (Multiword Expression) recognition.

This example demonstrates how to:
1. Initialize a Pipeline with MWE database
2. Process text containing MWEs
3. Inspect the output to see MWE annotations
"""

from trankit import Pipeline

# Define MWE database for Portuguese
# Format: {"surface_form": {"lemma": "...", "pos": "...", "type": "..."}}
portuguese_mwes = {
    "café da manhã": {
        "lemma": "café da manhã",
        "pos": "NOUN",
        "type": "fixed"
    },
    "uma a uma": {
        "lemma": "um a um",
        "pos": "ADV",
        "type": "fixed"
    },
    "de acordo com": {
        "lemma": "de acordo com",
        "pos": "ADP",
        "type": "fixed"
    },
    "por favor": {
        "lemma": "por favor",
        "pos": "ADV",
        "type": "fixed"
    },
    "de manhã": {
        "lemma": "de manhã",
        "pos": "ADV",
        "type": "fixed"
    }
}

def main():
    print("=" * 80)
    print("Trankit MWE Recognition Example")
    print("=" * 80)

    # Example 1: Basic MWE recognition (programmatic lemmatization)
    print("\n1. Initializing Trankit pipeline for Portuguese with MWE recognition...")
    p = Pipeline('portuguese', gpu=False, mwe_database=portuguese_mwes)
    print("   ✓ Pipeline initialized successfully")

    # Example 2: MWE recognition with custom lemma dictionary
    print("\n2. Initializing pipeline with custom lemma dictionary for better accuracy...")

    # Custom lemma dictionary with wordform → lemma mappings
    # This handles irregular forms and improves accuracy
    portuguese_lemmas = {
        "cafés": "café",
        "manhãs": "manhã",
        "tomei": "tomar",
        "lemos": "ler",
        "emails": "email",
        "veio": "vir",
        "vimos": "vir",
        "deu": "dar",
        "foram": "ser"
    }

    p_with_dict = Pipeline('portuguese', gpu=False,
                          mwe_database=portuguese_mwes,
                          lemma_dict=portuguese_lemmas)
    print("   ✓ Pipeline with lemma dictionary initialized successfully")

    # Example texts containing MWEs
    texts = [
        "Tomei café da manhã antes de sair.",
        "Lemos os emails uma a uma.",
        "De acordo com o relatório, tudo está correto.",
        "Café da manhã é a refeição mais importante.",
        "Por favor, venha de manhã."
    ]

    print("\n3. Processing texts containing MWEs...")
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

                # Check for MWE annotation
                mwe_info = ""
                if 'mwe_span' in token:
                    span = token['mwe_span']
                    mwe_type = token.get('mwe_type', 'unknown')
                    mwe_info = f"✓ MWE[{span[0]}-{span[1]}]:{mwe_type}"

                print(f"{token_id:<4} {text:<15} {lemma:<20} {pos:<8} {head:<6} {deprel:<12} {mwe_info}")

        print("\n" + "=" * 80)

    # Show MWE statistics
    print("\n4. MWE Database Statistics:")
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
    print("\n5. Adding MWEs dynamically:")
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
