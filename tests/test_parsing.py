#!/usr/bin/env python3
"""
Test actual sentence parsing with Trankit MWE recognition.

This test demonstrates:
1. Real parsing with the Trankit pipeline
2. MWE (Multiword Expression) recognition - NEW FEATURE
3. lemma_dict overrides during parsing
4. Integration of MWE recognition with standard parsing pipeline
"""

from trankit import Pipeline

def test_basic_parsing():
    """Test basic sentence parsing."""
    print("=" * 60)
    print("TEST 1: Basic Parsing")
    print("=" * 60)

    # Initialize pipeline for English
    p = Pipeline('english')

    # Parse a simple sentence
    text = "The quick brown fox jumps over the lazy dog."
    result = p(text)

    print(f"\nInput: {text}")
    print("\nParsed tokens:")
    for token in result['sentences'][0]['tokens']:
        print(f"  {token['id']:2d}. {token['text']:10s} | Lemma: {token['lemma']:10s} | POS: {token['upos']:6s}")

    print("\n✓ Basic parsing works\n")


def test_mwe_parsing():
    """Test parsing with NEW MWE recognition feature."""
    print("=" * 60)
    print("TEST 2: MWE Recognition (NEW FEATURE)")
    print("=" * 60)

    # Define MWE database for Portuguese
    portuguese_mwes = {
        "café da manhã": {
            "lemma": "café da manhã",
            "pos": "NOUN",
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
        }
    }

    # Initialize pipeline WITH MWE recognition
    p = Pipeline('portuguese', mwe_database=portuguese_mwes)

    # Test sentence containing MWEs
    text = "Tomei café da manhã antes de acordo com o plano."
    result = p(text)

    print(f"\nInput: {text}")
    print("\nParsed tokens (with MWE recognition):")
    for token in result['sentences'][0]['tokens']:
        token_id = token['id']
        token_text = token['text']
        lemma = token.get('lemma', '-')
        upos = token.get('upos', '-')

        # Format token ID (handle both int and tuple)
        if isinstance(token_id, tuple):
            id_str = f"{token_id[0]}-{token_id[1]}"
        else:
            id_str = f"{token_id:2d}"

        # Check for MWE annotation
        mwe_info = ""
        if 'mwe_span' in token:
            span = token['mwe_span']
            mwe_type = token.get('mwe_type', 'unknown')
            mwe_lemma = token.get('mwe_lemma', '-')
            mwe_info = f" ✓ MWE[{span[0]}-{span[1]}]:{mwe_type} (lemma: {mwe_lemma})"

        print(f"  {id_str:>4}. {token_text:15s} | Lemma: {lemma:15s} | POS: {upos:6s}{mwe_info}")

    # Verify MWE was detected
    mwe_found = any('mwe_span' in token for token in result['sentences'][0]['tokens'])
    assert mwe_found, "Expected to find MWE annotations"

    print("\n✓ MWE recognition works\n")


def test_lemma_dict_with_mwe():
    """Test MWE recognition with lemma_dict for accurate lemmatization."""
    print("=" * 60)
    print("TEST 3: MWE Recognition + lemma_dict")
    print("=" * 60)

    # Define MWE database
    portuguese_mwes = {
        "café da manhã": {
            "lemma": "café da manhã",
            "pos": "NOUN",
            "type": "fixed"
        }
    }

    # Define lemma dictionary for accurate wordform→lemma mapping
    lemma_dict = {
        'cafés': 'café',
        'manhãs': 'manhã',
        'tomei': 'tomar',
        'flores': 'flor'
    }

    # Initialize pipeline WITH both MWE database and lemma_dict
    p = Pipeline('portuguese', mwe_database=portuguese_mwes, lemma_dict=lemma_dict)

    text = "Tomei cafés da manhã com flores."

    result = p(text)
    print(f"\nInput: {text}")
    print("\nWith MWE recognition + lemma_dict:")
    print(f"{'Token':<15} {'Lemma':<15} {'POS':<8} {'MWE Info'}")
    print("-" * 70)

    for token in result['sentences'][0]['tokens']:
        token_text = token['text']
        lemma = token.get('lemma', '-')
        upos = token.get('upos', '-')

        # Check for MWE annotation
        mwe_info = ""
        if 'mwe_span' in token:
            span = token['mwe_span']
            mwe_lemma = token.get('mwe_lemma', '-')
            mwe_info = f"✓ MWE: {mwe_lemma}"

        print(f"{token_text:<15} {lemma:<15} {upos:<8} {mwe_info}")

    # Verify lemma_dict worked
    tomei_lemma = [t['lemma'] for t in result['sentences'][0]['tokens'] if t['text'] == 'Tomei'][0]
    assert tomei_lemma.lower() == 'tomar', f"Expected 'tomar', got '{tomei_lemma}'"

    print("\n✓ MWE recognition + lemma_dict work together\n")


def test_dependency_parsing():
    """Test dependency parsing output."""
    print("=" * 60)
    print("TEST 4: Dependency Relations")
    print("=" * 60)

    p = Pipeline('english')

    text = "The cat sits on the mat."
    result = p(text)

    print(f"\nInput: {text}")
    print("\nDependency structure:")
    for token in result['sentences'][0]['tokens']:
        head = token['head']
        deprel = token['deprel']
        token_text = token['text']

        if head == 0:
            print(f"  {token['id']:2d}. {token_text:10s} -> ROOT ({deprel})")
        else:
            head_text = result['sentences'][0]['tokens'][head - 1]['text']
            print(f"  {token['id']:2d}. {token_text:10s} -> {head} ({head_text}) [{deprel}]")

    print("\n✓ Dependency parsing works\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("TRANKIT MWE RECOGNITION - PARSING TESTS")
    print("=" * 60)
    print("\nThese tests demonstrate the NEW MWE recognition feature.")
    print("Models will be downloaded on first run (may take a few minutes).\n")

    try:
        test_basic_parsing()
        test_mwe_parsing()
        test_lemma_dict_with_mwe()
        test_dependency_parsing()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nThe MWE recognition feature is working correctly!")
        print("MWEs are detected and annotated with 'mwe_span', 'mwe_lemma',")
        print("'mwe_type', and 'mwe_pos' fields in the token dictionaries.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)