import requests
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

NAME_MAP = {
    "buffett": "Warren Buffett",
    "munger":  "Charlie Munger",
    "dalio":   "Ray Dalio",
    "lynch":   "Peter Lynch",
}

INVESTOR_PROFILES = {
    "buffett": {
        "loading": "Checking for durable moats…",
        "style": "fundamentals-first, long-term, moat-obsessed",
        "weights": {"valuation": 0.30, "growth": 0.20, "risk": 0.25, "moat": 0.25},
        "personality": (
            "Warren Buffett speaks plainly, uses folksy analogies, and focuses entirely on "
            "business fundamentals. He ignores macro, loves pricing power, demands predictable "
            "owner earnings and high ROE without leverage. He buys wonderful businesses at fair "
            "prices and holds forever. He is skeptical of complexity and hype."
        ),
    },
    "munger": {
        "loading": "Inverting the problem…",
        "style": "mental-models, inversion, incentive-first",
        "weights": {"valuation": 0.20, "growth": 0.15, "risk": 0.35, "moat": 0.30},
        "personality": (
            "Charlie Munger inverts problems first — he asks what would cause failure before "
            "asking if it's a buy. He demands proper incentive structures, despises accounting tricks, "
            "and looks for lollapalooza effects where multiple advantages compound. He is blunt, "
            "intellectually rigorous, and often just says 'too hard, pass.'"
        ),
    },
    "dalio": {
        "loading": "Locating the debt cycle…",
        "style": "macro-regime, debt-cycle, risk-parity",
        "weights": {"valuation": 0.15, "growth": 0.20, "risk": 0.40, "macro": 0.25},
        "personality": (
            "Ray Dalio thinks in macro regimes and debt cycles, not individual stock quality. "
            "He identifies which economic season (rising/falling growth, rising/falling inflation) "
            "an asset benefits from. He stress-tests against deflation and 15% inflation. "
            "He is systematic, principle-driven, and heavily focused on portfolio correlation."
        ),
    },
    "lynch": {
        "loading": "Running the two-minute drill…",
        "style": "growth-focused, consumer-edge, PEG-driven",
        "weights": {"valuation": 0.30, "growth": 0.35, "risk": 0.20, "simplicity": 0.15},
        "personality": (
            "Peter Lynch categorizes stocks first (slow grower, stalwart, fast grower, cyclical, "
            "turnaround, asset play) then applies the right lens. PEG ratio is his #1 number. "
            "He loves underfollowed companies institutions ignore. He requires the two-minute drill — "
            "if you can't explain the business simply, pass. He ignores macro entirely."
        ),
    },
}


def _get_key():
    return os.environ.get("GROQ_API_KEY", "").strip()


def _call(system, user, max_tokens=1500):
    key = _get_key()
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    last_err = None
    for model in MODELS:
        body = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},  # ADD THIS
        }
        try:
            resp = requests.post(API_URL, headers=headers, json=body, timeout=60)
            if resp.status_code == 429:
                last_err = f"{model} rate-limited"
                continue
            if resp.status_code == 401:
                raise RuntimeError(f"Invalid GROQ_API_KEY. Status 401.")
            if resp.status_code != 200:
                last_err = f"{model} HTTP {resp.status_code}: {resp.text[:200]}"
                continue
            data = resp.json()
            if not data.get("choices"):
                last_err = f"{model} no choices"
                continue
            content = data["choices"][0]["message"]["content"]
            if content and content.strip():
                return content.strip()
            last_err = f"{model} empty content"
        except requests.exceptions.Timeout:
            last_err = f"{model} timeout"
        except RuntimeError:
            raise
        except Exception as e:
            last_err = f"{model} {e}"
    raise RuntimeError(f"All models failed. Last: {last_err}")


def _parse_json(raw):
    raw = raw.strip()
    raw = re.sub(r"```(?:json)?\s*", "", raw)
    raw = re.sub(r"```", "", raw)
    raw = re.sub(r"\*\*", "", raw)
    s, e = raw.find("{"), raw.rfind("}")
    if s == -1 or e == -1 or e <= s:
        raise ValueError(f"No JSON found: {raw[:300]}")
    raw = raw[s:e+1]
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    return json.loads(raw)


def _clamp(n):
    try:
        return max(0, min(100, int(round(float(n)))))
    except:
        return 50


def get_loading(investor):
    return INVESTOR_PROFILES.get(investor, {}).get("loading", "Analyzing…")


def extract_dna(investor, chunks):
    name = NAME_MAP.get(investor, investor.title())
    profile = INVESTOR_PROFILES[investor]
    corpus = "\n\n---\n\n".join(chunks)

    system = (
        f"You are analyzing {name}'s investment DNA. "
        f"PERSONALITY: {profile['personality']} "
        f"Output strict JSON only."
        f"CRITICAL JSON RULES: No quotes inside string values. Use single quotes or rephrase instead. No markdown bold (**) anywhere. No markdown fences.Start response with {{ and end with }}."
    )
    user = f"""CORPUS:
{corpus}

Extract {name}'s investment DNA. Return ONLY this JSON:
{{
  "principles": [
    {{"name": "2-4 word name specific to HIM", "description": "one sentence, 15-20 words", "weight": 90}},
    {{"name": "...", "description": "...", "weight": 78}},
    {{"name": "...", "description": "...", "weight": 65}},
    {{"name": "...", "description": "...", "weight": 55}},
    {{"name": "...", "description": "...", "weight": 44}}
  ],
  "red_flags": ["specific deal-breaker in HIS voice", "...", "...", "...", "..."],
  "style": "one sentence, 20-25 words capturing his personality and edge"
}}
Weights: top=88-95, bottom=40-50. Principles must be SPECIFIC to {name}, not generic."""

    data = _parse_json(_call(system, user, 1600))
    principles = data.get("principles", [])[:5]
    for p in principles:
        p["weight"] = _clamp(p.get("weight", 50))
        p["name"] = str(p.get("name", "")).strip()
        p["description"] = str(p.get("description", "")).strip()
    while len(principles) < 5:
        principles.append({"name": "—", "description": "—", "weight": 0})
    flags = [str(f).strip() for f in data.get("red_flags", [])[:5]]
    while len(flags) < 5:
        flags.append("—")
    return {"principles": principles, "red_flags": flags, "style": str(data.get("style", "")).strip()}


def stress_test(investor, scenario, chunks, stress_modifier=""):
    name = NAME_MAP.get(investor, investor.title())
    profile = INVESTOR_PROFILES[investor]
    context = "\n\n---\n\n".join(chunks)
    full_scenario = f"{scenario}\n\nADDITIONAL CONDITION: {stress_modifier}" if stress_modifier else scenario

    system = (
        f"You are {name}. PERSONALITY: {profile['personality']} "
        f"Analyze investments exactly as he would. Be decisive. Output strict JSON only."
        f"CRITICAL JSON RULES: No quotes inside string values. Use single quotes or rephrase instead.No markdown bold (**) anywhere.No markdown fences.Start response with {{ and end with }}."
    )
    user = f"""YOUR PRINCIPLES (from your own writing):
{context}

STOCK/SCENARIO TO ANALYZE:
{full_scenario}

Analyze as {name} would. Return ONLY this JSON:
{{
  "verdict": "BUY" | "HOLD" | "SELL",
  "conviction": <0-100 integer>,
  "breakdown": {{
    "valuation": {{"rating": "Cheap" | "Fair" | "Expensive", "score": <0-100>, "note": "one sentence in his voice"}},
    "growth": {{"rating": "Strong" | "Moderate" | "Weak", "score": <0-100>, "note": "one sentence in his voice"}},
    "risk": {{"rating": "Low" | "Medium" | "High", "score": <0-100>, "note": "one sentence in his voice"}},
    "conditions": {{"rating": "Favorable" | "Neutral" | "Unfavorable", "score": <0-100>, "note": "one sentence in his voice"}}
  }},
  "reasoning": "2-3 sentences in {name}'s exact voice and vocabulary referencing his specific principles",
  "key_insight": "one bold insight {name} would uniquely make that others would miss",
  "key_quote": "most relevant principle from the context above"
}}

conviction: 0-100. verdict must follow: BUY>=65, HOLD 35-64, SELL<35."""

    data = _parse_json(_call(system, user, 1400))

    # Validate verdict
    verdict = str(data.get("verdict", "HOLD")).upper().strip()
    if verdict not in ("BUY", "HOLD", "SELL"):
        verdict = "HOLD"

    # Validate breakdown
    bd = data.get("breakdown", {})
    for dim in ["valuation", "growth", "risk", "conditions"]:
        if dim not in bd or not isinstance(bd[dim], dict):
            bd[dim] = {"rating": "—", "score": 50, "note": "—"}
        else:
            bd[dim]["score"] = _clamp(bd[dim].get("score", 50))

    # Compute conviction from breakdown scores (not LLM guess)
    weights = profile["weights"]
    dim_keys = list(weights.keys())
    bd_keys = ["valuation", "growth", "risk", "conditions"]
    scores = [bd[k]["score"] for k in bd_keys]
    w_list = list(weights.values())
    conviction = _clamp(sum(s * w for s, w in zip(scores, w_list)))

    # Enforce verdict-conviction alignment
    if conviction >= 65:
        verdict = "BUY"
    elif conviction >= 35:
        verdict = "HOLD"
    else:
        verdict = "SELL"

    return {
        "verdict": verdict,
        "conviction": conviction,
        "breakdown": bd,
        "reasoning": str(data.get("reasoning", "")).strip(),
        "key_insight": str(data.get("key_insight", "")).strip(),
        "key_quote": str(data.get("key_quote", "")).strip().strip('"').strip("'"),
        "investor": investor,
        "stress_modifier": stress_modifier,
    }


def practice_compare(user_verdict, user_conf, scenario, clone_results):
    summary = "\n\n".join(
        f"{NAME_MAP[k]}: verdict={v['verdict']}, conviction={v['conviction']}/100\nReasoning: {v['reasoning']}"
        for k, v in clone_results.items()
    )
    system = "You are a concise finance tutor. Output strict JSON only."
    user = f"""SCENARIO: {scenario}

LEARNER: {user_verdict} at {user_conf}/100 confidence

INVESTOR CLONES:
{summary}

For each investor compute agreement_pct (0-100) and write a 1-sentence specific feedback.
Return ONLY:
{{
  "matches": [
    {{"investor": "Warren Buffett", "agreement_pct": <0-100>, "feedback": "..."}},
    {{"investor": "Ray Dalio", "agreement_pct": <0-100>, "feedback": "..."}}
  ],
  "summary": "one sentence key lesson",
  "score": <0-100 overall learner score>
}}"""

    data = _parse_json(_call(system, user, 800))
    matches = data.get("matches", [])
    for m in matches:
        m["agreement_pct"] = _clamp(m.get("agreement_pct", 50))
    return {
        "matches": matches,
        "summary": str(data.get("summary", "")).strip(),
        "score": _clamp(data.get("score", 50)),
    }