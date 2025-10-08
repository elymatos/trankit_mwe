# Database Extraction Guide for MWE and Lemma Dictionaries

This guide explains how to extract MWE (Multiword Expression) and lemma dictionaries from your MariaDB database for use with Trankit's MWE recognition feature.

---

## Overview

The extraction script (`scripts/extract_dictionaries_from_db.py`) connects to your MariaDB database and extracts:

1. **MWE Database** - Multiword expressions from `view_lemma` table
2. **Lemma Dictionary** - Wordform→lemma mappings from `view_lexicon` and `view_lemma` tables

The extracted data is saved as JSON files that can be directly used with Trankit's Pipeline.

---

## Prerequisites

### 1. Database Access

Ensure you have:
- MariaDB/MySQL database with Portuguese linguistic data
- Database credentials in `DB.INI` file (already configured)
- Network access to the database server

### 2. Python Package

Install the MySQL connector:

```bash
# Activate your conda environment
conda activate trankit_mwe

# Install MySQL connector
pip install mysql-connector-python
```

---

## Database Schema

The script uses these SQL queries:

### MWE Extraction Query
```sql
SELECT name, udPOS
FROM view_lemma
WHERE name LIKE '% %'
```

This extracts all lemmas that contain spaces (i.e., multiword expressions).

### Lemma Dictionary Extraction Query
```sql
SELECT lx.form, lm.name as lemma, lm.udPOS
FROM view_lexicon lx
JOIN view_lemma lm ON (lx.idLemma = lm.idLemma)
WHERE lm.name NOT LIKE '% %'
```

This extracts all wordform→lemma relationships for accurate lemmatization.

**Important**: The `WHERE lm.name NOT LIKE '% %'` clause filters out MWE lemmas, ensuring only single-word lemmas are included. This prevents data quality issues where a wordform might incorrectly map to a multiword expression.

---

## Usage

### Basic Extraction

Run the extraction script from the project root:

```bash
python scripts/extract_dictionaries_from_db.py
```

This will:
1. Read database credentials from `DB.INI`
2. Connect to the database
3. Extract MWE and lemma data
4. Save JSON files to `data/portuguese/`

### Custom Output Directory

Specify a different output directory:

```bash
python scripts/extract_dictionaries_from_db.py --output-dir /path/to/output
```

### Custom Config File

Use a different configuration file:

```bash
python scripts/extract_dictionaries_from_db.py --config /path/to/config.ini
```

### Help

View all options:

```bash
python scripts/extract_dictionaries_from_db.py --help
```

---

## Expected Output

### Console Output

```
================================================================================
MWE and Lemma Dictionary Extraction from Database
================================================================================

Loading database configuration from: DB.INI
✓ Configuration loaded successfully
  Host: server3.frame.net.br
  Database: webtool40_db

Connecting to database...
✓ Connected successfully

Extracting MWE database...
Query: SELECT name, udPOS FROM view_lemma WHERE name LIKE '% %'
✓ Extracted 1,234 MWE expressions
  POS distribution: {'NOUN': 543, 'ADV': 321, 'ADP': 210, ...}

Extracting lemma dictionary...
Query: SELECT lx.form, lm.name as lemma, lm.udPOS FROM view_lexicon lx JOIN view_lemma lm ON (lx.idLemma = lm.idLemma)
✓ Extracted 45,678 wordform→lemma mappings
  Skipped 123 entries with NULL values
  POS distribution (top 5): {'VERB': 12345, 'NOUN': 9876, ...}

Saving JSON files...
✓ Saved to: data/portuguese/mwe_database.json
✓ Saved to: data/portuguese/lemma_dict.json

================================================================================
Extraction completed successfully!
================================================================================

Summary:
  MWE expressions:     1,234
  Lemma mappings:      45,678

Output files:
  data/portuguese/mwe_database.json
  data/portuguese/lemma_dict.json

You can now use these files with Trankit:
  p = Pipeline('portuguese',
               mwe_database='data/portuguese/mwe_database.json',
               lemma_dict='data/portuguese/lemma_dict.json')

✓ Database connection closed
```

### Generated Files

#### `data/portuguese/mwe_database.json`

Format:
```json
{
  "a fim de": {
    "lemma": "a fim de",
    "pos": "ADP",
    "type": "fixed"
  },
  "além de": {
    "lemma": "além de",
    "pos": "ADP",
    "type": "fixed"
  },
  "café da manhã": {
    "lemma": "café da manhã",
    "pos": "NOUN",
    "type": "fixed"
  },
  "de acordo com": {
    "lemma": "de acordo com",
    "pos": "ADP",
    "type": "fixed"
  }
}
```

#### `data/portuguese/lemma_dict.json`

Format:
```json
{
  "cafés": "café",
  "deu": "dar",
  "flores": "flor",
  "foi": "ser",
  "lemos": "ler",
  "manhãs": "manhã",
  "tomei": "tomar",
  "veio": "vir"
}
```

---

## Using Extracted Dictionaries with Trankit

### Method 1: Direct File Paths

```python
from trankit import Pipeline

# Initialize pipeline with extracted dictionaries
p = Pipeline('portuguese',
             mwe_database='data/portuguese/mwe_database.json',
             lemma_dict='data/portuguese/lemma_dict.json')

# Parse text
text = "Tomei café da manhã de acordo com o plano."
result = p(text)

# Check for MWE annotations
for token in result['sentences'][0]['tokens']:
    if 'mwe_span' in token:
        print(f"Found MWE: {token['text']} → {token['mwe_lemma']}")
```

### Method 2: Load and Pass as Dictionaries

```python
import json
from trankit import Pipeline

# Load dictionaries
with open('data/portuguese/mwe_database.json', 'r', encoding='utf-8') as f:
    mwe_db = json.load(f)

with open('data/portuguese/lemma_dict.json', 'r', encoding='utf-8') as f:
    lemma_dict = json.load(f)

# Initialize pipeline
p = Pipeline('portuguese',
             mwe_database=mwe_db,
             lemma_dict=lemma_dict)
```

---

## Troubleshooting

### Issue: "mysql-connector-python is not installed"

**Solution:**
```bash
pip install mysql-connector-python
```

### Issue: "Configuration file not found: DB.INI"

**Solution:**
- Ensure you're running the script from the project root directory
- Or use `--config` to specify the correct path:
  ```bash
  python scripts/extract_dictionaries_from_db.py --config /path/to/DB.INI
  ```

### Issue: "Error connecting to database"

**Possible causes:**
1. Database server is not accessible
2. Incorrect credentials in `DB.INI`
3. Firewall blocking connection
4. Network issues

**Solution:**
- Verify database credentials
- Test connection manually:
  ```bash
  mysql -h server3.frame.net.br -u fnbrasil -p webtool40_db
  ```

### Issue: "Empty or small output files"

**Possible causes:**
1. Database tables are empty
2. No multiword expressions in database
3. SQL query returned no results

**Solution:**
- Verify tables exist and contain data:
  ```sql
  SELECT COUNT(*) FROM view_lemma WHERE name LIKE '% %';
  SELECT COUNT(*) FROM view_lexicon;
  ```

### Issue: "UnicodeDecodeError"

**Solution:**
- Ensure database uses UTF-8 encoding
- Script already handles UTF-8 with `encoding='utf-8'`

---

## Data Quality Considerations

### MWE Database

- **Only multiword expressions**: Query filters for entries with spaces
- **All marked as "fixed"**: Type is set to "fixed" for all MWEs
- **POS tags**: Uses Universal Dependencies POS tags from database
- **Contraction handling**: MWEs with contractions (e.g., "café da manhã") are automatically expanded during trie building to match Trankit's MWT expansion

### Lemma Dictionary

- **Case-insensitive**: All entries lowercased for matching
- **No identity mappings**: Entries where form=lemma are skipped to reduce file size
- **Handles irregular forms**: Captures irregular conjugations and plurals
- **MWE lemmas filtered**: SQL query excludes lemmas containing spaces (prevents "manhã" → "fim da manhã")
- **Contractions excluded**: Portuguese contractions (da, do, na, no, etc.) are excluded because they're handled by Trankit's MWT expander
- **Conflict resolution**: When a wordform has multiple lemmas, keeps the shorter one (usually more basic)

### Data Quality Filters Applied

The extraction script applies several filters to ensure data quality:

1. **SQL-level filtering**: `WHERE lm.name NOT LIKE '% %'` excludes MWE lemmas
2. **Contraction exclusion**: ~50 Portuguese contractions filtered out (da, do, na, no, pela, pelo, etc.)
3. **Conflict resolution**: When form maps to multiple lemmas, keeps shorter lemma
4. **NULL value handling**: Skips entries with missing forms or lemmas

### Why Contractions Are Excluded

Portuguese contractions like "da", "do", "na", "no" are **not included in the lemma dictionary** because:

1. **Trankit's MWT expands them automatically**: "da" → "de" + "a"
2. **MWE matching happens after expansion**: The recognizer sees expanded tokens
3. **Prevents incorrect mappings**: Database often maps "da" to "dar" (verb) instead of "de" (preposition)
4. **MWE trie handles expansion**: When building the trie, "café da manhã" is automatically expanded to ["café", "de", "a", "manhã"] to match MWT output

### How MWE Matching Works with Contractions

Example: "cafés da manhã"

1. **Input**: "cafés da manhã"
2. **MWT expansion**: ["cafés"] + ["de", "a"] + ["manhã"]
3. **Lemmatization**: ["café", "de", "a", "manhã"]
4. **MWE trie lookup**:
   - Database has: "café da manhã"
   - Trie expanded: ["café", "de", "a", "manhã"]
   - ✓ Match found!

### Recommendations

1. **Review extracted data**: Check generated JSON files for correctness
2. **Manual curation**: Add missing MWEs manually if needed
3. **Regular updates**: Re-run extraction when database is updated
4. **Backup files**: Keep copies of working dictionaries
5. **Monitor conflicts**: Check extraction output for resolved conflicts

---

## Script Details

### Configuration File Format (`DB.INI`)

```ini
[DATABASE]
host = server3.frame.net.br
port = 3306
database = webtool40_db
user = fnbrasil
password = OssracF1982
```

### Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--output-dir` | `data/portuguese` | Output directory for JSON files |
| `--config` | `DB.INI` | Path to database configuration file |
| `--help` | - | Show help message |

### Script Features

- ✅ Automatic directory creation
- ✅ Progress reporting with statistics
- ✅ Error handling for connection issues
- ✅ POS distribution analysis
- ✅ Pretty-formatted JSON output (sorted, indented)
- ✅ Case-insensitive lemma matching
- ✅ NULL value filtering

---

## Integration with Trankit Pipeline

The extracted dictionaries integrate seamlessly with Trankit:

```
Input Text
    ↓
Load JSON dictionaries
    ↓
Initialize Pipeline with dictionaries
    ↓
Parse text with MWE recognition
    ↓
Output with MWE annotations
```

See `examples/mwe_example.py` for complete usage examples.

---

## Next Steps

After extracting the dictionaries:

1. **Test the extraction**:
   ```bash
   python scripts/extract_dictionaries_from_db.py
   ```

2. **Verify output files**:
   ```bash
   ls -lh data/portuguese/
   head data/portuguese/mwe_database.json
   ```

3. **Test with Trankit**:
   ```bash
   python tests/test_parsing.py
   ```

4. **Use in your application**:
   ```python
   from trankit import Pipeline
   p = Pipeline('portuguese',
                mwe_database='data/portuguese/mwe_database.json',
                lemma_dict='data/portuguese/lemma_dict.json')
   ```

---

## Maintenance

### Updating Dictionaries

When database is updated:

```bash
# Re-run extraction
python scripts/extract_dictionaries_from_db.py

# Backup old files first (optional)
cp data/portuguese/mwe_database.json data/portuguese/mwe_database.json.bak
cp data/portuguese/lemma_dict.json data/portuguese/lemma_dict.json.bak
```

### Version Control

Consider adding to `.gitignore` if dictionaries are large or contain sensitive data:

```
# .gitignore
data/portuguese/mwe_database.json
data/portuguese/lemma_dict.json
DB.INI
```

Or commit them if they're part of the project:

```bash
git add data/portuguese/*.json
git commit -m "Update MWE and lemma dictionaries from database"
```

---

## Support

For issues or questions:

1. Check this documentation
2. Review script output for error messages
3. Verify database connectivity and schema
4. See `MWE_EXTENSION_DOCUMENTATION.md` for MWE feature details
5. Check `examples/mwe_example.py` for usage examples

---

**Last Updated**: 2025-10-08
