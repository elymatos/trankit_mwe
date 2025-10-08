# Lemma Dictionary Guide for Trankit MWE Recognition

## Overview

The **lemma_dict** feature allows you to provide pre-computed wordform→lemma mappings for accurate MWE recognition. This is especially useful for handling irregular forms, verb conjugations, and other morphological variations that programmatic rules cannot handle reliably.

## Why Use a Lemma Dictionary?

### Problems with Programmatic Rules

Programmatic lemmatization rules are error-prone and limited:

```python
# Programmatic rule: remove 's' for plural
"cafés" → "café" ✓ (correct)
"papéis" → "papéi" ✗ (wrong! should be "papel")

# Rules can't handle irregular verbs
"deu" → ? (no rule knows this is from "dar")
"foram" → "foram" (stays unchanged, wrong!)
```

### Benefits of Lemma Dictionary

With a lemma dictionary, you get:

1. **100% accurate lemmatization** for all forms in your database
2. **Handles all irregulars**: verbs, plurals, gender agreement
3. **Fast lookup**: O(1) dictionary access vs rule processing
4. **Complete control**: you define what each form maps to
5. **Fallback support**: uses rules for words not in dictionary

## Basic Usage

### 1. Create Your Lemma Dictionary

```python
# Format: {"wordform": "lemma"}
portuguese_lemmas = {
    # Irregular verbs
    "deu": "dar",
    "deram": "dar",
    "dei": "dar",
    "dá": "dar",

    "foi": "ser",
    "foram": "ser",
    "é": "ser",

    "fez": "fazer",
    "fizeram": "fazer",

    # Irregular plurals
    "papéis": "papel",
    "anéis": "anel",
    "hotéis": "hotel",

    # Regular forms (optional, but improves speed)
    "cafés": "café",
    "carros": "carro",
    "casas": "casa",
}
```

### 2. Initialize Pipeline with Lemma Dictionary

```python
from trankit import Pipeline

mwe_database = {
    "dar certo": {"lemma": "dar certo", "pos": "VERB", "type": "fixed"},
    "papel de parede": {"lemma": "papel de parede", "pos": "NOUN", "type": "fixed"}
}

p = Pipeline('portuguese',
             gpu=False,
             mwe_database=mwe_database,
             lemma_dict=portuguese_lemmas)
```

### 3. Process Text

```python
# Inflected forms will match correctly
result = p("Tudo deu certo ontem.")  # "deu" → "dar" → matches "dar certo"
result = p("Os papéis de parede estão velhos.")  # "papéis" → "papel" → matches
```

## Loading from JSON File

You can store your lemma dictionary in a JSON file:

```json
{
  "deu": "dar",
  "deram": "dar",
  "dei": "dar",
  "foi": "ser",
  "foram": "ser",
  "papéis": "papel",
  "anéis": "anel"
}
```

Then load it:

```python
p = Pipeline('portuguese',
             gpu=False,
             mwe_database=mwe_database,
             lemma_dict="path/to/lemmas.json")
```

## How It Works

### Priority System

The lemmatization process follows this priority:

1. **Check lemma_dict first** (if provided)
2. **Fallback to programmatic rules** (if word not in dict)
3. **Return lowercase** (if no rule matches)

```python
def quick_lemmatize(word, language='portuguese', lemma_dict=None):
    word_lower = word.lower()

    # Priority 1: Dictionary lookup
    if lemma_dict and word_lower in lemma_dict:
        return lemma_dict[word_lower]

    # Priority 2: Programmatic rules
    if language == 'portuguese':
        return apply_portuguese_rules(word_lower)

    # Default: return lowercase
    return word_lower
```

### Case Insensitivity

All lookups are case-insensitive:

```python
lemma_dict = {"deu": "dar"}

# All these work:
"deu" → "dar"
"Deu" → "dar"
"DEU" → "dar"
```

## Creating Your Lemma Dictionary from Database

If you have a table with wordforms and lemmas, you can easily convert it:

### SQL Query Example

```sql
SELECT wordform, lemma
FROM word_forms
WHERE language = 'pt';
```

### Python Conversion

```python
import psycopg2
import json

# Connect to database
conn = psycopg2.connect(...)
cursor = conn.cursor()

# Query wordforms
cursor.execute("SELECT wordform, lemma FROM word_forms WHERE language = 'pt'")

# Build dictionary
lemma_dict = {}
for wordform, lemma in cursor.fetchall():
    lemma_dict[wordform.lower()] = lemma.lower()

# Save to JSON
with open('portuguese_lemmas.json', 'w', encoding='utf-8') as f:
    json.dump(lemma_dict, f, ensure_ascii=False, indent=2)

print(f"Created lemma dictionary with {len(lemma_dict)} entries")
```

### Pandas Example

```python
import pandas as pd
import json

# Load from CSV/Excel/SQL
df = pd.read_csv('wordforms.csv')  # Columns: wordform, lemma

# Create dictionary
lemma_dict = dict(zip(
    df['wordform'].str.lower(),
    df['lemma'].str.lower()
))

# Save to JSON
with open('lemmas.json', 'w', encoding='utf-8') as f:
    json.dump(lemma_dict, f, ensure_ascii=False, indent=2)
```

## Performance Considerations

### Dictionary Size

- **Small dictionaries** (< 10,000 entries): negligible memory impact
- **Medium dictionaries** (10,000 - 100,000 entries): ~1-2 MB RAM
- **Large dictionaries** (> 100,000 entries): ~10-20 MB RAM

Dictionary lookup is O(1), so size doesn't significantly impact speed.

### What to Include

You don't need to include every possible wordform. Focus on:

1. **Irregular forms** (essential)
2. **Common words** with inflections (recommended)
3. **MWE component words** (recommended)
4. **Regular forms** (optional, for speed)

## Example: Complete Workflow

```python
from trankit import Pipeline
import json

# 1. Define MWE database
mwe_database = {
    "dar certo": {"lemma": "dar certo", "pos": "VERB", "type": "fixed"},
    "fazer sentido": {"lemma": "fazer sentido", "pos": "VERB", "type": "fixed"},
    "de acordo com": {"lemma": "de acordo com", "pos": "ADP", "type": "fixed"}
}

# 2. Load lemma dictionary from your database export
with open('portuguese_lemmas.json', 'r', encoding='utf-8') as f:
    lemma_dict = json.load(f)

print(f"Loaded {len(lemma_dict)} lemma mappings")

# 3. Initialize pipeline
p = Pipeline('portuguese',
             gpu=False,
             mwe_database=mwe_database,
             lemma_dict=lemma_dict)

# 4. Process text with inflected MWEs
texts = [
    "Tudo deu certo no final.",              # deu → dar
    "As coisas deram certo.",                 # deram → dar
    "Isso não fez sentido para mim.",        # fez → fazer
    "De acordo com o relatório, tudo certo." # exact match
]

for text in texts:
    result = p(text)
    print(f"\nText: {text}")

    for sent in result['sentences']:
        for token in sent['tokens']:
            if 'mwe_span' in token:
                print(f"  MWE: {token['text']} → {token['mwe_lemma']}")
```

## Troubleshooting

### MWE Not Matching

If an MWE is not matching, check:

1. **Is the wordform in lemma_dict?**
   ```python
   print("deu" in lemma_dict)  # Should be True
   print(lemma_dict.get("deu"))  # Should be "dar"
   ```

2. **Is the lemma correct?**
   ```python
   # MWE: "dar certo"
   # Input: "deu certo"
   # lemma_dict["deu"] should be "dar" (not "deu")
   ```

3. **Are there extra spaces/characters?**
   ```python
   # Wrong:
   lemma_dict[" deu "] = "dar"  # Has spaces!

   # Correct:
   lemma_dict["deu"] = "dar"
   ```

### Testing Your Lemma Dictionary

```python
from trankit.utils.mwe_utils import quick_lemmatize

# Test individual words
test_words = ["deu", "deram", "papéis", "foram"]

for word in test_words:
    lemma = quick_lemmatize(word, 'portuguese', lemma_dict)
    print(f"{word} → {lemma}")
```

## Best Practices

1. **Start with irregulars**: Focus on irregular verbs and plurals first
2. **Use your corpus**: Extract wordforms from your actual text data
3. **Version control**: Keep lemma_dict in git for reproducibility
4. **Document sources**: Note where each mapping comes from
5. **Test coverage**: Verify all MWE component forms are covered

## Summary

The lemma_dict feature transforms Trankit MWE recognition from rule-based guessing to database-backed precision. By providing your own wordform→lemma mappings, you gain:

- ✅ 100% accurate lemmatization for your corpus
- ✅ Full control over irregular forms
- ✅ Better MWE matching recall
- ✅ Easy integration with existing linguistic databases
- ✅ Backward compatibility (optional feature)

For best results, extract wordforms from your linguistic database and use them with Trankit's MWE recognition!
