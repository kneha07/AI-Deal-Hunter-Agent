import os
import json
from datetime import date
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")


def _get_today() -> str:
    return date.today().strftime("%B %d, %Y")


def analyze_deal(product_data: dict, competitor_prices: list[dict]) -> dict:
    """Use Bedrock Claude to analyze the deal and generate a report."""
    client = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    reviews_text = "\n".join(product_data.get("reviews", [])[:10])
    competitor_text = "\n".join(
        [f"- {c['store']}: {c['price']} ({c.get('url', 'N/A')})" for c in competitor_prices]
    ) or "No competitor prices found."

    prompt = f"""You are a deal analysis expert and product dupe finder. Analyze this product and provide a comprehensive deal report.

Today's date: {_get_today()}

Product: {product_data.get('name', 'Unknown')}
Price: ${product_data.get('price', 'N/A')}
Rating: {product_data.get('rating', 'N/A')} stars ({product_data.get('review_count', 'N/A')} reviews)

Customer Reviews:
{reviews_text if reviews_text else 'No reviews available.'}

Competitor prices found:
{competitor_text}

Respond ONLY with valid JSON (no markdown, no code fences) with these exact fields:
{{
  "deal_grade": "letter grade A+ to F based on value proposition",
  "buy_or_wait": "Buy Now" or "Wait",
  "buy_or_wait_reason": "one sentence explaining why",
  "confidence_pct": 0-100 integer,
  "review_sentiment": {{
    "loves": ["top 3 things people love"],
    "complaints": ["top 3 complaints"],
    "deal_breakers": ["potential deal-breaker issues, empty if none"]
  }},
  "dupes": [
    {{
      "name": "cheaper alternative product name",
      "price": "$XX.XX estimated price",
      "why_its_a_dupe": "one sentence on why this is a good alternative",
      "url": "a search URL or product page URL where the user can find/buy this product"
    }}
  ],
  "price_prediction": {{
    "trend": "dropping" or "stable" or "rising",
    "prediction": "one sentence prediction about where the price is heading and why (mention specific upcoming sales events like Prime Day, Black Friday, back-to-school, etc.)",
    "best_time_to_buy": "when to buy — e.g. 'Now' or 'Wait for Prime Day (July)' or 'Wait for Black Friday (Nov 29)'",
    "confidence": "high" or "medium" or "low"
  }},
  "savings_potential": "Save $X by buying at Store Y" or "This is already the best price",
  "full_report_md": "A full markdown report (use ## headers, bullet points, bold) covering: Executive Summary, Price Analysis, Competitor Comparison, Dupe Alternatives, Review Analysis, Final Verdict"
}}

IMPORTANT for "dupes": Find 2-3 cheaper alternative products (dupes) that offer similar features/quality at a lower price. These can be lesser-known brands, previous generation models, or similar products from competitors. Only include products you are confident exist and provide realistic estimated prices (do NOT guess random low prices — if unsure of the exact price, give a reasonable range like "$30-40"). For the "url" field, provide an Amazon search URL like "https://www.amazon.com/s?k=product+name" so the user can find it. If no good dupes exist, return an empty array."""

    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
    )

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    response_body = json.loads(response["body"].read())
    assistant_text = response_body["content"][0]["text"]

    # Parse JSON from response (handle potential markdown fences)
    cleaned = assistant_text.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(cleaned.split("\n")[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    result = json.loads(cleaned)
    return result


def analyze_search_results(query: str, products: list[dict]) -> dict:
    """Use Bedrock Claude to pick the best deal from search results."""
    client = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    products_text = ""
    for i, p in enumerate(products):
        products_text += f"\n{i+1}. {p['name']}\n   Price: ${p['price']}\n   Rating: {p.get('rating', 'N/A')} stars ({p.get('review_count', 'N/A')} reviews)\n"

    prompt = f"""You are a deal-hunting expert. A user searched for: "{query}"

Here are the top results found on Amazon:
{products_text}

Analyze these options and pick the BEST DEAL (best value for money, considering price, ratings, and reviews).

Respond ONLY with valid JSON (no markdown, no code fences):
{{
  "best_pick_index": 0-based index of the best deal,
  "summary": "one sentence explaining your top pick, e.g. 'The X offers the best value at $Y with 4.5 stars and 2000+ reviews'",
  "reasons": ["one sentence reason for each product explaining its value proposition, in order"]
}}"""

    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
    )

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    response_body = json.loads(response["body"].read())
    assistant_text = response_body["content"][0]["text"]

    cleaned = assistant_text.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(cleaned.split("\n")[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    return json.loads(cleaned)
