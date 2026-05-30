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
    <title>Deal Hunter - Smart Shopping Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: #fafafa;
            color: #1a1a1a;
            min-height: 100vh;
        }
        /* Nav */
        .nav {
            background: #fff;
            border-bottom: 1px solid #eee;
            padding: 14px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            color: #1a1a1a;
            font-weight: 800;
            font-size: 1.1rem;
        }
        .nav-brand svg { width: 24px; height: 24px; }
        .nav-tag {
            font-size: 0.65rem;
            background: #fff0f0;
            color: #e53e3e;
            padding: 3px 8px;
            border-radius: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        /* Promo banner */
        .promo-bar {
            background: linear-gradient(90deg, #e53e3e, #dd6b20);
            color: #fff;
            text-align: center;
            padding: 10px 16px;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .promo-bar span { opacity: 0.85; }

        /* Hero */
        .hero {
            max-width: 640px;
            margin: 0 auto;
            padding: 72px 24px 48px;
            text-align: center;
        }
        .hero h1 {
            font-size: 2.6rem;
            font-weight: 800;
            line-height: 1.15;
            color: #1a1a1a;
            margin-bottom: 12px;
            letter-spacing: -0.02em;
        }
        .hero h1 .price-pop {
            background: linear-gradient(135deg, #e53e3e, #dd6b20);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-sub {
            font-size: 1.05rem;
            color: #666;
            line-height: 1.6;
            margin-bottom: 40px;
        }
        /* Search box */
        .search-card {
            background: #fff;
            border: 1px solid #e8e8e8;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.04);
            max-width: 560px;
            margin: 0 auto;
        }
        .tab-pills {
            display: flex;
            gap: 4px;
            background: #f5f5f5;
            border-radius: 10px;
            padding: 4px;
            margin-bottom: 20px;
        }
        .pill {
            flex: 1;
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            background: transparent;
            color: #888;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.2s;
        }
        .pill.active {
            background: #fff;
            color: #1a1a1a;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }
        .search-row {
            display: flex;
            gap: 10px;
        }
        .search-row input {
            flex: 1;
            padding: 14px 18px;
            border: 1.5px solid #e8e8e8;
            border-radius: 10px;
            font-size: 0.95rem;
            font-family: inherit;
            outline: none;
            color: #1a1a1a;
            background: #fafafa;
            transition: border-color 0.2s, background 0.2s;
        }
        .search-row input:focus {
            border-color: #e53e3e;
            background: #fff;
        }
        .search-row input::placeholder { color: #bbb; }
        .go-btn {
            padding: 14px 24px;
            background: #e53e3e;
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 0.9rem;
            font-weight: 700;
            cursor: pointer;
            font-family: inherit;
            white-space: nowrap;
            transition: background 0.15s, transform 0.1s;
        }
        .go-btn:hover { background: #c53030; }
        .go-btn:active { transform: scale(0.97); }
        .go-btn:disabled { background: #ddd; color: #999; cursor: not-allowed; transform: none; }
        /* Loading */
        .loader { display: none; text-align: center; margin-top: 20px; }
        .loader.active { display: block; }
        .loader-dots { display: flex; gap: 6px; justify-content: center; margin-bottom: 10px; }
        .loader-dots span {
            width: 8px; height: 8px; background: #e53e3e; border-radius: 50%;
            animation: bounce 1.4s ease-in-out infinite;
        }
        .loader-dots span:nth-child(2) { animation-delay: 0.2s; }
        .loader-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1); opacity: 1; }
        }
        .loader p { font-size: 0.82rem; color: #999; }
        .error-msg {
            display: none;
            margin-top: 14px;
            padding: 10px 14px;
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
            color: #c53030;
            font-size: 0.84rem;
        }

        /* Trust badges */
        .trust-row {
            display: flex;
            justify-content: center;
            gap: 32px;
            margin-top: 32px;
            flex-wrap: wrap;
        }
        .trust-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.78rem;
            color: #999;
        }
        .trust-item svg { width: 16px; height: 16px; color: #ccc; }

        /* How it works */
        .how-section {
            max-width: 800px;
            margin: 0 auto;
            padding: 64px 24px;
        }
        .how-section h2 {
            text-align: center;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 40px;
            color: #1a1a1a;
        }
        .steps {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
        }
        .step {
            text-align: center;
            padding: 24px 16px;
        }
        .step-num {
            width: 36px;
            height: 36px;
            background: #fff0f0;
            color: #e53e3e;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.9rem;
            margin-bottom: 14px;
        }
        .step h3 { font-size: 0.95rem; font-weight: 700; margin-bottom: 6px; }
        .step p { font-size: 0.82rem; color: #888; line-height: 1.5; }
        /* Stores strip */
        .stores-strip {
            text-align: center;
            padding: 32px 24px 64px;
            border-top: 1px solid #f0f0f0;
        }
        .stores-strip p {
            font-size: 0.75rem;
            color: #bbb;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 16px;
        }
        .store-logos {
            display: flex;
            justify-content: center;
            gap: 28px;
            flex-wrap: wrap;
            color: #ccc;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .store-logos span { opacity: 0.5; }

        @media (max-width: 640px) {
            .hero h1 { font-size: 1.9rem; }
            .search-row { flex-direction: column; }
            .go-btn { width: 100%; }
            .steps { grid-template-columns: 1fr; gap: 16px; }
            .hero { padding: 48px 20px 32px; }
            .nav { padding: 12px 16px; }
        }
    </style>
</head>
<body>
    <div class="promo-bar">&#x1F525; <span>AI-powered price hunting &mdash; compare 6+ stores in 30 seconds</span></div>
    <nav class="nav">
        <a href="/" class="nav-brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
            Deal Hunter
        </a>
        <span class="nav-tag">Beta</span>
    </nav>

    <div class="hero">
        <h1>Find the <span class="price-pop">lowest price</span> on anything you want to buy</h1>
        <p class="hero-sub">Paste a product link or search for what you need. Our AI checks prices across stores, reads reviews, and tells you if it's worth buying today.</p>

        <div class="search-card">
            <div class="tab-pills">
                <button class="pill active" onclick="switchTab('url')">&#x1F517; Paste a link</button>
                <button class="pill" onclick="switchTab('search')">&#x1F6D2; Search product</button>
            </div>
            <div id="url-tab">
                <div class="search-row">
                    <input type="url" id="urlInput" placeholder="https://amazon.com/dp/B0..." aria-label="Product URL" />
                    <button class="go-btn" id="analyzeBtn" onclick="analyzeProduct()">Hunt deal</button>
                </div>
            </div>
            <div id="search-tab" style="display:none">
                <div class="search-row">
                    <input type="text" id="searchInput" placeholder="wireless earbuds, air fryer, running shoes..." aria-label="Search" />
                    <button class="go-btn" id="searchBtn" onclick="searchDeals()">Find deals</button>
                </div>
            </div>
            <div class="loader" id="spinner">
                <div class="loader-dots"><span></span><span></span><span></span></div>
                <p id="spinnerText">Checking prices across stores...</p>
            </div>
            <div class="error-msg" id="errorMsg"></div>
        </div>

        <div class="trust-row">
            <div class="trust-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                No sign-up needed
            </div>
            <div class="trust-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Results in 30 seconds
            </div>
            <div class="trust-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                Avg $127 saved
            </div>
        </div>
    </div>

    <div class="how-section">
        <h2>How it works</h2>
        <div class="steps">
            <div class="step">
                <div class="step-num">1</div>
                <h3>Paste or search</h3>
                <p>Drop in any product URL from Amazon, Best Buy, Walmart — or just describe what you want</p>
            </div>
            <div class="step">
                <div class="step-num">2</div>
                <h3>AI hunts deals</h3>
                <p>We scrape prices from 6+ stores, analyze reviews, and check price history in seconds</p>
            </div>
            <div class="step">
                <div class="step-num">3</div>
                <h3>Buy or wait</h3>
                <p>Get a deal grade, price prediction, cheaper alternatives, and a clear buy/wait recommendation</p>
            </div>
        </div>
    </div>

    <div class="stores-strip">
        <p>Compares prices from</p>
        <div class="store-logos">
            <span>Amazon</span>
            <span>Walmart</span>
            <span>Best Buy</span>
            <span>Target</span>
            <span>Newegg</span>
            <span>eBay</span>
        </div>
    </div>

    <script>
        var msgs = ["Checking prices across stores...", "Reading customer reviews...", "Finding cheaper alternatives...", "Generating your deal report..."];
        function switchTab(t) {
            document.querySelectorAll(".pill").forEach(function(p,i){ p.classList.toggle("active", (t==="url"&&i===0)||(t==="search"&&i===1)); });
            document.getElementById("url-tab").style.display = t==="url"?"block":"none";
            document.getElementById("search-tab").style.display = t==="search"?"block":"none";
            document.getElementById("errorMsg").style.display = "none";
        }
        function showErr(m) { var e=document.getElementById("errorMsg"); e.textContent=m; e.style.display="block"; }
        function analyzeProduct() {
            var url = document.getElementById("urlInput").value.trim();
            if (!url) { showErr("Paste a product URL to get started."); return; }
            var btn = document.getElementById("analyzeBtn");
            var sp = document.getElementById("spinner");
            btn.disabled = true; sp.classList.add("active"); document.getElementById("errorMsg").style.display="none";
            var mi=0, iv=setInterval(function(){ mi=(mi+1)%msgs.length; document.getElementById("spinnerText").textContent=msgs[mi]; },3500);
            fetch("/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({product_url:url})})
            .then(function(r){return r.json();})
            .then(function(d){ clearInterval(iv); if(d.success&&d.report_id){window.location.href="/report/"+d.report_id;}else{showErr(d.message||"Couldn't analyze this product.");btn.disabled=false;sp.classList.remove("active");}})
            .catch(function(){clearInterval(iv);showErr("Network error. Try again.");btn.disabled=false;sp.classList.remove("active");});
        }
        function searchDeals() {
            var q = document.getElementById("searchInput").value.trim();
            if (!q) { showErr("Tell us what you're shopping for."); return; }
            var btn = document.getElementById("searchBtn");
            var sp = document.getElementById("spinner");
            btn.disabled = true; sp.classList.add("active"); document.getElementById("errorMsg").style.display="none";
            var sm=["Searching products...","Comparing prices...","Picking the best deal..."],mi=0;
            var iv=setInterval(function(){mi=(mi+1)%sm.length;document.getElementById("spinnerText").textContent=sm[mi];},3000);
            fetch("/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:q})})
            .then(function(r){return r.json();})
            .then(function(d){clearInterval(iv);if(d.success){window.location.href="/search-results?q="+encodeURIComponent(q)+"&id="+encodeURIComponent(d.search_id);}else{showErr(d.message||"Search failed.");btn.disabled=false;sp.classList.remove("active");}})
            .catch(function(){clearInterval(iv);showErr("Network error.");btn.disabled=false;sp.classList.remove("active");});
        }
        document.getElementById("urlInput").addEventListener("keydown",function(e){if(e.key==="Enter")analyzeProduct();});
        document.getElementById("searchInput").addEventListener("keydown",function(e){if(e.key==="Enter")searchDeals();});
        var pp=new URLSearchParams(window.location.search);if(pp.get("prefill")){document.getElementById("urlInput").value=pp.get("prefill");switchTab("url");}
    </script>
</body>
</html>"""


REPORT_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deal Report - Deal Hunter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: #f5f5f5;
            color: #1a1a1a;
            min-height: 100vh;
            padding-bottom: 60px;
        }
        .nav {
            background: #fff;
            border-bottom: 1px solid #eee;
            padding: 14px 32px;
            display: flex;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            color: #1a1a1a;
            font-weight: 800;
            font-size: 1.1rem;
        }
        .nav-brand svg { width: 22px; height: 22px; }
        .container { max-width: 820px; margin: 0 auto; padding: 32px 20px; }

        /* Product card at top */
        .product-card {
            background: #fff;
            border: 1px solid #e8e8e8;
            border-radius: 16px;
            padding: 28px;
            display: flex;
            gap: 24px;
            align-items: flex-start;
            margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.03);
        }
        .product-card img {
            width: 120px;
            height: 120px;
            object-fit: contain;
            background: #fafafa;
            border-radius: 12px;
            padding: 8px;
            border: 1px solid #f0f0f0;
            flex-shrink: 0;
        }
        .product-card .info { flex: 1; }
        .product-card h1 { font-size: 1.2rem; font-weight: 700; margin-bottom: 8px; line-height: 1.3; color: #1a1a1a; }
        .product-card .price-line { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
        .product-card .price { font-size: 1.8rem; font-weight: 800; color: #1a1a1a; }
        /* Grade badge */
        .grade {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 800;
        }
        .grade-a { background: #dcfce7; color: #166534; }
        .grade-b { background: #dbeafe; color: #1e40af; }
        .grade-c { background: #fef3c7; color: #92400e; }
        .grade-d { background: #fee2e2; color: #991b1b; }
        .grade-f { background: #f3f4f6; color: #6b7280; }

        /* Verdict */
        .verdict-banner {
            background: #fff;
            border: 1px solid #e8e8e8;
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.03);
        }
        .verdict-banner .label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #999;
            margin-bottom: 6px;
            font-weight: 600;
        }
        .verdict-banner .verdict-text {
            font-size: 1.3rem;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .v-buy { color: #16a34a; }
        .v-wait { color: #d97706; }
        .verdict-banner .reason {
            font-size: 0.9rem;
            color: #666;
            line-height: 1.6;
            margin-bottom: 14px;
        }
        .conf-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
        .conf-track { flex: 1; height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden; }
        .conf-bar { height: 100%; background: #e53e3e; border-radius: 3px; transition: width 1s ease; }
        .conf-label { font-size: 0.78rem; color: #999; font-weight: 600; min-width: 32px; }
        .savings-badge {
            display: inline-block;
            padding: 6px 12px;
            background: #dcfce7;
            color: #166534;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 700;
        }

        /* Cards */
        .card {
            background: #fff;
            border: 1px solid #e8e8e8;
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 16px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.03);
        }
        .card-title {
            font-size: 0.9rem;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-title .emoji { font-size: 1.1rem; }
        /* Table */
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 11px 0; text-align: left; font-size: 0.88rem; border-bottom: 1px solid #f0f0f0; }
        th { color: #999; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }
        td { color: #333; }
        td a { color: #e53e3e; text-decoration: none; font-weight: 600; }
        td a:hover { text-decoration: underline; }
        td:last-child, th:last-child { text-align: right; }

        /* Sentiment */
        .sent-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        .sent-col h4 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 700; margin-bottom: 10px; }
        .sent-col.loves h4 { color: #16a34a; }
        .sent-col.complaints h4 { color: #d97706; }
        .sent-col.breakers h4 { color: #dc2626; }
        .sent-col ul { list-style: none; }
        .sent-col li { font-size: 0.84rem; color: #555; padding: 6px 0; border-bottom: 1px solid #f5f5f5; line-height: 1.4; }

        /* Prediction */
        .trend-chip {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 5px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .trend-dropping { background: #dcfce7; color: #166534; }
        .trend-rising { background: #fee2e2; color: #991b1b; }
        .trend-stable { background: #fef3c7; color: #92400e; }
        .pred-text { font-size: 0.9rem; color: #555; line-height: 1.6; margin-bottom: 10px; }
        .best-time-chip {
            display: inline-block;
            padding: 6px 12px;
            background: #f5f5f5;
            border-radius: 6px;
            font-size: 0.8rem;
            color: #555;
            font-weight: 600;
        }

        /* Dupes */
        .dupe-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
        .dupe-card {
            border: 1px solid #f0f0f0;
            border-radius: 12px;
            padding: 16px;
            background: #fafafa;
        }
        .dupe-card h4 { font-size: 0.88rem; font-weight: 600; color: #333; margin-bottom: 4px; }
        .dupe-card .dp { font-size: 1.1rem; font-weight: 800; color: #16a34a; margin-bottom: 6px; }
        .dupe-card .dw { font-size: 0.78rem; color: #888; line-height: 1.4; }
        .dupe-card a { display: inline-block; margin-top: 8px; font-size: 0.78rem; color: #e53e3e; text-decoration: none; font-weight: 600; }
        .dupe-card a:hover { text-decoration: underline; }

        .box-link {
            display: inline-block;
            margin-top: 16px;
            padding: 10px 18px;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            color: #555;
            text-decoration: none;
            font-size: 0.84rem;
            font-weight: 600;
        }
        .box-link:hover { border-color: #bbb; }

        @media (max-width: 640px) {
            .product-card { flex-direction: column; align-items: center; text-align: center; }
            .sent-grid { grid-template-columns: 1fr; }
            .dupe-grid { grid-template-columns: 1fr; }
            .container { padding: 20px 16px; }
        }
    </style>
</head>
<body>
    <nav class="nav">
        <a href="/" class="nav-brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
            Deal Hunter
        </a>
    </nav>
    <div class="container" id="report-content"></div>
    <script type="text/plain" id="raw">REPORT_DATA_PLACEHOLDER</script>
    <script>
        var data = JSON.parse(document.getElementById("raw").textContent);
        var c = document.getElementById("report-content");
        function esc(s){if(!s)return "";var d=document.createElement("div");d.appendChild(document.createTextNode(s));return d.innerHTML;}
        function gc(g){var l=g.charAt(0).toUpperCase();if(l==="A")return"grade-a";if(l==="B")return"grade-b";if(l==="C")return"grade-c";if(l==="D")return"grade-d";return"grade-f";}

        var h = "";
        // Product
        h += '<div class="product-card">';
        if (data.product_image) h += '<img src="'+esc(data.product_image)+'" alt="Product" />';
        h += '<div class="info"><h1>'+esc(data.product_name)+'</h1>';
        h += '<div class="price-line"><span class="price">$'+esc(data.product_price)+'</span>';
        h += '<span class="grade '+gc(data.deal_grade)+'">'+esc(data.deal_grade)+' Deal</span></div></div></div>';

        // Verdict
        var vc = data.buy_or_wait.toLowerCase().indexOf("buy")>=0?"v-buy":"v-wait";
        h += '<div class="verdict-banner">';
        h += '<div class="label">AI Recommendation</div>';
        h += '<div class="verdict-text '+vc+'">'+esc(data.buy_or_wait)+'</div>';
        h += '<div class="reason">'+esc(data.buy_or_wait_reason)+'</div>';
        h += '<div class="conf-row"><div class="conf-track"><div class="conf-bar" style="width:'+data.confidence_pct+'%"></div></div><span class="conf-label">'+data.confidence_pct+'%</span></div>';
        if (data.savings_potential) h += '<span class="savings-badge">'+esc(data.savings_potential)+'</span>';
        h += '</div>';

        // Prediction
        if (data.price_prediction) {
            var tl="Stable",tc="trend-stable";
            if(data.price_prediction.trend==="dropping"){tl="Price Dropping";tc="trend-dropping";}
            else if(data.price_prediction.trend==="rising"){tl="Price Rising";tc="trend-rising";}
            h += '<div class="card"><div class="card-title"><span class="emoji">&#x1F4C9;</span> Price Prediction</div>';
            h += '<span class="trend-chip '+tc+'">'+tl+'</span>';
            h += '<div class="pred-text">'+esc(data.price_prediction.prediction)+'</div>';
            h += '<span class="best-time-chip">&#x1F4C5; '+esc(data.price_prediction.best_time_to_buy)+'</span></div>';
        }

        // Prices
        if (data.competitor_prices && data.competitor_prices.length > 0) {
            h += '<div class="card"><div class="card-title"><span class="emoji">&#x1F6D2;</span> Price Comparison</div>';
            h += '<table><thead><tr><th>Store</th><th>Price</th><th></th></tr></thead><tbody>';
            for(var i=0;i<data.competitor_prices.length;i++){var cp=data.competitor_prices[i];h+='<tr><td>'+esc(cp.store)+'</td><td style="font-weight:700">'+esc(cp.price)+'</td><td>'+(cp.url?'<a href="'+esc(cp.url)+'" target="_blank">Shop &rarr;</a>':'')+'</td></tr>';}
            h += '</tbody></table></div>';
        }

        // Sentiment
        if (data.review_sentiment) {
            h += '<div class="card"><div class="card-title"><span class="emoji">&#x1F4AC;</span> What Shoppers Say</div>';
            h += '<div class="sent-grid">';
            h += '<div class="sent-col loves"><h4>&#x2705; Love it</h4><ul>';
            for(var i=0;i<data.review_sentiment.loves.length;i++) h+='<li>'+esc(data.review_sentiment.loves[i])+'</li>';
            h += '</ul></div>';
            h += '<div class="sent-col complaints"><h4>&#x26A0;&#xFE0F; Meh</h4><ul>';
            for(var i=0;i<data.review_sentiment.complaints.length;i++) h+='<li>'+esc(data.review_sentiment.complaints[i])+'</li>';
            h += '</ul></div>';
            h += '<div class="sent-col breakers"><h4>&#x1F6A9; Avoid if</h4><ul>';
            if(data.review_sentiment.deal_breakers.length===0) h+='<li>No major issues found</li>';
            else for(var i=0;i<data.review_sentiment.deal_breakers.length;i++) h+='<li>'+esc(data.review_sentiment.deal_breakers[i])+'</li>';
            h += '</ul></div></div></div>';
        }

        // Dupes
        if (data.dupes && data.dupes.length > 0) {
            h += '<div class="card"><div class="card-title"><span class="emoji">&#x1F4A1;</span> Cheaper Alternatives</div>';
            h += '<div class="dupe-grid">';
            for(var i=0;i<data.dupes.length;i++){var d=data.dupes[i];h+='<div class="dupe-card"><h4>'+esc(d.name)+'</h4><div class="dp">'+esc(d.price)+'</div><div class="dw">'+esc(d.why_its_a_dupe)+'</div>'+(d.url?'<a href="'+esc(d.url)+'" target="_blank">View &rarr;</a>':'')+'</div>';}
            h += '</div></div>';
        }

        if (data.box_file_url) h += '<a class="box-link" href="'+esc(data.box_file_url)+'" target="_blank">&#x1F4CE; Full report on Box</a>';
        c.innerHTML = h;

        // Confetti for great deals
        var grade=data.deal_grade.toUpperCase();
        var isBuy=data.buy_or_wait.toLowerCase().indexOf("buy")>=0;
        if((grade==="A+"||grade==="A"||grade==="A-"||grade==="B+")&&isBuy){chaChing();confetti();}

        function chaChing(){try{var ctx=new(window.AudioContext||window.webkitAudioContext)();[{f:1318,s:0,d:0.1},{f:1568,s:0.1,d:0.1},{f:2093,s:0.2,d:0.3}].forEach(function(n){var o=ctx.createOscillator(),g=ctx.createGain();o.type="sine";o.frequency.value=n.f;g.gain.setValueAtTime(0.3,ctx.currentTime+n.s);g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+n.s+n.d);o.connect(g);g.connect(ctx.destination);o.start(ctx.currentTime+n.s);o.stop(ctx.currentTime+n.s+n.d);});}catch(e){}}

        function confetti(){var cv=document.createElement("canvas");cv.style.cssText="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;";document.body.appendChild(cv);cv.width=window.innerWidth;cv.height=window.innerHeight;var ctx=cv.getContext("2d");var ps=[],cols=["#e53e3e","#16a34a","#2563eb","#d97706","#7c3aed","#ec4899"];for(var i=0;i<120;i++)ps.push({x:Math.random()*cv.width,y:Math.random()*cv.height-cv.height,w:Math.random()*8+4,h:Math.random()*5+2,c:cols[Math.floor(Math.random()*cols.length)],vy:Math.random()*3+2,vx:(Math.random()-0.5)*2,r:Math.random()*360,rs:(Math.random()-0.5)*8});var t0=Date.now();(function draw(){var el=Date.now()-t0;if(el>3500){document.body.removeChild(cv);return;}ctx.clearRect(0,0,cv.width,cv.height);ctx.globalAlpha=el>2500?1-(el-2500)/1000:1;for(var i=0;i<ps.length;i++){var p=ps[i];p.y+=p.vy;p.x+=p.vx;p.r+=p.rs;ctx.save();ctx.translate(p.x,p.y);ctx.rotate(p.r*Math.PI/180);ctx.fillStyle=p.c;ctx.fillRect(-p.w/2,-p.h/2,p.w,p.h);ctx.restore();}requestAnimationFrame(draw);})();}
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
    <title>Search Results - Deal Hunter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: #f5f5f5;
            color: #1a1a1a;
            min-height: 100vh;
            padding-bottom: 60px;
        }
        .nav {
            background: #fff;
            border-bottom: 1px solid #eee;
            padding: 14px 32px;
            display: flex;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            color: #1a1a1a;
            font-weight: 800;
            font-size: 1.1rem;
        }
        .nav-brand svg { width: 22px; height: 22px; }
        .container { max-width: 820px; margin: 0 auto; padding: 32px 20px; }
        h1 { font-size: 1.4rem; font-weight: 800; margin-bottom: 4px; }
        .sub { color: #888; font-size: 0.88rem; margin-bottom: 24px; }
        .ai-pick-banner {
            background: #fff;
            border: 1px solid #dcfce7;
            border-left: 4px solid #16a34a;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 20px;
            font-size: 0.88rem;
            color: #166534;
            font-weight: 600;
        }
        .product-item {
            background: #fff;
            border: 1px solid #e8e8e8;
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 10px;
            display: flex;
            gap: 16px;
            align-items: center;
            position: relative;
            box-shadow: 0 1px 6px rgba(0,0,0,0.02);
            transition: box-shadow 0.2s;
        }
        .product-item:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
        .product-item.best { border-color: #bbf7d0; background: #f0fdf4; }
        .best-label {
            position: absolute;
            top: -8px;
            right: 16px;
            background: #16a34a;
            color: #fff;
            font-size: 0.65rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .product-item img {
            width: 72px;
            height: 72px;
            object-fit: contain;
            background: #fafafa;
            border-radius: 10px;
            padding: 4px;
            border: 1px solid #f0f0f0;
            flex-shrink: 0;
        }
        .pi-info { flex: 1; min-width: 0; }
        .pi-info h3 { font-size: 0.9rem; font-weight: 600; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .pi-row { display: flex; gap: 12px; align-items: center; margin-bottom: 4px; }
        .pi-price { font-size: 1.1rem; font-weight: 800; color: #1a1a1a; }
        .pi-rating { font-size: 0.78rem; color: #999; }
        .pi-reason { font-size: 0.78rem; color: #888; line-height: 1.4; }
        .pi-actions { display: flex; gap: 8px; flex-shrink: 0; }
        .btn-s {
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            text-decoration: none;
            border: 1px solid #e0e0e0;
            color: #555;
            background: #fff;
            cursor: pointer;
            transition: all 0.15s;
        }
        .btn-s:hover { border-color: #ccc; color: #1a1a1a; }
        .btn-s.red { background: #e53e3e; border-color: #e53e3e; color: #fff; }
        .btn-s.red:hover { background: #c53030; }

        @media (max-width: 640px) {
            .product-item { flex-direction: column; align-items: flex-start; }
            .pi-actions { width: 100%; }
            .btn-s { flex: 1; text-align: center; }
            .container { padding: 20px 16px; }
        }
    </style>
</head>
<body>
    <nav class="nav">
        <a href="/" class="nav-brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
            Deal Hunter
        </a>
    </nav>
    <div class="container" id="results-content"></div>
    <script type="text/plain" id="raw">SEARCH_DATA_PLACEHOLDER</script>
    <script>
        var data = JSON.parse(document.getElementById("raw").textContent);
        var c = document.getElementById("results-content");
        function esc(s){if(!s)return "";var d=document.createElement("div");d.appendChild(document.createTextNode(s));return d.innerHTML;}

        var h = '<h1>&#x1F6D2; Results</h1>';
        h += '<p class="sub">Deals for "'+esc(data.query)+'"</p>';
        if (data.ai_summary) h += '<div class="ai-pick-banner">&#x1F3AF; AI Pick: '+esc(data.ai_summary)+'</div>';

        for (var i=0;i<data.results.length;i++) {
            var p = data.results[i], best = p.ai_pick;
            h += '<div class="product-item'+(best?' best':'')+'">';
            if (best) h += '<span class="best-label">Best Deal</span>';
            if (p.image) h += '<img src="'+esc(p.image)+'" alt="" />';
            h += '<div class="pi-info"><h3>'+esc(p.name)+'</h3>';
            h += '<div class="pi-row"><span class="pi-price">$'+esc(p.price)+'</span>';
            if (p.rating) h += '<span class="pi-rating">'+p.rating+' &#x2B50; ('+( p.review_count||0)+' reviews)</span>';
            h += '</div>';
            if (p.ai_reason) h += '<div class="pi-reason">'+esc(p.ai_reason)+'</div>';
            h += '</div><div class="pi-actions">';
            if (p.url) h += '<a class="btn-s" href="'+esc(p.url)+'" target="_blank">View</a>';
            if (p.url) h += '<a class="btn-s red" href="/?prefill='+encodeURIComponent(p.url)+'">Analyze</a>';
            h += '</div></div>';
        }
        c.innerHTML = h;
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
