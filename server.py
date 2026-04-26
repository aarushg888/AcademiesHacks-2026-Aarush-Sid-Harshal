"""
DecisionDNA — Flask server bridging the React frontend with the Groq backend.
Run: python server.py
Then open http://localhost:5000
"""
from flask import Flask, send_from_directory, request, jsonify
from dotenv import load_dotenv
import os
import traceback

load_dotenv()
print("KEY:", os.environ.get("GROQ_API_KEY", "NOT FOUND")[:12] + "..." if os.environ.get("GROQ_API_KEY") else "NOT FOUND")

from rag import retrieve, is_ingested, get_dna_chunks, INVESTORS
from llm import (extract_dna, stress_test, practice_compare, analyze_portfolio,
                 get_loading, NAME_MAP, INVESTOR_PROFILES)
from market_data import get_fundamentals, detect_ticker

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("templates", filename)


@app.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "groq_key_set": bool(os.environ.get("GROQ_API_KEY", "").strip()),
        "investors_ready": [i for i in INVESTORS if is_ingested(i)],
    })


@app.route("/api/market/<ticker>")
def api_market(ticker):
    """Live fundamentals lookup — used by frontend for ticker badge / sparkline."""
    try:
        data = get_fundamentals(ticker)
        if not data:
            return jsonify({"error": "No data available", "ticker": ticker}), 404
        return jsonify(data)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/stress", methods=["POST"])
def api_stress():
    try:
        body = request.get_json(force=True)
        investor = body.get("investor", "buffett")
        scenario = body.get("scenario", "").strip()
        stress = body.get("stress", "")
        ticker_hint = body.get("ticker")  # optional explicit ticker from frontend

        if not scenario:
            return jsonify({"error": "Scenario is empty."}), 400
        if investor not in INVESTORS:
            return jsonify({"error": f"Unknown investor: {investor}"}), 400

        # Try to detect ticker and pull live data
        ticker = ticker_hint or detect_ticker(scenario)
        live_data = get_fundamentals(ticker) if ticker else None

        chunks = retrieve(investor, scenario, n=6)
        result = stress_test(investor, scenario, chunks, stress, live_data=live_data)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/compare", methods=["POST"])
def api_compare():
    try:
        body = request.get_json(force=True)
        a = body.get("investor_a", "buffett")
        b = body.get("investor_b", "dalio")
        scenario = body.get("scenario", "").strip()
        ticker_hint = body.get("ticker")

        if not scenario:
            return jsonify({"error": "Scenario is empty."}), 400
        if a == b:
            return jsonify({"error": "Pick two different investors."}), 400
        if a not in INVESTORS or b not in INVESTORS:
            return jsonify({"error": "Unknown investor."}), 400

        ticker = ticker_hint or detect_ticker(scenario)
        live_data = get_fundamentals(ticker) if ticker else None

        out = {}
        for inv in (a, b):
            chunks = retrieve(inv, scenario, n=6)
            out[inv] = stress_test(inv, scenario, chunks, live_data=live_data)
        return jsonify(out)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/practice", methods=["POST"])
def api_practice():
    try:
        body = request.get_json(force=True)
        scenario = body.get("scenario", "").strip()
        user_verdict = str(body.get("user_verdict", "HOLD")).upper()
        user_conf = int(body.get("user_confidence", 50))

        if not scenario:
            return jsonify({"error": "Scenario is empty."}), 400

        ticker = detect_ticker(scenario)
        live_data = get_fundamentals(ticker) if ticker else None

        clones = {}
        for inv in ("buffett", "dalio"):
            chunks = retrieve(inv, scenario, n=6)
            clones[inv] = stress_test(inv, scenario, chunks, live_data=live_data)
        match_data = practice_compare(user_verdict, user_conf, scenario, clones)
        score = match_data.get("score", 50)
        if score >= 70:
            summary = match_data.get("summary") or "Strong alignment with the masters. Pay attention to conviction sizing — the gap between your confidence and theirs reveals where your framework needs calibration."
        elif score >= 45:
            summary = match_data.get("summary") or "Mixed alignment. You identified the correct direction in some cases, but your conviction calibration differs significantly. Study how each investor weighs valuation vs. growth vs. risk."
        else:
            summary = match_data.get("summary") or "Significant divergence from both investors. This is valuable — it means your framework weighs the factors differently. Dig into each investor's reasoning to understand the key disagreements."
        return jsonify({
            "clones": clones,
            "matches": match_data.get("matches", []),
            "score": score,
            "summary": summary,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/dna", methods=["POST"])
def api_dna():
    try:
        body = request.get_json(force=True)
        investor = body.get("investor", "buffett")
        if investor not in INVESTORS:
            return jsonify({"error": f"Unknown investor: {investor}"}), 400
        if not is_ingested(investor):
            return jsonify({"error": "Investor data not loaded."}), 400
        chunks = get_dna_chunks(investor)
        dna = extract_dna(investor, chunks)
        return jsonify(dna)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/portfolio", methods=["POST"])
def api_portfolio():
    try:
        body = request.get_json(force=True)
        holdings = body.get("holdings", [])
        focus_investor = body.get("focus_investor", "buffett")
        if not holdings:
            return jsonify({"error": "No holdings provided."}), 400
        if len(holdings) > 10:
            return jsonify({"error": "Max 10 holdings."}), 400
        if focus_investor not in INVESTORS:
            return jsonify({"error": "Unknown investor."}), 400

        # Pull live data for every holding
        live_map = {}
        for h in holdings:
            t = h.get("ticker", "").upper()
            if t:
                ld = get_fundamentals(t)
                if ld:
                    live_map[t] = ld

        result = analyze_portfolio(holdings, focus_investor, live_data_map=live_map)
        # Attach live snapshots so frontend can render price chips
        result["live_snapshots"] = {
            t: {"price": d.get("price"), "change_pct": d.get("change_pct"),
                "pe_ratio": d.get("pe_ratio"), "market_cap_fmt": d.get("market_cap_fmt")}
            for t, d in live_map.items()
        }
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n  DecisionDNA running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
