# Vestio

**Fashion Data Pipeline** — Collect fashion content from social media, extract clothing attributes with vision AI, generate vector embeddings, and enable similarity search across a multimodal data lake.

Vestio (from Latin *vestis*, "garment") is a B2B fashion data infrastructure that powers trend intelligence and recommendation capabilities for brands and retailers.

## What It Does

```bash
Instagram Posts → Download Images → VLM Attribute Extraction → FashionCLIP Embeddings → LanceDB → Vector Search
```

1. **Collect** fashion posts from Instagram via Apify
2. **Analyze** each image with a Vision Language Model (Gemini 2.5 Flash via OpenRouter) to extract structured clothing attributes — category, color, pattern, material, style, brand, etc.
3. **Embed** every clothing item with [FashionCLIP](https://github.com/patrickjohncyh/fashion-clip), a fashion-domain fine-tuned CLIP model producing 512-dim vectors
4. **Store** everything in LanceDB — structured metadata, vector embeddings, and raw image blobs in a single multimodal data lake
5. **Search** by image or text query to find visually similar items, with optional category filters

## Architecture

```bash
┌─────────────────────────────────────────────────────────────────┐
│                         VESTIO PIPELINE                         │
│                                                                 │
│  ┌───────────────────┐     ┌──────────────────────────────────┐ │
│  │ Collectors (TS)   │     │ Processor (Python)               │ │
│  │                   │     │                                  │ │
│  │ Instagram → Apify │───->│ Download → VLM Extract → Embed   │ │
│  │ (more platforms   │     │                                  │ │
│  │  planned)         │     │ • Gemini 2.5 Flash (OpenRouter)  │ │
│  └───────────────────┘     │ • FashionCLIP (512-dim)          │ │
│                            └──────────────┬───────────────────┘ │
│                                           │                     │
│                                           ▼                     │
│                            ┌──────────────────────────────────┐ │
│                            │ Store (LanceDB)                  │ │
│                            │                                  │ │
│                            │ posts  — social media metadata   │ │
│                            │ items  — clothing + embeddings   │ │
│                            │          + image blobs           │ │
│                            └──────────────┬───────────────────┘ │
│                                           │                     │
│                                           ▼                     │
│                            ┌──────────────────────────────────┐ │
│                            │ CLI                              │ │
│                            │                                  │ │
│                            │ • Process raw posts              │ │
│                            │ • Search by image or text        │ │
│                            │ • Filter by category             │ │
│                            └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Why |
| --- | --- | --- |
| Collection | TypeScript + Apify | Async IO-heavy scraping, Apify handles Instagram anti-bot |
| VLM Extraction | Gemini 2.5 Flash via OpenRouter | Best cost/quality ratio (~$1.6/1000 images), native JSON output |
| Embeddings | FashionCLIP (`patrickjohncyh/fashion-clip`) | Fashion-domain fine-tuned CLIP, outperforms generic CLIP on clothing |
| Storage | LanceDB (Lance format) | Unified multimodal store: structured data + vectors + blobs, zero ops |
| GPU | PyTorch + CUDA 12.8 | FashionCLIP inference on local GPU |

### Data Model

**`posts` table** — Social media post metadata:

- Platform, author, caption, hashtags
- Engagement metrics (likes, comments, shares)
- Timestamps, media type, location

**`items` table** — Individual clothing items extracted from posts:

- Raw image (stored as blob)
- 512-dim FashionCLIP embedding vector
- Structured attributes: category, subtype, colors, pattern, material, style tags
- Brand, season, occasion, confidence score
- Bounding box coordinates

## Project Structure

```bash
vestio/
├── packages/
│   └── collectors/          # TypeScript — Instagram data collection
│       └── src/
│           ├── types.ts     # RawPost unified interface
│           ├── instagram.ts # Apify Instagram collector
│           └── cli.ts       # Collection CLI entry point
├── pipeline/                # Python — core data processing
│   ├── processor/
│   │   ├── vlm.py           # VLM attribute extraction (OpenRouter)
│   │   ├── prompts.py       # Fashion extraction prompt
│   │   ├── embedder.py      # FashionCLIP embedding generator
│   │   ├── downloader.py    # Image download utility
│   │   └── pipeline.py      # End-to-end pipeline orchestration
│   ├── store/
│   │   ├── schema.py        # LanceDB table schemas (PyArrow)
│   │   └── db.py            # LanceDB read/write wrapper
│   ├── cli.py               # Pipeline CLI (process + search)
│   └── pyproject.toml
├── .test/                   # All tests (mirrors source structure)
│   ├── collectors/          # TypeScript tests (Vitest)
│   └── pipeline/            # Python tests (pytest)
│       ├── processor/       # Component tests for each processor module
│       ├── store/           # Component tests for LanceDB store
│       ├── test_e2e_simulation.py  # E2E: 100 fake posts full pipeline
│       └── conftest.py      # Shared fixtures & fake data generators
├── data/
│   ├── raw/                 # Collected Instagram posts (JSON)
│   └── vestio.lance/        # LanceDB database files
├── .env                     # API keys (gitignored)
└── package.json             # Monorepo root (npm workspaces)
```

## Getting Started

### Prerequisites

- Node.js >= 20
- Python 3.12 (via Conda)
- NVIDIA GPU with CUDA 12.8 (for FashionCLIP)

### Installation

```bash
# Clone
git clone https://github.com/Pthahnix/Vestio.git
cd Vestio

# TypeScript dependencies
npm install

# Python environment
conda create -n vestio python=3.12 -y
conda activate vestio

# PyTorch with CUDA 12.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Pipeline dependencies
cd pipeline
pip install -e .
```

### Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

```env
# OpenRouter — register at https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
VLM_MODEL=google/gemini-2.5-flash

# Apify — register at https://console.apify.com/account/integrations
TOKEN_APIFY=apify_api_your-token-here

# LanceDB storage path
LANCEDB_URI=data/vestio.lance
```

## Usage

### 1. Collect Instagram Posts

```bash
# Collect by hashtags
TOKEN_APIFY=your_token npm run collect -- --hashtags ootd,streetstyle --limit 100

# Collect by profiles
TOKEN_APIFY=your_token npm run collect -- --profiles fashionblogger123 --limit 50
```

Output: `data/raw/instagram-<timestamp>.json`

### 2. Process Into LanceDB

```bash
cd pipeline
python -m cli process --input ../data/raw/*.json --db ../data/vestio.lance
```

This runs the full pipeline for each post:

- Downloads all images
- Calls VLM to extract clothing attributes per image
- Generates FashionCLIP embeddings
- Stores posts + items in LanceDB

### 3. Search

```bash
# Search by image — find items visually similar to a query image
python -m cli search --db ../data/vestio.lance --image path/to/query.jpg --limit 10

# Search by text — find items matching a text description
python -m cli search --db ../data/vestio.lance --text "red floral summer dress" --limit 10

# Search with category filter
python -m cli search --db ../data/vestio.lance --text "casual sneakers" --category footwear --limit 5
```

## VLM Extracted Attributes

Each clothing item gets these structured attributes from the Vision Language Model:

| Attribute | Example Values |
| --- | --- |
| **category** | top, bottom, dress, outerwear, footwear, accessory |
| **subtype** | t-shirt, blazer, jeans, maxi dress, sneakers, handbag |
| **colors** | ["navy", "white"] |
| **pattern** | solid, striped, floral, plaid, geometric, animal_print |
| **material** | cotton, denim, silk, leather, knit, wool, polyester |
| **style_tags** | ["casual", "minimalist"], ["formal", "preppy"] |
| **brand** | Detected from visible logos, or null |
| **season** | spring, summer, fall, winter |
| **occasion** | everyday, work, party, date, sport, beach |
| **confidence** | 0.0 – 1.0 |
| **bbox** | [x_min, y_min, x_max, y_max] normalized to 0–1 |

## Testing

```bash
# Run all tests (TS + Python)
npm test

# Python tests only
cd pipeline
conda run -n vestio python -m pytest ../.test/pipeline/ -v

# TypeScript tests only
npx vitest run

# FashionCLIP GPU tests (requires GPU, slower)
cd pipeline
conda run -n vestio python -m pytest ../.test/pipeline/processor/test_embedder.py -v
```

Test coverage includes:

- **48 tests total** (43 Python + 5 TypeScript)
- Component tests for every module
- Module gate tests (store: 14 tests, processor: 25 tests)
- E2E simulation with 100 fake posts, realistic fake data, and flaky failure scenarios

## Roadmap

### Current (MVP)

- [x] Instagram collection via Apify
- [x] VLM clothing attribute extraction (Gemini 2.5 Flash)
- [x] FashionCLIP 512-dim embeddings
- [x] LanceDB multimodal storage (posts + items)
- [x] Vector similarity search (image + text)
- [x] CLI interface

### Planned

- [ ] YouTube, TikTok, X (Twitter) collectors
- [ ] Bilibili, Xiaohongshu (小红书) collectors
- [ ] Video understanding / keyframe extraction
- [ ] Outfit composition table + knowledge graph
- [ ] Outfit recommendation (GNN / LLM-based)
- [ ] Trend analysis and forecasting
- [ ] REST API server
- [ ] Scheduled pipeline orchestration
- [ ] Cloud deployment (Railway + GPU)

## Cost Estimates

| Component | Cost | Notes |
| --- | --- | --- |
| VLM extraction | ~$1.6 / 1000 images | Gemini 2.5 Flash via OpenRouter |
| Instagram collection | Free tier $5/month | Apify |
| FashionCLIP inference | Free (local GPU) | ~10s per batch of 8 images |
| LanceDB storage | Free (local files) | ~1KB metadata + image blob per item |

## License

Apache License 2.0
