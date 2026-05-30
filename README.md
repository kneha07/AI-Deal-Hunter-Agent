# 🔍 AI Deal Hunter Agent

**Save $200 in 30 seconds.** Paste any product URL — Amazon, Best Buy, Walmart, or any online store — or search for what you want. Get an instant AI-powered deal analysis with price comparisons, cheaper alternatives, price predictions, and a buy/wait recommendation.

Built for the **Cascadia AI Hackathon**. Developed with [Kiro](https://kiro.dev) — an AI-powered IDE.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)
![AI](https://img.shields.io/badge/AI-Amazon%20Bedrock%20Claude-orange)
![Built with](https://img.shields.io/badge/Built%20with-Kiro-blueviolet)

---

## ✨ Features

### 🔍 Deal Search
Don't have a URL? Just type what you're looking for (e.g. "best wireless earbuds under $50") and the agent searches Amazon, compares the top results, and picks the best deal with AI.

### 📊 Deal Report Card
Every product gets a comprehensive report with a letter grade (A+ to F) based on value, pricing, and reviews.

### 🤖 AI Buy/Wait Predictor
Claude analyzes the product and tells you whether to **Buy Now** or **Wait** — with a confidence percentage and reasoning.

### 📈 Price History Prediction
AI-powered price trend analysis that considers seasonality and upcoming sales events (Prime Day, Black Friday, etc.) to predict where the price is heading.

### 💰 Competitor Price Comparison
Automatically searches the web for the same product at other retailers (Walmart, Best Buy, Target, Newegg, etc.) and shows you where it's cheapest.

### 🔍 Dupe Finder
Finds 2-3 cheaper alternative products that offer similar features and quality at a lower price — lesser-known brands, previous-gen models, or competitor equivalents. Each dupe includes a link to find it.

### ❤️ Review Sentiment Analysis
Summarizes what customers love, their top complaints, and any deal-breaker issues — so you don't have to read hundreds of reviews.

### 🎉 Confetti + Sound Effects
When you find a great deal (A/A+/B+ grade with a "Buy Now" verdict), the app celebrates with confetti and a cha-ching sound.

### 📄 Box Export
Reports are uploaded to Box as shareable markdown files with a public link you can send to anyone.

---

## 🏗️ Architecture

```
User pastes URL  OR  searches for a product
        ↓                      ↓
┌──────────────────┐  ┌──────────────────────┐
│ Product Scraper  │  │ Product Search       │
│ (Apify Amazon)   │  │ (Apify Amazon)       │
└──────────────────┘  └──────────────────────┘
        ↓                      ↓
┌──────────────────┐  ┌──────────────────────┐
│ Competitor Search │  │ AI Best Pick         │
│ (Apify Google)    │  │ (Bedrock Claude)     │
└──────────────────┘  └──────────────────────┘
        ↓                      ↓
┌──────────────────┐  ┌──────────────────────┐
│ AI Deal Analysis │  │ Search Results Page   │
│ - Deal Grade     │  │ - Ranked products    │
│ - Buy/Wait       │  │ - Best Deal badge    │
│ - Price Predict  │  │ - Analyze button     │
│ - Dupes          │  └──────────────────────┘
│ - Sentiment      │
└──────────────────┘
        ↓
┌──────────────────┐
│ Box Export       │
│ (shared link)    │
└──────────────────┘
        ↓
┌──────────────────┐
│ Report Page      │
│ + Confetti 🎉    │
└──────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, Uvicorn |
| AI | Amazon Bedrock (Claude Haiku 4.5) |
| Scraping | Apify (Amazon Crawler + Google Search) |
| Storage | Box (shareable report files) |
| Frontend | Inline HTML/CSS/JS served by FastAPI |
| Development | Kiro (AI-powered IDE) |

---

## 📁 Project Structure

```
deal-hunter-agent/
├── main.py                  # FastAPI app, routes, HTML pages
├── agent/
│   ├── scraper.py           # Apify product scraping + search + competitor prices
│   ├── analyzer.py          # Bedrock Claude deal analysis + search ranking
│   ├── exporter.py          # Box file upload
│   └── orchestrator.py      # Pipelines: analyze + search
├── models/
│   └── schemas.py           # Pydantic request/response models
├── .env                     # API keys (not committed)
├── .env.example             # Template for environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone and install

```bash
cd deal-hunter-agent
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

You'll need:
- **Apify API token** — [Get one here](https://apify.com/)
- **AWS credentials** — For Amazon Bedrock access
- **Box developer token** — [Box Developer Console](https://app.box.com/developers/console)

### 3. Run

```bash
python3 main.py
```

Open **http://localhost:8000** in your browser.

### 4. Use it

**Option A — Analyze a specific product:**
1. Click "Analyze URL" tab
2. Paste any product URL (Amazon, Best Buy, Walmart, or any store)
3. Click "Hunt Deal"
4. Get your full Deal Report Card

**Option B — Search for the best deal:**
1. Click "Search Deals" tab
2. Type what you're looking for (e.g. "noise cancelling headphones")
3. Click "Find Deals"
4. See AI-ranked results with a "Best Deal" badge
5. Click "Analyze" on any result for a full deep-dive report

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `APIFY_API_TOKEN` | Apify API token for web scraping |
| `AWS_ACCESS_KEY_ID` | AWS access key for Bedrock |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for Bedrock |
| `AWS_REGION` | AWS region (default: us-west-2) |
| `BEDROCK_MODEL_ID` | Claude model ID on Bedrock |
| `BOX_CLIENT_ID` | Box OAuth2 client ID |
| `BOX_CLIENT_SECRET` | Box OAuth2 client secret |
| `BOX_DEV_TOKEN` | Box developer token (expires every 60 min) |
| `BOX_FOLDER_ID` | Box folder to upload reports to |
| `APP_PORT` | Server port (default: 8000) |

---

## 📝 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Home page with URL input and search tabs |
| POST | `/analyze` | Analyze a product URL (JSON: `{"product_url": "..."}`) |
| GET | `/report/{id}` | View a generated deal report |
| POST | `/search` | Search for deals (JSON: `{"query": "..."}`) |
| GET | `/search-results?id=X` | View search results page |

---

## 🎯 How It Works

### URL Analysis Flow
1. **URL Cleaning** — Strips tracking parameters, adds `https://`, normalizes Amazon URLs
2. **Product Scraping** — Apify Amazon Crawler gets product name, price, rating, and reviews
3. **Competitor Search** — Apify Google Search finds the same product at other stores
4. **AI Analysis** — Claude generates deal grade, buy/wait verdict, price prediction, review sentiment, and dupe alternatives
5. **Report Generation** — Beautiful full-page report with confetti for great deals
6. **Box Export** — Uploads markdown report to Box for sharing

### Deal Search Flow
1. **Amazon Search** — Apify crawls Amazon search results (capped at 8 items for speed)
2. **AI Ranking** — Claude compares all results and picks the best value
3. **Results Page** — Shows ranked products with "Best Deal" badge and per-product reasoning
4. **Deep Dive** — Click "Analyze" on any result to run the full analysis pipeline

---

## ⚠️ Notes

- **Box tokens expire every 60 minutes** — refresh before a demo
- **URL analysis takes ~30 seconds** (scraping + competitor search + AI)
- **Deal search takes ~15-20 seconds** (Amazon search + AI ranking)
- **URL format is flexible** — handles URLs with or without `https://`, with tracking params, etc.
- **Confetti triggers** on A+, A, A-, or B+ grades with a "Buy Now" verdict

---

## 🔌 Service Usage Breakdown

### Apify — 3 calls per analysis

| # | Actor | Purpose | When |
|---|-------|---------|------|
| 1 | `junglee/amazon-crawler` | Scrape product page (name, price, rating, reviews) | URL analysis |
| 2 | `apify/google-search-scraper` | Search competitor prices across retailers | URL analysis |
| 3 | `junglee/amazon-crawler` | Search Amazon for products by keyword | Deal search flow |

- Used in: `agent/scraper.py`
- Total calls per URL analysis: **2** (product scrape + competitor search)
- Total calls per deal search: **1** (Amazon keyword search)

### Amazon Bedrock (Claude Haiku 4.5) — 1-2 calls per request

| # | Purpose | When |
|---|---------|------|
| 1 | Full deal analysis (grade, buy/wait, price prediction, sentiment, dupes, report) | URL analysis |
| 2 | Compare and rank search results, pick best deal | Deal search flow |

- Used in: `agent/analyzer.py`
- Model: `us.anthropic.claude-haiku-4-5-20251001-v1:0`
- Total calls per URL analysis: **1**
- Total calls per deal search: **1**
- Total calls if user searches then analyzes a result: **2**

### Box — 1 call per analysis

| # | Purpose | When |
|---|---------|------|
| 1 | Upload markdown report + generate shared link | After URL analysis completes |

- Used in: `agent/exporter.py`
- Auth: OAuth2 with developer token
- Total calls per URL analysis: **1** (upload + shared link)
- Not used in deal search flow (only on full analysis)

### Total API calls per full flow

| Flow | Apify | Bedrock | Box | Total |
|------|-------|---------|-----|-------|
| URL Analysis | 2 | 1 | 1 | **4** |
| Deal Search | 1 | 1 | 0 | **2** |
| Search → Analyze | 3 | 2 | 1 | **6** |


