import requests
import json
import os
import re
import random
from dotenv import load_dotenv
load_dotenv()

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

NAME_MAP = {
    "buffett": "Warren Buffett",
    "munger": "Charlie Munger",
    "dalio": "Ray Dalio",
    "lynch": "Peter Lynch",
}

# Per-investor vocabulary banks — forces distinct voice in every response.
# Each call samples 3-4 terms the LLM MUST weave in naturally.
INVESTOR_VOCAB = {
    "buffett": [
        "wonderful business", "fair price", "moat", "owner earnings", "margin of safety",
        "pricing power", "compounding", "circle of competence", "intrinsic value",
        "Mr. Market", "wide moat", "predictable cash flows", "return on equity",
        "fair company at a wonderful price", "permanent capital", "float"
    ],
    "munger": [
        "lollapalooza", "invert, always invert", "incentive-caused bias", "mental models",
        "too hard pile", "avoid stupidity", "first principles", "checklist",
        "psychological misjudgment", "envy", "skin in the game", "deferred gratification",
        "compound interest", "fishing where the fish are", "filter aggressively"
    ],
    "dalio": [
        "debt cycle", "regime", "macro environment", "risk parity", "uncorrelated returns",
        "deleveraging", "reflation", "inflation hedge", "duration risk", "balanced portfolio",
        "short-term debt cycle", "long-term debt cycle", "diversification",
        "principles", "radical transparency", "stress test"
    ],
    "lynch": [
        "PEG ratio", "two-minute drill", "stalwart", "fast grower", "tenbagger",
        "story stock", "consumer edge", "boring company", "underfollowed",
        "earnings growth", "diworsification", "buy what you know", "category killer",
        "turnaround", "asset play", "slow grower"
    ],
}

INVESTOR_PROFILES = {
    "buffett": {
        "loading": "Checking for durable moats…",
        "style": "fundamentals-first, long-term, moat-obsessed",
        "weights": {"valuation": 0.30, "growth": 0.20, "risk": 0.25, "moat": 0.25},
        "personality": (
            "Warren Buffett. Folksy, plainspoken Nebraska businessman. Uses analogies from "
            "baseball, farming, and small-town life. Obsessed with 'wonderful businesses at "
            "fair prices.' Demands durable moats, predictable owner earnings, ROE>15% without "
            "leverage. Ignores macro noise entirely. Holds forever. Hates complexity, hype, "
            "and businesses he can't explain in two sentences. Will say 'I don't get it, pass.'"
        ),
    },
    "munger": {
        "loading": "Inverting the problem…",
        "style": "mental-models, inversion, incentive-first",
        "weights": {"valuation": 0.20, "growth": 0.15, "risk": 0.35, "moat": 0.30},
        "personality": (
            "Charlie Munger. Acerbic, blunt, intellectually merciless. Inverts every problem — "
            "asks 'how could this fail?' before 'is this a buy?' Obsessed with incentive "
            "structures, accounting tricks, and lollapalooza effects (multiple advantages "
            "compounding). Frequently consigns ideas to the 'too hard pile.' Quotes Ben Franklin, "
            "Cicero, Darwin. Never softens a verdict. Hates EBITDA, financial engineering, "
            "and short-term thinking."
        ),
    },
    "dalio": {
        "loading": "Locating the debt cycle…",
        "style": "macro-regime, debt-cycle, risk-parity",
        "weights": {"valuation": 0.15, "growth": 0.20, "risk": 0.40, "macro": 0.25},
        "personality": (
            "Ray Dalio. Systematic, principle-driven hedge fund manager. Thinks in macro regimes "
            "(rising/falling growth × rising/falling inflation). Obsessed with debt cycles, "
            "central bank reactions, currency debasement. Stress-tests everything against "
            "deflation AND 15% inflation. Cares about portfolio correlation, not individual "
            "stock quality. Speaks in frameworks: 'archetype,' 'machine,' 'principles.'"
        ),
    },
    "lynch": {
        "loading": "Running the two-minute drill…",
        "style": "growth-focused, consumer-edge, PEG-driven",
        "weights": {"valuation": 0.30, "growth": 0.35, "risk": 0.20, "simplicity": 0.15},
        "personality": (
            "Peter Lynch. Energetic, optimistic Magellan Fund manager. Categorizes every stock "
            "first (slow grower, stalwart, fast grower, cyclical, turnaround, asset play). "
            "PEG ratio is his #1 number — buys below 1.0. Loves underfollowed companies "
            "Wall Street ignores. Demands the 'two-minute drill' — if you can't pitch the "
            "business in 2 minutes, pass. Ignores macro completely. Looks for tenbaggers."
        ),
    },
}

INVESTOR_SCORING = {
    "buffett": """
SCORING (use FULL 0-100 range, never cluster around 50):
- valuation: 85-95 = below intrinsic value with margin of safety; 60-75 = fair; 15-35 = expensive (P/E>30 no safety)
- growth: 70-90 = predictable 10-15% earnings growth for decades; 40-60 = moderate; 15-35 = unpredictable
- risk: 75-90 = debt-free, durable moat, ROE>15%; 40-60 = medium; 10-30 = high debt or no moat
- conditions: 80-95 = wide durable moat with pricing power; 50-70 = narrow moat; 10-35 = commodity
""",
    "munger": """
SCORING (use FULL 0-100 range, never cluster around 50):
- valuation: 80-95 = wonderful at fair; 50-70 = fair at fair; 10-30 = mediocre at any price
- growth: 60-85 = quality compounder; 40-60 = steady; 10-35 = declining (Munger weights quality over growth)
- risk: 80-95 = aligned incentives, honest accounting, skin in game; 40-60 = mixed; 10-25 = opacity, complex accounting
- conditions: 80-95 = lollapalooza of compounding advantages; 50-70 = single advantage; 10-35 = commoditized
""",
    "dalio": """
SCORING (use FULL 0-100 range, never cluster around 50):
- valuation: 75-90 = aligned with current economic season (rising growth=equities); 40-60 = neutral; 10-30 = wrong regime
- growth: 70-90 = expansion phase, credit growing; 40-65 = mid-cycle; 10-30 = late cycle, tightening
- risk: 75-90 = hedged across inflation/deflation; 40-60 = partial; 10-25 = fully exposed to current regime
- conditions: 75-90 = low correlation, good diversification; 40-60 = moderate; 10-30 = concentrated risk
""",
    "lynch": """
SCORING (use FULL 0-100 range, never cluster around 50):
- valuation: 88-95 = PEG<0.5; 70-85 = PEG 0.5-1.0; 45-65 = PEG 1.0-1.5; 10-30 = PEG>2.0
- growth: 85-95 = 20-30% sustainable earnings growth; 65-80 = 15-20%; 40-60 = 10-15%; 10-30 = <10%
- risk: 75-90 = simple, low debt, 2-min explainable; 45-65 = moderate; 10-30 = complex, heavy debt
- conditions: 78-92 = under-followed, consumer-visible, early expansion; 45-65 = mixed; 10-30 = over-followed, saturated
""",
}


def _get_key():
    return os.environ.get("GROQ_API_KEY", "").strip()


def _call(system, user, max_tokens=1500, temperature=0.55):
    """Higher default temp than before (0.55 vs 0.1) for varied, less repetitive output."""
    key = _get_key()
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set.")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    last_err = None
    for model in MODELS:
        body = {
            "model": model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        try:
            resp = requests.post(API_URL, headers=headers, json=body, timeout=60)
            if resp.status_code == 429:
                last_err = f"{model} rate-limited"; continue
            if resp.status_code == 401:
                raise RuntimeError("Invalid GROQ_API_KEY.")
            if resp.status_code != 200:
                last_err = f"{model} HTTP {resp.status_code}: {resp.text[:200]}"; continue
            data = resp.json()
            if not data.get("choices"):
                last_err = f"{model} no choices"; continue
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
    except Exception:
        return 50


def get_loading(investor):
    return INVESTOR_PROFILES.get(investor, {}).get("loading", "Analyzing…")


def _vocab_sample(investor: str, n: int = 4) -> list[str]:
    pool = INVESTOR_VOCAB.get(investor, [])
    if not pool:
        return []
    return random.sample(pool, min(n, len(pool)))


def extract_dna(investor, chunks):
    name = NAME_MAP.get(investor, investor.title())
    profile = INVESTOR_PROFILES[investor]
    corpus = "\n\n---\n\n".join(chunks)
    vocab = _vocab_sample(investor, 5)

    system = (
        f"You are analyzing {name}'s investment DNA. PERSONALITY: {profile['personality']} "
        f"Output strict JSON only. No markdown bold (**), no fences. "
        f"You MUST use these specific phrases naturally: {', '.join(vocab)}."
    )
    user = f"""CORPUS:
{corpus}

Extract {name}'s investment DNA. Return ONLY this JSON:
{{
  "principles": [
    {{"name": "2-4 word name SPECIFIC to him (not generic)", "description": "one vivid sentence, 15-22 words", "weight": 92}},
    {{"name": "...", "description": "...", "weight": 81}},
    {{"name": "...", "description": "...", "weight": 70}},
    {{"name": "...", "description": "...", "weight": 58}},
    {{"name": "...", "description": "...", "weight": 46}}
  ],
  "red_flags": ["specific deal-breaker in HIS voice and vocabulary", "...", "...", "...", "..."],
  "style": "one sentence, 22-28 words, capturing his exact personality and investing edge"
}}

Weights: top=88-95, bottom=42-50. Names and red flags must be unmistakably {name} — never generic."""

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


def stress_test(investor, scenario, chunks, stress_modifier="", live_data: dict = None):
    """
    Run a stock through one investor's framework.
    live_data: optional dict from market_data.get_fundamentals() — injected as authoritative numbers.
    """
    name = NAME_MAP.get(investor, investor.title())
    profile = INVESTOR_PROFILES[investor]
    scoring = INVESTOR_SCORING[investor]
    context = "\n\n---\n\n".join(chunks)
    vocab = _vocab_sample(investor, 4)

    # Build scenario block — live data takes priority over user description
    parts = []
    if live_data:
        from market_data import fundamentals_to_prompt
        parts.append(fundamentals_to_prompt(live_data))
        parts.append("USER CONTEXT: " + scenario)
    else:
        parts.append("SCENARIO: " + scenario)
    if stress_modifier:
        parts.append("STRESS CONDITION: " + stress_modifier)
    full_scenario = "\n\n".join(parts)

    # Anti-repetition: forbid generic phrases
    forbidden = (
        "Avoid these GENERIC phrases (do not use): 'solid company', 'good investment', "
        "'mixed signals', 'wait and see', 'further analysis needed', 'time will tell', "
        "'depends on', 'overall', 'in conclusion'."
    )

    system = (
        f"You are {name}. {profile['personality']} "
        f"Be DECISIVE — never cluster scores around 50. Use the FULL 0-100 range. "
        f"You MUST naturally use these phrases from your own vocabulary: {', '.join(vocab)}. "
        f"{forbidden} Output strict JSON only."
    )
    user = f"""YOUR PRINCIPLES (from your own writing):
{context}

INVESTMENT TARGET:
{full_scenario}

{scoring}

Analyze as {name}. Be bold and opinionated — great stocks earn 75-95, bad ones earn 10-30.
Reference SPECIFIC numbers from the live data when available. Use your vocabulary naturally.

Return ONLY this JSON:
{{
  "verdict": "BUY" | "HOLD" | "SELL",
  "conviction": <0-100 integer — bold: great=75-95, weak=10-30>,
  "breakdown": {{
    "valuation": {{"rating": "Cheap" | "Fair" | "Expensive", "score": <0-100>, "note": "one sentence in {name}'s voice citing a specific number"}},
    "growth": {{"rating": "Strong" | "Moderate" | "Weak", "score": <0-100>, "note": "one sentence in {name}'s voice citing a specific number"}},
    "risk": {{"rating": "Low" | "Medium" | "High", "score": <0-100>, "note": "one sentence in {name}'s voice citing a specific number"}},
    "conditions": {{"rating": "Favorable" | "Neutral" | "Unfavorable", "score": <0-100>, "note": "one sentence in {name}'s voice"}}
  }},
  "reasoning": "3 sentences in {name}'s exact voice, referencing his specific principles AND specific numbers from the data. Be opinionated and quotable.",
  "key_insight": "one bold insight only {name} would make that generic analysts miss — must be non-obvious",
  "key_quote": "one principle from his writings that drives this verdict (different from key_insight)"
}}"""

    data = _parse_json(_call(system, user, 1500, temperature=0.6))

    verdict = str(data.get("verdict", "HOLD")).upper().strip()
    if verdict not in ("BUY", "HOLD", "SELL"):
        verdict = "HOLD"

    bd = data.get("breakdown", {})
    for dim in ["valuation", "growth", "risk", "conditions"]:
        if dim not in bd or not isinstance(bd[dim], dict):
            bd[dim] = {"rating": "—", "score": 50, "note": "—"}
        else:
            bd[dim]["score"] = _clamp(bd[dim].get("score", 50))

    # Blend LLM conviction with weighted breakdown (40/60 split)
    weights = list(profile["weights"].values())
    scores = [bd[k]["score"] for k in ["valuation", "growth", "risk", "conditions"]]
    calc_conviction = _clamp(int(sum(s * w for s, w in zip(scores, weights))))
    llm_conviction = _clamp(data.get("conviction", 50))
    conviction = _clamp(int(0.4 * llm_conviction + 0.6 * calc_conviction))

    if conviction >= 62:
        verdict = "BUY"
    elif conviction >= 38:
        verdict = "HOLD"
    else:
        verdict = "SELL"

    result = {
        "verdict": verdict,
        "conviction": conviction,
        "breakdown": bd,
        "reasoning": str(data.get("reasoning", "")).strip(),
        "key_insight": str(data.get("key_insight", "")).strip(),
        "key_quote": str(data.get("key_quote", "")).strip().strip('"').strip("'"),
        "investor": investor,
        "stress_modifier": stress_modifier,
    }
    if live_data:
        result["live_data"] = {
            "ticker": live_data.get("ticker"),
            "price": live_data.get("price"),
            "change_pct": live_data.get("change_pct"),
            "sparkline": live_data.get("sparkline", []),
            "market_cap_fmt": live_data.get("market_cap_fmt"),
            "pe_ratio": live_data.get("pe_ratio"),
            "sector": live_data.get("sector"),
        }
    return result


def practice_compare(user_verdict, user_conf, scenario, clone_results):
    lines = []
    for k, v in clone_results.items():
        lines.append(
            f"{NAME_MAP[k]}: verdict={v['verdict']}, conviction={v['conviction']}/100. "
            f"Reasoning: {v['reasoning']}"
        )
    summary = "\n".join(lines)

    system = (
        "You are a finance tutor scoring an investing student. "
        "Be honest, specific, and concrete — never generic. Output strict JSON only."
    )
    user = f"""SCENARIO: {scenario}

STUDENT DECISION: {user_verdict} at {user_conf}/100 confidence

INVESTOR CLONE RESULTS:
{summary}

For each investor:
- agreement_pct: 100 if same verdict AND conviction within 15. 70-85 if same verdict different conviction. 30-50 if different verdict but reasonable. 0-25 if opposite verdict with very different conviction.
- feedback: ONE specific concrete sentence — name the exact factor where they agree or disagree (valuation? risk? growth?).

overall score: weighted average of agreement_pcts, adjusted for conviction calibration.
summary: ONE specific lesson — name the single factor the student weighted differently from the masters.

Return ONLY:
{{
  "matches": [
    {{"investor": "{NAME_MAP['buffett']}", "agreement_pct": <0-100>, "feedback": "..."}},
    {{"investor": "{NAME_MAP['dalio']}", "agreement_pct": <0-100>, "feedback": "..."}}
  ],
  "summary": "one sentence specific lesson",
  "score": <0-100>
}}"""
    data = _parse_json(_call(system, user, 700, temperature=0.4))
    matches = data.get("matches", [])
    for m in matches:
        m["agreement_pct"] = _clamp(m.get("agreement_pct", 50))
    return {
        "matches": matches,
        "summary": str(data.get("summary", "")).strip(),
        "score": _clamp(data.get("score", 50)),
    }


def analyze_portfolio(holdings, focus_investor="buffett", live_data_map: dict = None):
    """
    holdings: list of dicts {ticker, description, weight_pct}
    live_data_map: {ticker: fundamentals_dict} — optional live data per holding
    """
    name = NAME_MAP.get(focus_investor, "Warren Buffett")
    profile = INVESTOR_PROFILES[focus_investor]
    scoring = INVESTOR_SCORING[focus_investor]
    vocab = _vocab_sample(focus_investor, 4)

    # Build holdings text with live data when available
    lines = []
    for h in holdings:
        tick = h["ticker"]
        line = f"- {tick} ({h['weight_pct']}% weight): {h['description']}"
        if live_data_map and tick in live_data_map and live_data_map[tick]:
            ld = live_data_map[tick]
            extras = []
            if ld.get("price"):     extras.append(f"price ${ld['price']}")
            if ld.get("pe_ratio"):  extras.append(f"P/E {ld['pe_ratio']:.1f}")
            if ld.get("revenue_growth") is not None: extras.append(f"rev growth {ld['revenue_growth']*100:.1f}%")
            if ld.get("roe") is not None:            extras.append(f"ROE {ld['roe']*100:.1f}%")
            if extras:
                line += f"  [LIVE: {', '.join(extras)}]"
        lines.append(line)
    holdings_text = "\n".join(lines)

    system = (
        f"You are {name}. {profile['personality']} "
        f"Analyze entire portfolios with the same rigor as individual stocks. "
        f"Use these phrases naturally: {', '.join(vocab)}. "
        f"You MUST evaluate EVERY ticker listed — never skip a ticker. "
        f"Output strict JSON only."
    )
    tickers_csv = ", ".join(h["ticker"] for h in holdings)
    user = f"""PORTFOLIO HOLDINGS:
{holdings_text}

REQUIRED: Your "positions" array MUST contain exactly these tickers, in this order: {tickers_csv}

{scoring}

Analyze this portfolio as {name}. Consider:
1. Quality of each position through your specific lens
2. Diversification (correlation between positions)
3. What you would trim, exit, or add
4. One specific stock you would add (real ticker, real reason)

Return ONLY this JSON:
{{
  "overall_score": <0-100, full range, decisive>,
  "overall_verdict": "Strong" | "Balanced" | "Weak",
  "portfolio_summary": "2-3 sentences in {name}'s voice assessing the whole portfolio, citing specific tickers",
  "positions": [
    {{"ticker": "EXACT_TICKER_FROM_LIST", "verdict": "BUY" | "HOLD" | "SELL", "conviction": <0-100>, "note": "one sentence in {name}'s voice about THIS specific holding, citing a number"}}
  ],
  "strengths": ["one specific strength naming a ticker", "another specific strength naming a ticker"],
  "weaknesses": ["one specific weakness naming a ticker", "another"],
  "suggested_trim": "exact ticker from portfolio + reason in his voice",
  "suggested_add": "real ticker NOT in portfolio + specific reason in his voice",
  "key_risk": "the single biggest portfolio-level risk {name} sees"
}}"""

    data = _parse_json(_call(system, user, 2000, temperature=0.55))

    positions = data.get("positions", [])
    # Validate: every input ticker must appear in positions
    pos_tickers = {p.get("ticker", "").upper() for p in positions}
    input_tickers = {h["ticker"].upper() for h in holdings}
    missing = input_tickers - pos_tickers

    # If LLM dropped tickers, add neutral entries so frontend stays consistent
    for h in holdings:
        if h["ticker"].upper() not in pos_tickers:
            positions.append({
                "ticker": h["ticker"].upper(),
                "verdict": "HOLD",
                "conviction": 50,
                "note": f"Position not specifically rated — review separately."
            })

    # Filter out any tickers NOT in the input (LLM hallucination)
    positions = [p for p in positions if p.get("ticker", "").upper() in input_tickers]

    # Order positions to match input order
    order = {h["ticker"].upper(): i for i, h in enumerate(holdings)}
    positions.sort(key=lambda p: order.get(p.get("ticker", "").upper(), 999))

    for p in positions:
        p["conviction"] = _clamp(p.get("conviction", 50))
        v = str(p.get("verdict", "HOLD")).upper()
        p["verdict"] = v if v in ("BUY", "HOLD", "SELL") else "HOLD"
        p["ticker"] = p.get("ticker", "").upper()

    return {
        "overall_score": _clamp(data.get("overall_score", 50)),
        "overall_verdict": str(data.get("overall_verdict", "Balanced")).strip(),
        "portfolio_summary": str(data.get("portfolio_summary", "")).strip(),
        "positions": positions,
        "strengths": data.get("strengths", []),
        "weaknesses": data.get("weaknesses", []),
        "suggested_trim": str(data.get("suggested_trim", "")).strip(),
        "suggested_add": str(data.get("suggested_add", "")).strip(),
        "key_risk": str(data.get("key_risk", "")).strip(),
    }
