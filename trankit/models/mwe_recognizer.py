"""
Multiword Expression (MWE) Recognizer for Trankit.

This module provides MWE recognition capabilities using lemma-based
dictionary matching. It identifies fixed expressions, idioms, and
other multiword units that should be treated as single linguistic units.
"""

from ..utils.mwe_utils import (
    load_mwe_database,
    load_lemma_dict,
    build_mwe_trie,
    match_mwe_spans,
    mark_mwe_tokens,
    get_mwe_statistics
)
from ..utils.conll import *


class MWERecognizer:
    """
    Recognizes and marks Multiword Expressions in tokenized text.

    This class uses a dictionary-based approach with lemma normalization
    to identify MWEs. It supports:
    - Fixed expressions (e.g., "de acordo com")
    - Inflected MWEs (e.g., "café da manhã", "cafés da manhã")
    - Longest-match-first matching strategy
    - Fast trie-based lookup
    - Optional wordform→lemma dictionary for accurate lemmatization

    Attributes:
        language (str): Language code
        mwe_database (dict): Raw MWE dictionary
        lemma_dict (dict): Wordform→lemma mapping dictionary
        mwe_trie (dict): Trie structure for efficient matching
        max_mwe_length (int): Maximum MWE length to consider
        enabled (bool): Whether MWE recognition is active
    """

    def __init__(self, language, mwe_database=None, lemma_dict=None, max_mwe_length=10):
        """
        Initialize the MWE recognizer.

        Args:
            language (str): Language code (e.g., 'portuguese', 'pt')
            mwe_database: MWE dictionary or path to JSON file
            lemma_dict: Optional wordform→lemma dictionary or path to JSON file.
                       If provided, this is used for accurate lemmatization instead
                       of programmatic rules.
            max_mwe_length (int): Maximum number of tokens in an MWE
        """
        self.language = language
        self.max_mwe_length = max_mwe_length

        # Load MWE database
        self.mwe_database = load_mwe_database(mwe_database, language)

        # Load lemma dictionary
        self.lemma_dict = load_lemma_dict(lemma_dict, language)

        # Build trie for efficient matching
        if self.mwe_database:
            self.mwe_trie = build_mwe_trie(self.mwe_database, language, self.lemma_dict)
            self.enabled = True
            lemma_info = f" with {len(self.lemma_dict)} lemma mappings" if self.lemma_dict else ""
            print(f'Loaded MWE recognizer for {language}: {len(self.mwe_database)} expressions{lemma_info}')
        else:
            self.mwe_trie = {}
            self.enabled = False

    def recognize_in_sentence(self, sentence_tokens):
        """
        Recognize MWEs in a single sentence.

        Args:
            sentence_tokens (list): List of token dictionaries with 'text' field

        Returns:
            list: Token list with MWE annotations added
        """
        if not self.enabled or not sentence_tokens:
            return sentence_tokens

        # Find MWE spans
        mwe_spans = match_mwe_spans(
            sentence_tokens,
            self.mwe_trie,
            self.language,
            self.max_mwe_length,
            self.lemma_dict
        )

        # Mark tokens with MWE information
        if mwe_spans:
            marked_tokens = mark_mwe_tokens(sentence_tokens, mwe_spans)
            return marked_tokens

        return sentence_tokens

    def recognize_in_document(self, document):
        """
        Recognize MWEs in a document (list of sentences).

        Args:
            document (list): List of sentence dicts, each with TOKENS field

        Returns:
            list: Document with MWE annotations added to tokens
        """
        if not self.enabled or not document:
            return document

        processed_doc = []

        for sentence in document:
            if TOKENS not in sentence:
                processed_doc.append(sentence)
                continue

            # Process tokens in this sentence
            tokens = sentence[TOKENS]

            # Handle expanded tokens (from MWT)
            processed_tokens = []
            for token in tokens:
                if EXPANDED in token and token[EXPANDED]:
                    # Token has been expanded by MWT - process expanded words
                    expanded_words = token[EXPANDED]
                    marked_expanded = self.recognize_in_sentence(expanded_words)

                    # Update the expanded words with MWE annotations
                    token_copy = dict(token)
                    token_copy[EXPANDED] = marked_expanded
                    processed_tokens.append(token_copy)
                else:
                    processed_tokens.append(token)

            # Also check for MWEs at the main token level
            # (for languages without MWT or after MWT expansion)
            marked_tokens = self.recognize_in_sentence(processed_tokens)

            # Create updated sentence
            updated_sentence = dict(sentence)
            updated_sentence[TOKENS] = marked_tokens
            processed_doc.append(updated_sentence)

        return processed_doc

    def get_statistics(self):
        """
        Get statistics about the loaded MWE database.

        Returns:
            dict: Statistics including count, length distribution, etc.
        """
        return get_mwe_statistics(self.mwe_database)

    def add_mwe(self, mwe_text, lemma=None, pos='X', mwe_type='fixed'):
        """
        Add a new MWE to the database at runtime.

        Args:
            mwe_text (str): Surface form of MWE (e.g., "café da manhã")
            lemma (str): Lemma form (defaults to mwe_text)
            pos (str): Part-of-speech tag
            mwe_type (str): MWE type ('fixed', 'flat', 'compound')
        """
        if lemma is None:
            lemma = mwe_text

        self.mwe_database[mwe_text] = {
            'lemma': lemma,
            'pos': pos,
            'type': mwe_type
        }

        # Rebuild trie
        self.mwe_trie = build_mwe_trie(self.mwe_database, self.language, self.lemma_dict)
        self.enabled = True

    def remove_mwe(self, mwe_text):
        """
        Remove an MWE from the database.

        Args:
            mwe_text (str): Surface form to remove
        """
        if mwe_text in self.mwe_database:
            del self.mwe_database[mwe_text]

            # Rebuild trie
            self.mwe_trie = build_mwe_trie(self.mwe_database, self.language, self.lemma_dict)

            if not self.mwe_database:
                self.enabled = False


class MWEWrapper:
    """
    Wrapper class for MWE recognition compatible with Trankit's architecture.

    This provides a similar interface to MWTWrapper and LemmaWrapper
    for consistency with Trankit's design patterns.
    """

    def __init__(self, config, treebank_name, language=None):
        """
        Initialize MWE wrapper.

        Args:
            config: Trankit configuration object
            treebank_name (str): Treebank identifier
            language (str): Language code (optional, inferred from config)
        """
        self.config = config
        self.treebank_name = treebank_name

        if language is None:
            from ..utils.tbinfo import treebank2lang
            language = treebank2lang.get(treebank_name, 'unknown')

        # Get MWE database from config
        mwe_database = getattr(config, 'mwe_database', None)
        max_length = getattr(config, 'mwe_max_length', 10)

        # Initialize recognizer
        self.recognizer = MWERecognizer(
            language=language,
            mwe_database=mwe_database,
            max_mwe_length=max_length
        )

    def predict(self, tokenized_doc):
        """
        Recognize MWEs in tokenized document.

        Args:
            tokenized_doc: Document dict or list of sentence dicts

        Returns:
            Document with MWE annotations
        """
        return self.recognizer.recognize_in_document(tokenized_doc)

    @property
    def enabled(self):
        """Check if MWE recognition is enabled."""
        return self.recognizer.enabled
