#!/usr/bin/env python3
"""
Extract MWE and Lemma Dictionaries from MariaDB Database

This script connects to a MariaDB database and extracts:
1. MWE (Multiword Expression) database from view_lemma
2. Lemma dictionary (wordform→lemma mappings) from view_lexicon

Usage:
    python scripts/extract_dictionaries_from_db.py [--output-dir data/portuguese]

Requirements:
    pip install mysql-connector-python

Configuration:
    Database credentials are read from DB.INI file in the project root.

Output:
    - data/portuguese/mwe_database.json
    - data/portuguese/lemma_dict.json
"""

import sys
import os
import json
import configparser
import argparse
from collections import defaultdict
from pathlib import Path

try:
    import mysql.connector
except ImportError:
    print("Error: mysql-connector-python is not installed.")
    print("Please install it with: pip install mysql-connector-python")
    sys.exit(1)


def load_db_config(config_file='DB.INI'):
    """
    Load database configuration from INI file.

    Args:
        config_file (str): Path to the INI configuration file

    Returns:
        dict: Database connection parameters
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    config = configparser.ConfigParser()
    config.read(config_file)

    if 'DATABASE' not in config:
        raise ValueError("DATABASE section not found in configuration file")

    db_config = {
        'host': config['DATABASE']['host'],
        'port': int(config['DATABASE']['port']),
        'database': config['DATABASE']['database'],
        'user': config['DATABASE']['user'],
        'password': config['DATABASE']['password']
    }

    return db_config


def extract_mwe_database(cursor):
    """
    Extract MWE database from view_lemma table.

    Query: SELECT name, udPOS FROM view_lemma WHERE name LIKE '% %'

    Args:
        cursor: MySQL cursor object

    Returns:
        dict: MWE database in format:
            {
                "café da manhã": {
                    "lemma": "café da manhã",
                    "pos": "NOUN",
                    "type": "fixed"
                },
                ...
            }
    """
    print("\nExtracting MWE database...")
    print("Query: SELECT name, udPOS FROM view_lemma WHERE name LIKE '% %'")

    query = """
        SELECT name, udPOS
        FROM view_lemma
        WHERE name LIKE '% %'
    """

    cursor.execute(query)
    results = cursor.fetchall()

    mwe_database = {}
    pos_stats = defaultdict(int)

    for row in results:
        name, udpos = row

        # Skip if name or POS is None
        if not name or not udpos:
            continue

        # Create MWE entry
        mwe_database[name] = {
            "lemma": name,
            "pos": udpos,
            "type": "fixed"  # All MWEs from database are marked as "fixed"
        }

        pos_stats[udpos] += 1

    print(f"✓ Extracted {len(mwe_database)} MWE expressions")
    print(f"  POS distribution: {dict(pos_stats)}")

    return mwe_database


def extract_lemma_dictionary(cursor):
    """
    Extract lemma dictionary from view_lexicon and view_lemma tables.

    Query: SELECT lx.form, lm.name as lemma, lm.udPOS
           FROM view_lexicon lx
           JOIN view_lemma lm ON (lx.idLemma = lm.idLemma)

    Args:
        cursor: MySQL cursor object

    Returns:
        dict: Lemma dictionary in format:
            {
                "flores": "flor",
                "cafés": "café",
                ...
            }
    """
    print("\nExtracting lemma dictionary...")
    print("Query: SELECT lx.form, lm.name as lemma, lm.udPOS FROM view_lexicon lx JOIN view_lemma lm ON (lx.idLemma = lm.idLemma) WHERE lm.name NOT LIKE '% %'")

    query = """
        SELECT lx.form, lm.name as lemma, lm.udPOS
        FROM view_lexicon lx
        JOIN view_lemma lm ON (lx.idLemma = lm.idLemma)
        WHERE lm.name NOT LIKE '% %'
    """

    cursor.execute(query)
    results = cursor.fetchall()

    lemma_dict = {}
    pos_stats = defaultdict(int)
    skipped = 0
    conflicts = 0

    for row in results:
        form, lemma, udpos = row

        # Skip if form or lemma is None
        if not form or not lemma:
            skipped += 1
            continue

        # Lowercase for case-insensitive matching
        form_lower = form.lower()
        lemma_lower = lemma.lower()

        # Skip identity mappings (form == lemma) to save space
        if form_lower == lemma_lower:
            continue

        # PORTUGUESE-SPECIFIC FILTER: Skip contractions
        # Contractions are handled by Trankit's MWT expander and shouldn't be in lemma_dict
        # Common Portuguese contractions: da, do, das, dos, na, no, nas, nos, ao, aos, à, às, etc.
        portuguese_contractions = {
            'da', 'do', 'das', 'dos',       # de + article
            'na', 'no', 'nas', 'nos',       # em + article
            'ao', 'aos', 'à', 'às',         # a + article
            'pela', 'pelo', 'pelas', 'pelos', # por + article
            'dum', 'duma', 'duns', 'dumas', # de + um
            'num', 'numa', 'nuns', 'numas', # em + um
            'dele', 'dela', 'deles', 'delas', # de + pronoun
            'nele', 'nela', 'neles', 'nelas', # em + pronoun
            'deste', 'desta', 'destes', 'destas', # de + demonstrative
            'neste', 'nesta', 'nestes', 'nestas', # em + demonstrative
            'desse', 'dessa', 'desses', 'dessas', # de + demonstrative
            'nesse', 'nessa', 'nesses', 'nessas', # em + demonstrative
            'daquele', 'daquela', 'daqueles', 'daquelas', # de + demonstrative
            'naquele', 'naquela', 'naqueles', 'naquelas', # em + demonstrative
            'disto', 'disso', 'daquilo',    # de + demonstrative
            'nisto', 'nisso', 'naquilo'     # em + demonstrative
        }

        if form_lower in portuguese_contractions:
            skipped += 1
            continue

        # DATA QUALITY FILTER: Handle conflicts when form has multiple lemmas
        # (e.g., "da" could map to both "dar" (verb) and "de" (preposition))
        if form_lower in lemma_dict:
            existing_lemma = lemma_dict[form_lower]
            if existing_lemma != lemma_lower:
                # Conflict detected - keep the shorter lemma (usually more basic)
                if len(lemma_lower) < len(existing_lemma):
                    lemma_dict[form_lower] = lemma_lower
                    conflicts += 1
                else:
                    conflicts += 1
                continue

        # Add mapping
        lemma_dict[form_lower] = lemma_lower
        pos_stats[udpos] += 1

    print(f"✓ Extracted {len(lemma_dict)} wordform→lemma mappings")
    print(f"  Skipped {skipped} entries (NULL values, contractions, or identity mappings)")
    print(f"  Resolved {conflicts} conflicting mappings (kept shorter lemma)")
    print(f"  POS distribution (top 5): {dict(sorted(pos_stats.items(), key=lambda x: x[1], reverse=True)[:5])}")

    return lemma_dict


def save_json(data, filepath):
    """
    Save data to JSON file with pretty formatting.

    Args:
        data (dict): Data to save
        filepath (str): Output file path
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"✓ Saved to: {filepath}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Extract MWE and Lemma dictionaries from MariaDB database'
    )
    parser.add_argument(
        '--output-dir',
        default='data/portuguese',
        help='Output directory for JSON files (default: data/portuguese)'
    )
    parser.add_argument(
        '--config',
        default='DB.INI',
        help='Path to database configuration file (default: DB.INI)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("MWE and Lemma Dictionary Extraction from Database")
    print("=" * 80)

    # Load database configuration
    try:
        print(f"\nLoading database configuration from: {args.config}")
        db_config = load_db_config(args.config)
        print(f"✓ Configuration loaded successfully")
        print(f"  Host: {db_config['host']}")
        print(f"  Database: {db_config['database']}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Connect to database
    try:
        print(f"\nConnecting to database...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        print(f"✓ Connected successfully")
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

    try:
        # Extract MWE database
        mwe_database = extract_mwe_database(cursor)

        # Extract lemma dictionary
        lemma_dict = extract_lemma_dictionary(cursor)

        # Save to JSON files
        print("\nSaving JSON files...")
        mwe_output = os.path.join(args.output_dir, 'mwe_database.json')
        lemma_output = os.path.join(args.output_dir, 'lemma_dict.json')

        save_json(mwe_database, mwe_output)
        save_json(lemma_dict, lemma_output)

        # Summary
        print("\n" + "=" * 80)
        print("Extraction completed successfully!")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  MWE expressions:     {len(mwe_database):,}")
        print(f"  Lemma mappings:      {len(lemma_dict):,}")
        print(f"\nOutput files:")
        print(f"  {mwe_output}")
        print(f"  {lemma_output}")
        print("\nYou can now use these files with Trankit:")
        print(f"  p = Pipeline('portuguese',")
        print(f"               mwe_database='{mwe_output}',")
        print(f"               lemma_dict='{lemma_output}')")

    except Exception as e:
        print(f"\nError during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Close database connection
        cursor.close()
        connection.close()
        print("\n✓ Database connection closed")


if __name__ == '__main__':
    main()
