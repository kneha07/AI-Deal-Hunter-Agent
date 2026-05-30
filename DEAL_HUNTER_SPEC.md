# AI Deal Hunter Agent — Full Project Spec

## Overview
An AI-powered deal analysis agent for a hackathon (Cascadia AI Hackathon). User pastes a product URL (Amazon, Best Buy, etc.) and the agent scrapes the product, finds competitor prices, analyzes reviews, and generates a "Deal Report Card" with a buy/wait recommendation.

## Judging Criteria (each 10 pts)
- Technical Chops: Multi-source scraping, structured AI output, comparison logic
- Cool Factor: "Dupe Finder" + "Buy/Wait" predictor + Deal Grade
- Presentation: "Save $200 in 30 seconds" pitch
- Demo Success: Paste any Amazon link → instant results

---

## Tech Stack
- **Backend:** Python 3.14, FastAPI, uvicorn
- **AI:** Amazon Bedrock (Claude) — model: `us.anthropic.claude-haiku-4-5-20251001-v1:0`
- **Scraping:** Apify (actors for Amazon + Google Search)
- **Storage:** Box (upload shareable deal reports)
- **Frontend:** Inline HTML served by FastAPI (no separate framework)

## Environment Variables (.env)
```
APIFY_API_TOKEN=<your-apify-token>
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
BOX_CLIENT_ID=<your-box-client-id>
BOX_CLIENT_SECRET=<your-box-client-secret>
BOX_DEV_TOKEN=<get fresh token from Box Developer Console>
BOX_FOLDER_ID=0
APP_PORT=8000
```

## Dependencies (requirements.txt)
```
fastapi
uvicorn
pydantic
python-dotenv
apify-client
boto3
httpx
boxsdk>=3.9,<4
```

NOTE: System has Python 3.14. Do NOT pin versions — install without version pins so compatible wheels are found.

---

## Architecture

```
User pastes product URL
        ↓
┌────────────────────────────────────┐
│  1. ProductScraper (Apify)         │
│     - Scrape product page          │
│     - Scrape competitor prices     │
│     - Collect reviews              │
└────────────────────────────────────┘
        ↓
┌────────────────────────────────────┐
│  2. DealAnalyzer (Bedrock Claude)  │
│     - Buy/Wait prediction          │
│     - Review sentiment analysis    │
│     - Deal grade (A+ to F)         │
│     - Competitor comparison        │
│     - Full markdown report         │
└────────────────────────────────────┘
        ↓
┌────────────────────────────────────┐
│  3. ReportExporter (Box)           │
│     - Upload report as .md file    │
│     - Generate shared link         │
└────────────────────────────────────┘
        ↓
┌────────────────────────────────────┐
│  4. Web UI                         │
│     - Form: paste URL, submit      │
│     - Redirect to /report/<id>     │
│     - Full-page rendered report    │
└────────────────────────────────────┘
```

---

## Project Structure

```
deal-hunter-agent/
├── main.py                  # FastAPI app, routes, HTML pages
├── agent/
│   ├── __init__.py
│   ├── scraper.py           # Apify product + competitor scraping
│   ├── analyzer.py          # Bedrock Claude deal analysis
│   ├── exporter.py          # Box file upload
│   └── orchestrator.py      # Pipeline: scrape → analyze → export
├── models/
│   ├── __init__.py
│   └── schemas.py           # Pydantic request/response models
├── .env
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Data Models (models/schemas.py)

```python
class DealRequest(BaseModel):
    product_url: str  # URL to analyze

class CompetitorPrice(BaseModel):
    store: str
    price: str
    url: Optional[str] = None

class ReviewSentiment(BaseModel):
    loves: list[str]        # Top 3 things people love
    complaints: list[str]   # Top 3 complaints
    deal_breakers: list[str] # Potential deal-breaker issues

class DealReport(BaseModel):
    success: bool
    product_name: str
    product_price: str
    product_image: Optional[str]
    deal_grade: str              # A+ to F
    buy_or_wait: str             # "Buy Now" or "Wait"
    buy_or_wait_reason: str
    confidence_pct: int          # 0-100
    competitor_prices: list[CompetitorPrice]
    savings_potential: str
    review_sentiment: Optional[ReviewSentiment]
    report_id: Optional[str]
    box_file_url: Optional[str]
    full_report_md: Optional[str]
    message: str
```

---

## Key Implementation Details

### Scraper (agent/scraper.py)
- Use `junglee/amazon-crawler` Apify actor for Amazon URLs
- Use `apify/google-search-scraper` to find competitor prices (search: product name + "price")
- Return structured product data + competitor results

### Analyzer (agent/analyzer.py)
- Single call to Bedrock Claude with all scraped data
- Prompt asks for JSON output with: deal_grade, buy_or_wait, confidence, review_sentiment, competitor_comparison, full_report_markdown
- Parse the JSON response into structured data

### Prompt Strategy
```
You are a deal analysis expert. Analyze this product and provide a comprehensive deal report.

Product: {name}
Price: {price}
Reviews: {reviews_summary}
Competitor prices found: {competitor_data}

Respond in JSON with these fields:
- deal_grade: letter grade A+ to F
- buy_or_wait: "Buy Now" or "Wait"  
- buy_or_wait_reason: one sentence why
- confidence_pct: 0-100
- review_sentiment: {loves: [...], complaints: [...], deal_breakers: [...]}
- competitor_prices: [{store, price, url}...]
- savings_potential: "Save $X by buying at Store Y"
- full_report_md: full markdown report with all analysis
```

### Exporter (agent/exporter.py)
- Upload markdown report to Box
- Use OAuth2 with developer token (same pattern as travel agent)
- Return shared link URL

### Web UI
- Home page (`/`): Simple form with one input (product URL) + submit button
- On submit: POST to `/analyze`, show spinner, redirect to `/report/<id>` on success
- Report page (`/report/<id>`): Full-page rendered deal report with:
  - Deal grade badge (big, colorful)
  - Buy/Wait verdict with confidence meter
  - Price comparison table
  - Review sentiment breakdown
  - Link to Box file
  - "Back to Search" link

---

## Build Order (incremental)
1. Project skeleton + FastAPI + home page with form
2. Product scraper (Apify Amazon actor)
3. AI analyzer (Bedrock Claude) — deal grade + buy/wait
4. Report page UI (render the analysis beautifully)
5. Competitor price search (Apify Google Search)
6. Review sentiment analysis
7. Box export
8. Polish: loading states, error handling, styling

---

## Important Notes from Previous Experience
- Python 3.14 is on this machine — don't pin dependency versions
- boxsdk v10+ uses `box_sdk_gen` module name. Install `boxsdk>=3.9,<4` for the `boxsdk` import
- Box developer tokens expire in 60 min — refresh before demo
- Bedrock model `us.anthropic.claude-haiku-4-5-20251001-v1:0` is confirmed working
- Use `r"""..."""` for HTML template strings to avoid Python escape warnings
- Don't use JS template literals (backticks) in inline HTML — they can break with AI-generated content containing special chars. Use string concatenation instead.
- For the report page: put content in a `<script type="text/plain" id="raw">` tag and render with JS to avoid HTML injection issues
