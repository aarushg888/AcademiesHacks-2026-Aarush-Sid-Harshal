import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()
from rag import retrieve, is_ingested, get_dna_chunks, INVESTORS
from llm import extract_dna, stress_test, practice_compare, get_loading, NAME_MAP, INVESTOR_PROFILES

st.set_page_config(page_title="DecisionDNA", page_icon="◐", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,700;9..144,900&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #F5F1E8 !important;
    color: #1A1A1A;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
}
[data-testid="stAppViewContainer"] > .main { padding: 0 !important; }
[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }


.nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 40px; height: 56px;
    background: #F5F1E8;
    border-bottom: 1px solid rgba(26,26,26,0.1);
    position: sticky; top: 0; z-index: 100;
}
.nav-logo {
    font-family: 'Fraunces', serif;
    font-size: 20px; font-weight: 700; letter-spacing: -0.8px; color: #1A1A1A;
}
.nav-logo span { color: #8B1538; }
.nav-tag {
    font-size: 11px; font-weight: 500; letter-spacing: 0.08em;
    text-transform: uppercase; color: rgba(26,26,26,0.5);
    background: rgba(139,21,56,0.07); border: 1px solid rgba(139,21,56,0.2);
    padding: 4px 12px; border-radius: 20px;
}

.hero-wrap {
    display: grid; grid-template-columns: 1fr 420px; gap: 48px; align-items: center;
    padding: 56px 56px 40px; max-width: 1200px; margin: 0 auto;
}
.hero-left {}
.hero-right { display: flex; justify-content: center; }
.hero-eyebrow {
    font-size: 11px; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase;
    color: #8B1538; margin-bottom: 18px;
}
.hero-wrap h1 {
    font-family: 'Fraunces', serif;
    font-size: clamp(32px, 4vw, 54px); font-weight: 700; line-height: 1.08;
    letter-spacing: -1.5px; color: #1A1A1A; margin-bottom: 20px;
}
.hero-wrap h1 span { color: #8B1538; }
.hero-sub {
    font-family: 'Inter', sans-serif;
    font-size: 14px; line-height: 1.75; color: rgba(26,26,26,0.65); max-width: 520px; margin-bottom: 24px;
}
.hero-features { display: flex; flex-direction: column; gap: 10px; }
.hero-feat { display: flex; align-items: center; gap: 10px; }
.feat-dot { width: 6px; height: 6px; border-radius: 50%; background: #8B1538; flex-shrink: 0; }
.hero-feat span { font-family: 'Inter', sans-serif; font-size: 13px; color: rgba(26,26,26,0.7); }


.feat-tabs-row {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
    max-width: 1200px; margin: 0 auto 0; padding: 0 56px 48px;
}
.feat-tab {
    background: #FFFFFF;
    border: 1px solid rgba(26,26,26,0.06);
    border-radius: 14px;
    padding: 22px 24px;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s;
    box-shadow: 0 1px 3px rgba(26,26,26,0.03), 0 2px 8px rgba(26,26,26,0.02);
    cursor: default;
    position: relative; overflow: hidden;
}
.feat-tab::after {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #8B1538, transparent);
    opacity: 0; transition: opacity 0.3s;
}
.feat-tab:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(26,26,26,0.08), 0 4px 12px rgba(26,26,26,0.04);
}
.feat-tab:hover::after { opacity: 1; }
.feat-tab-num {
    font-family: 'Fraunces', serif; font-size: 32px; font-weight: 300;
    color: rgba(139,21,56,0.35); margin-bottom: 10px; letter-spacing: -1px; line-height: 1;
}
.feat-tab-title {
    font-family: 'Fraunces', serif; font-size: 18px; font-weight: 600;
    color: #1A1A1A; margin-bottom: 8px; letter-spacing: -0.3px;
}
.feat-tab-desc {
    font-family: 'Inter', sans-serif; font-size: 12px; color: rgba(26,26,26,0.55); line-height: 1.6;
}


.input-area {
    padding: 0 40px 40px; display: flex; flex-direction: column; gap: 16px;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] > div { animation: fadeUp 0.4s ease-out; }
.card, .feat-tab, .inv-card, .breakdown-cell, .verdict-wrap, .match-card { animation: fadeUp 0.5s ease-out; }
html { scroll-behavior: smooth; }
.stock-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip {
    font-size: 12px; font-weight: 600; padding: 6px 16px;
    background: transparent; border: 1px solid rgba(26,26,26,0.2);
    border-radius: 20px; color: #1A1A1A; cursor: pointer; transition: all 0.15s;
    font-family: 'Inter', sans-serif; letter-spacing: 0.02em;
}
.chip:hover { background: #8B1538; border-color: #8B1538; color: #F5F1E8; }

.card {
    background: #FFFFFF;
    border: 1px solid rgba(26,26,26,0.06);
    border-radius: 14px;
    padding: 28px;
    box-shadow: 0 1px 3px rgba(26,26,26,0.03), 0 4px 16px rgba(26,26,26,0.04);
    transition: transform 0.3s, box-shadow 0.3s;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(26,26,26,0.04), 0 12px 32px rgba(26,26,26,0.06);
}
.card-sm {
    background: #FFFFFF;
    border: 1px solid rgba(26,26,26,0.06);
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(26,26,26,0.03);
}

.inv-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; padding: 0 40px 32px; max-width: 1200px; margin: 0 auto; }
.inv-card {
    background: #FFFFFF;
    border: 1px solid rgba(26,26,26,0.08);
    border-radius: 14px;
    padding: 22px 20px;
    cursor: pointer;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s, border-color 0.2s;
    box-shadow: 0 1px 3px rgba(26,26,26,0.03);
}
.inv-card.active {
    border-color: #8B1538;
    background: linear-gradient(135deg, #FFFFFF, rgba(139,21,56,0.04));
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(139,21,56,0.15), 0 2px 6px rgba(139,21,56,0.08);
}
.inv-card:hover:not(.active) {
    transform: translateY(-3px);
    border-color: rgba(139,21,56,0.25);
    box-shadow: 0 8px 20px rgba(26,26,26,0.06), 0 2px 4px rgba(26,26,26,0.04);
}
.inv-initial { font-family: 'Fraunces', serif; font-size: 22px; font-weight: 700; color: #8B1538; margin-bottom: 10px; opacity: 0.7; }
.inv-name { font-size: 14px; font-weight: 600; color: #1A1A1A; margin-bottom: 4px; }
.inv-style { font-size: 11px; color: rgba(26,26,26,0.4); line-height: 1.4; }

.verdict-wrap { margin-bottom: 16px; border-radius: 10px; overflow: hidden; }
.verdict-top {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 24px;
}
.verdict-buy { background: linear-gradient(135deg, #064E3B, #065F46); }
.verdict-hold { background: linear-gradient(135deg, #451A03, #78350F); }
.verdict-sell { background: linear-gradient(135deg, #450A0A, #7F1D1D); }
.verdict-label {
    font-family: 'Fraunces', serif;
    font-size: 40px; font-weight: 700; letter-spacing: -1px; color: #1A1A1A;
}
.verdict-buy .verdict-label { color: #6EE7B7; }
.verdict-hold .verdict-label { color: #FCD34D; }
.verdict-sell .verdict-label { color: #FCA5A5; }
.conviction-block { text-align: right; }
.conviction-num {
    font-family: 'Fraunces', serif;
    font-size: 52px; font-weight: 700; letter-spacing: -2px; color: #1A1A1A;
}
.conviction-label { font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(26,26,26,0.5); }

.breakdown-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.breakdown-cell {
    background: #FFFFFF;
    border: 1px solid rgba(26,26,26,0.06);
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 1px 2px rgba(26,26,26,0.03);
    transition: transform 0.2s, box-shadow 0.2s;
}
.breakdown-cell:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(26,26,26,0.06);
}
.breakdown-dim { font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(26,26,26,0.4); margin-bottom: 6px; }
.breakdown-rating {
    font-family: 'Fraunces', serif; font-size: 16px; font-weight: 600; margin-bottom: 8px;
}
.rating-green { color: #34D399; }
.rating-amber { color: #FBBF24; }
.rating-red { color: #F87171; }
.bar-track { height: 4px; background: rgba(26,26,26,0.1); border-radius: 2px; overflow: hidden; margin-bottom: 8px; }
.bar-fill { height: 100%; border-radius: 2px; }
.fill-green { background: #34D399; }
.fill-amber { background: #FBBF24; }
.fill-red { background: #F87171; }
.breakdown-note { font-size: 12px; color: rgba(26,26,26,0.5); line-height: 1.5; }

.reasoning-box { background: #F5F1E8; border-left: 2px solid #8B1538; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-bottom: 12px; }
.reasoning-text { font-size: 13px; line-height: 1.65; color: rgba(26,26,26,0.75); }
.insight-box { background: rgba(139,21,56,0.05); border: 1px solid rgba(139,21,56,0.18); border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; }
.insight-label { font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: #8B1538; margin-bottom: 6px; }
.insight-text { font-size: 13px; line-height: 1.6; color: rgba(26,26,26,0.8); font-style: italic; }
.quote-box { border: 1px solid rgba(26,26,26,0.08); border-radius: 8px; padding: 14px 18px; }
.quote-label { font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(26,26,26,0.4); margin-bottom: 6px; }
.quote-text { font-size: 12px; color: rgba(26,26,26,0.5); line-height: 1.6; font-style: italic; }

.stress-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.stress-chip {
    font-size: 11px; font-weight: 500; padding: 5px 12px;
    background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2);
    border-radius: 6px; color: #FCA5A5; cursor: pointer; transition: all 0.15s;
}
.stress-chip:hover { background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.4); }
.stress-chip.active { background: rgba(239,68,68,0.2); border-color: #EF4444; color: #1A1A1A; }

.principle-row { padding: 14px 0; border-bottom: 1px solid rgba(26,26,26,0.06); }
.principle-row:last-child { border-bottom: none; }
.principle-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.principle-name { font-size: 13px; font-weight: 600; color: #1A1A1A; }
.principle-weight { font-family: 'Fraunces', serif; font-size: 20px; font-weight: 700; color: #8B1538; }
.principle-desc { font-size: 12px; color: rgba(26,26,26,0.5); line-height: 1.55; margin-bottom: 8px; }
.p-bar-track { height: 2px; background: rgba(26,26,26,0.08); border-radius: 1px; }
.p-bar-fill { height: 100%; background: #8B1538; border-radius: 1px; }

.flag-row { display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px solid rgba(26,26,26,0.06); align-items: flex-start; }
.flag-row:last-child { border-bottom: none; }
.flag-dot { width: 6px; height: 6px; background: #EF4444; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
.flag-text { font-size: 12px; color: rgba(26,26,26,0.6); line-height: 1.55; }

.section-label {
    font-size: 10px; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase;
    color: rgba(26,26,26,0.4); margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}
.section-label::before { content: ''; width: 12px; height: 1px; background: rgba(26,26,26,0.25); }

.match-card { background: #FFFFFF; border: 1px solid rgba(26,26,26,0.1); border-radius: 10px; padding: 18px 20px; margin-bottom: 10px; }
.match-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.match-name { font-size: 14px; font-weight: 600; color: #1A1A1A; }
.match-pct { font-family: 'Fraunces', serif; font-size: 28px; font-weight: 700; }
.match-green { color: #34D399; }
.match-amber { color: #FBBF24; }
.match-red { color: #F87171; }
.match-bar { height: 4px; border-radius: 2px; margin-bottom: 10px; }
.match-feedback { font-size: 12px; color: rgba(26,26,26,0.6); line-height: 1.55; }
.score-banner { background: rgba(139,21,56,0.07); border: 1px solid rgba(139,21,56,0.2); border-radius: 10px; padding: 20px 24px; margin-bottom: 20px; display: flex; align-items: center; gap: 20px; }
.score-big { font-family: 'Fraunces', serif; font-size: 52px; font-weight: 700; color: #8B1538; letter-spacing: -2px; }
.score-meta { font-size: 12px; color: rgba(26,26,26,0.5); line-height: 1.6; }
.summary-box { background: #FFFFFF; border-left: 2px solid #8B1538; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-bottom: 20px; font-size: 13px; color: rgba(26,26,26,0.75); line-height: 1.6; font-style: italic; }

textarea, [data-testid="stTextArea"] textarea {
    background: #FFFFFF !important; border: 1px solid rgba(26,26,26,0.15) !important;
    border-radius: 8px !important; color: #1A1A1A !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
    padding: 14px 16px !important; resize: vertical !important;
}
textarea:focus { border-color: #8B1538 !important; outline: none !important; }
[data-testid="stTextInput"] input {
    background: #FFFFFF !important; border: 1px solid rgba(26,26,26,0.15) !important;
    border-radius: 8px !important; color: #1A1A1A !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
    padding: 10px 14px !important;
}
[data-testid="stTextInput"] input:focus { border-color: #8B1538 !important; outline: none !important; }
[data-testid="stSelectbox"] > div > div {
    background: #FFFFFF !important; border: 1px solid rgba(26,26,26,0.15) !important;
    border-radius: 8px !important; color: #1A1A1A !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
}
[data-testid="stSelectbox"] svg { fill: #1A1A1A !important; }

[data-testid="stButton"] button {
    background: #FFFFFF !important;
    color: #1A1A1A !important;
    border: 1px solid rgba(26,26,26,0.12) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 10px 18px !important;
    cursor: pointer !important;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s, border-color 0.2s, background 0.15s !important;
    width: 100% !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 1px 2px rgba(26,26,26,0.04), 0 2px 6px rgba(26,26,26,0.03) !important;
}
[data-testid="stButton"] button:hover {
    transform: translateY(-2px) !important;
    background: #8B1538 !important;
    color: #F5F1E8 !important;
    border-color: #8B1538 !important;
    box-shadow: 0 8px 20px rgba(139,21,56,0.18), 0 4px 8px rgba(139,21,56,0.12) !important;
}
[data-testid="stButton"] button:active {
    transform: translateY(0px) !important;
    box-shadow: 0 1px 2px rgba(139,21,56,0.15) !important;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #FFFFFF !important;
    border: 1px solid rgba(26,26,26,0.08) !important;
    border-radius: 12px !important;
    gap: 4px !important;
    padding: 6px !important;
    margin: 0 56px 32px !important;
    max-width: calc(1200px - 112px) !important;
    width: fit-content !important;
    box-shadow: 0 1px 3px rgba(26,26,26,0.03), 0 2px 8px rgba(26,26,26,0.02) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important; color: rgba(26,26,26,0.55) !important;
    font-family: 'Inter', sans-serif !important; font-size: 13px !important;
    font-weight: 500 !important; padding: 10px 22px !important;
    border: none !important;
    border-radius: 8px !important;
    margin: 0 !important;
    transition: all 0.2s !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover { color: #1A1A1A !important; }
[data-testid="stTabs"] [aria-selected="true"] {
    color: #F5F1E8 !important;
    background: #1A1A1A !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(26,26,26,0.15) !important;
}
[data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTabs"] [data-baseweb="tab-panel"] { padding: 0 !important; background: transparent !important; }

[data-testid="stAlert"] {
    background: rgba(139,21,56,0.06) !important; border: 1px solid rgba(139,21,56,0.2) !important;
    border-radius: 8px !important; color: #1A1A1A !important;
    font-family: 'Inter', sans-serif !important; font-size: 13px !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] > div:nth-child(2) > div { background: #8B1538 !important; }
[data-testid="stSlider"] [role="slider"] { background: #8B1538 !important; border-color: #8B1538 !important; }
[data-testid="stRadio"] label { font-family: 'Inter', sans-serif !important; font-size: 14px !important; color: #1A1A1A !important; }
[data-testid="stSpinner"] p { color: rgba(26,26,26,0.5) !important; font-size: 13px !important; font-style: italic !important; }
label, [data-testid="stWidgetLabel"] label, [data-testid="stWidgetLabel"] p {
    font-family: 'Inter', sans-serif !important; font-size: 11px !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important;
    color: rgba(26,26,26,0.4) !important; font-weight: 600 !important;
}
.stMarkdown p { color: rgba(26,26,26,0.7); font-size: 13px; font-family: 'Inter', sans-serif; }
hr { border-color: rgba(26,26,26,0.08) !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }



.block-container > div, [data-testid="stTabs"] [data-baseweb="tab-panel"] > div { max-width: 1200px !important; margin: 0 auto !important; }

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #FFFFFF !important;
    border: 1px solid rgba(26,26,26,0.08) !important;
    border-radius: 14px !important;
    gap: 4px !important;
    padding: 6px !important;
    margin: 8px auto 32px !important;
    width: fit-content !important;
    box-shadow: 0 2px 8px rgba(26,26,26,0.05), 0 8px 24px rgba(26,26,26,0.04) !important;
    display: inline-flex !important;
}
[data-testid="stTabs"] {
    text-align: center !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important; color: rgba(26,26,26,0.5) !important;
    font-family: 'Inter', sans-serif !important; font-size: 13px !important;
    font-weight: 500 !important; padding: 11px 26px !important;
    border: none !important;
    border-radius: 10px !important;
    margin: 0 !important;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    letter-spacing: 0.01em !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: #1A1A1A !important;
    background: rgba(26,26,26,0.04) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #FFFFFF !important;
    background: #1A1A1A !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(26,26,26,0.2) !important;
    transform: translateY(-1px) !important;
}
[data-baseweb="tab-highlight"] { display: none !important; }


[data-testid="stButton"] button {
    background: #FFFFFF !important;
    color: #1A1A1A !important;
    border: 1px solid rgba(26,26,26,0.1) !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 12px 18px !important;
    cursor: pointer !important;
    transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.25s, background 0.2s, color 0.2s, border-color 0.2s !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 1px 2px rgba(26,26,26,0.04), 0 3px 8px rgba(26,26,26,0.04) !important;
    transform: translateY(0px) !important;
}
[data-testid="stButton"] button:hover {
    transform: translateY(-3px) !important;
    background: #1A1A1A !important;
    color: #FFFFFF !important;
    border-color: #1A1A1A !important;
    box-shadow: 0 12px 28px rgba(26,26,26,0.18), 0 6px 12px rgba(26,26,26,0.1) !important;
}
[data-testid="stButton"] button:active {
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 6px rgba(26,26,26,0.15) !important;
}

.card, .verdict-wrap, .breakdown-cell, .inv-card, .feat-tab, .match-card, .score-banner {
    box-shadow: 0 1px 3px rgba(26,26,26,0.04), 0 4px 16px rgba(26,26,26,0.05) !important;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s !important;
}
.card:hover, .breakdown-cell:hover, .feat-tab:hover, .match-card:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 24px rgba(26,26,26,0.08), 0 16px 40px rgba(26,26,26,0.06) !important;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes slideRight {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] > div { animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) !important; }
.card, .feat-tab, .inv-card, .breakdown-cell, .verdict-wrap, .match-card { animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) !important; }
.hero-left h1, .hero-left .hero-eyebrow, .hero-left .hero-sub { animation: slideRight 0.7s cubic-bezier(0.16, 1, 0.3, 1) !important; }
.hero-right svg { animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) !important; }
html { scroll-behavior: smooth !important; }

[data-testid="stSelectbox"] > div > div {
    background: #FFFFFF !important;
    border: 1px solid rgba(26,26,26,0.1) !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 2px rgba(26,26,26,0.04) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stSelectbox"] > div > div:hover {
    border-color: rgba(26,26,26,0.25) !important;
    box-shadow: 0 2px 8px rgba(26,26,26,0.06) !important;
}

textarea, [data-testid="stTextArea"] textarea {
    background: #FFFFFF !important;
    border: 1px solid rgba(26,26,26,0.1) !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 2px rgba(26,26,26,0.04) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    padding: 16px 18px !important;
}
textarea:focus, [data-testid="stTextArea"] textarea:focus {
    border-color: #1A1A1A !important;
    box-shadow: 0 0 0 3px rgba(26,26,26,0.06), 0 4px 12px rgba(26,26,26,0.04) !important;
    outline: none !important;
}

.section-label { margin-top: 24px !important; }



.picker-card {
    background: #FFFFFF;
    border: 1px solid rgba(26,26,26,0.08);
    border-radius: 16px;
    padding: 28px 32px 36px;
    margin-bottom: 0;
    box-shadow: 0 1px 3px rgba(26,26,26,0.04), 0 8px 24px rgba(26,26,26,0.04);
    max-width: 1080px;
    transition: box-shadow 0.3s;
}
.picker-card:hover {
    box-shadow: 0 4px 8px rgba(26,26,26,0.04), 0 16px 40px rgba(26,26,26,0.06);
}
.picker-head {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 24px; margin-bottom: 20px;
}
.picker-eyebrow {
    font-family: 'Inter', sans-serif;
    font-size: 11px; font-weight: 700; letter-spacing: 0.18em;
    color: #8B1538; text-transform: uppercase; margin-bottom: 8px;
}
.picker-title {
    font-family: 'Fraunces', serif;
    font-size: 24px; font-weight: 600; letter-spacing: -0.6px;
    color: #1A1A1A; margin-bottom: 8px; line-height: 1.2;
}
.picker-sub {
    font-family: 'Inter', sans-serif;
    font-size: 13px; line-height: 1.65; color: rgba(26,26,26,0.6);
    max-width: 540px;
}
.picker-num {
    font-family: 'Fraunces', serif;
    font-size: 56px; font-weight: 300; letter-spacing: -2px;
    color: rgba(139,21,56,0.15); line-height: 1;
}
.picker-divider {
    height: 1px; background: rgba(26,26,26,0.08); margin: 4px 0 18px;
}
.picker-label {
    font-family: 'Inter', sans-serif;
    font-size: 10px; font-weight: 700; letter-spacing: 0.18em;
    color: rgba(26,26,26,0.4); text-transform: uppercase;
    margin-bottom: 14px;
}

</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
INVESTOR_META = {
    "buffett": {"name": "Warren Buffett", "initials": "WB", "style": "Value · Moats · Patience"},
    "munger":  {"name": "Charlie Munger",  "initials": "CM", "style": "Mental Models · Inversion"},
    "dalio":   {"name": "Ray Dalio",       "initials": "RD", "style": "Macro · Cycles · Risk Parity"},
    "lynch":   {"name": "Peter Lynch",     "initials": "PL", "style": "Growth · PEG · Consumer Edge"},
}

PRELOADED_STOCKS = {
    "NVDA": "Nvidia (NVDA) is the dominant AI chip maker. P/E of 60x. Revenue grew 122% YoY driven by data center GPU demand. Gross margins at 75%+. $25B cash. Main risk: customer concentration (Microsoft, Meta, Google) and rising competition from AMD and custom silicon.",
    "AAPL": "Apple (AAPL) trades at 30x earnings. iPhone revenue growing 4% YoY. Services segment growing 15% annually. $180B in cash and buybacks. Strong brand moat. Risk: China exposure (18% of revenue) and slowing upgrade cycles.",
    "TSLA": "Tesla (TSLA) is an EV and energy company trading at 80x earnings. Deliveries grew 6% YoY, margins compressed to 17%. Elon Musk distraction risk. Strong brand but increasing competition from BYD, GM, and others in the EV market.",
    "MSFT": "Microsoft (MSFT) at 35x earnings. Azure cloud growing 29% YoY. Copilot AI integration across Office 365. $80B cash, AAA balance sheet. Near-monopoly in enterprise software. Risk: antitrust scrutiny and OpenAI dependency.",
    "AMZN": "Amazon (AMZN) at 45x earnings. AWS growing 19% YoY and is the #1 cloud provider. Advertising business ($47B) growing 27%. Retail margins thin but improving. Risk: regulatory pressure and slowing AWS growth.",
}

STRESS_OPTIONS = {
    "Rates +2%": "Interest rates rise by 200 basis points due to persistent inflation.",
    "Market -30%": "Broad market crash of 30% due to recession fears.",
    "Earnings Miss": "Company misses earnings by 20% and lowers full-year guidance.",
    "Sector Boom": "The company's sector experiences a major tailwind and sector-wide rally of 40%.",
}

# Session state
for k, v in {
    "dna_cache": {},
    "test_result": None,
    "compare_results": {},
    "selected_dna": "buffett",
    "scenario_text": "",
    "compare_scenario": "",
    "stress_modifier": "",
    "practice_phase": "input",
    "practice_user_verdict": "HOLD",
    "practice_user_conf": 50,
    "practice_clones": {},
    "practice_match": None,
    "practice_scenario": "",
    "practice_score_history": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def api_ok():
    return bool(os.environ.get("GROQ_API_KEY", "").strip())

def rating_color(rating):
    pos = {"Buy", "BUY", "Cheap", "Strong", "Low", "Favorable"}
    neg = {"Sell", "SELL", "Expensive", "Weak", "High", "Unfavorable"}
    if rating in pos: return "rating-green"
    if rating in neg: return "rating-red"
    return "rating-amber"

def bar_color(score):
    if score >= 65: return "fill-green"
    if score >= 35: return "fill-amber"
    return "fill-red"

def render_verdict_card(result):
    verdict = result.get("verdict", "HOLD")
    conviction = result.get("conviction", 50)
    bd = result.get("breakdown", {})
    reasoning = result.get("reasoning", "")
    insight = result.get("key_insight", "")
    quote = result.get("key_quote", "")
    vc = {"BUY": "verdict-buy", "HOLD": "verdict-hold", "SELL": "verdict-sell"}.get(verdict, "verdict-hold")
    vl = {"BUY": "verdict-buy", "HOLD": "verdict-hold", "SELL": "verdict-sell"}.get(verdict, "verdict-hold")

    breakdown_html = '<div class="breakdown-grid">'
    for dim_key, dim_label in [("valuation", "Valuation"), ("growth", "Growth"), ("risk", "Risk"), ("conditions", "Conditions")]:
        cell = bd.get(dim_key, {})
        rating = cell.get("rating", "—")
        score = cell.get("score", 50)
        note = cell.get("note", "")
        rc = rating_color(rating)
        bc = bar_color(score)
        breakdown_html += (
            f'<div class="breakdown-cell">'
            f'<div class="breakdown-dim">{dim_label}</div>'
            f'<div class="breakdown-rating {rc}">{rating}</div>'
            f'<div class="bar-track"><div class="bar-fill {bc}" style="width:{score}%"></div></div>'
            f'<div class="breakdown-note">{note}</div>'
            f'</div>'
        )
    breakdown_html += '</div>'

    html = (
        f'<div class="verdict-wrap">'
        f'<div class="verdict-top {vc}">'
        f'<div><div class="verdict-label">{verdict}</div><div style="font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(26,26,26,0.5);margin-top:4px;">Verdict</div></div>'
        f'<div class="conviction-block"><div class="conviction-num">{conviction}</div><div class="conviction-label">Conviction · /100</div></div>'
        f'</div>'
        f'</div>'
        f'{breakdown_html}'
        f'<div class="reasoning-box"><div class="reasoning-text">{reasoning}</div></div>'
    )
    if insight:
        html += f'<div class="insight-box"><div class="insight-label">Key Insight</div><div class="insight-text">{insight}</div></div>'
    if quote:
        html += f'<div class="quote-box"><div class="quote-label">Driving Principle</div><div class="quote-text">"{quote}"</div></div>'
    st.markdown(html, unsafe_allow_html=True)


# ── NAV ───────────────────────────────────────────────────────────────────────
st.markdown('''<div class="nav">
  <div class="nav-logo">Decision<span>DNA</span></div>
  <div style="display:flex;align-items:center;gap:24px;">
    <span class="nav-tag">AI Investor Intelligence</span>
  </div>
</div>''', unsafe_allow_html=True)

# ── HERO ─────────────────────────────────────────────────────────────────────
st.markdown('''
<div class="hero-wrap">
  <div class="hero-left">
    <div class="hero-eyebrow">AI-Powered Investor Intelligence</div>
    <h1>See any stock through<br>the eyes of the<br><span>greatest investors.</span></h1>
    <div class="hero-sub">
      DecisionDNA clones the decision-making frameworks of legendary investors — Buffett, Munger, Dalio, and Lynch — directly from their own writing and interviews.
      <br><br>
      Pick any stock. Get instant verdicts from each cloned mind: what they would buy, hold, or sell, and exactly why. Then practice your own analysis and see how your thinking stacks up against theirs.
      <br><br>
      Whether you are just starting out or an experienced investor, DecisionDNA gives you a window into how the world's best think about markets.
    </div>
    <div class="hero-features">
      <div class="hero-feat"><div class="feat-dot"></div><span>Stress test any stock in seconds</span></div>
      <div class="hero-feat"><div class="feat-dot"></div><span>Compare two investor frameworks side by side</span></div>
      <div class="hero-feat"><div class="feat-dot"></div><span>Practice mode with scoring and feedback</span></div>
      <div class="hero-feat"><div class="feat-dot"></div><span>See the DNA behind each investor's decisions</span></div>
    </div>
  </div>
  <div class="hero-right">
    <svg viewBox="0 0 420 380" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:420px;">
      <defs>
        <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#FFFFFF;stop-opacity:1"/>
          <stop offset="100%" style="stop-color:#F5F1E8;stop-opacity:1"/>
        </linearGradient>
      </defs>
      <!-- Background circle -->
      <circle cx="210" cy="190" r="170" fill="rgba(139,21,56,0.05)" stroke="rgba(139,21,56,0.1)" stroke-width="1"/>
      <!-- Buffett card -->
      <rect x="20" y="30" width="180" height="110" rx="12" fill="url(#cardGrad)" stroke="rgba(26,26,26,0.12)" stroke-width="1"/>
      <text x="36" y="60" font-family="Georgia,serif" font-size="13" font-weight="700" fill="#1A1A1A">Warren Buffett</text>
      <text x="36" y="78" font-family="Arial,sans-serif" font-size="10" fill="rgba(26,26,26,0.5)">Value · Moats · Patience</text>
      <rect x="36" y="90" width="60" height="22" rx="4" fill="#1F5F3F"/>
      <text x="66" y="105" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" font-weight="700" fill="#6EE7B7">BUY</text>
      <text x="36" y="128" font-family="Arial,sans-serif" font-size="10" fill="rgba(26,26,26,0.5)">Conviction</text>
      <text x="120" y="128" font-family="Georgia,serif" font-size="18" font-weight="700" fill="#8B1538">84</text>
      <!-- Dalio card -->
      <rect x="220" y="60" width="180" height="110" rx="12" fill="url(#cardGrad)" stroke="rgba(26,26,26,0.12)" stroke-width="1"/>
      <text x="236" y="90" font-family="Georgia,serif" font-size="13" font-weight="700" fill="#1A1A1A">Ray Dalio</text>
      <text x="236" y="108" font-family="Arial,sans-serif" font-size="10" fill="rgba(26,26,26,0.5)">Macro · Cycles · Risk</text>
      <rect x="236" y="118" width="60" height="22" rx="4" fill="#78350F"/>
      <text x="266" y="133" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" font-weight="700" fill="#FCD34D">HOLD</text>
      <text x="236" y="158" font-family="Arial,sans-serif" font-size="10" fill="rgba(26,26,26,0.5)">Conviction</text>
      <text x="316" y="158" font-family="Georgia,serif" font-size="18" font-weight="700" fill="#8B1538">51</text>
      <!-- Score bars card -->
      <rect x="60" y="175" width="300" height="130" rx="12" fill="url(#cardGrad)" stroke="rgba(26,26,26,0.12)" stroke-width="1"/>
      <text x="76" y="200" font-family="Arial,sans-serif" font-size="10" font-weight="700" fill="rgba(26,26,26,0.5)" letter-spacing="1">BREAKDOWN</text>
      <text x="76" y="222" font-family="Arial,sans-serif" font-size="11" fill="rgba(26,26,26,0.6)">Valuation</text>
      <rect x="76" y="228" width="264" height="4" rx="2" fill="rgba(26,26,26,0.08)"/>
      <rect x="76" y="228" width="190" height="4" rx="2" fill="#34D399"/>
      <text x="76" y="250" font-family="Arial,sans-serif" font-size="11" fill="rgba(26,26,26,0.6)">Risk</text>
      <rect x="76" y="256" width="264" height="4" rx="2" fill="rgba(26,26,26,0.08)"/>
      <rect x="76" y="256" width="100" height="4" rx="2" fill="#F87171"/>
      <text x="76" y="278" font-family="Arial,sans-serif" font-size="11" fill="rgba(26,26,26,0.6)">Growth</text>
      <rect x="76" y="284" width="264" height="4" rx="2" fill="rgba(26,26,26,0.08)"/>
      <rect x="76" y="284" width="220" height="4" rx="2" fill="#34D399"/>
      <!-- DNA strand dots -->
      <circle cx="210" cy="340" r="4" fill="#8B1538" opacity="0.4"/>
      <circle cx="230" cy="350" r="3" fill="#8B1538" opacity="0.3"/>
      <circle cx="190" cy="355" r="3" fill="#8B1538" opacity="0.25"/>
      <circle cx="248" cy="340" r="2" fill="#8B1538" opacity="0.2"/>
      <circle cx="172" cy="342" r="2" fill="#8B1538" opacity="0.2"/>
    </svg>
  </div>
</div>

<!-- Feature tabs row -->
<div class="feat-tabs-row">
  <div class="feat-tab">
    <div class="feat-tab-num">01</div>
    <div class="feat-tab-title">Stress Test</div>
    <div class="feat-tab-desc">Run any stock through one investor's full framework and get a structured verdict.</div>
  </div>
  <div class="feat-tab">
    <div class="feat-tab-num">02</div>
    <div class="feat-tab-title">Side-by-Side</div>
    <div class="feat-tab-desc">Compare how two different investors would analyze the exact same stock.</div>
  </div>
  <div class="feat-tab">
    <div class="feat-tab-num">03</div>
    <div class="feat-tab-title">Practice Mode</div>
    <div class="feat-tab-desc">Make your own call first — then reveal what the masters decided and see your score.</div>
  </div>
  <div class="feat-tab">
    <div class="feat-tab-num">04</div>
    <div class="feat-tab-title">DNA Lab</div>
    <div class="feat-tab-desc">Explore the core principles and red flags that define each investor's decision style.</div>
  </div>
</div>
''', unsafe_allow_html=True)

if not api_ok():
    st.markdown('<div style="padding: 0 40px 24px;">', unsafe_allow_html=True)
    st.warning('Add `GROQ_API_KEY=gsk_...` to your `.env` file and restart.')
    st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["  Stress Test  ", "  Side-by-Side  ", "  Practice Mode  ", "  DNA Lab  "])

# ═══════════════════════════════════════════════════════
# TAB 1 — STRESS TEST (main feature, shown first)
# ═══════════════════════════════════════════════════════
with tab1:
    st.markdown('<div style="padding: 0 56px 0; max-width:1200px; margin: 0 auto;">', unsafe_allow_html=True)

    # Stock picker card
    st.markdown('''
    <div class="picker-card">
      <div class="picker-head">
        <div>
          <div class="picker-eyebrow">STEP 1</div>
          <div class="picker-title">Pick a stock or describe one</div>
          <div class="picker-sub">Use a preset to load a real scenario, or paste your own analysis below. The clone will run it through the chosen investor's framework.</div>
        </div>
        <div class="picker-num">01</div>
      </div>
      <div class="picker-divider"></div>
      <div class="picker-label">Quick stock select</div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('<div style="max-width:1080px;margin-top:-22px;padding:0 32px 28px;">', unsafe_allow_html=True)
    chip_cols = st.columns(5, gap="small")
    for i, (ticker, desc) in enumerate(PRELOADED_STOCKS.items()):
        with chip_cols[i]:
            if st.button(ticker, key=f"chip_{ticker}"):
                st.session_state.scenario_text = desc
                st.session_state.stress_modifier = ""
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    col_input, col_output = st.columns([1, 1.1], gap="large")

    with col_input:
        st.markdown('<div class="section-label">Investor Clone</div>', unsafe_allow_html=True)
        investor_options = {v["name"]: k for k, v in INVESTOR_META.items()}
        selected_name = st.selectbox("", list(investor_options.keys()), key="test_investor_sel", label_visibility="collapsed")
        selected_key = investor_options[selected_name]

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Stock / Scenario</div>', unsafe_allow_html=True)
        scenario = st.text_area(
            "",
            value=st.session_state.scenario_text,
            placeholder="Describe the stock: ticker, P/E, revenue growth, competitive position, risks, balance sheet…",
            height=160,
            key="scenario_input",
            label_visibility="collapsed",
        )
        st.session_state.scenario_text = scenario

        # Stress test modifiers
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Stress conditions (optional)</div>', unsafe_allow_html=True)
        stress_cols = st.columns(2, gap="small")
        for i, (label, modifier) in enumerate(STRESS_OPTIONS.items()):
            col = stress_cols[i % 2]
            with col:
                if st.button(label, key=f"stress_{i}"):
                    is_active = st.session_state.stress_modifier == modifier
                    st.session_state.stress_modifier = "" if is_active else modifier
                    st.rerun()

        if st.session_state.stress_modifier:
            st.markdown(f'<div style="font-size:11px;color:#FCA5A5;margin-top:8px;padding:8px 12px;background:rgba(239,68,68,0.08);border-radius:6px;border:1px solid rgba(239,68,68,0.2);">⚡ Active condition: {st.session_state.stress_modifier}</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        run = st.button("Analyze →", key="run_stress")

    with col_output:
        if run:
            if not scenario.strip():
                st.error("Enter a stock or scenario first.")
            elif not api_ok():
                st.error("Set GROQ_API_KEY in .env file.")
            else:
                with st.spinner(get_loading(selected_key)):
                    try:
                        chunks = retrieve(selected_key, scenario, n=6)
                        result = stress_test(selected_key, scenario, chunks, st.session_state.stress_modifier)
                        st.session_state.test_result = (selected_key, result)
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

        if st.session_state.test_result:
            inv_key, result = st.session_state.test_result
            st.markdown(f'<div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid rgba(26,26,26,0.1);">{INVESTOR_META[inv_key]["name"]}</div>', unsafe_allow_html=True)
            render_verdict_card(result)

    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 2 — SIDE-BY-SIDE
# ═══════════════════════════════════════════════════════
with tab2:
    st.markdown('<div style="padding: 0 56px 0; max-width:1200px; margin: 0 auto;">', unsafe_allow_html=True)

    # Demo mode
    if st.button("⚡ Demo: Buffett vs Dalio on Nvidia", key="demo_compare"):
        st.session_state.compare_scenario = PRELOADED_STOCKS["NVDA"]
        try:
            st.session_state.compare_results = {}
            for inv_key in ["buffett", "dalio"]:
                with st.spinner(get_loading(inv_key)):
                    chunks = retrieve(inv_key, st.session_state.compare_scenario, n=6)
                    result = stress_test(inv_key, st.session_state.compare_scenario, chunks)
                    st.session_state.compare_results[inv_key] = result
        except Exception as e:
            st.error(f"Demo failed: {e}")
        st.rerun()

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    sel_col1, sel_col2 = st.columns(2, gap="large")
    inv_names = {v["name"]: k for k, v in INVESTOR_META.items()}

    with sel_col1:
        compare_a_name = st.selectbox("First Investor", list(inv_names.keys()), index=0, key="compare_a")
    with sel_col2:
        compare_b_name = st.selectbox("Second Investor", list(inv_names.keys()), index=2, key="compare_b")

    compare_a_key = inv_names[compare_a_name]
    compare_b_key = inv_names[compare_b_name]

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

    # Stock picker card
    st.markdown('''
    <div class="picker-card">
      <div class="picker-head">
        <div>
          <div class="picker-eyebrow">STEP 2</div>
          <div class="picker-title">Pick a stock to compare</div>
          <div class="picker-sub">The same scenario will run through both investor frameworks at once so you can see exactly where their thinking diverges.</div>
        </div>
        <div class="picker-num">02</div>
      </div>
      <div class="picker-divider"></div>
      <div class="picker-label">Quick stock select</div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('<div style="max-width:1080px;margin-top:-22px;padding:0 32px 28px;">', unsafe_allow_html=True)
    chip_cols2 = st.columns(5, gap="small")
    for i, (ticker, desc) in enumerate(PRELOADED_STOCKS.items()):
        with chip_cols2[i]:
            if st.button(ticker, key=f"compare_chip_{ticker}"):
                st.session_state.compare_scenario = desc
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    compare_scenario = st.text_area(
        "",
        value=st.session_state.compare_scenario,
        placeholder="Stock or scenario to compare across both investors…",
        height=140,
        key="compare_input",
        label_visibility="collapsed",
    )
    st.session_state.compare_scenario = compare_scenario

    run_compare = st.button("Compare Both Clones →", key="run_compare")

    if run_compare:
        if not compare_scenario.strip():
            st.error("Enter a scenario first.")
        elif compare_a_key == compare_b_key:
            st.error("Select two different investors.")
        elif not api_ok():
            st.error("Set GROQ_API_KEY.")
        else:
            st.session_state.compare_results = {}
            for inv_key in [compare_a_key, compare_b_key]:
                with st.spinner(get_loading(inv_key)):
                    try:
                        chunks = retrieve(inv_key, compare_scenario, n=6)
                        result = stress_test(inv_key, compare_scenario, chunks)
                        st.session_state.compare_results[inv_key] = result
                    except Exception as e:
                        st.error(f"{INVESTOR_META[inv_key]['name']} failed: {e}")

    if st.session_state.compare_results:
        st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2, gap="large")
        for inv_key, col in [(compare_a_key, col_a), (compare_b_key, col_b)]:
            if inv_key in st.session_state.compare_results:
                with col:
                    st.markdown(f'<div style="font-size:15px;font-weight:700;color:#fff;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid rgba(26,26,26,0.1);">{INVESTOR_META[inv_key]["name"]}</div>', unsafe_allow_html=True)
                    render_verdict_card(st.session_state.compare_results[inv_key])

        # Why did they disagree section
        if len(st.session_state.compare_results) == 2:
            res_a = st.session_state.compare_results.get(compare_a_key, {})
            res_b = st.session_state.compare_results.get(compare_b_key, {})
            if res_a.get("verdict") != res_b.get("verdict"):
                st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="insight-box">'
                    f'<div class="insight-label">Why did they disagree?</div>'
                    f'<div class="insight-text">'
                    f'{INVESTOR_META[compare_a_key]["name"]} said <strong>{res_a.get("verdict")}</strong> ({res_a.get("conviction")}/100 conviction) — '
                    f'{INVESTOR_META[compare_b_key]["name"]} said <strong>{res_b.get("verdict")}</strong> ({res_b.get("conviction")}/100 conviction). '
                    f'This reflects a fundamental difference in their frameworks: '
                    f'{INVESTOR_META[compare_a_key]["name"]}\'s style is {INVESTOR_PROFILES[compare_a_key]["style"]}, while '
                    f'{INVESTOR_META[compare_b_key]["name"]}\'s is {INVESTOR_PROFILES[compare_b_key]["style"]}.'
                    f'</div></div>',
                    unsafe_allow_html=True
                )

    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 3 — PRACTICE MODE
# ═══════════════════════════════════════════════════════
with tab3:
    st.markdown('<div style="padding: 0 56px 0; max-width:1200px; margin: 0 auto;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:14px;color:rgba(26,26,26,0.6);max-width:640px;margin-bottom:28px;line-height:1.65;">Pick a stock. Make your own verdict before the investor clones reveal theirs. See how your thinking aligns with the greatest investors of all time — and learn exactly where you diverged.</div>', unsafe_allow_html=True)

    if st.session_state.practice_phase == "input":
        # Stock picker card with heading + description + chips inside
        st.markdown('''
        <div class="picker-card">
          <div class="picker-head">
            <div>
              <div class="picker-eyebrow">STEP 1</div>
              <div class="picker-title">Pick a stock to analyze</div>
              <div class="picker-sub">Choose any of the stocks below to load a detailed scenario. You will make your own verdict first, then reveal what the investor clones decided.</div>
            </div>
            <div class="picker-num">01</div>
          </div>
          <div class="picker-divider"></div>
          <div class="picker-label">Quick stock select</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('<div style="max-width:1080px;margin-top:-22px;padding:0 32px 28px;">', unsafe_allow_html=True)
        p_cols = st.columns(5, gap="small")
        for i, (ticker, desc) in enumerate(PRELOADED_STOCKS.items()):
            with p_cols[i]:
                if st.button(ticker, key=f"practice_chip_{ticker}"):
                    st.session_state.practice_scenario = desc
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.practice_scenario:
            st.markdown(f'<div class="card" style="margin-bottom:20px;"><div class="section-label">The Scenario</div><div style="font-size:14px;line-height:1.65;color:rgba(26,26,26,0.75);">{st.session_state.practice_scenario}</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-label">Your Verdict</div>', unsafe_allow_html=True)
            v_col, c_col = st.columns([1, 2])
            with v_col:
                user_verdict = st.radio("", ["BUY", "HOLD", "SELL"], horizontal=True, key="user_verdict_r", label_visibility="collapsed")
            with c_col:
                user_conf = st.slider("Confidence", 0, 100, 50, key="user_conf_s")

            if st.button("Reveal the Masters →", key="reveal_btn"):
                if not api_ok():
                    st.error("Set GROQ_API_KEY.")
                else:
                    st.session_state.practice_user_verdict = user_verdict
                    st.session_state.practice_user_conf = user_conf
                    st.session_state.practice_clones = {}
                    try:
                        for inv_key in ["buffett", "dalio"]:
                            with st.spinner(get_loading(inv_key)):
                                chunks = retrieve(inv_key, st.session_state.practice_scenario, n=6)
                                result = stress_test(inv_key, st.session_state.practice_scenario, chunks)
                                st.session_state.practice_clones[inv_key] = result
                        with st.spinner("Scoring your reasoning…"):
                            match = practice_compare(
                                user_verdict, user_conf,
                                st.session_state.practice_scenario,
                                st.session_state.practice_clones,
                            )
                            st.session_state.practice_match = match
                            st.session_state.practice_score_history.append(match.get("score", 50))
                        st.session_state.practice_phase = "reveal"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Reveal failed: {e}")

    else:  # reveal
        match = st.session_state.practice_match or {}
        score = match.get("score", 50)
        summary = match.get("summary", "")
        matches = match.get("matches", [])

        # Score banner
        st.markdown(
            f'<div class="score-banner">'
            f'<div class="score-big">{score}</div>'
            f'<div class="score-meta"><strong style="color:#fff;">Your Investor Score</strong><br>'
            f'Your call: <span style="color:#8B1538;font-weight:600;">{st.session_state.practice_user_verdict}</span> at {st.session_state.practice_user_conf}/100 confidence<br>'
            f'Sessions played: {len(st.session_state.practice_score_history)}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        if summary:
            st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

        # Per-investor match cards
        for m in matches:
            pct = m.get("agreement_pct", 50)
            cls = "match-green" if pct >= 70 else "match-amber" if pct >= 40 else "match-red"
            bc = "fill-green" if pct >= 70 else "fill-amber" if pct < 40 else "fill-amber"
            st.markdown(
                f'<div class="match-card">'
                f'<div class="match-header"><span class="match-name">{m.get("investor", "")}</span>'
                f'<span class="match-pct {cls}">{pct}%</span></div>'
                f'<div class="bar-track match-bar"><div class="bar-fill {bc}" style="width:{pct}%"></div></div>'
                f'<div class="match-feedback">{m.get("feedback", "")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Full Clone Verdicts</div>', unsafe_allow_html=True)
        clone_col_a, clone_col_b = st.columns(2, gap="large")
        clones = list(st.session_state.practice_clones.items())
        if len(clones) >= 1:
            with clone_col_a:
                k, v = clones[0]
                st.markdown(f'<div style="font-size:14px;font-weight:700;color:#fff;margin-bottom:12px;">{INVESTOR_META[k]["name"]}</div>', unsafe_allow_html=True)
                render_verdict_card(v)
        if len(clones) >= 2:
            with clone_col_b:
                k, v = clones[1]
                st.markdown(f'<div style="font-size:14px;font-weight:700;color:#fff;margin-bottom:12px;">{INVESTOR_META[k]["name"]}</div>', unsafe_allow_html=True)
                render_verdict_card(v)

        if st.button("← Try Another Stock", key="practice_reset"):
            st.session_state.practice_phase = "input"
            st.session_state.practice_scenario = ""
            st.session_state.practice_clones = {}
            st.session_state.practice_match = None
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 4 — DNA LAB
# ═══════════════════════════════════════════════════════
with tab4:
    st.markdown('<div style="padding: 0 56px 0; max-width:1200px; margin: 0 auto;">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Select Investor</div>', unsafe_allow_html=True)

    selected_dna = st.session_state.selected_dna
    inv_grid_html = '<div class="inv-grid" style="padding:0;margin-bottom:24px;">'
    for key, meta in INVESTOR_META.items():
        active = "active" if selected_dna == key else ""
        inv_grid_html += (
            f'<div class="inv-card {active}">'
            f'<div class="inv-initial">{meta["initials"]}</div>'
            f'<div class="inv-name">{meta["name"]}</div>'
            f'<div class="inv-style">{meta["style"]}</div>'
            f'</div>'
        )
    inv_grid_html += '</div>'
    st.markdown(inv_grid_html, unsafe_allow_html=True)

    btn_cols = st.columns(4)
    for i, (key, meta) in enumerate(INVESTOR_META.items()):
        with btn_cols[i]:
            if st.button(f"Select {meta['name'].split()[-1]}", key=f"dna_sel_{key}"):
                st.session_state.selected_dna = key
                st.rerun()

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    investor_name = INVESTOR_META[selected_dna]["name"]

    if st.button(f"Extract {investor_name}'s DNA", key="extract_btn"):
        if not is_ingested(selected_dna):
            st.error("Investor data not found.")
        elif not api_ok():
            st.error("Set GROQ_API_KEY.")
        else:
            with st.spinner(get_loading(selected_dna)):
                try:
                    chunks = get_dna_chunks(selected_dna)
                    dna = extract_dna(selected_dna, chunks)
                    st.session_state.dna_cache[selected_dna] = dna
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

    if selected_dna in st.session_state.dna_cache:
        dna = st.session_state.dna_cache[selected_dna]
        principles = dna.get("principles", [])
        red_flags = dna.get("red_flags", [])
        style = dna.get("style", "")

        if style:
            st.markdown(f'<div class="card" style="margin-bottom:20px;border-left:2px solid #8B1538;"><div class="section-label">Investor Profile</div><div style="font-size:14px;line-height:1.65;color:rgba(26,26,26,0.8);font-style:italic;">{style}</div></div>', unsafe_allow_html=True)

        col_l, col_r = st.columns(2, gap="large")
        with col_l:
            st.markdown('<div class="section-label">Core Principles</div>', unsafe_allow_html=True)
            p_html = '<div class="card">'
            for p in principles:
                w = p.get("weight", 50)
                p_html += (
                    f'<div class="principle-row">'
                    f'<div class="principle-header"><span class="principle-name">{p.get("name","")}</span><span class="principle-weight">{w}</span></div>'
                    f'<div class="principle-desc">{p.get("description","")}</div>'
                    f'<div class="p-bar-track"><div class="p-bar-fill" style="width:{w}%"></div></div>'
                    f'</div>'
                )
            p_html += '</div>'
            st.markdown(p_html, unsafe_allow_html=True)

        with col_r:
            st.markdown('<div class="section-label">Red Flags — Deal Breakers</div>', unsafe_allow_html=True)
            f_html = '<div class="card">'
            for flag in red_flags:
                f_html += f'<div class="flag-row"><div class="flag-dot"></div><div class="flag-text">{flag}</div></div>'
            f_html += '</div>'
            st.markdown(f_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
