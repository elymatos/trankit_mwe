"""
Utility functions for Multiword Expression (MWE) recognition and processing.

This module provides:
- MWE database loading and management
- Fast lemmatization for Portuguese and other languages
- MWE span matching algorithms
- Token annotation with MWE metadata
"""

import re
import json
from collections import defaultdict
from .conll import *


def load_mwe_database(database_source, language='portuguese'):
    """
    Load MWE database from various sources.

    Args:
        database_source: Can be:
            - dict: Direct MWE dictionary
            - str: Path to JSON file
            - None: Returns empty dict
        language: Language code for language-specific processing

    Returns:
        dict: MWE database with structure:
            {
                "café da manhã": {
                    "lemma": "café da manhã",
                    "pos": "NOUN",
                    "type": "fixed"
                },
                ...
            }
    """
    if database_source is None:
        return {}

    if isinstance(database_source, dict):
        return database_source

    if isinstance(database_source, str):
        # Load from JSON file
        try:
            with open(database_source, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: MWE database file not found: {database_source}")
            return {}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in MWE database: {database_source}")
            return {}

    return {}


def load_lemma_dict(lemma_dict_source, language='portuguese'):
    """
    Load wordform-to-lemma dictionary from various sources.

    Args:
        lemma_dict_source: Can be:
            - dict: Direct wordform→lemma mapping {"wordform": "lemma", ...}
            - str: Path to JSON file with same structure
            - None: Returns empty dict

    Returns:
        dict: Lemma dictionary with structure {"wordform": "lemma", ...}
              All keys and values are lowercased for case-insensitive matching.
    """
    if lemma_dict_source is None:
        return {}

    if isinstance(lemma_dict_source, dict):
        # Lowercase all keys and values for consistent matching
        return {k.lower(): v.lower() for k, v in lemma_dict_source.items()}

    if isinstance(lemma_dict_source, str):
        # Load from JSON file
        try:
            with open(lemma_dict_source, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Lowercase all keys and values
                return {k.lower(): v.lower() for k, v in data.items()}
        except FileNotFoundError:
            print(f"Warning: Lemma dictionary file not found: {lemma_dict_source}")
            return {}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in lemma dictionary: {lemma_dict_source}")
            return {}

    return {}


def quick_lemmatize(word, language='portuguese', lemma_dict=None):
    """
    Fast lemmatization using dictionary lookup or morphological rules.

    This function prioritizes dictionary lookup for accuracy, then falls back
    to programmatic rules for words not in the dictionary.

    Args:
        word: Input word (string)
        language: Language code
        lemma_dict: Optional dictionary mapping wordforms to lemmas.
                   If provided, this is checked first before applying rules.

    Returns:
        str: Lemmatized form
    """
    if not word:
        return word

    word_lower = word.lower()

    # Priority 1: Check lemma dictionary if provided
    if lemma_dict and word_lower in lemma_dict:
        return lemma_dict[word_lower]

    # Priority 2: Fallback to programmatic rules
    if language == 'portuguese' or language == 'pt':
        return _lemmatize_portuguese(word_lower)

    # Default: return lowercase
    return word_lower


def _lemmatize_portuguese(word):
    """
    Portuguese-specific lemmatization rules.

    Handles common plural and verb conjugation patterns.
    """
    # Plural to singular patterns
    if word.endswith('ões'):
        return word[:-3] + 'ão'  # limões → limão
    if word.endswith('ães'):
        return word[:-3] + 'ão'  # pães → pão
    if word.endswith('ãos'):
        return word[:-3] + 'ão'  # mãos → mão
    if word.endswith('eis'):
        if len(word) > 4 and word[-4] in 'aeiouáéíóú':
            return word[:-3] + 'l'  # papéis → papel
        return word[:-3] + 'il'  # barris → barril
    if word.endswith('óis'):
        return word[:-3] + 'ol'  # sóis → sol
    if word.endswith('res'):
        return word[:-2]  # flores → flor (simplified)
    if word.endswith('ses'):
        return word[:-2]  # meses → mês (simplified)
    if word.endswith('zes'):
        return word[:-2]  # luzes → luz
    if word.endswith('ns'):
        return word[:-2] + 'm'  # jardins → jardim
    if word.endswith('s') and len(word) > 2:
        # Simple plural: cafés → café
        return word[:-1]

    # Verb conjugations (simplified - only common patterns)
    # This is intentionally basic; for full lemmatization, use Trankit's lemmatizer
    if word.endswith(('ando', 'endo', 'indo')):  # gerund
        return word[:-4] + 'ar' if word.endswith('ando') else word[:-4] + 'er'

    return word


def _expand_portuguese_contractions(word):
    """
    Expand Portuguese contractions to match MWT expansion.

    Returns list of expanded tokens, or [word] if not a contraction.
    """
    # Mapping of contractions to their expansions
    contraction_map = {
        'da': ['de', 'a'],
        'do': ['de', 'o'],
        'das': ['de', 'as'],
        'dos': ['de', 'os'],
        'na': ['em', 'a'],
        'no': ['em', 'o'],
        'nas': ['em', 'as'],
        'nos': ['em', 'os'],
        'ao': ['a', 'o'],
        'aos': ['a', 'os'],
        'à': ['a', 'a'],
        'às': ['a', 'as'],
        'pela': ['por', 'a'],
        'pelo': ['por', 'o'],
        'pelas': ['por', 'as'],
        'pelos': ['por', 'os'],
        'dum': ['de', 'um'],
        'duma': ['de', 'uma'],
        'duns': ['de', 'uns'],
        'dumas': ['de', 'umas'],
        'num': ['em', 'um'],
        'numa': ['em', 'uma'],
        'nuns': ['em', 'uns'],
        'numas': ['em', 'umas']
    }

    word_lower = word.lower()
    return contraction_map.get(word_lower, [word])


def build_mwe_trie(mwe_database, language='portuguese', lemma_dict=None):
    """
    Build a trie structure for efficient MWE matching.

    The trie stores lemmatized forms of MWEs for fast lookup.
    For Portuguese, contractions in MWEs are expanded to match MWT expansion.

    Args:
        mwe_database: MWE dictionary
        language: Language code for lemmatization
        lemma_dict: Optional wordform→lemma dictionary for accurate lemmatization

    Returns:
        dict: Trie structure where each node contains:
            - children: dict of next tokens
            - mwe_info: MWE metadata if this is an endpoint
    """
    trie = {}

    for mwe_text, mwe_info in mwe_database.items():
        # Tokenize the MWE
        tokens = mwe_text.split()

        # Expand contractions (for Portuguese)
        if language in ['portuguese', 'pt']:
            expanded_tokens = []
            for token in tokens:
                expanded_tokens.extend(_expand_portuguese_contractions(token))
            tokens = expanded_tokens

        # Lemmatize tokens
        lemmas = [quick_lemmatize(t, language, lemma_dict) for t in tokens]

        # Build trie path
        current = trie
        for lemma in lemmas:
            if lemma not in current:
                current[lemma] = {}
            current = current[lemma]

        # Mark endpoint with MWE info
        current['__MWE_INFO__'] = {
            'original': mwe_text,
            'lemma': mwe_info.get('lemma', mwe_text),
            'pos': mwe_info.get('pos', 'X'),
            'type': mwe_info.get('type', 'fixed'),
            'length': len(lemmas)
        }

    return trie


def match_mwe_spans(tokens, mwe_trie, language='portuguese', max_length=10, lemma_dict=None):
    """
    Find all MWE spans in a token sequence using longest-match-first.

    Args:
        tokens: List of token dicts with 'text' field (and optionally 'lemma')
        mwe_trie: Trie structure from build_mwe_trie()
        language: Language code for lemmatization
        max_length: Maximum MWE length to consider
        lemma_dict: Optional wordform→lemma dictionary for accurate lemmatization

    Returns:
        list: List of (start_idx, end_idx, mwe_info) tuples, where:
            - start_idx: Starting token index (inclusive)
            - end_idx: Ending token index (exclusive)
            - mwe_info: Dict with MWE metadata
    """
    mwe_spans = []
    num_tokens = len(tokens)
    matched_positions = set()  # Track already matched tokens

    i = 0
    while i < num_tokens:
        # Skip if this position already part of an MWE
        if i in matched_positions:
            i += 1
            continue

        # Try to match MWE starting at position i
        longest_match = None
        longest_length = 0

        current_trie = mwe_trie
        for j in range(i, min(i + max_length, num_tokens)):
            if j in matched_positions:
                break  # Don't match across already matched tokens

            # Get lemma for current token
            token = tokens[j]
            if 'lemma' in token and token['lemma']:
                lemma = token['lemma'].lower()
            else:
                lemma = quick_lemmatize(token.get('text', token.get(TEXT, '')), language, lemma_dict)

            # Check if lemma is in trie
            if lemma not in current_trie:
                break  # No match possible

            current_trie = current_trie[lemma]

            # Check if this is a complete MWE
            if '__MWE_INFO__' in current_trie:
                longest_match = current_trie['__MWE_INFO__']
                longest_length = j - i + 1

        # If we found a match, record it
        if longest_match:
            end_idx = i + longest_length
            mwe_spans.append((i, end_idx, longest_match))
            # Mark these positions as matched
            for k in range(i, end_idx):
                matched_positions.add(k)
            i = end_idx  # Jump past the matched span
        else:
            i += 1

    return mwe_spans


def mark_mwe_tokens(tokens, mwe_spans):
    """
    Annotate tokens with MWE information.

    Args:
        tokens: List of token dicts
        mwe_spans: List of (start_idx, end_idx, mwe_info) from match_mwe_spans()

    Returns:
        list: Updated token list with MWE annotations
    """
    # Create a copy to avoid modifying original
    marked_tokens = []

    for idx, token in enumerate(tokens):
        marked_token = dict(token)  # Shallow copy

        # Check if this token is part of any MWE
        for start_idx, end_idx, mwe_info in mwe_spans:
            if start_idx <= idx < end_idx:
                # Mark token as part of MWE
                marked_token['mwe_span'] = (start_idx, end_idx)
                marked_token['mwe_lemma'] = mwe_info['lemma']
                marked_token['mwe_pos'] = mwe_info['pos']
                marked_token['mwe_type'] = mwe_info['type']
                marked_token['mwe_head'] = start_idx  # First token is head
                marked_token['mwe_position'] = idx - start_idx  # Position within MWE
                break

        marked_tokens.append(marked_token)

    return marked_tokens


def get_mwe_statistics(mwe_database):
    """
    Get statistics about an MWE database.

    Args:
        mwe_database: MWE dictionary

    Returns:
        dict: Statistics including count, length distribution, POS distribution
    """
    if not mwe_database:
        return {
            'total_mwes': 0,
            'length_distribution': {},
            'pos_distribution': {},
            'type_distribution': {}
        }

    length_dist = defaultdict(int)
    pos_dist = defaultdict(int)
    type_dist = defaultdict(int)

    for mwe_text, mwe_info in mwe_database.items():
        length = len(mwe_text.split())
        length_dist[length] += 1

        pos = mwe_info.get('pos', 'UNK')
        pos_dist[pos] += 1

        mwe_type = mwe_info.get('type', 'unknown')
        type_dist[mwe_type] += 1

    return {
        'total_mwes': len(mwe_database),
        'length_distribution': dict(length_dist),
        'pos_distribution': dict(pos_dist),
        'type_distribution': dict(type_dist)
    }
