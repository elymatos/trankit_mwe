#!/usr/bin/env sh

# Pre-start script for Trankit MWE API
# This script runs before the API starts

echo "Running pre-start checks..."

# Check if MWE database exists
if [ -f "data/portuguese/mwe_database.json" ]; then
    echo "✓ MWE database found"
else
    echo "⚠ Warning: MWE database not found at data/portuguese/mwe_database.json"
    echo "  MWE recognition will be disabled"
    echo "  To enable, run: python scripts/extract_dictionaries_from_db.py"
fi

# Check if lemma dictionary exists
if [ -f "data/portuguese/lemma_dict.json" ]; then
    echo "✓ Lemma dictionary found"
else
    echo "⚠ Warning: Lemma dictionary not found at data/portuguese/lemma_dict.json"
    echo "  Using without lemma dictionary (may reduce accuracy)"
fi

# Create cache directory if it doesn't exist
mkdir -p ./cache/trankit/
echo "✓ Cache directory ready"

echo "Pre-start checks complete"
