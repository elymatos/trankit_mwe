# Trankit MWE API Documentation

## Overview

The Trankit MWE (Multiword Expression) API is a RESTful web service that provides state-of-the-art NLP processing with specialized support for multiword expression recognition. Built on top of Trankit's transformer-based architecture, it offers sentence segmentation, tokenization, POS tagging, morphological analysis, dependency parsing, and MWE recognition for 100+ languages.

**Base URL**: `http://localhost:8406/api/v1`

**OpenAPI Documentation**: `http://localhost:8406/api/v1/docs`

**ReDoc Documentation**: `http://localhost:8406/api/v1/redoc`

## Features

- 🚀 **Fast Processing**: Transformer-based models with GPU acceleration support
- 🌍 **Multilingual**: Support for 100+ languages
- 🔤 **MWE Recognition**: Dictionary-based multiword expression detection with lemmatization
- 📦 **Batch Processing**: Efficient batch endpoint for multiple texts
- 🐳 **Docker Ready**: Containerized deployment with docker-compose
- 📊 **Production Ready**: Gunicorn + Uvicorn with health checks

## Quick Start

### Using Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd trankit_source

# 2. Extract MWE database (if not already done)
python scripts/extract_dictionaries_from_db.py

# 3. Create .env file from example
cp .env.example .env

# 4. Start the API server
docker-compose up -d

# 5. Check health
curl http://localhost:8406/api/v1/health
```

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements-api.txt

# 2. Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Or with gunicorn for production
gunicorn app.main:app -c app/gunicorn_conf.py
```

## API Endpoints

### 1. Health Check

**GET** `/api/v1/health`

Check API health and get information about loaded models.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "models_loaded": ["portuguese"],
  "mwe_enabled": true,
  "mwe_database_size": 15234,
  "lemma_dict_size": 342567
}
```

**Example**:
```bash
curl http://localhost:8406/api/v1/health
```

---

### 2. Parse Text

**POST** `/api/v1/parse`

Parse text with full NLP pipeline including MWE recognition.

**Request Body**:
```json
{
  "text": "Tomei café da manhã antes de sair.",
  "language": "portuguese",
  "mwe_enabled": true
}
```

**Parameters**:
- `text` (string, required): Text to parse
- `language` (string, optional): Language code (default: "portuguese")
- `mwe_enabled` (boolean, optional): Enable MWE recognition (default: true)

**Response**:
```json
{
  "sentences": [
    {
      "id": 1,
      "text": "Tomei café da manhã antes de sair.",
      "tokens": [
        {
          "id": 1,
          "text": "Tomei",
          "lemma": "tomar",
          "upos": "VERB",
          "xpos": "V",
          "feats": "Mood=Ind|Number=Sing|Person=1|Tense=Past|VerbForm=Fin",
          "head": 0,
          "deprel": "root"
        },
        {
          "id": 2,
          "text": "café",
          "lemma": "café da manhã",
          "upos": "NOUN",
          "xpos": "N",
          "head": 1,
          "deprel": "obj",
          "mwe_span": [2, 4],
          "mwe_lemma": "café da manhã",
          "mwe_pos": "NOUN",
          "mwe_type": "fixed"
        },
        {
          "id": "3-4",
          "text": "da",
          "misc": "MWT=Yes"
        },
        {
          "id": 3,
          "text": "de",
          "lemma": "café da manhã",
          "upos": "ADP",
          "xpos": "ADP",
          "head": 2,
          "deprel": "fixed",
          "mwe_span": [2, 4],
          "mwe_lemma": "café da manhã",
          "mwe_pos": "NOUN",
          "mwe_type": "fixed"
        },
        {
          "id": 4,
          "text": "a",
          "lemma": "café da manhã",
          "upos": "DET",
          "xpos": "DET",
          "head": 2,
          "deprel": "fixed",
          "mwe_span": [2, 4],
          "mwe_lemma": "café da manhã",
          "mwe_pos": "NOUN",
          "mwe_type": "fixed"
        },
        {
          "id": 5,
          "text": "manhã",
          "lemma": "café da manhã",
          "upos": "NOUN",
          "xpos": "N",
          "head": 2,
          "deprel": "fixed",
          "mwe_span": [2, 4],
          "mwe_lemma": "café da manhã",
          "mwe_pos": "NOUN",
          "mwe_type": "fixed"
        }
      ]
    }
  ],
  "mwe_count": 1,
  "mwes": [
    {
      "span": [2, 4],
      "text": "café da manhã",
      "lemma": "café da manhã",
      "pos": "NOUN",
      "type": "fixed",
      "tokens": ["café", "de", "a", "manhã"]
    }
  ],
  "language": "portuguese",
  "processing_time": 0.234
}
```

**Example**:
```bash
curl -X POST http://localhost:8406/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Tomei café da manhã antes de sair.",
    "language": "portuguese",
    "mwe_enabled": true
  }'
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:8406/api/v1/parse",
    json={
        "text": "Tomei café da manhã antes de sair.",
        "language": "portuguese",
        "mwe_enabled": True
    }
)

result = response.json()
print(f"Found {result['mwe_count']} MWEs")
for mwe in result['mwes']:
    print(f"  - {mwe['text']} ({mwe['lemma']})")
```

---

### 3. Parse Batch

**POST** `/api/v1/parse_batch`

Parse multiple texts in batch for better efficiency.

**Request Body**:
```json
{
  "texts": [
    "Tomei café da manhã.",
    "De acordo com o relatório, tudo está correto."
  ],
  "language": "portuguese",
  "mwe_enabled": true
}
```

**Parameters**:
- `texts` (array of strings, required): List of texts to parse
- `language` (string, optional): Language code (default: "portuguese")
- `mwe_enabled` (boolean, optional): Enable MWE recognition (default: true)

**Response**:
```json
{
  "results": [
    {
      "sentences": [...],
      "mwe_count": 1,
      "mwes": [...],
      "language": "portuguese",
      "processing_time": null
    },
    {
      "sentences": [...],
      "mwe_count": 1,
      "mwes": [...],
      "language": "portuguese",
      "processing_time": null
    }
  ],
  "total_texts": 2,
  "total_mwes": 2,
  "total_processing_time": 0.456
}
```

**Example**:
```bash
curl -X POST http://localhost:8406/api/v1/parse_batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Tomei café da manhã.",
      "De acordo com o relatório, tudo está correto."
    ],
    "language": "portuguese",
    "mwe_enabled": true
  }'
```

---

### 4. MWE Recognition Only

**POST** `/api/v1/mwe_only`

Perform only MWE recognition without full parsing (lighter and faster).

**Request Body**:
```json
{
  "text": "Tomei café da manhã de acordo com o plano.",
  "language": "portuguese"
}
```

**Parameters**:
- `text` (string, required): Text to analyze for MWEs
- `language` (string, optional): Language code (default: "portuguese")

**Response**:
```json
{
  "text": "Tomei café da manhã de acordo com o plano.",
  "mwe_count": 2,
  "mwes": [
    {
      "span": [2, 4],
      "text": "café da manhã",
      "lemma": "café da manhã",
      "pos": "NOUN",
      "type": "fixed",
      "tokens": ["café", "de", "a", "manhã"]
    },
    {
      "span": [5, 7],
      "text": "de acordo com",
      "lemma": "de acordo com",
      "pos": "ADP",
      "type": "fixed",
      "tokens": ["de", "acordo", "com"]
    }
  ],
  "language": "portuguese",
  "processing_time": 0.145
}
```

**Example**:
```bash
curl -X POST http://localhost:8406/api/v1/mwe_only \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Tomei café da manhã de acordo com o plano.",
    "language": "portuguese"
  }'
```

---

### 5. Parse Pre-tokenized Text

**POST** `/api/v1/parse_tokens`

Parse text that has already been tokenized.

**Request Body**:
```json
{
  "tokens": ["Tomei", "café", "da", "manhã", "."],
  "language": "portuguese",
  "mwe_enabled": true
}
```

**Parameters**:
- `tokens` (array of strings, required): List of tokens
- `language` (string, optional): Language code (default: "portuguese")
- `mwe_enabled` (boolean, optional): Enable MWE recognition (default: true)

**Response**:
Same format as `/parse` endpoint.

**Example**:
```bash
curl -X POST http://localhost:8406/api/v1/parse_tokens \
  -H "Content-Type: application/json" \
  -d '{
    "tokens": ["Tomei", "café", "da", "manhã", "."],
    "language": "portuguese",
    "mwe_enabled": true
  }'
```

---

## MWE Recognition Details

### How It Works

1. **Tokenization**: Text is tokenized and contractions are expanded (e.g., "da" → "de" + "a")
2. **Lemmatization**: Tokens are lemmatized using the lemma dictionary
3. **MWE Matching**: Lemmatized forms are matched against MWE trie structure
4. **Annotation**: Matching tokens are annotated with MWE information

### Contraction Handling

Portuguese contractions are automatically handled:

| Contraction | Expansion | Example |
|-------------|-----------|---------|
| da | de + a | "café da manhã" → "café de a manhã" |
| do | de + o | "em cima do morro" |
| na | em + a | "na hora" |
| no | em + o | "no meio" |
| pela | por + a | "pela manhã" |
| pelo | por + o | "pelo menos" |

### MWE Types

- **fixed**: Fixed expressions (e.g., "café da manhã", "de acordo com")
- **flat**: Flat multiword names (e.g., "São Paulo")
- **compound**: Compound words (e.g., "guarda-chuva")

### Example MWE Annotations

```json
{
  "span": [2, 4],           // Token positions (inclusive)
  "text": "café da manhã",  // Surface form
  "lemma": "café da manhã", // Canonical form
  "pos": "NOUN",            // Part-of-speech tag
  "type": "fixed",          // MWE type
  "tokens": ["café", "de", "a", "manhã"]  // Individual tokens
}
```

---

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Key Settings**:

```bash
# Server
PORT=80  # Internal container port (host port 8406 set in docker-compose.yml)
WORKERS=1

# GPU
GPU_ENABLED=false

# Language
DEFAULT_LANGUAGE=portuguese

# MWE
MWE_ENABLED=true
MWE_DATABASE_PATH=data/portuguese/mwe_database.json
LEMMA_DICT_PATH=data/portuguese/lemma_dict.json

# Cache
CACHE_DIR=./cache/trankit/
EMBEDDING_MODEL=xlm-roberta-base

# Timeouts
TIMEOUT=600
```

### GPU Support

To enable GPU acceleration:

1. Set `GPU_ENABLED=true` in `.env`
2. Ensure NVIDIA GPU and nvidia-docker are installed
3. Uncomment GPU section in `docker-compose.yml`
4. Set `WORKERS=1` (GPU doesn't support multiple processes)

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `500 Internal Server Error`: Processing error

**Error Response Format**:
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 500
}
```

---

## Performance Considerations

### CPU Mode

- Can use multiple workers: `WORKERS = 2 * CPU_CORES + 1`
- Good for handling concurrent requests
- Slower per-request processing

### GPU Mode

- **MUST use 1 worker**: `WORKERS=1`
- Fast per-request processing
- Limited concurrency (sequential processing)
- Requires NVIDIA GPU with CUDA support

### Batch Processing

- Use `/parse_batch` for multiple texts
- More efficient than individual requests
- Reduces model loading overhead

### Caching

- Models are cached per language
- First request per language is slower (model loading)
- Subsequent requests are faster

---

## Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Docker Build

```bash
# Build image
docker build -t trankit-mwe-api .

# Run container
docker run -d \
  -p 8406:80 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  -e GPU_ENABLED=false \
  trankit-mwe-api
```

### Kubernetes (Optional)

See `k8s/` directory for Kubernetes manifests (if available).

---

## Monitoring

### Health Check

The `/health` endpoint provides service status:

```bash
curl http://localhost:8406/api/v1/health
```

### Docker Health Check

Built-in health check runs every 30 seconds:

```bash
docker ps  # Check container health status
```

### Logs

View application logs:

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f <container-id>
```

---

## Troubleshooting

### MWE Database Not Found

**Error**: "MWE database not found"

**Solution**:
```bash
python scripts/extract_dictionaries_from_db.py
```

### Port Already in Use

**Error**: "Port 8406 already in use"

**Solution**: Change the host port mapping in `docker-compose.yml` (e.g., `"8407:80"`)

### GPU Not Available

**Error**: "CUDA device not found"

**Solution**:
- Set `GPU_ENABLED=false`
- Or install NVIDIA drivers and nvidia-docker

### Timeout Errors

**Error**: "Request timeout"

**Solution**: Increase `TIMEOUT` in `.env` (default: 600 seconds)

### Out of Memory

**Solution**:
- Reduce `WORKERS` count
- Use smaller `EMBEDDING_MODEL` (xlm-roberta-base instead of large)
- Increase Docker memory limit

### NumPy 2.x Compatibility Error

**Error**: "A module that was compiled using NumPy 1.x cannot be run in NumPy 2.0.x"

**Symptoms**:
- Container crashes on startup
- Import errors related to NumPy version mismatch
- Error message about recompiling with NumPy 2.0

**Solution**:
The Docker image pins NumPy to 1.x for compatibility with PyTorch/Trankit. If you see this error:

```bash
# 1. Rebuild the image with --no-cache
docker-compose build --no-cache

# 2. Restart the container
docker-compose up -d
```

**Root Cause**: PyTorch and Trankit were compiled with NumPy 1.x and are not compatible with NumPy 2.x. The `requirements-docker.txt` file now includes `numpy>=1.19.0,<2.0.0` to prevent this issue.

**Prevention**: Always use the provided Docker image or ensure NumPy < 2.0 in your environment.

---

## Examples

### Python Client

```python
import requests

class TrankitMWEClient:
    def __init__(self, base_url="http://localhost:8406/api/v1"):
        self.base_url = base_url

    def parse(self, text, language="portuguese", mwe_enabled=True):
        response = requests.post(
            f"{self.base_url}/parse",
            json={
                "text": text,
                "language": language,
                "mwe_enabled": mwe_enabled
            }
        )
        return response.json()

    def parse_batch(self, texts, language="portuguese", mwe_enabled=True):
        response = requests.post(
            f"{self.base_url}/parse_batch",
            json={
                "texts": texts,
                "language": language,
                "mwe_enabled": mwe_enabled
            }
        )
        return response.json()

    def mwe_only(self, text, language="portuguese"):
        response = requests.post(
            f"{self.base_url}/mwe_only",
            json={
                "text": text,
                "language": language
            }
        )
        return response.json()

    def health(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = TrankitMWEClient()

# Parse single text
result = client.parse("Tomei café da manhã.")
print(f"Found {result['mwe_count']} MWEs")

# Parse batch
results = client.parse_batch([
    "Tomei café da manhã.",
    "De acordo com o plano."
])
print(f"Total MWEs: {results['total_mwes']}")

# MWE only
mwes = client.mwe_only("Tomei café da manhã de acordo com o plano.")
for mwe in mwes['mwes']:
    print(f"  - {mwe['text']} ({mwe['type']})")

# Health check
health = client.health()
print(f"Status: {health['status']}, Models: {health['models_loaded']}")
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

class TrankitMWEClient {
  constructor(baseURL = 'http://localhost:8406/api/v1') {
    this.client = axios.create({ baseURL });
  }

  async parse(text, language = 'portuguese', mweEnabled = true) {
    const response = await this.client.post('/parse', {
      text,
      language,
      mwe_enabled: mweEnabled
    });
    return response.data;
  }

  async parseBatch(texts, language = 'portuguese', mweEnabled = true) {
    const response = await this.client.post('/parse_batch', {
      texts,
      language,
      mwe_enabled: mweEnabled
    });
    return response.data;
  }

  async mweOnly(text, language = 'portuguese') {
    const response = await this.client.post('/mwe_only', {
      text,
      language
    });
    return response.data;
  }

  async health() {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Usage
const client = new TrankitMWEClient();

(async () => {
  // Parse single text
  const result = await client.parse('Tomei café da manhã.');
  console.log(`Found ${result.mwe_count} MWEs`);

  // Health check
  const health = await client.health();
  console.log(`Status: ${health.status}`);
})();
```

---

## API Versioning

Current version: **v1**

The API uses URL-based versioning: `/api/v1/...`

Future versions will be available at `/api/v2/...`, etc.

---

## License

See main project LICENSE file.

---

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [repository-url]/docs
- MWE Extension Guide: `MWE_EXTENSION_DOCUMENTATION.md`

---

## Changelog

### Version 1.0.0 (2024)

- Initial API release
- MWE recognition support for Portuguese
- Full NLP pipeline (tokenization, POS, morphology, dependency parsing)
- Batch processing endpoint
- MWE-only lightweight endpoint
- Docker containerization
- GPU acceleration support
- Health check and monitoring
