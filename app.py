"""CryptoComply — Multi-Agent Crypto Compliance Intelligence Platform.

Gradio application entry point for HuggingFace Spaces.
Single-page vertical flow. Design: deep forest glassmorphism with sage-teal accents.
"""

import os
import re
import traceback

import gradio as gr

# ═══════════════════════════════════════════════════════════════════════════
# COMPLIANCE GLOSSARY  (30 plain-language definitions)
# ═══════════════════════════════════════════════════════════════════════════
COMPLIANCE_GLOSSARY: dict[str, str] = {
    "Howey Test": "A 4-question legal test from a 1946 US court case. If all 4 are YES for your token, the SEC may treat it as a security.",
    "VASP": "Virtual Asset Service Provider \u2014 the legal term for crypto businesses. If you run one, you must follow AML rules.",
    "CASP": "Crypto-Asset Service Provider \u2014 the EU\u2019s term for crypto businesses under MiCA.",
    "Travel Rule": "Requires crypto businesses to share sender and receiver details for transfers above a certain amount.",
    "AML": "Anti-Money Laundering \u2014 laws requiring businesses to check users aren\u2019t hiding criminal money.",
    "KYC": "Know Your Customer \u2014 verifying who your users are by checking ID and address.",
    "EMT": "E-Money Token \u2014 under MiCA, a stablecoin pegged to one currency like EUR. Strict rules apply.",
    "ART": "Asset-Referenced Token \u2014 under MiCA, a stablecoin backed by multiple assets. Most regulated crypto in the EU.",
    "MiCA": "Markets in Crypto-Assets Regulation \u2014 the EU\u2019s main crypto law, fully in force from December 2024.",
    "FinCEN": "Financial Crimes Enforcement Network \u2014 US Treasury agency regulating crypto money service businesses.",
    "MSB": "Money Services Business \u2014 the US category for crypto exchanges. Must register with FinCEN.",
    "MPI Licence": "Major Payment Institution Licence \u2014 Singapore\u2019s main licence for larger crypto businesses.",
    "DTSP": "Digital Token Service Provider \u2014 new Singapore category (June 2025) for crypto firms serving international clients.",
    "VARA": "Virtual Assets Regulatory Authority \u2014 Dubai\u2019s dedicated crypto regulator.",
    "FCA": "Financial Conduct Authority \u2014 the UK\u2019s financial regulator. Crypto firms must register for AML.",
    "EDD": "Enhanced Due Diligence \u2014 extra identity checks for high-risk customers like politicians.",
    "PEP": "Politically Exposed Person \u2014 senior politicians, judges, military officers, or their close associates.",
    "Unhosted Wallet": "A self-controlled crypto wallet (like MetaMask) not held by an exchange.",
    "Whitepaper": "Under MiCA, a legal disclosure document token issuers must publish before launch.",
    "OFAC": "US Treasury\u2019s sanctions list. Crypto businesses must screen users against it.",
    "CDD": "Customer Due Diligence \u2014 basic identity checks before opening an account.",
    "SAR": "Suspicious Activity Report \u2014 filed with the government when a transaction looks criminal.",
    "STR": "Suspicious Transaction Report \u2014 same as SAR, used in Singapore and UAE.",
    "BSA": "Bank Secrecy Act \u2014 the main US anti-money laundering law applying to crypto exchanges.",
    "ESMA": "European Securities and Markets Authority \u2014 maintains the EU CASP register.",
    "Reg D": "Regulation D \u2014 US exemption to sell security tokens to accredited investors without full SEC registration.",
    "Reg S": "Regulation S \u2014 US exemption for selling tokens to people outside the United States only.",
    "FATF": "Financial Action Task Force \u2014 global body setting anti-money laundering standards. 99 countries follow its rules.",
    "Passporting": "Under MiCA, one EU licence lets you operate across all 27 member states.",
    "Cold Storage": "Keeping crypto keys offline. Most regulators require 80%+ of customer crypto in cold storage.",
}

_sorted_terms = sorted(COMPLIANCE_GLOSSARY.keys(), key=len, reverse=True)
_glossary_re = re.compile(
    r"(?<!\w)(" + "|".join(re.escape(t) for t in _sorted_terms) + r")(?!\w)",
    re.IGNORECASE,
)


def glossarise(text: str) -> str:
    """Wrap first occurrence of each compliance term in a tooltip span."""
    seen: set[str] = set()

    def _repl(m: re.Match) -> str:
        raw = m.group(0)
        key = next((k for k in COMPLIANCE_GLOSSARY if k.lower() == raw.lower()), None)
        if key is None or key in seen:
            return raw
        seen.add(key)
        tip = COMPLIANCE_GLOSSARY[key].replace('"', "&quot;")
        return f'<span class="tt" data-tip="{tip}">{raw}</span>'

    return _glossary_re.sub(_repl, text)


# ═══════════════════════════════════════════════════════════════════════════
# FONTS  — loaded via @import inside CSS, no separate HTML tag needed
# ═══════════════════════════════════════════════════════════════════════════
FONT_LINK = ""  # empty — fonts loaded via @import in CUSTOM_CSS

# ═══════════════════════════════════════════════════════════════════════════
# CSS — Deep forest glassmorphism with sage-teal accents
# ═══════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500&family=JetBrains+Mono:wght@400;500&display=swap');

/* ══ BASE ══════════════════════════════════════════════════════════════ */
body, .gradio-container, .main, .wrap, .contain {
  background: #040d12 !important;
  color: #e8f4f1 !important;
  font-family: 'DM Sans', sans-serif !important;
  min-height: 100vh;
}
.gradio-container { max-width: 880px !important; margin: 0 auto !important; }

h1, h2, h3, .prose h1, .prose h2, .prose h3 {
  font-family: 'Sora', sans-serif !important;
  color: #e8f4f1 !important;
  font-weight: 600 !important;
}

/* ══ SCROLLBAR ═════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,201,167,0.2); border-radius: 2px; }

/* ══ AURORA (injected via #aurora div) ═════════════════════════════════ */
#aurora { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; overflow: hidden; }
#aurora .blob1 {
  position: absolute; top: -120px; right: -100px;
  width: 600px; height: 600px; border-radius: 50%;
  background: radial-gradient(circle, rgba(0,201,167,0.06), transparent 70%);
  animation: drift1 25s ease-in-out infinite;
}
#aurora .blob2 {
  position: absolute; bottom: -100px; left: -80px;
  width: 500px; height: 500px; border-radius: 50%;
  background: radial-gradient(circle, rgba(0,201,167,0.04), transparent 70%);
  animation: drift2 30s ease-in-out infinite;
}
@keyframes drift1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-60px,40px)} }
@keyframes drift2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(40px,-50px)} }

/* ══ GLASS CARDS ═══════════════════════════════════════════════════════ */
.glass, .gr-group, .gradio-group {
  background: rgba(0,201,167,0.04) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
  border: 1px solid rgba(0,201,167,0.12) !important;
  border-radius: 16px !important;
  transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}
.glass:hover, .gr-group:hover {
  border-color: rgba(0,201,167,0.22) !important;
  box-shadow: 0 8px 32px rgba(0,201,167,0.08) !important;
}

/* ══ TEXT INPUTS ════════════════════════════════════════════════════════ */
.gr-panel, .gr-box, .gr-form { background: transparent !important; border: none !important; }

textarea, input[type="text"], .gr-textbox textarea {
  background: rgba(0,0,0,0.3) !important;
  border: 1px solid rgba(0,201,167,0.15) !important;
  border-radius: 10px !important;
  color: #e8f4f1 !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  padding: 14px 16px !important;
  line-height: 1.6 !important;
  transition: border-color 0.2s ease !important;
}
textarea:focus, input[type="text"]:focus {
  border-color: rgba(0,201,167,0.4) !important;
  box-shadow: 0 0 0 3px rgba(0,201,167,0.08) !important;
  outline: none !important;
}
textarea::placeholder { color: rgba(232,244,241,0.25) !important; }

/* ══ LABELS ════════════════════════════════════════════════════════════ */
label, .gr-label, span.svelte-1gfkn6j {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
  color: rgba(232,244,241,0.6) !important;
  letter-spacing: 0.2px !important;
}

/* ══ CHECKBOXES — glass pills ══════════════════════════════════════════ */
.gr-check-radio, .gr-checkbox-group { display: flex !important; flex-wrap: wrap !important; gap: 8px !important; }

.gr-check-radio label, .gr-checkbox-group label {
  background: rgba(0,201,167,0.05) !important;
  border: 1px solid rgba(0,201,167,0.15) !important;
  border-radius: 20px !important;
  padding: 6px 14px !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
  color: rgba(232,244,241,0.7) !important;
}
.gr-check-radio label:hover, .gr-checkbox-group label:hover {
  border-color: rgba(0,201,167,0.3) !important;
  background: rgba(0,201,167,0.08) !important;
}
.gr-check-radio label:has(input:checked), .gr-checkbox-group label:has(input:checked) {
  background: rgba(0,201,167,0.15) !important;
  border-color: #00C9A7 !important;
  color: #00C9A7 !important;
  box-shadow: 0 0 14px rgba(0,201,167,0.10);
}
.gr-check-radio input[type="checkbox"], .gr-checkbox-group input[type="checkbox"] {
  display: none !important;
}

/* ══ PRIMARY BUTTON ════════════════════════════════════════════════════ */
.gr-button-primary {
  background: transparent !important;
  border: 1px solid #00C9A7 !important;
  color: #00C9A7 !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 500 !important;
  font-size: 15px !important;
  border-radius: 12px !important;
  padding: 14px 28px !important;
  letter-spacing: 0.3px !important;
  transition: all 0.2s ease !important;
  position: relative !important;
  overflow: hidden !important;
}
.gr-button-primary:hover {
  background: rgba(0,201,167,0.1) !important;
  box-shadow: 0 0 24px rgba(0,201,167,0.2) !important;
  transform: translateY(-1px) !important;
}
.gr-button-primary:active { transform: translateY(0) !important; }

/* ══ ACCORDIONS ════════════════════════════════════════════════════════ */
.gr-accordion {
  background: rgba(0,201,167,0.03) !important;
  border: 1px solid rgba(0,201,167,0.1) !important;
  border-radius: 12px !important;
  margin-bottom: 8px !important;
  overflow: hidden;
}
.gr-accordion > .label-wrap, .gr-accordion .label-wrap {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: #e8f4f1 !important;
  padding: 14px 18px !important;
}

/* ══ MARKDOWN ══════════════════════════════════════════════════════════ */
.prose, .md, .markdown-text {
  color: #e8f4f1 !important;
  font-family: 'DM Sans', sans-serif !important;
  line-height: 1.7 !important;
}
.prose strong { color: #e8f4f1 !important; }
.prose table { border-collapse: collapse; width: 100%; }
.prose th {
  background: rgba(0,201,167,0.06); color: #00C9A7;
  padding: 9px 12px; text-align: left;
  font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 500;
  border-bottom: 1px solid rgba(0,201,167,0.12);
}
.prose td {
  padding: 9px 12px; font-size: 13px;
  border-bottom: 1px solid rgba(0,201,167,0.06);
}
.prose code {
  background: rgba(0,201,167,0.07); padding: 2px 7px; border-radius: 5px;
  color: #6ee7b0; font-family: 'JetBrains Mono', monospace; font-size: 12px;
}

/* ══ TOOLTIPS ══════════════════════════════════════════════════════════ */
.tt {
  color: #6ee7b0; border-bottom: 1px dotted rgba(0,201,167,0.25);
  cursor: help; position: relative;
}
.tt:hover::after {
  content: attr(data-tip); position: absolute; bottom: calc(100% + 10px); left: 50%;
  transform: translateX(-50%); background: #071a14;
  border: 1px solid rgba(0,201,167,0.15); color: #e8f4f1;
  font-size: 12px; font-family: 'DM Sans', sans-serif; line-height: 1.5;
  padding: 11px 14px; border-radius: 10px; width: 270px; z-index: 999;
  pointer-events: none; box-shadow: 0 10px 40px rgba(0,0,0,0.6);
}

/* ══ ANIMATIONS ════════════════════════════════════════════════════════ */
@keyframes breathe { 0%,100%{opacity:0.8} 50%{opacity:1} }
@keyframes pulse-dot { 0%,100%{opacity:0.3;transform:scale(1)} 50%{opacity:1;transform:scale(1.4)} }
.pulse {
  display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  background: #00C9A7; animation: pulse-dot 1.4s ease-in-out infinite;
  margin-right: 6px; vertical-align: middle;
}

/* ══ RISK COLOURS ══════════════════════════════════════════════════════ */
.r-low  { color: #34d399 !important; }
.r-mod  { color: #00C9A7 !important; }
.r-high { color: #d4a942 !important; }
.r-elev { color: #cf7b2e !important; }
.r-crit { color: #d94545 !important; font-weight: 700; }

/* ══ AGENT STATUS CARDS ════════════════════════════════════════════════ */
.ag {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 10px;
  background: rgba(0,201,167,0.03);
  border: 1px solid rgba(0,201,167,0.08);
  margin-bottom: 5px; font-size: 13px;
  font-family: 'DM Sans', sans-serif;
}
.ag-n  { font-weight: 500; color: #e8f4f1; min-width: 130px; }
.ag-t  { color: rgba(232,244,241,0.35); flex: 1; font-size: 12px; }
.ag .done { color: #34d399; font-size: 11px; }
.ag .work { color: #00C9A7; font-size: 11px; }
.ag .wait { color: rgba(232,244,241,0.25); font-size: 11px; }

/* ══ PROGRESS BAR ══════════════════════════════════════════════════════ */
.pbar {
  background: rgba(0,201,167,0.05); border: 1px solid rgba(0,201,167,0.08);
  border-radius: 100px; height: 4px; overflow: hidden; margin-top: 10px;
}
.pfill { height: 100%; background: #00C9A7; border-radius: 100px; transition: width 0.8s ease; }

/* ══ DIVIDER ═══════════════════════════════════════════════════════════ */
.divider {
  height: 1px; margin: 28px 0;
  background: linear-gradient(90deg, transparent, rgba(0,201,167,0.10), transparent);
}

/* ══ FILE UPLOAD ═══════════════════════════════════════════════════════ */
.gr-file {
  background: rgba(0,201,167,0.03) !important;
  border: 1px solid rgba(0,201,167,0.10) !important;
  border-radius: 10px !important;
  min-height: auto !important; max-height: 56px !important;
}
.gr-file .wrap { min-height: auto !important; padding: 8px !important; }

/* ══ RESPONSIVE ════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .tt:hover::after { width: 200px; font-size: 11px; }
}
"""

# ═══════════════════════════════════════════════════════════════════════════
# JURISDICTION & ACTIVITY MAPS
# ═══════════════════════════════════════════════════════════════════════════
JURISDICTION_MAP = {
    "European Union": "EU",
    "United States": "US",
    "Singapore": "SG",
    "United Kingdom": "UK",
    "UAE / Dubai": "AE",
}
JURISDICTION_CHOICES = list(JURISDICTION_MAP.keys())

ACTIVITY_MAP = {
    "Let users buy/sell crypto": "exchange",
    "Issue a token or digital asset": "token_issuance",
    "Hold/store crypto for users": "custody",
    "Offer lending or yield": "lending",
    "Process payments in crypto": "payment_processing",
    "Run a DeFi protocol": "defi",
    "NFT marketplace": "nft",
    "Staking services": "staking",
    "OTC / institutional trading": "otc",
}
ACTIVITY_CHOICES = list(ACTIVITY_MAP.keys())

HF_TOKEN = os.environ.get("HF_TOKEN", "")
DEMO_MODE = not bool(HF_TOKEN)
_orchestrator = None


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from src.agents.orchestrator import ComplianceOrchestrator
        _orchestrator = ComplianceOrchestrator()
    return _orchestrator


# ═══════════════════════════════════════════════════════════════════════════
# SVG RISK GAUGE
# ═══════════════════════════════════════════════════════════════════════════
def _svg_gauge(score: int, label: str) -> str:
    circ = 283
    arc = circ * 0.75
    off = arc - (arc * score / 100)
    if score <= 30:
        c, cls = "var(--green)", "r-low"
    elif score <= 50:
        c, cls = "var(--accent)", "r-mod"
    elif score <= 70:
        c, cls = "var(--gold)", "r-high"
    elif score <= 85:
        c, cls = "var(--amber)", "r-elev"
    else:
        c, cls = "var(--red)", "r-crit"

    return f"""
<div style="text-align:center;padding:32px 0 16px;">
  <svg width="190" height="190" viewBox="0 0 100 100" style="transform:rotate(135deg)">
    <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(62,178,127,.07)"
            stroke-width="7" stroke-dasharray="{arc}" stroke-linecap="round"/>
    <circle cx="50" cy="50" r="45" fill="none" stroke="{c}" stroke-width="7"
            stroke-dasharray="{arc}" stroke-linecap="round"
            style="stroke-dashoffset:{off};transition:stroke-dashoffset 1.4s cubic-bezier(.23,1,.32,1)"/>
  </svg>
  <div style="margin-top:-115px;position:relative;">
    <div style="font-family:var(--mono);font-size:2.8em;font-weight:700;color:{c}">{score}</div>
    <div style="font-family:var(--head);font-size:1em;font-weight:600;margin-top:2px;letter-spacing:.08em" class="{cls}">{label.upper()}</div>
  </div>
</div>"""


def _score_summary(scores: dict, label: str) -> str:
    urgent = sum(1 for k, v in scores.items() if k != "overall" and v > 50)
    if urgent == 0:
        return "Your compliance posture looks manageable. Review the recommendations below to stay on track."
    return f"You have **{urgent} area{'s' if urgent != 1 else ''}** that need{'s' if urgent == 1 else ''} urgent attention before operating legally."


def _sub_scores_html(scores: dict) -> str:
    labels = {"licensing": "Licensing", "aml": "AML / KYC", "token": "Token risk", "disclosure": "Disclosure", "operational": "Operational"}
    rows = ""
    for k, d in labels.items():
        v = scores.get(k, 0)
        w = v  # bar width %
        if v <= 30:
            bc = "var(--green)"
        elif v <= 50:
            bc = "var(--accent)"
        elif v <= 70:
            bc = "var(--gold)"
        else:
            bc = "var(--red)"
        rows += (
            f'<div style="display:flex;align-items:center;gap:12px;margin:5px 0;">'
            f'<span style="width:100px;font-size:13px;color:var(--txt2)">{d}</span>'
            f'<div style="flex:1;height:6px;background:rgba(62,178,127,.07);border-radius:99px;overflow:hidden">'
            f'<div style="width:{w}%;height:100%;background:{bc};border-radius:99px;transition:width 1s ease"></div></div>'
            f'<span style="font-family:var(--mono);font-size:12px;width:42px;text-align:right">{v}/100</span>'
            f'</div>'
        )
    return f'<div style="max-width:420px;margin:12px auto 0">{rows}</div>'


# ═══════════════════════════════════════════════════════════════════════════
# AGENT STATUS
# ═══════════════════════════════════════════════════════════════════════════
AGENTS = [
    ("Token Analyst", "Reviewing your token against securities laws"),
    ("AML Specialist", "Checking anti-money laundering obligations"),
    ("Regulatory Mapper", "Mapping rules for each country"),
    ("Licensing Guide", "Estimating licences, costs and timelines"),
    ("Case Researcher", "Finding similar compliance cases"),
    ("Report Writer", "Drafting your compliance report"),
]


def _agent_html(statuses=None):
    if statuses is None:
        statuses = ["wait"] * 6
    h = ""
    for i, (n, t) in enumerate(AGENTS):
        s = statuses[i] if i < len(statuses) else "wait"
        if s == "done":
            badge = '<span class="done">\u2713 Done</span>'
        elif s == "work":
            badge = '<span class="work"><span class="pulse"></span>Working</span>'
        else:
            badge = '<span class="wait">Queued</span>'
        h += f'<div class="ag"><span class="ag-n">{n}</span><span class="ag-t">{t}</span>{badge}</div>'
    return h


def _pbar(pct):
    return f'<div class="pbar"><div class="pfill" style="width:{pct}%"></div></div>'


# ═══════════════════════════════════════════════════════════════════════════
# STATIC CONTENT
# ═══════════════════════════════════════════════════════════════════════════
QUICK_REF = """
## Jurisdiction comparison

| | EU (MiCA) | US (SEC/FinCEN) | Singapore (MAS) | UK (FCA) | UAE (VARA) |
|---|---|---|---|---|---|
| **Main law** | MiCA Reg. 2023/1114 | Securities Act / BSA | Payment Services Act | FSMA + MLR 2017 | Dubai Law No. 4/2022 |
| **Licence** | CASP authorisation | MSB + State MTL | SPI / MPI / DTSP | MLR registration | VASP licence |
| **Capital** | \u20ac50K\u2013150K | Varies by state | SGD 100K\u2013250K | No fixed min | AED 500K\u201315M |
| **Timeline** | 3\u20136 mo | 2\u20134 wk + 3\u201312 mo (state) | 6\u201312 mo | 3\u20136 mo | 6\u201312 mo |
| **Passport** | 27 EU states | No | No | No | Dubai only |
| **Travel Rule** | All transfers | $3,000 | SGD 1,500 | \u00a31,000 | All transfers |

---

## Howey Test \u2014 quick check

| # | Question | If YES |
|---|----------|--------|
| 1 | Do people pay money or crypto to get your token? | Investment of money |
| 2 | Are proceeds pooled to fund your project? | Common enterprise |
| 3 | Do buyers expect the price to go up? | Expectation of profit |
| 4 | Does your team drive the token\u2019s value? | Efforts of others |

**All 4 = YES \u2192 Likely a security.** Get legal advice before selling.
"""

ABOUT_MD = """
## How it works

Six specialist AI agents analyse your business in sequence:

1. **Token Analyst** \u2014 Howey Test (US) + MiCA classification (EU)
2. **AML Specialist** \u2014 anti-money-laundering and identity verification
3. **Regulatory Mapper** \u2014 rules that apply in each country
4. **Licensing Guide** \u2014 licences needed, timelines, costs
5. **Case Researcher** \u2014 similar businesses that faced enforcement
6. **Report Writer** \u2014 plain-language compliance report

Behind the scenes: **FAISS** semantic search over 291 regulatory documents + **Mistral-7B** for narrative summaries.

### Knowledge base

5 jurisdictions \u00b7 175+ regulation entries \u00b7 42 enforcement cases \u00b7 20 precedents \u00b7 70 SOP steps \u00b7 6 critical 2025 updates

---

<div style="text-align:center;margin-top:20px;color:var(--txt3);font-size:12px">
CryptoComply by Arjit Mathur<br>
MiCA \u00b7 FATF 2025 \u00b7 SEC Project Crypto \u00b7 MAS DTSP 2025 \u00b7 FCA \u00b7 VARA
</div>
"""

DISCLAIMER = (
    "This tool provides **general regulatory information only** and does **not** constitute legal advice. "
    "Always consult qualified legal counsel before making compliance decisions."
)

# ═══════════════════════════════════════════════════════════════════════════
# GRADIO THEME — override at theme level so Base() can't fight back
# ═══════════════════════════════════════════════════════════════════════════
THEME = gr.themes.Base(
    primary_hue=gr.themes.Color(
        c50="#e6faf5", c100="#b3f0e0", c200="#80e6cc",
        c300="#4ddbb7", c400="#1ad1a3", c500="#00C9A7",
        c600="#00a88c", c700="#008770", c800="#006655",
        c900="#004539", c950="#002e26",
    ),
    secondary_hue=gr.themes.Color(
        c50="#e6faf5", c100="#b3f0e0", c200="#80e6cc",
        c300="#4ddbb7", c400="#1ad1a3", c500="#00C9A7",
        c600="#00a88c", c700="#008770", c800="#006655",
        c900="#004539", c950="#002e26",
    ),
    neutral_hue=gr.themes.Color(
        c50="#e8f4f1", c100="#c0d8d0", c200="#98bcaf",
        c300="#70a08e", c400="#48846d", c500="#30695a",
        c600="#1e4a3f", c700="#153328", c800="#0d2119",
        c900="#08140f", c950="#040d12",
    ),
    font=["DM Sans", "system-ui", "sans-serif"],
    font_mono=["JetBrains Mono", "monospace"],
).set(
    # Page
    body_background_fill="#040d12",
    body_background_fill_dark="#040d12",
    body_text_color="#e8f4f1",
    body_text_color_dark="#e8f4f1",
    body_text_color_subdued="rgba(232,244,241,0.5)",
    body_text_color_subdued_dark="rgba(232,244,241,0.5)",

    # Blocks / panels
    background_fill_primary="#040d12",
    background_fill_primary_dark="#040d12",
    background_fill_secondary="#071a14",
    background_fill_secondary_dark="#071a14",
    block_background_fill="rgba(0,201,167,0.03)",
    block_background_fill_dark="rgba(0,201,167,0.03)",
    block_border_color="rgba(0,201,167,0.10)",
    block_border_color_dark="rgba(0,201,167,0.10)",
    block_label_text_color="rgba(232,244,241,0.6)",
    block_label_text_color_dark="rgba(232,244,241,0.6)",
    block_label_background_fill="transparent",
    block_label_background_fill_dark="transparent",
    block_label_border_color="transparent",
    block_label_border_color_dark="transparent",
    block_title_text_color="#e8f4f1",
    block_title_text_color_dark="#e8f4f1",
    block_radius="16px",
    block_border_width="1px",

    # Inputs
    input_background_fill="rgba(0,0,0,0.3)",
    input_background_fill_dark="rgba(0,0,0,0.3)",
    input_border_color="rgba(0,201,167,0.15)",
    input_border_color_dark="rgba(0,201,167,0.15)",
    input_border_color_focus="rgba(0,201,167,0.4)",
    input_border_color_focus_dark="rgba(0,201,167,0.4)",
    input_placeholder_color="rgba(232,244,241,0.25)",
    input_placeholder_color_dark="rgba(232,244,241,0.25)",
    input_radius="10px",
    input_shadow="none",
    input_shadow_dark="none",
    input_shadow_focus="0 0 0 3px rgba(0,201,167,0.08)",
    input_shadow_focus_dark="0 0 0 3px rgba(0,201,167,0.08)",

    # Buttons
    button_primary_background_fill="transparent",
    button_primary_background_fill_dark="transparent",
    button_primary_background_fill_hover="rgba(0,201,167,0.12)",
    button_primary_background_fill_hover_dark="rgba(0,201,167,0.12)",
    button_primary_text_color="#00C9A7",
    button_primary_text_color_dark="#00C9A7",
    button_primary_text_color_hover="#00C9A7",
    button_primary_text_color_hover_dark="#00C9A7",
    button_primary_border_color="#00C9A7",
    button_primary_border_color_dark="#00C9A7",
    button_primary_border_color_hover="#00C9A7",
    button_primary_border_color_hover_dark="#00C9A7",
    button_border_width="1px",
    button_shadow="none",
    button_shadow_hover="0 0 24px rgba(0,201,167,0.15)",
    button_shadow_active="none",
    button_large_radius="12px",
    button_large_padding="14px 28px",

    button_secondary_background_fill="transparent",
    button_secondary_background_fill_dark="transparent",
    button_secondary_text_color="rgba(232,244,241,0.6)",
    button_secondary_text_color_dark="rgba(232,244,241,0.6)",
    button_secondary_border_color="rgba(0,201,167,0.15)",
    button_secondary_border_color_dark="rgba(0,201,167,0.15)",

    # Borders
    border_color_primary="rgba(0,201,167,0.12)",
    border_color_primary_dark="rgba(0,201,167,0.12)",
    border_color_accent="rgba(0,201,167,0.20)",
    border_color_accent_dark="rgba(0,201,167,0.20)",

    # Shadows
    shadow_drop="none",
    shadow_drop_lg="none",
    shadow_spread="0px",

    # Blocks
    block_padding="16px",
    block_shadow="none",
    block_shadow_dark="none",
)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def run_analysis(biz, tok, jxd, actd):
    if not biz or len(biz.strip()) < 20:
        raise gr.Error("Please describe your business in more detail (at least 20 characters).")
    if not jxd:
        raise gr.Error("Select at least one jurisdiction.")
    if not actd:
        raise gr.Error("Select at least one activity.")

    jx = [JURISDICTION_MAP[j] for j in jxd if j in JURISDICTION_MAP]
    ac = [ACTIVITY_MAP[a] for a in actd if a in ACTIVITY_MAP]

    try:
        gr.Info("Loading knowledge base and agents\u2026")
        orch = _get_orchestrator()
        gr.Info("Running multi-agent compliance analysis\u2026")
        result = orch.run(business_description=biz, jurisdictions=jx, activities=ac, token_description=tok or "")
        fmt = _fmt(result)
        return (
            _agent_html(["done"] * 6),
            _pbar(100),
            '<span style="color:var(--green)">\u2713 Analysis complete \u2014 see results below</span>',
            *fmt,
        )
    except Exception as e:
        traceback.print_exc()
        raise gr.Error(f"Analysis failed: {e}")


def _fmt(r):
    sc = r.get("risk_scores", {})
    lb = r.get("risk_label", "Medium")
    pt = r.get("metadata", {}).get("processing_time_s", 0)

    gauge = _svg_gauge(sc.get("overall", 0), lb)
    sent = _score_summary(sc, lb)
    subs = _sub_scores_html(sc)
    risk_h = f'{gauge}<div style="text-align:center;font-size:15px;margin:10px 0">{glossarise(sent)}</div>{subs}'

    summary = glossarise(r.get("summary", ""))

    fm = {"EU": "\U0001f1ea\U0001f1fa", "US": "\U0001f1fa\U0001f1f8", "SG": "\U0001f1f8\U0001f1ec", "UK": "\U0001f1ec\U0001f1e7", "AE": "\U0001f1e6\U0001f1ea"}
    jp = []
    for j in r.get("jurisdiction_analysis", []):
        c = j.get("code", "")
        jp.append(f"### {fm.get(c,'')} {j.get('name',c)}\n**Status:** {j.get('status','')}")
        if j.get("detail"):
            jp.append(j["detail"])
        jp.append("")
    jx_md = glossarise("\n".join(jp)) if jp else ""

    tc = r.get("token_analysis", {})
    if tc and tc.get("us_classification"):
        sec = tc.get("is_security", False)
        sw = "**Yes**" if sec else "**Unlikely**"
        tc_md = glossarise(
            f"**Is your token a security?** {sw}\n\n"
            f"Howey Test: `{tc.get('us_classification','N/A')}` \u00b7 MiCA: `{tc.get('mica_type','N/A')}`\n\n"
            f"{tc.get('howey_result','')}\n\n"
            f"**Next steps:** Get a legal opinion \u00b7 "
            f"{'Register or secure Reg D/S exemption' if sec else 'Document classification analysis'} \u00b7 "
            f"Prepare MiCA whitepaper if targeting EU"
        )
    else:
        tc_md = "*Add a token description above to get classification.*"

    aml = r.get("aml_analysis", {})
    ap = []
    yes_msg = "**Yes** \u2014 mandatory for your activities."
    no_msg = "Pending."
    ap.append(f"**Do you need KYC/AML?** {yes_msg if aml.get('needed') else no_msg}\n")
    for it in aml.get("needed", [])[:6]:
        ap.append(f"- {it}")
    if aml.get("missing"):
        ap.append("\n**Gaps found:**")
        for it in aml["missing"]:
            ap.append(f"- \u26a0\ufe0f {it}")
    aml_md = glossarise("\n".join(ap))

    lic = r.get("licensing", {})
    lp = []
    for l in lic.get("required_licences", []):
        lp.append(
            f"### {l.get('jurisdiction','')} \u2014 {l.get('licence_type','')}\n"
            f"**Regulator:** {l.get('regulator','N/A')} \u00b7 **Timeline:** {l.get('timeline_months','?')} months \u00b7 **Cost:** {l.get('total_cost_range','TBD')}\n\n"
            f"Triggered by: {', '.join(l.get('triggers',[]))}\n"
        )
    if lic.get("sequencing"):
        lp.append("### Recommended order")
        for s in lic["sequencing"]:
            lp.append(f"- {s}")
    lic_md = glossarise("\n".join(lp)) if lp else ""

    cs = r.get("enforcement_cases", [])
    cp = []
    if cs:
        cp.append("*Businesses similar to yours that faced enforcement:*\n")
    for c in cs[:5]:
        nm = c.get("case_name", c.get("title", ""))
        cp.append(f"**{nm}**")
        if c.get("key_lesson"):
            cp.append(f"{c['key_lesson'][:250]}")
        cp.append("")
    case_md = glossarise("\n".join(cp)) if cp else ""

    acts = r.get("action_plan", [])
    axp = []
    for tag, title in [("[CRITICAL]", "### This week"), ("[URGENT]", "\n### Next 30 days"), ("[HIGH]", ""), ("[MEDIUM]", "\n### Next 90 days"), ("[LOW]", "")]:
        items = [a for a in acts if tag in a]
        if items and title:
            axp.append(title)
        for a in items:
            axp.append(f"- [ ] {a.replace(tag + ' ', '')}")
    act_md = glossarise("\n".join(axp)) if axp else ""

    full = r.get("markdown_report", "") + f"\n\n---\n*Completed in {pt:.1f}s*"

    pdf = r.get("pdf_path", "")
    pdf_out = pdf if pdf and os.path.exists(pdf) else None

    return (risk_h, summary, jx_md, tc_md, aml_md, lic_md, case_md, act_md, full, pdf_out)


# ═══════════════════════════════════════════════════════════════════════════
# HERO HTML (inline SVG shield + breathing animation)
# ═══════════════════════════════════════════════════════════════════════════
HERO_HTML = """
<div id="aurora"><div class="blob1"></div><div class="blob2"></div></div>
<div style="text-align:center;padding:48px 20px 10px;position:relative;z-index:1;">
  <div style="display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:6px;">
    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" style="animation:breathe 3s ease-in-out infinite;">
      <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"
            fill="rgba(0,201,167,0.15)" stroke="#00C9A7" stroke-width="1.5"/>
      <path d="M10 12l2 2 4-4" stroke="#00C9A7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span style="font-family:'Sora',sans-serif;font-weight:700;font-size:28px;color:#fff;">CryptoComply</span>
  </div>
  <div style="font-family:'DM Sans',sans-serif;font-weight:300;font-size:14px;color:rgba(0,201,167,0.7);">
    Regulatory intelligence for crypto businesses
  </div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:2px;color:rgba(232,244,241,0.3);margin-top:8px;">
    MiCA &middot; SEC &middot; MAS &middot; FCA &middot; VARA &middot; FATF
  </div>
  <div style="height:1px;background:rgba(0,201,167,0.1);margin:20px auto 0;max-width:500px;"></div>
</div>
"""

DEMO_BANNER_HTML = (
    '<div style="background:rgba(0,201,167,0.08);border:1px solid rgba(0,201,167,0.2);'
    'border-radius:10px;padding:12px 18px;margin:0 auto 16px;max-width:640px;'
    'color:rgba(232,244,241,0.8);font-size:13px;font-family:\'DM Sans\',sans-serif;text-align:center;">'
    'Demo mode \u2014 HF_TOKEN not set. Summaries use templates. '
    'Set HF_TOKEN in Space settings for full AI analysis.'
    '</div>'
)

# ═══════════════════════════════════════════════════════════════════════════
# BUILD UI
# ═══════════════════════════════════════════════════════════════════════════

with gr.Blocks(theme=THEME, css=CUSTOM_CSS, title="CryptoComply") as demo:

    # ── HERO ──
    gr.HTML(HERO_HTML)

    if DEMO_MODE:
        gr.HTML(DEMO_BANNER_HTML)

    with gr.Accordion("Disclaimer", open=False):
        gr.Markdown(DISCLAIMER)

    # ── INPUT SECTION ──
    gr.HTML(
        '<div style="font-family:\'Sora\',sans-serif;font-size:20px;font-weight:600;'
        'color:#e8f4f1;margin:24px 0 2px;">Tell us about your business</div>'
        '<div style="font-family:\'DM Sans\',sans-serif;font-size:13px;'
        'color:rgba(232,244,241,0.45);margin-bottom:16px;">'
        'Write in plain language \u2014 no legal knowledge needed</div>'
    )

    biz_in = gr.Textbox(
        label="What does your business do?", lines=4,
        placeholder="Example: We\u2019re launching a crypto exchange in Europe. Users can trade Bitcoin, Ethereum and our own token. We want to serve customers in Germany, UK and Singapore\u2026",
    )
    tok_in = gr.Textbox(
        label="Do you have a token or digital asset? (optional)", lines=2,
        placeholder="Example: A utility token giving users lower trading fees. No profit rights, no voting\u2026",
    )
    jx_in = gr.CheckboxGroup(
        label="Where do you want to operate?",
        choices=JURISDICTION_CHOICES,
        value=["European Union", "United States"],
    )
    gr.HTML(
        '<div style="font-size:11px;color:rgba(232,244,241,0.25);margin-top:-2px;">'
        'Not sure? Select all \u2014 we\u2019ll tell you which apply.</div>'
    )
    act_in = gr.CheckboxGroup(label="What will your business do?", choices=ACTIVITY_CHOICES)

    btn = gr.Button("Analyse my compliance requirements \u2192", variant="primary", size="lg")

    # ── ANALYSIS STATUS ──
    gr.HTML('<div class="divider"></div>')
    narr = gr.HTML('<span style="color:rgba(232,244,241,0.3);font-size:13px;">&nbsp;</span>')
    agents = gr.HTML("")
    pbar = gr.HTML("")

    # ── RESULTS ──
    risk_out = gr.HTML()

    with gr.Accordion("Executive summary", open=True):
        sum_out = gr.Markdown()
    with gr.Accordion("Jurisdiction analysis", open=False):
        jx_out = gr.Markdown()
    with gr.Accordion("Token classification", open=False):
        tok_out = gr.Markdown()
    with gr.Accordion("AML and identity verification", open=False):
        aml_out = gr.Markdown()
    with gr.Accordion("Your licensing journey", open=False):
        lic_out = gr.Markdown()
    with gr.Accordion("What to do next", open=False):
        act_out = gr.Markdown()
    with gr.Accordion("Similar enforcement cases", open=False):
        case_out = gr.Markdown()

    pdf_out = gr.File(label="PDF Report", visible=True)

    with gr.Accordion("Full markdown report", open=False):
        full_out = gr.Markdown()

    # ── REFERENCE & ABOUT ──
    gr.HTML('<div class="divider" style="margin-top:40px;"></div>')
    with gr.Accordion("Quick reference \u2014 jurisdictions, thresholds, Howey Test", open=False):
        gr.Markdown(QUICK_REF)
    with gr.Accordion("About CryptoComply", open=False):
        gr.Markdown(ABOUT_MD)

    # ── FOOTER ──
    gr.HTML(
        '<div style="text-align:center;padding:40px 20px 24px;">'
        '<div style="display:flex;align-items:center;justify-content:center;gap:6px;margin-bottom:4px;">'
        '  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">'
        '    <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"'
        '          fill="none" stroke="rgba(0,201,167,0.4)" stroke-width="1.5"/>'
        '  </svg>'
        '  <span style="font-family:\'Sora\',sans-serif;font-weight:600;font-size:13px;'
        '  color:rgba(232,244,241,0.5);">CryptoComply</span>'
        '</div>'
        '<div style="font-family:\'DM Sans\',sans-serif;font-size:11px;color:rgba(232,244,241,0.2);">'
        'by Arjit Mathur &middot; MiCA &middot; FATF 2025 &middot; SEC &middot; MAS &middot; FCA &middot; VARA</div>'
        '</div>'
    )

    # ── EVENTS ──
    btn.click(
        fn=run_analysis,
        inputs=[biz_in, tok_in, jx_in, act_in],
        outputs=[agents, pbar, narr, risk_out, sum_out, jx_out, tok_out, aml_out, lic_out, case_out, act_out, full_out, pdf_out],
    )

# ═══════════════════════════════════════════════════════════════════════════
# LAUNCH
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__" or True:
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
