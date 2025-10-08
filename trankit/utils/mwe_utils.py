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


def quick_lemmatize(word, language='portuguese'):
    """
    Fast lemmatization using morphological rules.

    This is a simplified lemmatizer for MWE matching. It applies
    common morphological patterns to normalize inflected forms.

    Args:
        word: Input word (string)
        language: Language code

    Returns:
        str: Lemmatized form
    """
    if not word:
        return word

    word_lower = word.lower()

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
        if len(word) > 4 and word[-4] in 'aeiou':
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


def build_mwe_trie(mwe_database, language='portuguese'):
    """
    Build a trie structure for efficient MWE matching.

    The trie stores lemmatized forms of MWEs for fast lookup.

    Args:
        mwe_database: MWE dictionary
        language: Language code for lemmatization

    Returns:
        dict: Trie structure where each node contains:
            - children: dict of next tokens
            - mwe_info: MWE metadata if this is an endpoint
    """
    trie = {}

    for mwe_text, mwe_info in mwe_database.items():
        # Tokenize and lemmatize the MWE
        tokens = mwe_text.split()
        lemmas = [quick_lemmatize(t, language) for t in tokens]

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


def match_mwe_spans(tokens, mwe_trie, language='portuguese', max_length=10):
    """
    Find all MWE spans in a token sequence using longest-match-first.

    Args:
        tokens: List of token dicts with 'text' field (and optionally 'lemma')
        mwe_trie: Trie structure from build_mwe_trie()
        language: Language code for lemmatization
        max_length: Maximum MWE length to consider

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
                lemma = quick_lemmatize(token.get('text', token.get(TEXT, '')), language)

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
