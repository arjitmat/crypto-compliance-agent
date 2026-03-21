"""CryptoComply — Multi-Agent Crypto Compliance Intelligence Platform.

Gradio application entry point for HuggingFace Spaces.
Single-page vertical flow with teal glassmorphism design system.
"""

import os
import re
import traceback
import time as _time

import gradio as gr

# ═══════════════════════════════════════════════════════════════════════════
# COMPLIANCE GLOSSARY  (30 plain-language definitions)
# ═══════════════════════════════════════════════════════════════════════════
COMPLIANCE_GLOSSARY: dict[str, str] = {
    "Howey Test": "A 4-question legal test from a 1946 US court case. If all 4 questions are YES for your token, the SEC may treat it as a security and require registration.",
    "VASP": "Virtual Asset Service Provider. The legal term for crypto businesses. If you run a VASP, you must follow AML rules in most countries.",
    "CASP": "Crypto-Asset Service Provider. The EU\u2019s term for crypto businesses under MiCA. Similar to VASP but specific to Europe.",
    "Travel Rule": "A rule that requires crypto businesses to collect and share the names and account details of senders and receivers for transfers above a certain amount.",
    "AML": "Anti-Money Laundering. A set of laws requiring businesses to check that their users aren\u2019t using the service to hide or move criminal money.",
    "KYC": "Know Your Customer. The process of verifying who your users are \u2014 usually by checking their ID and address.",
    "EMT": "E-Money Token. Under EU MiCA, a type of stablecoin pegged to one official currency (like EUR). Stricter rules than other crypto.",
    "ART": "Asset-Referenced Token. Under EU MiCA, a stablecoin backed by multiple assets (currencies, commodities). The most regulated crypto type in Europe.",
    "MiCA": "Markets in Crypto-Assets Regulation. The EU\u2019s main crypto law, fully in force from December 2024.",
    "FinCEN": "Financial Crimes Enforcement Network. The US Treasury agency that regulates money service businesses including crypto firms.",
    "MSB": "Money Services Business. The US category for crypto exchanges and money transmitters. Must register with FinCEN.",
    "MPI Licence": "Major Payment Institution Licence. The main Singapore licence for crypto businesses handling significant transaction volumes.",
    "DTSP": "Digital Token Service Provider. A new Singapore category (from June 2025) for crypto firms serving international clients.",
    "VARA": "Virtual Assets Regulatory Authority. Dubai\u2019s dedicated crypto regulator. Required for most crypto businesses operating in Dubai.",
    "FCA": "Financial Conduct Authority. The UK\u2019s main financial regulator. Crypto businesses must register with them for AML purposes.",
    "EDD": "Enhanced Due Diligence. Extra identity checks for high-risk customers, such as politicians (PEPs) or users from high-risk countries.",
    "PEP": "Politically Exposed Person. A current or former senior politician, judge, military officer, or their close family/associates. Requires extra checks.",
    "Unhosted Wallet": "A crypto wallet controlled by the user themselves (like a MetaMask wallet), not held by an exchange. Travel Rule rules for these wallets are still being worked out globally.",
    "Whitepaper": "Under MiCA, a legal document that token issuers must publish before launch. Similar to a prospectus \u2014 must describe the token, its risks, and the issuer\u2019s details.",
    "OFAC": "US Treasury\u2019s sanctions list. Crypto businesses must check users against it. If a user is on the list, you cannot serve them.",
    "CDD": "Customer Due Diligence. The basic level of identity checks \u2014 verifying names, addresses, and IDs before opening an account.",
    "SAR": "Suspicious Activity Report. A report crypto businesses must file with the government when they spot transactions that might involve crime.",
    "STR": "Suspicious Transaction Report. The same as a SAR but used in some countries (e.g. Singapore, UAE) instead of SAR.",
    "BSA": "Bank Secrecy Act. The main US anti-money laundering law. Applies to crypto exchanges that register as MSBs.",
    "ESMA": "European Securities and Markets Authority. The EU-wide body that coordinates crypto regulation and maintains the CASP register.",
    "Reg D": "Regulation D. A US exemption that lets you sell security tokens to accredited (wealthy/sophisticated) investors without full SEC registration.",
    "Reg S": "Regulation S. A US exemption for selling tokens to people outside the United States only.",
    "FATF": "Financial Action Task Force. The global body that sets anti-money laundering standards. 99 countries follow its rules.",
    "Passporting": "Under MiCA, a licence in one EU country lets you operate across all 27 EU member states. Like a passport for your crypto business.",
    "Cold Storage": "Keeping crypto keys offline (not connected to the internet). Most regulators require at least 80% of customer crypto in cold storage.",
}

# Build a regex pattern that matches glossary terms (longest-first to avoid partial matches)
_sorted_terms = sorted(COMPLIANCE_GLOSSARY.keys(), key=len, reverse=True)
_glossary_re = re.compile(
    r"(?<!\w)(" + "|".join(re.escape(t) for t in _sorted_terms) + r")(?!\w)",
    re.IGNORECASE,
)


def glossarise(text: str) -> str:
    """Wrap recognised compliance terms in tooltip spans (first occurrence only)."""
    seen: set[str] = set()

    def _replace(m: re.Match) -> str:
        raw = m.group(0)
        key = next((k for k in COMPLIANCE_GLOSSARY if k.lower() == raw.lower()), None)
        if key is None or key in seen:
            return raw
        seen.add(key)
        tip = COMPLIANCE_GLOSSARY[key].replace('"', "&quot;")
        return f'<span class="tooltip-term" data-tip="{tip}">{raw}</span>'

    return _glossary_re.sub(_replace, text)


# ═══════════════════════════════════════════════════════════════════════════
# FONT LINK  (injected via gr.HTML at top of page)
# ═══════════════════════════════════════════════════════════════════════════
FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700'
    '&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500'
    '&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
)

# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM CSS — teal glassmorphism design system
# ═══════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = r"""
/* ── CSS VARIABLES ────────────────────────────────── */
:root {
  --void:        #040d12;
  --surface:     #070f15;
  --surface-2:   #0a1520;
  --glass-bg:    rgba(0,201,167,0.04);
  --glass-border:rgba(0,201,167,0.12);
  --teal:        #00C9A7;
  --teal-dim:    #007A66;
  --gold:        #FFB800;
  --amber:       #FF7A00;
  --red:         #FF3B3B;
  --green:       #00E676;
  --text-primary:   #E8F4F1;
  --text-secondary: rgba(232,244,241,0.55);
  --text-tertiary:  rgba(232,244,241,0.30);
}

/* ── BASE ─────────────────────────────────────────── */
body, .gradio-container, .main, .wrap, .contain {
  background: var(--surface) !important;
  color: var(--text-primary) !important;
  font-family: 'DM Sans', system-ui, sans-serif !important;
}

/* Aurora background */
.gradio-container::before,
.gradio-container::after {
  content: '';
  position: fixed;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  filter: blur(120px);
  opacity: 0.12;
}
.gradio-container::before {
  width: 800px; height: 800px;
  background: radial-gradient(circle, var(--teal) 0%, transparent 70%);
  top: -200px; right: -200px;
  animation: aurora-drift 60s ease-in-out infinite alternate;
}
.gradio-container::after {
  width: 600px; height: 600px;
  background: radial-gradient(circle, var(--teal-dim) 0%, transparent 70%);
  bottom: -150px; left: -150px;
  animation: aurora-drift 60s ease-in-out infinite alternate-reverse;
}
@keyframes aurora-drift {
  0%   { transform: translate(0, 0); }
  100% { transform: translate(100px, -60px); }
}

/* ── GLASS CARDS ──────────────────────────────────── */
.glass {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 16px !important;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.glass:hover {
  border-color: rgba(0,201,167,0.22) !important;
  box-shadow: 0 0 30px rgba(0,201,167,0.06);
}
@keyframes breathe {
  0%, 100% { box-shadow: 0 0 15px rgba(0,201,167,0.04); }
  50%      { box-shadow: 0 0 30px rgba(0,201,167,0.10); }
}
.glass-breathe { animation: breathe 4s ease-in-out infinite; }

/* ── FORM INPUTS (glass style) ────────────────────── */
.gr-panel, .gr-box, .gr-form {
  background: transparent !important;
  border: none !important;
}
textarea, input[type="text"], .gr-input, .gr-textbox textarea {
  background: var(--glass-bg) !important;
  backdrop-filter: blur(12px) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 12px !important;
  color: var(--text-primary) !important;
  font-family: 'DM Sans', system-ui, sans-serif !important;
  font-size: 15px !important;
  padding: 14px 16px !important;
}
textarea:focus, input[type="text"]:focus {
  border-color: var(--teal) !important;
  box-shadow: 0 0 0 2px rgba(0,201,167,0.18) !important;
  outline: none !important;
}
textarea::placeholder { color: var(--text-tertiary) !important; }

/* Labels */
label, .gr-check-radio label, span.svelte-1gfkn6j {
  color: var(--text-secondary) !important;
  font-family: 'DM Sans', system-ui, sans-serif !important;
  font-weight: 500 !important;
  font-size: 14px !important;
}

/* ── PILL CHECKBOXES ──────────────────────────────── */
.gr-check-radio {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
}
.gr-check-radio label {
  background: var(--glass-bg) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 100px !important;
  padding: 6px 16px !important;
  font-size: 13px !important;
  cursor: pointer;
  transition: all 0.2s !important;
}
.gr-check-radio label:hover {
  border-color: rgba(0,201,167,0.30) !important;
}
.gr-check-radio input:checked + span,
.gr-check-radio label:has(input:checked) {
  background: rgba(0,201,167,0.12) !important;
  border-color: var(--teal) !important;
  color: var(--teal) !important;
}

/* ── PRIMARY BUTTON ───────────────────────────────── */
.cta-btn, .gr-button-primary {
  background: var(--teal) !important;
  color: var(--void) !important;
  font-family: 'DM Sans', system-ui, sans-serif !important;
  font-weight: 500 !important;
  font-size: 16px !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 14px 32px !important;
  cursor: pointer;
  transition: all 0.25s !important;
  letter-spacing: 0.01em;
}
.cta-btn:hover, .gr-button-primary:hover {
  background: #00ddb6 !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 30px rgba(0,201,167,0.30) !important;
}

/* ── ACCORDION ────────────────────────────────────── */
.gr-accordion {
  background: var(--glass-bg) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 14px !important;
  overflow: hidden;
  margin-bottom: 8px !important;
}
.gr-accordion .label-wrap {
  color: var(--text-primary) !important;
  font-family: 'DM Sans', system-ui, sans-serif !important;
}

/* ── MARKDOWN CONTENT ─────────────────────────────── */
.prose, .md, .markdown-text {
  color: var(--text-primary) !important;
  font-family: 'DM Sans', system-ui, sans-serif !important;
  line-height: 1.65 !important;
}
.prose h1, .prose h2, .prose h3, .md h1, .md h2, .md h3 {
  font-family: 'Sora', system-ui, sans-serif !important;
  color: var(--text-primary) !important;
  font-weight: 600 !important;
}
.prose strong { color: var(--text-primary) !important; }
.prose table { border-collapse: collapse; width: 100%; }
.prose th {
  background: rgba(0,201,167,0.08);
  color: var(--teal);
  padding: 10px 12px;
  text-align: left;
  font-family: 'DM Sans', system-ui, sans-serif;
  font-size: 13px;
  font-weight: 500;
  border-bottom: 1px solid var(--glass-border);
}
.prose td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(0,201,167,0.06);
  font-size: 13px;
}
.prose code {
  background: rgba(0,201,167,0.08);
  padding: 2px 7px;
  border-radius: 5px;
  color: var(--teal);
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}

/* ── TOOLTIP ON GLOSSARY TERMS ────────────────────── */
.tooltip-term {
  color: var(--teal);
  border-bottom: 1px dotted rgba(0,201,167,0.35);
  cursor: help;
  position: relative;
}
.tooltip-term:hover::after {
  content: attr(data-tip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: #0d1d1a;
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  font-size: 12px;
  font-family: 'DM Sans', system-ui, sans-serif;
  line-height: 1.45;
  padding: 10px 14px;
  border-radius: 10px;
  width: 280px;
  z-index: 999;
  pointer-events: none;
  box-shadow: 0 8px 30px rgba(0,0,0,0.5);
}

/* ── STAGGERED REVEAL ─────────────────────────────── */
@keyframes slide-up {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}
.reveal { animation: slide-up 0.5s ease-out forwards; }
.reveal-d1 { animation-delay: 0.15s; opacity: 0; }
.reveal-d2 { animation-delay: 0.30s; opacity: 0; }
.reveal-d3 { animation-delay: 0.45s; opacity: 0; }
.reveal-d4 { animation-delay: 0.60s; opacity: 0; }

/* ── PULSE DOT (agent working) ────────────────────── */
@keyframes pulse-dot {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50%      { opacity: 1;   transform: scale(1.3); }
}
.pulse-teal {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--teal);
  animation: pulse-dot 1.4s ease-in-out infinite;
  margin-right: 6px;
  vertical-align: middle;
}

/* ── RISK COLOURS ─────────────────────────────────── */
.risk-low      { color: var(--green) !important; }
.risk-moderate { color: var(--teal) !important; }
.risk-high     { color: var(--gold) !important; }
.risk-elevated { color: var(--amber) !important; }
.risk-critical { color: var(--red) !important; font-weight: 700; }

/* ── FILE DOWNLOAD ────────────────────────────────── */
.gr-file { background: var(--glass-bg) !important; border: 1px solid var(--glass-border) !important; border-radius: 12px !important; }

/* ── SECTION DIVIDER ──────────────────────────────── */
.teal-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
  margin: 32px 0;
}

/* ── HERO ──────────────────────────────────────────── */
.hero-logo {
  font-family: 'Sora', system-ui, sans-serif;
  font-weight: 600;
  font-size: 2.2em;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}
.hero-logo .glyph {
  width: 36px; height: 36px;
  border-radius: 8px;
  background: var(--teal);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--void);
}
.hero-tagline {
  font-family: 'DM Sans', system-ui, sans-serif;
  font-weight: 300;
  font-size: 1.05em;
  color: var(--teal-dim);
  text-align: center;
  margin-top: 4px;
}
.hero-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78em;
  color: var(--text-tertiary);
  text-align: center;
  margin-top: 6px;
  letter-spacing: 0.04em;
}

/* ── AGENT STATUS CARDS ───────────────────────────── */
.agent-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  margin-bottom: 6px;
  font-size: 14px;
}
.agent-row .agent-name {
  font-weight: 500;
  color: var(--text-primary);
  min-width: 130px;
}
.agent-row .agent-task {
  color: var(--text-secondary);
  flex: 1;
}
.badge-queued   { color: var(--text-tertiary); font-size: 12px; }
.badge-working  { color: var(--teal); font-size: 12px; }
.badge-done     { color: var(--green); font-size: 12px; }

/* ── PROGRESS BAR ─────────────────────────────────── */
.progress-outer {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 100px;
  height: 6px;
  overflow: hidden;
  margin-top: 12px;
}
.progress-inner {
  height: 100%;
  background: var(--teal);
  border-radius: 100px;
  transition: width 0.6s ease;
}

/* ── RESPONSIVE ───────────────────────────────────── */
@media (max-width: 768px) {
  .hero-logo { font-size: 1.6em; }
  .tooltip-term:hover::after { width: 200px; font-size: 11px; }
}
"""

# ═══════════════════════════════════════════════════════════════════════════
# JURISDICTION MAP
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
    """Render an animated SVG circular risk gauge."""
    # 270-degree arc on a circle of radius 45 → circumference fraction
    circumference = 283  # 2 * pi * 45
    arc_length = circumference * 0.75  # 270 degrees
    offset = arc_length - (arc_length * score / 100)

    if score <= 30:
        color = "var(--green)"
    elif score <= 50:
        color = "var(--teal)"
    elif score <= 70:
        color = "var(--gold)"
    elif score <= 85:
        color = "var(--amber)"
    else:
        color = "var(--red)"

    css_class = {
        "Low": "risk-low",
        "Medium": "risk-moderate",
        "High": "risk-elevated",
        "Critical": "risk-critical",
    }.get(label, "risk-moderate")

    return f"""
<div style="text-align:center;padding:28px 0;">
  <svg width="180" height="180" viewBox="0 0 100 100" style="transform:rotate(135deg)">
    <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(0,201,167,0.08)" stroke-width="8"
            stroke-dasharray="{arc_length}" stroke-dashoffset="0" stroke-linecap="round"/>
    <circle cx="50" cy="50" r="45" fill="none" stroke="{color}" stroke-width="8"
            stroke-dasharray="{arc_length}" stroke-linecap="round"
            style="stroke-dashoffset:{offset};transition:stroke-dashoffset 1.2s ease-out;"/>
  </svg>
  <div style="margin-top:-110px;position:relative;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:2.6em;font-weight:700;{f'color:{color};' if score > 50 else f'color:{color};'}">{score}</div>
    <div style="font-family:'Sora',sans-serif;font-size:1.1em;font-weight:600;margin-top:2px;" class="{css_class}">{label.upper()}</div>
  </div>
</div>
"""


def _score_summary_sentence(scores: dict, label: str) -> str:
    """One plain-English sentence about the risk score."""
    urgent = sum(1 for k, v in scores.items() if k != "overall" and v > 50)
    if urgent == 0:
        return "Your compliance posture looks manageable. Review the recommendations below to stay ahead."
    return f"You have **{urgent} area{'s' if urgent != 1 else ''}** that need{'s' if urgent == 1 else ''} urgent attention before operating legally."


def _sub_scores_html(scores: dict) -> str:
    """Render sub-scores as a small table."""
    rows = ""
    labels = {
        "licensing": "Licensing",
        "aml": "AML / KYC",
        "token": "Token risk",
        "disclosure": "Disclosure",
        "operational": "Operational",
    }
    for key, display in labels.items():
        v = scores.get(key, 0)
        rows += f'<tr><td style="padding:5px 10px;color:var(--text-secondary);font-size:13px;">{display}</td><td style="padding:5px 10px;font-family:\'JetBrains Mono\',monospace;font-size:13px;font-weight:500;">{v}/100</td></tr>'
    return f'<table style="margin:0 auto;border-collapse:collapse;">{rows}</table>'


# ═══════════════════════════════════════════════════════════════════════════
# AGENT STATUS HTML
# ═══════════════════════════════════════════════════════════════════════════
AGENTS_INFO = [
    ("Token Analyst", "Reviewing your token against securities laws"),
    ("AML Specialist", "Checking anti-money laundering obligations"),
    ("Regulatory Mapper", "Mapping rules for each country"),
    ("Licensing Guide", "Estimating licences needed and costs"),
    ("Case Researcher", "Finding similar compliance cases"),
    ("Report Writer", "Drafting your compliance report"),
]


def _agent_status_html(statuses: list[str] | None = None) -> str:
    """Render agent status cards. statuses: list of 'queued'|'working'|'done'."""
    if statuses is None:
        statuses = ["queued"] * 6
    html = '<div style="display:flex;flex-direction:column;gap:6px;">'
    for i, (name, task) in enumerate(AGENTS_INFO):
        st = statuses[i] if i < len(statuses) else "queued"
        if st == "done":
            badge = '<span class="badge-done">&#10003; Done</span>'
        elif st == "working":
            badge = '<span class="badge-working"><span class="pulse-teal"></span>Working</span>'
        else:
            badge = '<span class="badge-queued">Queued</span>'
        html += f'<div class="agent-row"><span class="agent-name">{name}</span><span class="agent-task">{task}</span>{badge}</div>'
    html += '</div>'
    return html


def _progress_html(pct: int) -> str:
    return f'<div class="progress-outer"><div class="progress-inner" style="width:{pct}%"></div></div>'


# ═══════════════════════════════════════════════════════════════════════════
# QUICK REFERENCE  (static markdown — no LLM)
# ═══════════════════════════════════════════════════════════════════════════
QUICK_REF = """
## Jurisdiction comparison

| | EU (MiCA) | US (SEC/FinCEN) | Singapore (MAS) | UK (FCA) | UAE (VARA) |
|---|---|---|---|---|---|
| **Main law** | MiCA Reg. 2023/1114 | Securities Act / BSA | Payment Services Act 2019 | FSMA 2000 + MLR 2017 | Dubai Law No. 4 of 2022 |
| **Licence** | CASP authorisation | MSB + State MTL | SPI / MPI / DTSP | MLR registration | VASP licence (7 types) |
| **Capital** | €50K\u2013€150K | Varies by state | SGD 100K\u2013250K | No fixed minimum | AED 500K\u201315M |
| **Timeline** | 3\u20136 months | 2\u20134 wk (FinCEN) + 3\u201312 m (state) | 6\u201312 months | 3\u20136 months | 6\u201312 months |
| **Passporting** | Yes \u2014 27 states | No (per state) | No | No | Dubai only |
| **Travel Rule** | All transfers (\u20ac0) | $3,000 | SGD 1,500 | \u00a31,000 | All transfers (AED 0) |
| **Approval rate** | TBD | ~90% (FinCEN) | ~11% | ~15\u201320% | Selective |

---

## Howey Test \u2014 self-assessment

| # | Question | If YES \u2192 |
|---|----------|------------|
| 1 | Do people pay money or crypto to get your token? | Investment of money |
| 2 | Are sale proceeds pooled to fund your project? | Common enterprise |
| 3 | Do buyers expect the price to go up? | Expectation of profit |
| 4 | Does your team drive the token\u2019s value? | Efforts of others |

**All 4 = YES \u2192 Likely a security.** Get legal advice before selling.

---

## Travel Rule thresholds

| Country | Threshold | You must collect sender & receiver info for transfers above this |
|---------|-----------|---------------------------------------------------------------|
| EU | \u20ac0 (every transfer) | Strictest in the world \u2014 no minimum |
| US | $3,000 | FinCEN proposed $250 but not finalised |
| UK | \u00a31,000 | Since September 2023 |
| Singapore | SGD 1,500 | Aligned with FATF |
| UAE | AED 0 (every transfer) | Same as EU \u2014 no minimum |
"""

ABOUT_MD = """
## How CryptoComply works

Six specialist AI agents analyse your business in sequence:

1. **Token Analyst** \u2014 checks if your token might be a security (Howey Test) or an EU-regulated asset (MiCA)
2. **AML Specialist** \u2014 determines anti-money-laundering and identity-verification requirements
3. **Regulatory Mapper** \u2014 maps the specific rules that apply in each country you selected
4. **Licensing Guide** \u2014 tells you which licences you need, how long they take, and how much they cost
5. **Case Researcher** \u2014 finds businesses similar to yours that faced regulatory action
6. **Report Writer** \u2014 combines everything into a plain-language report

Behind the scenes: **FAISS** semantic search over 200+ regulatory documents, powered by **sentence-transformers**. Narrative summaries by **Mistral-7B** via the HuggingFace Inference API.

---

### Knowledge base

- **5 jurisdictions**, 175+ regulation entries (MiCA, SEC, MAS, FCA, VARA)
- **42 enforcement cases** (Ripple, FTX, Binance, Coinbase, Three Arrows Capital\u2026)
- **20 legal precedents** (Howey, Telegram, LBRY\u2026)
- **70 compliance procedure steps** (KYC, Travel Rule, Token Offering)
- **6 critical 2025 updates** (SEC Project Crypto, MiCA Phase 2, Singapore DTSP, Trump EO)

### Limitations

This tool gives **general information only** \u2014 not legal advice. Always consult qualified lawyers.

---

<div style="text-align:center;margin-top:24px;color:var(--text-tertiary);font-size:13px;">
CryptoComply by Arjit Mathur<br>
Built on: MiCA \u00b7 FATF 2025 \u00b7 SEC Project Crypto \u00b7 MAS DTSP 2025 \u00b7 FCA 2023 \u00b7 VARA
</div>
"""

DISCLAIMER_TEXT = (
    "This tool provides **general regulatory information only** and does **not** "
    "constitute legal advice. The analysis is generated by an AI system and may "
    "contain errors. Always consult qualified legal counsel before making compliance "
    "decisions. The creators accept no liability for actions taken based on this output."
)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def run_analysis(business_desc, token_desc, jurisdictions_display, activities_display):
    """Full pipeline: validate, run agents, return all outputs.

    Returns a flat tuple of strings/None — no gr.update() to avoid
    gradio-client schema introspection bugs.
    """

    if not business_desc or len(business_desc.strip()) < 20:
        raise gr.Error("Please describe your business in more detail (at least 20 characters).")
    if not jurisdictions_display:
        raise gr.Error("Please select at least one jurisdiction.")
    if not activities_display:
        raise gr.Error("Please select at least one business activity.")

    jurisdictions = [JURISDICTION_MAP[j] for j in jurisdictions_display if j in JURISDICTION_MAP]
    activities = [ACTIVITY_MAP[a] for a in activities_display if a in ACTIVITY_MAP]

    try:
        gr.Info("Initialising agents and knowledge base \u2014 this may take 30\u201360 s on first run\u2026")
        orchestrator = _get_orchestrator()

        gr.Info("Running multi-agent compliance analysis\u2026")
        result = orchestrator.run(
            business_description=business_desc,
            jurisdictions=jurisdictions,
            activities=activities,
            token_description=token_desc or "",
        )

        formatted = _format_results(result)

        # Return: agent_status, progress, narration, then 10 result outputs
        return (
            _agent_status_html(["done"] * 6),                    # agent_status
            _progress_html(100),                                 # progress_bar
            '<span style="color:var(--green);">\u2705 Analysis complete \u2014 see results below.</span>',  # narration
            *formatted,                                          # 10 result outputs
        )

    except Exception as e:
        traceback.print_exc()
        raise gr.Error(f"Analysis failed: {e}")


def _format_results(result: dict) -> tuple:
    """Format the orchestrator result dict into UI components. Returns 10 values."""
    scores = result.get("risk_scores", {})
    label = result.get("risk_label", "Medium")
    processing_time = result.get("metadata", {}).get("processing_time_s", 0)

    # 1. Risk gauge
    gauge = _svg_gauge(scores.get("overall", 0), label)
    summary_sentence = _score_summary_sentence(scores, label)
    sub_scores = _sub_scores_html(scores)
    risk_html = f'{gauge}<div style="text-align:center;font-size:15px;margin:8px 0;">{glossarise(summary_sentence)}</div>{sub_scores}'

    # 2. Executive summary
    summary = glossarise(result.get("summary", "*Run an analysis to see results.*"))

    # 3. Jurisdiction cards
    jx_parts = []
    flag_map = {"EU": "\U0001F1EA\U0001F1FA", "US": "\U0001F1FA\U0001F1F8", "SG": "\U0001F1F8\U0001F1EC", "UK": "\U0001F1EC\U0001F1E7", "AE": "\U0001F1E6\U0001F1EA"}
    for jx in result.get("jurisdiction_analysis", []):
        code = jx.get("code", "")
        flag = flag_map.get(code, "")
        jx_parts.append(f"### {flag} {jx.get('name', code)}")
        status = jx.get("status", "")
        jx_parts.append(f"**Status:** {status}")
        if jx.get("detail"):
            jx_parts.append(jx["detail"])
        jx_parts.append("")
    jx_md = glossarise("\n".join(jx_parts)) if jx_parts else "*Select jurisdictions and run the analysis.*"

    # 4. Token classification
    tc = result.get("token_analysis", {})
    if tc and tc.get("us_classification"):
        is_sec = tc.get("is_security", False)
        sec_word = "**Yes**" if is_sec else ("**Likely**" if tc.get("us_classification") == "security" else "**Unlikely**")
        tc_md = (
            f"**Is your token a security?** {sec_word}\n\n"
            f"Based on the Howey Test, your token is classified as: `{tc.get('us_classification', 'N/A')}`\n\n"
            f"**Howey Test result:** {tc.get('howey_result', 'N/A')}\n\n"
            f"**Under MiCA (EU):** `{tc.get('mica_type', 'N/A')}`\n\n"
            f"**What to do next:**\n"
            f"- Get a formal legal opinion from securities counsel in each target jurisdiction\n"
            f"- {'Register with the SEC or secure an exemption (Reg D/S) before any sale' if is_sec else 'Document your classification analysis for regulatory examination'}\n"
            f"- Prepare a MiCA-compliant whitepaper if targeting the EU"
        )
    else:
        tc_md = "*No token was described. Add a token description above to get a classification.*"
    tc_md = glossarise(tc_md)

    # 5. AML
    aml = result.get("aml_analysis", {})
    aml_parts = []
    has_gaps = bool(aml.get("missing"))
    yes_msg = "**Yes** \u2014 this is mandatory for your activities."
    no_msg = "Assessment pending."
    aml_answer = yes_msg if aml.get("needed") else no_msg
    aml_parts.append(f"**Do you need a KYC/AML program?** {aml_answer}\n")
    if aml.get("needed"):
        aml_parts.append("**What you need:**")
        for item in aml["needed"][:6]:
            aml_parts.append(f"- {item}")
    if has_gaps:
        aml_parts.append("\n**Gaps we found:**")
        for item in aml["missing"]:
            aml_parts.append(f"- \u26A0\uFE0F {item}")
    aml_md = glossarise("\n".join(aml_parts))

    # 6. Licensing roadmap
    lic = result.get("licensing", {})
    lic_parts = []
    for l in lic.get("required_licences", []):
        lic_parts.append(
            f"### {l.get('jurisdiction', '')} \u2014 {l.get('licence_type', '')}\n"
            f"**What it is:** The licence you need to operate legally in this jurisdiction.\n\n"
            f"**Regulator:** {l.get('regulator', 'N/A')}\n\n"
            f"**Timeline:** {l.get('timeline_months', 'TBD')} months\n\n"
            f"**Cost:** {l.get('total_cost_range', 'TBD')}\n\n"
            f"**Why you need it:** Your activities ({', '.join(l.get('triggers', []))}) trigger this requirement.\n"
        )
    if lic.get("sequencing"):
        lic_parts.append("### Recommended order")
        for s in lic["sequencing"]:
            lic_parts.append(f"- {s}")
    lic_md = glossarise("\n".join(lic_parts)) if lic_parts else "*No specific licences identified.*"

    # 7. Enforcement cases
    cases = result.get("enforcement_cases", [])
    case_parts = []
    if cases:
        case_parts.append("*These businesses had activities similar to yours and faced regulatory action. Learning from their mistakes can save you time and money.*\n")
    for c in cases[:5]:
        name = c.get("case_name", c.get("title", ""))
        case_parts.append(f"**{name}**")
        if c.get("outcome"):
            case_parts.append(f"What happened: {c['outcome'][:250]}")
        if c.get("key_lesson"):
            case_parts.append(f"What this means for you: {c['key_lesson'][:250]}")
        case_parts.append("")
    case_md = glossarise("\n".join(case_parts)) if case_parts else "*No closely analogous cases found.*"

    # 8. Action plan
    actions = result.get("action_plan", [])
    action_parts = []
    immediate = [a for a in actions if "[CRITICAL]" in a]
    month1 = [a for a in actions if "[URGENT]" in a or "[HIGH]" in a]
    month3 = [a for a in actions if "[MEDIUM]" in a or "[LOW]" in a]
    if immediate:
        action_parts.append("### This week")
        for a in immediate:
            action_parts.append(f"- [ ] {a.replace('[CRITICAL] ', '')}")
    if month1:
        action_parts.append("\n### Next 30 days")
        for a in month1:
            action_parts.append(f"- [ ] {a.replace('[URGENT] ', '').replace('[HIGH] ', '')}")
    if month3:
        action_parts.append("\n### Next 90 days")
        for a in month3:
            action_parts.append(f"- [ ] {a.replace('[MEDIUM] ', '').replace('[LOW] ', '')}")
    action_md = glossarise("\n".join(action_parts)) if action_parts else "*No action items generated.*"

    # 9. Full markdown report
    full_report = result.get("markdown_report", "")
    full_report += f"\n\n---\n*Analysis completed in {processing_time:.1f}s*"

    # 10. PDF path
    pdf_path = result.get("pdf_path", "")
    pdf_output = pdf_path if pdf_path and os.path.exists(pdf_path) else None

    return (risk_html, summary, jx_md, tc_md, aml_md, lic_md, case_md, action_md, full_report, pdf_output)


# ═══════════════════════════════════════════════════════════════════════════
# BUILD UI
# ═══════════════════════════════════════════════════════════════════════════

with gr.Blocks(theme=gr.themes.Base(), css=CUSTOM_CSS, title="CryptoComply") as demo:
    # Fonts
    gr.HTML(FONT_LINK)

    # ── HERO ──────────────────────────────────────────
    gr.HTML(
        '<div style="text-align:center;padding:40px 20px 8px;">'
        '  <div class="hero-logo"><span class="glyph">\U0001F512</span> CryptoComply</div>'
        '  <div class="hero-tagline">Regulatory intelligence for crypto businesses</div>'
        '  <div class="hero-sub">Covers MiCA \u00b7 SEC \u00b7 MAS \u00b7 FCA \u00b7 VARA \u00b7 FATF</div>'
        '</div>'
        '<div class="teal-divider"></div>'
    )

    if DEMO_MODE:
        gr.HTML(
            '<div style="background:rgba(0,201,167,0.06);border:1px solid rgba(0,201,167,0.18);'
            'border-radius:12px;padding:12px 18px;margin:0 auto 16px;max-width:700px;'
            'color:var(--teal-dim);font-size:13px;text-align:center;">'
            '\u26A0\uFE0F <strong>Demo mode</strong> \u2014 HF_TOKEN not set. '
            'Narrative summaries use templates. Set HF_TOKEN in Space settings for full AI analysis.'
            '</div>'
        )

    with gr.Accordion("\U0001F6C8 Disclaimer", open=False):
        gr.Markdown(DISCLAIMER_TEXT)

    # ── INPUT SECTION ─────────────────────────────────
    gr.HTML('<div style="height:12px;"></div>')
    gr.Markdown("## Tell us about your business", elem_classes=["reveal"])
    gr.Markdown('<span style="color:var(--text-secondary);font-size:14px;">Write in plain language \u2014 no legal knowledge needed</span>')

    business_input = gr.Textbox(
        label="What does your business do?",
        lines=4,
        placeholder="Example: We're launching a crypto exchange in Europe. Users can trade Bitcoin, Ethereum and our own token. We want to serve customers in Germany, UK and Singapore...",
    )
    token_input = gr.Textbox(
        label="Do you have a token or digital asset? (optional)",
        lines=2,
        placeholder="Example: Yes \u2014 a utility token that gives users access to lower trading fees. Holders don't get profits or voting rights...",
    )

    jurisdiction_input = gr.CheckboxGroup(
        label="Where do you want to operate?",
        choices=JURISDICTION_CHOICES,
        value=["European Union", "United States"],
    )
    gr.HTML('<div style="color:var(--text-tertiary);font-size:12px;margin-top:-4px;">Not sure? Select all \u2014 we\u2019ll tell you which apply to you.</div>')

    activity_input = gr.CheckboxGroup(
        label="What will your business do? (check all that apply)",
        choices=ACTIVITY_CHOICES,
    )

    analyse_btn = gr.Button(
        "Analyse my compliance requirements \u2192",
        variant="primary",
        size="lg",
        elem_classes=["cta-btn"],
    )

    # ── ANALYSIS IN PROGRESS ──────────────────────────
    gr.HTML('<div class="teal-divider"></div>')
    gr.HTML('<div style="font-family:\'Sora\',sans-serif;font-size:1.4em;font-weight:600;margin-bottom:4px;">Analysis</div>')
    progress_narration = gr.HTML('<span style="color:var(--text-secondary);font-size:14px;">Click the button above to start.</span>')
    agent_status = gr.HTML(_agent_status_html())
    progress_bar = gr.HTML(_progress_html(0))

    # ── RESULTS ───────────────────────────────────────
    gr.HTML('<div class="teal-divider"></div>')

    # Risk Score
    risk_display = gr.HTML()

    # Executive Summary
    with gr.Accordion("Executive Summary", open=True, elem_classes=["glass"]):
        summary_output = gr.Markdown()

    # Jurisdiction Analysis
    with gr.Accordion("Jurisdiction-by-jurisdiction analysis", open=True, elem_classes=["glass"]):
        jx_output = gr.Markdown()

    # Token Classification
    with gr.Accordion("Token classification", open=True, elem_classes=["glass"]):
        token_output = gr.Markdown()

    # AML
    with gr.Accordion("AML and identity verification", open=True, elem_classes=["glass"]):
        aml_output = gr.Markdown()

    # Enforcement Cases
    with gr.Accordion("Businesses like yours that faced regulatory action", open=False, elem_classes=["glass"]):
        cases_output = gr.Markdown()

    # Licensing Roadmap
    with gr.Accordion("Your licensing journey", open=True, elem_classes=["glass"]):
        licensing_output = gr.Markdown()

    # Action Plan
    with gr.Accordion("What to do next", open=True, elem_classes=["glass"]):
        action_output = gr.Markdown()

    # Export
    gr.HTML('<div class="teal-divider"></div>')
    gr.Markdown("### Download your report")
    pdf_download = gr.File(label="PDF Compliance Report")
    gr.HTML('<div style="color:var(--text-tertiary);font-size:12px;margin-top:6px;">This is general information only. Always consult qualified legal counsel.</div>')

    with gr.Accordion("Full markdown report", open=False, elem_classes=["glass"]):
        full_report_output = gr.Markdown()

    # ── QUICK REFERENCE ───────────────────────────────
    gr.HTML('<div class="teal-divider" style="margin-top:48px;"></div>')
    with gr.Accordion("Quick reference \u2014 jurisdictions, thresholds, Howey Test", open=False, elem_classes=["glass"]):
        gr.Markdown(QUICK_REF)

    # ── ABOUT ─────────────────────────────────────────
    with gr.Accordion("About CryptoComply", open=False, elem_classes=["glass"]):
        gr.Markdown(ABOUT_MD)

    # ── FOOTER ────────────────────────────────────────
    gr.HTML(
        '<div style="text-align:center;padding:40px 20px 24px;color:var(--text-tertiary);font-size:12px;">'
        '<span style="font-family:\'Sora\',sans-serif;font-weight:600;color:var(--text-secondary);">\U0001F512 CryptoComply</span> by Arjit Mathur<br>'
        'Built on: MiCA \u00b7 FATF 2025 \u00b7 SEC Project Crypto \u00b7 MAS DTSP 2025 \u00b7 FCA 2023 \u00b7 VARA'
        '</div>'
    )

    # ── WIRE EVENTS ───────────────────────────────────
    analyse_btn.click(
        fn=run_analysis,
        inputs=[business_input, token_input, jurisdiction_input, activity_input],
        outputs=[
            agent_status,
            progress_bar,
            progress_narration,
            risk_display,
            summary_output,
            jx_output,
            token_output,
            aml_output,
            licensing_output,
            cases_output,
            action_output,
            full_report_output,
            pdf_download,
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════
# LAUNCH
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__" or True:
    is_hf_space = os.environ.get("SPACE_ID") is not None
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
