"""
DecisionDNA — Flask server bridging the React frontend with the Groq backend.
Run: python server.py
Then open http://localhost:5000
"""
from flask import Flask, send_from_directory, request, jsonify
from dotenv import load_dotenv
import os
load_dotenv()
print("KEY:", os.environ.get("GROQ_API_KEY", "NOT FOUND"))


import os
import traceback
from rag import retrieve, is_ingested, get_dna_chunks, INVESTORS
from llm import extract_dna, stress_test, practice_compare, NAME_MAP


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


@app.route("/api/stress", methods=["POST"])
def api_stress():
    try:
        body = request.get_json(force=True)
        investor = body.get("investor", "buffett")
        scenario = body.get("scenario", "").strip()
        stress = body.get("stress", "")
        if not scenario:
            return jsonify({"error": "Scenario is empty."}), 400
        if investor not in INVESTORS:
            return jsonify({"error": f"Unknown investor: {investor}"}), 400
        chunks = retrieve(investor, scenario, n=6)
        result = stress_test(investor, scenario, chunks, stress)
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
        if not scenario:
            return jsonify({"error": "Scenario is empty."}), 400
        if a == b:
            return jsonify({"error": "Pick two different investors."}), 400
        if a not in INVESTORS or b not in INVESTORS:
            return jsonify({"error": "Unknown investor."}), 400
        out = {}
        for inv in (a, b):
            chunks = retrieve(inv, scenario, n=6)
            out[inv] = stress_test(inv, scenario, chunks)
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
        clones = {}
        for inv in ("buffett", "dalio"):
            chunks = retrieve(inv, scenario, n=6)
            clones[inv] = stress_test(inv, scenario, chunks)
        match_data = practice_compare(user_verdict, user_conf, scenario, clones)
        score = match_data.get("score", 50)
        if score >= 70:
            summary = match_data.get("summary") or "Strong alignment with the master investors. Your fundamental analysis is on the right track. Pay attention to conviction sizing — the gap between your confidence and theirs reveals where your framework needs calibration."
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


if __name__ == "__main__":
    print("\n DecisionDNA running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)


