import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from models.schemas import DealRequest, SearchRequest
from agent.orchestrator import run_deal_analysis, run_deal_search

load_dotenv()

app = FastAPI(title="AI Deal Hunter Agent")

# In-memory report store
reports: dict = {}


HOME_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Deal Hunter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }
        .container {
            text-align: center;
            max-width: 600px;
            padding: 40px;
        }
        .logo {
            font-size: 4rem;
            margin-bottom: 10px;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #f7971e, #ffd200);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .tagline {
            font-size: 1.2rem;
            color: #aaa;
            margin-bottom: 40px;
        }
        .tabs {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin-bottom: 24px;
        }
        .tab {
            padding: 10px 24px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 8px;
            color: #aaa;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab:hover {
            background: rgba(255,255,255,0.1);
            transform: none;
            box-shadow: none;
        }
        .tab.active {
            background: linear-gradient(135deg, #f7971e, #ffd200);
            color: #000;
            border-color: transparent;
        }
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        input[type="url"] {
            flex: 1;
            padding: 16px 20px;
            border: 2px solid #444;
            border-radius: 12px;
            background: rgba(255,255,255,0.05);
            color: #fff;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }
        input[type="url"]:focus {
            border-color: #ffd200;
        }
        input[type="url"]::placeholder {
            color: #666;
        }
        button {
            padding: 16px 32px;
            background: linear-gradient(135deg, #f7971e, #ffd200);
            border: none;
            border-radius: 12px;
            color: #000;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 210, 0, 0.3);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .spinner {
            display: none;
            margin: 30px auto;
        }
        .spinner.active {
            display: block;
        }
        .spinner div {
            width: 50px;
            height: 50px;
            margin: 0 auto 15px;
            border: 4px solid rgba(255,210,0,0.2);
            border-top-color: #ffd200;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .spinner p {
            color: #aaa;
            font-size: 0.95rem;
        }
        .error {
            color: #ff6b6b;
            margin-top: 15px;
            display: none;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 50px;
        }
        .feature {
            padding: 20px;
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .feature-icon { font-size: 1.8rem; margin-bottom: 8px; }
        .feature h3 { font-size: 0.9rem; color: #ddd; }
        .feature p { font-size: 0.75rem; color: #888; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">&#x1F50D;</div>
        <h1>AI Deal Hunter</h1>
        <p class="tagline">Save $200 in 30 seconds. Paste any product URL.</p>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('url')">Analyze URL</button>
            <button class="tab" onclick="switchTab('search')">Search Deals</button>
        </div>

        <div id="url-tab">
            <div class="input-group">
                <input type="url" id="urlInput" placeholder="Paste Amazon, Best Buy, or any product URL..." aria-label="Product URL" />
                <button id="analyzeBtn" onclick="analyzeProduct()">Hunt Deal</button>
            </div>
        </div>

        <div id="search-tab" style="display:none">
            <div class="input-group">
                <input type="text" id="searchInput" placeholder="e.g. best wireless earbuds under $50..." aria-label="Search query" style="flex:1;padding:16px 20px;border:2px solid #444;border-radius:12px;background:rgba(255,255,255,0.05);color:#fff;font-size:1rem;outline:none;" />
                <button id="searchBtn" onclick="searchDeals()">Find Deals</button>
            </div>
        </div>

        <div class="spinner" id="spinner">
            <div></div>
            <p id="spinnerText">Scraping product data...</p>
        </div>

        <p class="error" id="errorMsg"></p>

        <div class="features">
            <div class="feature">
                <div class="feature-icon">&#x1F4B0;</div>
                <h3>Price Comparison</h3>
                <p>Finds prices across stores</p>
            </div>
            <div class="feature">
                <div class="feature-icon">&#x1F4CA;</div>
                <h3>Deal Grade</h3>
                <p>A+ to F rating system</p>
            </div>
            <div class="feature">
                <div class="feature-icon">&#x1F916;</div>
                <h3>AI Analysis</h3>
                <p>Buy now or wait verdict</p>
            </div>
        </div>
    </div>

    <script>
        var spinnerMessages = [
            "Scraping product data...",
            "Searching competitor prices...",
            "Analyzing reviews with AI...",
            "Generating deal report..."
        ];

        function analyzeProduct() {
            var url = document.getElementById("urlInput").value.trim();
            if (!url) {
                showError("Please paste a product URL.");
                return;
            }

            var btn = document.getElementById("analyzeBtn");
            var spinner = document.getElementById("spinner");
            var errorMsg = document.getElementById("errorMsg");

            btn.disabled = true;
            spinner.classList.add("active");
            errorMsg.style.display = "none";

            var msgIndex = 0;
            var msgInterval = setInterval(function() {
                msgIndex = (msgIndex + 1) % spinnerMessages.length;
                document.getElementById("spinnerText").textContent = spinnerMessages[msgIndex];
            }, 4000);

            fetch("/analyze", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({product_url: url})
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                clearInterval(msgInterval);
                if (data.success && data.report_id) {
                    window.location.href = "/report/" + data.report_id;
                } else {
                    showError(data.message || "Analysis failed. Try another URL.");
                    btn.disabled = false;
                    spinner.classList.remove("active");
                }
            })
            .catch(function(err) {
                clearInterval(msgInterval);
                showError("Network error. Please try again.");
                btn.disabled = false;
                spinner.classList.remove("active");
            });
        }

        function showError(msg) {
            var el = document.getElementById("errorMsg");
            el.textContent = msg;
            el.style.display = "block";
        }

        document.getElementById("urlInput").addEventListener("keydown", function(e) {
            if (e.key === "Enter") analyzeProduct();
        });

        function switchTab(tab) {
            var tabs = document.querySelectorAll(".tab");
            tabs[0].classList.toggle("active", tab === "url");
            tabs[1].classList.toggle("active", tab === "search");
            document.getElementById("url-tab").style.display = tab === "url" ? "block" : "none";
            document.getElementById("search-tab").style.display = tab === "search" ? "block" : "none";
            document.getElementById("errorMsg").style.display = "none";
        }

        function searchDeals() {
            var query = document.getElementById("searchInput").value.trim();
            if (!query) {
                showError("Please enter what you're looking for.");
                return;
            }

            var btn = document.getElementById("searchBtn");
            var spinner = document.getElementById("spinner");
            var errorMsg = document.getElementById("errorMsg");

            btn.disabled = true;
            spinner.classList.add("active");
            errorMsg.style.display = "none";

            var searchMessages = [
                "Searching Amazon...",
                "Comparing products...",
                "AI picking the best deal..."
            ];
            var msgIndex = 0;
            var msgInterval = setInterval(function() {
                msgIndex = (msgIndex + 1) % searchMessages.length;
                document.getElementById("spinnerText").textContent = searchMessages[msgIndex];
            }, 3000);

            fetch("/search", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({query: query})
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                clearInterval(msgInterval);
                if (data.success) {
                    window.location.href = "/search-results?q=" + encodeURIComponent(query) + "&id=" + encodeURIComponent(data.search_id);
                } else {
                    showError(data.message || "Search failed. Try different terms.");
                    btn.disabled = false;
                    spinner.classList.remove("active");
                }
            })
            .catch(function(err) {
                clearInterval(msgInterval);
                showError("Network error. Please try again.");
                btn.disabled = false;
                spinner.classList.remove("active");
            });
        }

        document.getElementById("searchInput").addEventListener("keydown", function(e) {
            if (e.key === "Enter") searchDeals();
        });

        // Prefill URL from query param (from search results "Analyze" button)
        var params = new URLSearchParams(window.location.search);
        var prefill = params.get("prefill");
        if (prefill) {
            document.getElementById("urlInput").value = prefill;
            switchTab("url");
        }
    </script>
</body>
</html>"""


REPORT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deal Report - AI Deal Hunter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            color: #fff;
            padding: 40px 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .back-link {
            color: #ffd200;
            text-decoration: none;
            font-size: 0.9rem;
            display: inline-block;
            margin-bottom: 20px;
        }
        .back-link:hover { text-decoration: underline; }
        .header {
            display: flex;
            gap: 24px;
            align-items: flex-start;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .product-image {
            width: 120px;
            height: 120px;
            object-fit: contain;
            background: #fff;
            border-radius: 12px;
            padding: 8px;
        }
        .product-info { flex: 1; min-width: 200px; }
        .product-info h1 { font-size: 1.5rem; margin-bottom: 8px; }
        .product-info .price { font-size: 1.8rem; color: #ffd200; font-weight: 700; }
        .grade-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            font-size: 2rem;
            font-weight: 900;
        }
        .grade-a { background: linear-gradient(135deg, #00b894, #00cec9); color: #fff; }
        .grade-b { background: linear-gradient(135deg, #0984e3, #74b9ff); color: #fff; }
        .grade-c { background: linear-gradient(135deg, #fdcb6e, #f39c12); color: #000; }
        .grade-d { background: linear-gradient(135deg, #e17055, #d63031); color: #fff; }
        .grade-f { background: linear-gradient(135deg, #636e72, #2d3436); color: #fff; }
        .verdict-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }
        .verdict-title {
            font-size: 1.3rem;
            margin-bottom: 8px;
        }
        .verdict-buy { color: #00b894; }
        .verdict-wait { color: #fdcb6e; }
        .confidence-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            margin-top: 12px;
            overflow: hidden;
        }
        .confidence-fill {
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(90deg, #ffd200, #f7971e);
            transition: width 1s ease;
        }
        .confidence-label {
            font-size: 0.85rem;
            color: #aaa;
            margin-top: 6px;
        }
        .section {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .section h2 {
            font-size: 1.1rem;
            margin-bottom: 12px;
            color: #ffd200;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        th { color: #aaa; font-size: 0.85rem; text-transform: uppercase; }
        td a { color: #74b9ff; text-decoration: none; }
        td a:hover { text-decoration: underline; }
        .sentiment-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }
        .sentiment-col h3 {
            font-size: 0.9rem;
            margin-bottom: 8px;
        }
        .sentiment-col.loves h3 { color: #00b894; }
        .sentiment-col.complaints h3 { color: #fdcb6e; }
        .sentiment-col.breakers h3 { color: #ff6b6b; }
        .sentiment-col ul {
            list-style: none;
            padding: 0;
        }
        .sentiment-col li {
            padding: 6px 0;
            font-size: 0.9rem;
            color: #ccc;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .box-link {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 24px;
            background: rgba(0, 107, 228, 0.2);
            border: 1px solid #006be4;
            border-radius: 8px;
            color: #74b9ff;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .box-link:hover { background: rgba(0, 107, 228, 0.3); }
        .savings {
            font-size: 1.1rem;
            color: #00b894;
            font-weight: 600;
            margin-top: 8px;
        }
        .dupe-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
        }
        .dupe-card {
            background: rgba(167, 0, 255, 0.08);
            border: 1px solid rgba(167, 0, 255, 0.3);
            border-radius: 12px;
            padding: 16px;
        }
        .dupe-card h3 {
            font-size: 0.95rem;
            margin-bottom: 6px;
            color: #d4a5ff;
        }
        .dupe-card .dupe-price {
            font-size: 1.2rem;
            font-weight: 700;
            color: #00b894;
            margin-bottom: 6px;
        }
        .dupe-card .dupe-reason {
            font-size: 0.85rem;
            color: #bbb;
            line-height: 1.4;
        }
        .prediction-card {
            background: rgba(9, 132, 227, 0.08);
            border: 1px solid rgba(9, 132, 227, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .prediction-card h2 {
            font-size: 1.1rem;
            margin-bottom: 12px;
            color: #74b9ff;
        }
        .trend-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .trend-dropping { color: #00b894; }
        .trend-rising { color: #ff6b6b; }
        .trend-stable { color: #fdcb6e; }
        .prediction-text {
            font-size: 0.95rem;
            color: #ddd;
            margin-bottom: 10px;
            line-height: 1.5;
        }
        .best-time {
            display: inline-block;
            padding: 6px 14px;
            background: rgba(0, 184, 148, 0.15);
            border: 1px solid rgba(0, 184, 148, 0.4);
            border-radius: 20px;
            font-size: 0.85rem;
            color: #00b894;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">&larr; Back to Search</a>
        <div id="report-content"></div>
    </div>
    <script type="text/plain" id="raw">REPORT_DATA_PLACEHOLDER</script>
    <script>
        var rawEl = document.getElementById("raw");
        var data = JSON.parse(rawEl.textContent);
        var container = document.getElementById("report-content");

        function gradeClass(grade) {
            var g = grade.charAt(0).toUpperCase();
            if (g === "A") return "grade-a";
            if (g === "B") return "grade-b";
            if (g === "C") return "grade-c";
            if (g === "D") return "grade-d";
            return "grade-f";
        }

        function escapeHtml(str) {
            if (!str) return "";
            var div = document.createElement("div");
            div.appendChild(document.createTextNode(str));
            return div.innerHTML;
        }

        var html = "";

        // Header
        html += '<div class="header">';
        if (data.product_image) {
            html += '<img class="product-image" src="' + escapeHtml(data.product_image) + '" alt="Product" />';
        }
        html += '<div class="product-info">';
        html += '<h1>' + escapeHtml(data.product_name) + '</h1>';
        html += '<div class="price">$' + escapeHtml(data.product_price) + '</div>';
        html += '</div>';
        html += '<div class="grade-badge ' + gradeClass(data.deal_grade) + '">' + escapeHtml(data.deal_grade) + '</div>';
        html += '</div>';

        // Verdict
        var verdictClass = data.buy_or_wait.toLowerCase().indexOf("buy") >= 0 ? "verdict-buy" : "verdict-wait";
        html += '<div class="verdict-card">';
        html += '<div class="verdict-title ' + verdictClass + '">' + escapeHtml(data.buy_or_wait) + '</div>';
        html += '<p>' + escapeHtml(data.buy_or_wait_reason) + '</p>';
        html += '<div class="confidence-bar"><div class="confidence-fill" style="width:' + data.confidence_pct + '%"></div></div>';
        html += '<div class="confidence-label">Confidence: ' + data.confidence_pct + '%</div>';
        html += '<div class="savings">' + escapeHtml(data.savings_potential) + '</div>';
        html += '</div>';

        // Price Prediction
        if (data.price_prediction) {
            var trendIcon = "&#x27A1;";
            var trendClass = "trend-stable";
            var trendLabel = "Stable";
            if (data.price_prediction.trend === "dropping") {
                trendIcon = "&#x2198;";
                trendClass = "trend-dropping";
                trendLabel = "Price Dropping";
            } else if (data.price_prediction.trend === "rising") {
                trendIcon = "&#x2197;";
                trendClass = "trend-rising";
                trendLabel = "Price Rising";
            }
            html += '<div class="prediction-card">';
            html += '<h2>&#x1F4C8; Price Prediction</h2>';
            html += '<div class="trend-indicator ' + trendClass + '">' + trendIcon + ' ' + trendLabel + '</div>';
            html += '<div class="prediction-text">' + escapeHtml(data.price_prediction.prediction) + '</div>';
            html += '<span class="best-time">&#x1F4C5; Best time to buy: ' + escapeHtml(data.price_prediction.best_time_to_buy) + '</span>';
            html += '</div>';
        }

        // Competitor Prices
        if (data.competitor_prices && data.competitor_prices.length > 0) {
            html += '<div class="section">';
            html += '<h2>Price Comparison</h2>';
            html += '<table><thead><tr><th>Store</th><th>Price</th><th>Link</th></tr></thead><tbody>';
            for (var i = 0; i < data.competitor_prices.length; i++) {
                var cp = data.competitor_prices[i];
                html += '<tr>';
                html += '<td>' + escapeHtml(cp.store) + '</td>';
                html += '<td>' + escapeHtml(cp.price) + '</td>';
                if (cp.url) {
                    html += '<td><a href="' + escapeHtml(cp.url) + '" target="_blank">View</a></td>';
                } else {
                    html += '<td>-</td>';
                }
                html += '</tr>';
            }
            html += '</tbody></table></div>';
        }

        // Review Sentiment
        if (data.review_sentiment) {
            html += '<div class="section">';
            html += '<h2>Review Analysis</h2>';
            html += '<div class="sentiment-grid">';

            html += '<div class="sentiment-col loves"><h3>&#x2764; People Love</h3><ul>';
            for (var i = 0; i < data.review_sentiment.loves.length; i++) {
                html += '<li>' + escapeHtml(data.review_sentiment.loves[i]) + '</li>';
            }
            html += '</ul></div>';

            html += '<div class="sentiment-col complaints"><h3>&#x26A0; Complaints</h3><ul>';
            for (var i = 0; i < data.review_sentiment.complaints.length; i++) {
                html += '<li>' + escapeHtml(data.review_sentiment.complaints[i]) + '</li>';
            }
            html += '</ul></div>';

            html += '<div class="sentiment-col breakers"><h3>&#x1F6A8; Deal Breakers</h3><ul>';
            if (data.review_sentiment.deal_breakers.length === 0) {
                html += '<li>None found</li>';
            } else {
                for (var i = 0; i < data.review_sentiment.deal_breakers.length; i++) {
                    html += '<li>' + escapeHtml(data.review_sentiment.deal_breakers[i]) + '</li>';
                }
            }
            html += '</ul></div>';

            html += '</div></div>';
        }

        // Dupe Finder
        if (data.dupes && data.dupes.length > 0) {
            html += '<div class="section">';
            html += '<h2>&#x1F50D; Dupe Finder &mdash; Cheaper Alternatives</h2>';
            html += '<div class="dupe-grid">';
            for (var i = 0; i < data.dupes.length; i++) {
                var dupe = data.dupes[i];
                html += '<div class="dupe-card">';
                html += '<h3>' + escapeHtml(dupe.name) + '</h3>';
                html += '<div class="dupe-price">' + escapeHtml(dupe.price) + '</div>';
                html += '<div class="dupe-reason">' + escapeHtml(dupe.why_its_a_dupe) + '</div>';
                if (dupe.url) {
                    html += '<a href="' + escapeHtml(dupe.url) + '" target="_blank" style="display:inline-block;margin-top:8px;color:#74b9ff;font-size:0.85rem;text-decoration:none;">View Product &rarr;</a>';
                }
                html += '</div>';
            }
            html += '</div></div>';
        }

        // Box link
        if (data.box_file_url) {
            html += '<a class="box-link" href="' + escapeHtml(data.box_file_url) + '" target="_blank">&#x1F4C4; View Full Report on Box</a>';
        }

        container.innerHTML = html;

        // Confetti + sound for great deals
        var grade = data.deal_grade.toUpperCase();
        var isBuy = data.buy_or_wait.toLowerCase().indexOf("buy") >= 0;
        var isGreatDeal = (grade === "A+" || grade === "A" || grade === "A-" || grade === "B+") && isBuy;

        if (isGreatDeal) {
            playChaChing();
            launchConfetti();
        }

        function playChaChing() {
            try {
                var ctx = new (window.AudioContext || window.webkitAudioContext)();
                var notes = [
                    {freq: 1318, start: 0, dur: 0.1},
                    {freq: 1568, start: 0.1, dur: 0.1},
                    {freq: 2093, start: 0.2, dur: 0.3}
                ];
                notes.forEach(function(n) {
                    var osc = ctx.createOscillator();
                    var gain = ctx.createGain();
                    osc.type = "sine";
                    osc.frequency.value = n.freq;
                    gain.gain.setValueAtTime(0.3, ctx.currentTime + n.start);
                    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + n.start + n.dur);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(ctx.currentTime + n.start);
                    osc.stop(ctx.currentTime + n.start + n.dur);
                });
            } catch(e) {}
        }

        function launchConfetti() {
            var canvas = document.createElement("canvas");
            canvas.id = "confetti-canvas";
            canvas.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;";
            document.body.appendChild(canvas);
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            var ctx = canvas.getContext("2d");
            var particles = [];
            var colors = ["#ffd200","#f7971e","#00b894","#74b9ff","#ff6b6b","#d4a5ff","#fd79a8"];

            for (var i = 0; i < 150; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height - canvas.height,
                    w: Math.random() * 10 + 5,
                    h: Math.random() * 6 + 3,
                    color: colors[Math.floor(Math.random() * colors.length)],
                    vy: Math.random() * 3 + 2,
                    vx: (Math.random() - 0.5) * 2,
                    rot: Math.random() * 360,
                    rotSpeed: (Math.random() - 0.5) * 10
                });
            }

            var startTime = Date.now();
            function animate() {
                var elapsed = Date.now() - startTime;
                if (elapsed > 4000) {
                    document.body.removeChild(canvas);
                    return;
                }
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                var opacity = elapsed > 3000 ? 1 - (elapsed - 3000) / 1000 : 1;
                ctx.globalAlpha = opacity;
                for (var i = 0; i < particles.length; i++) {
                    var p = particles[i];
                    p.y += p.vy;
                    p.x += p.vx;
                    p.rot += p.rotSpeed;
                    ctx.save();
                    ctx.translate(p.x, p.y);
                    ctx.rotate(p.rot * Math.PI / 180);
                    ctx.fillStyle = p.color;
                    ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
                    ctx.restore();
                }
                requestAnimationFrame(animate);
            }
            animate();
        }
    </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return HOME_HTML


@app.post("/analyze")
async def analyze(request: DealRequest):
    report = run_deal_analysis(request.product_url)
    if report.report_id:
        reports[report.report_id] = report
    return report.model_dump()


# In-memory search results store
search_results: dict = {}


@app.post("/search")
async def search(request: SearchRequest):
    import uuid
    result = run_deal_search(request.query)
    search_id = uuid.uuid4().hex[:8]
    search_results[search_id] = result
    response = result.model_dump()
    response["search_id"] = search_id
    return response


SEARCH_RESULTS_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results - AI Deal Hunter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            color: #fff;
            padding: 40px 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .back-link {
            color: #ffd200;
            text-decoration: none;
            font-size: 0.9rem;
            display: inline-block;
            margin-bottom: 20px;
        }
        .back-link:hover { text-decoration: underline; }
        h1 { font-size: 1.8rem; margin-bottom: 8px; }
        .query-label { color: #aaa; margin-bottom: 24px; font-size: 1rem; }
        .ai-summary {
            background: rgba(0, 184, 148, 0.1);
            border: 1px solid rgba(0, 184, 148, 0.3);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 24px;
            font-size: 1rem;
            color: #00b894;
            font-weight: 600;
        }
        .product-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
            display: flex;
            gap: 16px;
            align-items: center;
            transition: border-color 0.2s;
        }
        .product-card:hover {
            border-color: rgba(255,255,255,0.2);
        }
        .product-card.best-pick {
            border-color: #00b894;
            background: rgba(0, 184, 148, 0.05);
            position: relative;
        }
        .best-badge {
            position: absolute;
            top: -10px;
            right: 16px;
            background: linear-gradient(135deg, #00b894, #00cec9);
            color: #fff;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 12px;
        }
        .product-card img {
            width: 80px;
            height: 80px;
            object-fit: contain;
            background: #fff;
            border-radius: 8px;
            padding: 4px;
            flex-shrink: 0;
        }
        .product-details { flex: 1; min-width: 0; }
        .product-details h3 {
            font-size: 0.95rem;
            margin-bottom: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .product-meta {
            display: flex;
            gap: 16px;
            align-items: center;
            margin-bottom: 6px;
        }
        .product-price {
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffd200;
        }
        .product-rating {
            font-size: 0.85rem;
            color: #aaa;
        }
        .product-reason {
            font-size: 0.85rem;
            color: #bbb;
            line-height: 1.4;
        }
        .product-actions {
            display: flex;
            gap: 8px;
            flex-shrink: 0;
        }
        .btn-view {
            padding: 8px 16px;
            background: rgba(116, 185, 255, 0.15);
            border: 1px solid #74b9ff;
            border-radius: 8px;
            color: #74b9ff;
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .btn-view:hover { background: rgba(116, 185, 255, 0.25); }
        .btn-analyze {
            padding: 8px 16px;
            background: rgba(255, 210, 0, 0.15);
            border: 1px solid #ffd200;
            border-radius: 8px;
            color: #ffd200;
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-analyze:hover { background: rgba(255, 210, 0, 0.25); }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">&larr; Back to Search</a>
        <div id="results-content"></div>
    </div>
    <script type="text/plain" id="raw">SEARCH_DATA_PLACEHOLDER</script>
    <script>
        var rawEl = document.getElementById("raw");
        var data = JSON.parse(rawEl.textContent);
        var container = document.getElementById("results-content");

        function escapeHtml(str) {
            if (!str) return "";
            var div = document.createElement("div");
            div.appendChild(document.createTextNode(str));
            return div.innerHTML;
        }

        var html = "";
        html += '<h1>&#x1F50D; Deal Search Results</h1>';
        html += '<p class="query-label">Showing best deals for: "' + escapeHtml(data.query) + '"</p>';

        if (data.ai_summary) {
            html += '<div class="ai-summary">&#x1F3C6; AI Pick: ' + escapeHtml(data.ai_summary) + '</div>';
        }

        for (var i = 0; i < data.results.length; i++) {
            var p = data.results[i];
            var isBest = p.ai_pick;
            html += '<div class="product-card' + (isBest ? ' best-pick' : '') + '">';
            if (isBest) {
                html += '<span class="best-badge">BEST DEAL</span>';
            }
            if (p.image) {
                html += '<img src="' + escapeHtml(p.image) + '" alt="Product" />';
            }
            html += '<div class="product-details">';
            html += '<h3>' + escapeHtml(p.name) + '</h3>';
            html += '<div class="product-meta">';
            html += '<span class="product-price">$' + escapeHtml(p.price) + '</span>';
            if (p.rating) {
                html += '<span class="product-rating">' + p.rating + ' &#x2B50; (' + (p.review_count || 0) + ' reviews)</span>';
            }
            html += '</div>';
            if (p.ai_reason) {
                html += '<div class="product-reason">' + escapeHtml(p.ai_reason) + '</div>';
            }
            html += '</div>';
            html += '<div class="product-actions">';
            if (p.url) {
                html += '<a class="btn-view" href="' + escapeHtml(p.url) + '" target="_blank">View</a>';
            }
            if (p.url) {
                html += '<a class="btn-analyze" href="/?prefill=' + encodeURIComponent(p.url) + '">Analyze</a>';
            }
            html += '</div>';
            html += '</div>';
        }

        container.innerHTML = html;
    </script>
</body>
</html>"""


@app.get("/search-results", response_class=HTMLResponse)
async def get_search_results(id: str = ""):
    result = search_results.get(id)
    if not result:
        return HTMLResponse(
            content="<h1>Results not found</h1><p><a href='/'>Go back</a></p>",
            status_code=404,
        )
    result_json = json.dumps(result.model_dump(), ensure_ascii=False)
    html = SEARCH_RESULTS_HTML.replace("SEARCH_DATA_PLACEHOLDER", result_json)
    return html


@app.get("/report/{report_id}", response_class=HTMLResponse)
async def get_report(report_id: str):
    report = reports.get(report_id)
    if not report:
        return HTMLResponse(
            content="<h1>Report not found</h1><p><a href='/'>Go back</a></p>",
            status_code=404,
        )
    report_json = json.dumps(report.model_dump(), ensure_ascii=False)
    html = REPORT_HTML.replace("REPORT_DATA_PLACEHOLDER", report_json)
    return html


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
