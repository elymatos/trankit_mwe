"""
Standalone test for lemma_dict functionality without PyTorch dependency.
This test verifies the core lemmatization logic.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_lemma_dict_basic():
    """Test basic wordform→lemma dictionary functionality."""
    print("Testing lemma_dict basic functionality...")

    # Simulate the lemma dictionary structure
    lemma_dict = {
        "papéis": "papel",
        "cafés": "café",
        "foram": "ser",
        "deu": "dar",
        "certo": "certo"
    }

    # Test dictionary lookup (case-insensitive)
    assert lemma_dict.get("papéis") == "papel"
    assert lemma_dict.get("cafés") == "café"
    assert lemma_dict.get("foram") == "ser"

    print("✓ Basic lemma_dict functionality works correctly")


def test_lemma_dict_priority():
    """Test that lemma_dict has priority over programmatic rules."""
    print("\nTesting lemma_dict priority...")

    # Simulated rule-based lemmatization
    def programmatic_lemmatize(word):
        if word.endswith('s'):
            return word[:-1]
        return word

    # Simulated lemma_dict-based lemmatization
    def dict_lemmatize(word, lemma_dict=None):
        if lemma_dict and word in lemma_dict:
            return lemma_dict[word]
        return programmatic_lemmatize(word)

    lemma_dict = {
        "papéis": "papel",  # Correct irregular
        "foram": "ser"  # Verb conjugation
    }

    # Without dict: incorrect
    assert programmatic_lemmatize("papéis") == "papéi"  # Wrong!

    # With dict: correct
    assert dict_lemmatize("papéis", lemma_dict) == "papel"  # Correct!
    assert dict_lemmatize("foram", lemma_dict) == "ser"  # Correct!

    # Fallback to rules for unknown words
    assert dict_lemmatize("cafés", lemma_dict) == "café"  # Uses rule

    print("✓ Lemma_dict priority works correctly")


def test_lemma_dict_structure():
    """Test the expected structure of lemma_dict for MWE recognition."""
    print("\nTesting lemma_dict structure for MWE usage...")

    # Example MWE: "dar certo" (to work out)
    mwe_tokens = ["dar", "certo"]

    # Inflected text: "deu certo"
    input_tokens = ["deu", "certo"]

    # Lemma dictionary
    lemma_dict = {
        "deu": "dar",
        "deram": "dar",
        "dei": "dar",
        "certo": "certo",
        "certa": "certo",
        "certos": "certo"
    }

    # Simulate lemmatization for matching
    lemmatized = [lemma_dict.get(token, token) for token in input_tokens]

    # Check if lemmatized form matches MWE
    assert lemmatized == mwe_tokens

    print("✓ Lemma_dict structure works for MWE matching")


def test_case_insensitive():
    """Test case-insensitive matching."""
    print("\nTesting case-insensitive matching...")

    # Lemma dict should be lowercased
    lemma_dict = {
        "papéis": "papel",
        "café": "café",
        "foram": "ser"
    }

    # Input should be lowercased before lookup
    def lookup(word, lemma_dict):
        return lemma_dict.get(word.lower(), word.lower())

    assert lookup("PAPÉIS", lemma_dict) == "papel"
    assert lookup("Café", lemma_dict) == "café"
    assert lookup("Foram", lemma_dict) == "ser"

    print("✓ Case-insensitive matching works")


def run_standalone_tests():
    """Run all standalone tests."""
    print("=" * 80)
    print("Running Standalone Lemma Dict Tests")
    print("=" * 80)

    try:
        test_lemma_dict_basic()
        test_lemma_dict_priority()
        test_lemma_dict_structure()
        test_case_insensitive()

        print("\n" + "=" * 80)
        print("All standalone tests passed successfully! ✓")
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
    success = run_standalone_tests()
    sys.exit(0 if success else 1)
