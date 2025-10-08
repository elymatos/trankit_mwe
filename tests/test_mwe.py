"""
Unit tests for MWE recognition functionality.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trankit.utils.mwe_utils import (
    load_mwe_database,
    quick_lemmatize,
    build_mwe_trie,
    match_mwe_spans,
    mark_mwe_tokens
)


def test_load_mwe_database():
    """Test loading MWE database from dict."""
    print("Testing load_mwe_database...")

    mwe_dict = {
        "café da manhã": {"lemma": "café da manhã", "pos": "NOUN"},
        "uma a uma": {"lemma": "um a um", "pos": "ADV"}
    }

    loaded = load_mwe_database(mwe_dict)
    assert len(loaded) == 2
    assert "café da manhã" in loaded
    assert loaded["café da manhã"]["pos"] == "NOUN"

    print("✓ load_mwe_database test passed")


def test_quick_lemmatize_portuguese():
    """Test Portuguese lemmatization rules."""
    print("\nTesting quick_lemmatize...")

    test_cases = [
        ("cafés", "café"),
        ("manhãs", "manhã"),
        ("papéis", "papel"),
        ("flores", "flore"),  # Simplified rule
        ("jardins", "jardim"),
        ("uma", "uma"),  # No change
        ("da", "da"),  # No change
    ]

    for word, expected in test_cases:
        result = quick_lemmatize(word, 'portuguese')
        assert result == expected, f"Expected '{expected}', got '{result}' for '{word}'"

    print("✓ quick_lemmatize test passed")


def test_build_mwe_trie():
    """Test trie construction."""
    print("\nTesting build_mwe_trie...")

    mwe_dict = {
        "café da manhã": {"lemma": "café da manhã", "pos": "NOUN"},
        "de manhã": {"lemma": "de manhã", "pos": "ADV"}
    }

    trie = build_mwe_trie(mwe_dict, 'portuguese')

    # Check that trie is built
    assert 'café' in trie
    assert 'da' in trie['café']
    assert 'manhã' in trie['café']['da']
    assert '__MWE_INFO__' in trie['café']['da']['manhã']

    print("✓ build_mwe_trie test passed")


def test_match_mwe_spans():
    """Test MWE span matching."""
    print("\nTesting match_mwe_spans...")

    mwe_dict = {
        "café da manhã": {"lemma": "café da manhã", "pos": "NOUN", "type": "fixed"},
        "uma a uma": {"lemma": "um a um", "pos": "ADV", "type": "fixed"}
    }

    trie = build_mwe_trie(mwe_dict, 'portuguese')

    # Test with exact match
    tokens = [
        {"text": "Tomei"},
        {"text": "café"},
        {"text": "da"},
        {"text": "manhã"}
    ]

    spans = match_mwe_spans(tokens, trie, 'portuguese')
    assert len(spans) == 1
    assert spans[0][0] == 1  # Start index
    assert spans[0][1] == 4  # End index
    assert spans[0][2]['lemma'] == "café da manhã"

    # Test with inflected form
    tokens2 = [
        {"text": "Tomei"},
        {"text": "cafés"},  # Plural
        {"text": "da"},
        {"text": "manhã"}
    ]

    spans2 = match_mwe_spans(tokens2, trie, 'portuguese')
    assert len(spans2) == 1  # Should still match via lemmatization

    print("✓ match_mwe_spans test passed")


def test_mark_mwe_tokens():
    """Test token marking with MWE information."""
    print("\nTesting mark_mwe_tokens...")

    tokens = [
        {"text": "Tomei", "id": 1},
        {"text": "café", "id": 2},
        {"text": "da", "id": 3},
        {"text": "manhã", "id": 4}
    ]

    mwe_spans = [(1, 4, {
        "lemma": "café da manhã",
        "pos": "NOUN",
        "type": "fixed",
        "length": 3
    })]

    marked = mark_mwe_tokens(tokens, mwe_spans)

    # Check first token (not in MWE)
    assert 'mwe_span' not in marked[0]

    # Check MWE tokens
    assert 'mwe_span' in marked[1]
    assert marked[1]['mwe_span'] == (1, 4)
    assert marked[1]['mwe_lemma'] == "café da manhã"
    assert marked[1]['mwe_pos'] == "NOUN"
    assert marked[1]['mwe_position'] == 0  # First token in MWE

    assert marked[2]['mwe_position'] == 1  # Second token
    assert marked[3]['mwe_position'] == 2  # Third token

    print("✓ mark_mwe_tokens test passed")


def test_overlapping_mwes():
    """Test handling of overlapping MWEs (should use longest match)."""
    print("\nTesting overlapping MWEs...")

    mwe_dict = {
        "de manhã": {"lemma": "de manhã", "pos": "ADV", "type": "fixed"},
        "café da manhã": {"lemma": "café da manhã", "pos": "NOUN", "type": "fixed"}
    }

    trie = build_mwe_trie(mwe_dict, 'portuguese')

    tokens = [
        {"text": "Tomei"},
        {"text": "café"},
        {"text": "da"},
        {"text": "manhã"}
    ]

    spans = match_mwe_spans(tokens, trie, 'portuguese')

    # Should match the longer MWE "café da manhã", not "de manhã"
    assert len(spans) == 1
    assert spans[0][2]['lemma'] == "café da manhã"
    assert spans[0][1] - spans[0][0] == 3  # Length 3

    print("✓ overlapping MWEs test passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("Running MWE Recognition Tests")
    print("=" * 80)

    try:
        test_load_mwe_database()
        test_quick_lemmatize_portuguese()
        test_build_mwe_trie()
        test_match_mwe_spans()
        test_mark_mwe_tokens()
        test_overlapping_mwes()

        print("\n" + "=" * 80)
        print("All tests passed successfully! ✓")
        print("=" * 80)
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        print("=" * 80)
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
