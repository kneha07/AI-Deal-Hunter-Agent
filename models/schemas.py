from pydantic import BaseModel
from typing import Optional


class DealRequest(BaseModel):
    product_url: str


class CompetitorPrice(BaseModel):
    store: str
    price: str
    url: Optional[str] = None


class ReviewSentiment(BaseModel):
    loves: list[str]
    complaints: list[str]
    deal_breakers: list[str]


class PricePrediction(BaseModel):
    trend: str  # "dropping", "stable", "rising"
    prediction: str  # e.g. "Price likely to drop 15-20% in 3 weeks for Black Friday"
    best_time_to_buy: str  # e.g. "Wait for Black Friday (Nov 29)"
    confidence: str  # "high", "medium", "low"


class DupeProduct(BaseModel):
    name: str
    price: str
    why_its_a_dupe: str
    url: Optional[str] = None


class DealReport(BaseModel):
    success: bool
    product_name: str
    product_price: str
    product_image: Optional[str] = None
    deal_grade: str
    buy_or_wait: str
    buy_or_wait_reason: str
    confidence_pct: int
    competitor_prices: list[CompetitorPrice] = []
    savings_potential: str
    review_sentiment: Optional[ReviewSentiment] = None
    dupes: list[DupeProduct] = []
    price_prediction: Optional[PricePrediction] = None
    report_id: Optional[str] = None
    box_file_url: Optional[str] = None
    full_report_md: Optional[str] = None
    message: str


class SearchRequest(BaseModel):
    query: str


class SearchResultItem(BaseModel):
    name: str
    price: str
    image: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    url: str
    asin: str = ""
    ai_pick: bool = False
    ai_reason: str = ""


class SearchResponse(BaseModel):
    success: bool
    query: str
    results: list[SearchResultItem] = []
    best_pick_index: int = 0
    ai_summary: str = ""
    message: str
