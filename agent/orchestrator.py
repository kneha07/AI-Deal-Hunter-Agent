import uuid
import logging
from agent.scraper import scrape_amazon_product, search_competitor_prices
from agent.analyzer import analyze_deal
from agent.exporter import upload_report
from models.schemas import DealReport, CompetitorPrice, ReviewSentiment, DupeProduct, PricePrediction

logger = logging.getLogger(__name__)


def run_deal_analysis(product_url: str) -> DealReport:
    """Full pipeline: scrape -> analyze -> export -> return report."""
    report_id = uuid.uuid4().hex[:8]

    # Step 1: Scrape product
    try:
        product_data = scrape_amazon_product(product_url)
        if not product_data:
            return DealReport(
                success=False,
                product_name="Unknown",
                product_price="N/A",
                deal_grade="N/A",
                buy_or_wait="N/A",
                buy_or_wait_reason="Could not scrape product data.",
                confidence_pct=0,
                savings_potential="N/A",
                report_id=report_id,
                message="Failed to scrape product. Please check the URL and try again.",
            )
    except Exception as e:
        return DealReport(
            success=False,
            product_name="Unknown",
            product_price="N/A",
            deal_grade="N/A",
            buy_or_wait="N/A",
            buy_or_wait_reason=str(e),
            confidence_pct=0,
            savings_potential="N/A",
            report_id=report_id,
            message=f"Scraping error: {str(e)}",
        )

    # Step 2: Search competitor prices
    try:
        competitor_prices = search_competitor_prices(
            product_data.get("name", ""),
            product_data.get("price", ""),
        )
    except Exception:
        competitor_prices = []

    # Step 3: AI analysis
    try:
        analysis = analyze_deal(product_data, competitor_prices)
    except Exception as e:
        return DealReport(
            success=False,
            product_name=product_data.get("name", "Unknown"),
            product_price=str(product_data.get("price", "N/A")),
            product_image=product_data.get("image"),
            deal_grade="N/A",
            buy_or_wait="N/A",
            buy_or_wait_reason=str(e),
            confidence_pct=0,
            savings_potential="N/A",
            report_id=report_id,
            message=f"Analysis error: {str(e)}",
        )

    # Step 4: Build competitor price models
    comp_models = []
    for cp in analysis.get("competitor_prices", competitor_prices):
        if isinstance(cp, dict):
            comp_models.append(
                CompetitorPrice(
                    store=cp.get("store", "Unknown"),
                    price=cp.get("price", "N/A"),
                    url=cp.get("url"),
                )
            )

    # Step 5: Build review sentiment
    sentiment_data = analysis.get("review_sentiment")
    review_sentiment = None
    if sentiment_data and isinstance(sentiment_data, dict):
        review_sentiment = ReviewSentiment(
            loves=sentiment_data.get("loves", []),
            complaints=sentiment_data.get("complaints", []),
            deal_breakers=sentiment_data.get("deal_breakers", []),
        )

    # Step 6: Export to Box
    full_report_md = analysis.get("full_report_md", "")
    box_result = {"file_url": None}
    try:
        box_result = upload_report(full_report_md, product_data.get("name", ""), report_id)
    except Exception:
        pass

    # Step 7: Build dupe models
    dupe_models = []
    for dupe in analysis.get("dupes", []):
        if isinstance(dupe, dict):
            dupe_models.append(
                DupeProduct(
                    name=dupe.get("name", "Unknown"),
                    price=dupe.get("price", "N/A"),
                    why_its_a_dupe=dupe.get("why_its_a_dupe", ""),
                    url=dupe.get("url"),
                )
            )

    # Step 8: Build price prediction
    price_prediction = None
    pred_data = analysis.get("price_prediction")
    if pred_data and isinstance(pred_data, dict):
        price_prediction = PricePrediction(
            trend=pred_data.get("trend", "stable"),
            prediction=pred_data.get("prediction", ""),
            best_time_to_buy=pred_data.get("best_time_to_buy", "Now"),
            confidence=pred_data.get("confidence", "medium"),
        )

    return DealReport(
        success=True,
        product_name=product_data.get("name", "Unknown"),
        product_price=str(product_data.get("price", "N/A")),
        product_image=product_data.get("image"),
        deal_grade=analysis.get("deal_grade", "N/A"),
        buy_or_wait=analysis.get("buy_or_wait", "N/A"),
        buy_or_wait_reason=analysis.get("buy_or_wait_reason", ""),
        confidence_pct=analysis.get("confidence_pct", 0),
        competitor_prices=comp_models,
        savings_potential=analysis.get("savings_potential", "N/A"),
        review_sentiment=review_sentiment,
        dupes=dupe_models,
        price_prediction=price_prediction,
        report_id=report_id,
        box_file_url=box_result.get("file_url"),
        full_report_md=full_report_md,
        message="Deal analysis complete!",
    )


def run_deal_search(query: str):
    """Search Amazon for products and use AI to pick the best deal."""
    from agent.scraper import search_amazon_products
    from agent.analyzer import analyze_search_results
    from models.schemas import SearchResponse, SearchResultItem

    # Step 1: Search Amazon
    try:
        products = search_amazon_products(query, max_results=5)
        if not products:
            return SearchResponse(
                success=False,
                query=query,
                message="No products found. Try a different search term.",
            )
    except Exception as e:
        return SearchResponse(
            success=False,
            query=query,
            message=f"Search error: {str(e)}",
        )

    # Step 2: AI picks the best deal
    try:
        ai_result = analyze_search_results(query, products)
    except Exception:
        ai_result = {"best_pick_index": 0, "summary": "Could not analyze.", "reasons": []}

    # Step 3: Build response
    result_items = []
    best_idx = ai_result.get("best_pick_index", 0)
    reasons = ai_result.get("reasons", [])

    for i, p in enumerate(products):
        result_items.append(
            SearchResultItem(
                name=p["name"],
                price=str(p["price"]),
                image=p.get("image"),
                rating=p.get("rating"),
                review_count=p.get("review_count"),
                url=p.get("url", ""),
                asin=p.get("asin", ""),
                ai_pick=(i == best_idx),
                ai_reason=reasons[i] if i < len(reasons) else "",
            )
        )

    return SearchResponse(
        success=True,
        query=query,
        results=result_items,
        best_pick_index=best_idx,
        ai_summary=ai_result.get("summary", ""),
        message="Search complete!",
    )
