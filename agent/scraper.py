import os
import re
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")


def _clean_amazon_url(url: str) -> str:
    """Normalize an Amazon URL: ensure https://, strip tracking params."""
    url = url.strip()

    # Add scheme if missing
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url.lstrip("/")

    # Replace http with https
    if url.startswith("http://"):
        url = "https://" + url[7:]

    # Ensure www. is present for amazon.com
    if "://amazon.com" in url:
        url = url.replace("://amazon.com", "://www.amazon.com")

    # Strip query parameters and fragment
    url = url.split("?")[0].split("#")[0]

    # For Amazon /dp/ URLs, trim to just the ASIN
    dp_match = re.search(r"(https://[^/]+/.*/dp/[A-Z0-9]{10})", url)
    if dp_match:
        return dp_match.group(1)

    return url


def scrape_amazon_product(url: str) -> dict:
    """Scrape product details from an Amazon URL using Apify."""
    client = ApifyClient(APIFY_TOKEN)

    # Clean and normalize the URL
    url = _clean_amazon_url(url)

    run_input = {
        "categoryOrProductUrls": [{"url": url}],
        "maxReviews": 10,
        "proxy": {"useApifyProxy": True},
    }

    run = client.actor("junglee/amazon-crawler").call(run_input=run_input)
    items = list(client.dataset(run.default_dataset_id).iterate_items())

    if not items:
        return {}

    product = items[0]
    return {
        "name": product.get("title", "Unknown Product"),
        "price": product.get("price", {}).get("value", "N/A")
        if isinstance(product.get("price"), dict)
        else str(product.get("price", "N/A")),
        "currency": product.get("price", {}).get("currency", "USD")
        if isinstance(product.get("price"), dict)
        else "USD",
        "image": product.get("thumbnailImage") or product.get("mainImage"),
        "rating": product.get("stars"),
        "review_count": product.get("reviewsCount"),
        "reviews": _extract_reviews(product),
        "url": url,
    }


def _extract_reviews(product: dict) -> list[str]:
    """Extract review text from product data."""
    reviews = []
    for review in product.get("reviews", [])[:10]:
        text = review.get("text") or review.get("review") or ""
        if text:
            reviews.append(text[:500])
    return reviews


def search_competitor_prices(product_name: str, product_price: str = "") -> list[dict]:
    """Search Google for competitor prices using Apify."""
    client = ApifyClient(APIFY_TOKEN)

    # Clean product name for search
    clean_name = re.sub(r"[^\w\s]", "", product_name)[:80]
    query = f"{clean_name} price"

    run_input = {
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": 10,
        "languageCode": "en",
        "countryCode": "us",
    }

    run = client.actor("apify/google-search-scraper").call(run_input=run_input)
    items = list(client.dataset(run.default_dataset_id).iterate_items())

    # Parse the original product price for comparison
    ref_price = _parse_price(product_price)

    competitors = []
    for item in items:
        for result in item.get("organicResults", [])[:8]:
            title = result.get("title", "")
            snippet = result.get("description", "")
            link = result.get("url", "")

            # Find ALL prices in the text and pick the most plausible one
            all_prices = re.findall(r"\$[\d,]+\.?\d*", title + " " + snippet)
            best_price = _pick_best_price(all_prices, ref_price)

            if best_price:
                store = _extract_store_name(link)
                if store:
                    competitors.append(
                        {
                            "store": store,
                            "price": best_price,
                            "url": link,
                        }
                    )

    return competitors[:5]


def _parse_price(price_str: str) -> float:
    """Parse a price string into a float. Returns 0 if unparseable."""
    if not price_str:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", str(price_str))
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def _pick_best_price(prices: list[str], ref_price: float) -> str:
    """Pick the most plausible price from a list.
    
    Strategy: if we know the product price, pick the price closest to it
    (within a reasonable range: 30%-300% of ref price). This filters out
    $9.99 accessories and $999 bundles that appear on the same page.
    If no ref price, return the first match.
    """
    if not prices:
        return ""
    if not ref_price or ref_price == 0:
        return prices[0]

    best = None
    best_distance = float("inf")
    low_bound = ref_price * 0.3
    high_bound = ref_price * 3.0

    for p_str in prices:
        p_val = _parse_price(p_str)
        if p_val <= 0:
            continue
        # Must be in a reasonable range relative to the product price
        if p_val < low_bound or p_val > high_bound:
            continue
        distance = abs(p_val - ref_price)
        if distance < best_distance:
            best_distance = distance
            best = p_str

    return best or ""


def _extract_store_name(url: str) -> str:
    """Extract a readable store name from a URL."""
    store_map = {
        "walmart": "Walmart",
        "bestbuy": "Best Buy",
        "target": "Target",
        "newegg": "Newegg",
        "bhphoto": "B&H Photo",
        "costco": "Costco",
        "ebay": "eBay",
        "amazon": "Amazon",
        "adorama": "Adorama",
        "microcenter": "Micro Center",
    }
    url_lower = url.lower()
    for key, name in store_map.items():
        if key in url_lower:
            return name
    # Fallback: extract domain
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if match:
        domain = match.group(1).split(".")[0].capitalize()
        return domain
    return ""


def search_amazon_products(query: str, max_results: int = 5) -> list[dict]:
    """Search Amazon for products matching a query using Apify."""
    client = ApifyClient(APIFY_TOKEN)

    search_url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"

    run_input = {
        "categoryOrProductUrls": [{"url": search_url}],
        "maxReviews": 0,
        "maxItemsPerStartUrl": 8,
        "proxy": {"useApifyProxy": True},
    }

    run = client.actor("junglee/amazon-crawler").call(run_input=run_input)
    items = list(client.dataset(run.default_dataset_id).iterate_items())

    products = []
    for item in items[:max_results]:
        price_val = "N/A"
        if isinstance(item.get("price"), dict):
            price_val = item["price"].get("value", "N/A")
        elif item.get("price") is not None:
            price_val = str(item["price"])

        if price_val == "N/A" or not price_val:
            continue

        products.append({
            "name": item.get("title", "Unknown"),
            "price": price_val,
            "image": item.get("thumbnailImage") or item.get("mainImage"),
            "rating": item.get("stars"),
            "review_count": item.get("reviewsCount"),
            "url": item.get("url") or item.get("productUrl") or "",
            "asin": item.get("asin", ""),
        })

    return products
