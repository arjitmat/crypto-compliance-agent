"""Aegis — Multi-Agent Crypto Compliance Intelligence Platform.

Gradio application entry point for HuggingFace Spaces.
Single-page vertical flow. Design: deep forest glassmorphism with sage-teal accents.
"""

import os
import re
import traceback

# Fix tokenizer fork crash on macOS (must be before any HF import)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

# Monkey-patch gradio_client schema bug before importing gradio
try:
    import gradio_client.utils as _gc_utils
    _orig_get_type = _gc_utils.get_type
    def _patched_get_type(schema):
        if not isinstance(schema, dict):
            return "str"
        return _orig_get_type(schema)
    _gc_utils.get_type = _patched_get_type

    _orig_json_schema = _gc_utils._json_schema_to_python_type
    def _patched_json_schema(schema, defs=None):
        if not isinstance(schema, dict):
            return "Any"
        return _orig_json_schema(schema, defs)
    _gc_utils._json_schema_to_python_type = _patched_json_schema
except Exception:
    pass

import gradio as gr

# ═══════════════════════════════════════════════════════════════════════════
# COMPLIANCE GLOSSARY  (30 plain-language definitions)
# ═══════════════════════════════════════════════════════════════════════════
COMPLIANCE_GLOSSARY: dict[str, str] = {
    "Howey Test": "A 4-question legal test from a 1946 US court case. If all 4 are YES for your token, the SEC may treat it as a security.",
    "VASP": "Virtual Asset Service Provider — the legal term for crypto businesses. If you run one, you must follow AML rules.",
    "CASP": "Crypto-Asset Service Provider — the EU's term for crypto businesses under MiCA.",
    "Travel Rule": "Requires crypto businesses to share sender and receiver details for transfers above a certain amount.",
    "AML": "Anti-Money Laundering — laws requiring businesses to check users aren't hiding criminal money.",
    "KYC": "Know Your Customer — verifying who your users are by checking ID and address.",
    "EMT": "E-Money Token — under MiCA, a stablecoin pegged to one currency like EUR. Strict rules apply.",
    "ART": "Asset-Referenced Token — under MiCA, a stablecoin backed by multiple assets. Most regulated crypto in the EU.",
    "MiCA": "Markets in Crypto-Assets Regulation — the EU's main crypto law, fully in force from December 2024.",
    "FinCEN": "Financial Crimes Enforcement Network — US Treasury agency regulating crypto money service businesses.",
    "MSB": "Money Services Business — the US category for crypto exchanges. Must register with FinCEN.",
    "MPI Licence": "Major Payment Institution Licence — Singapore's main licence for larger crypto businesses.",
    "DTSP": "Digital Token Service Provider — new Singapore category (June 2025) for crypto firms serving international clients.",
    "VARA": "Virtual Assets Regulatory Authority — Dubai's dedicated crypto regulator.",
    "FCA": "Financial Conduct Authority — the UK's financial regulator. Crypto firms must register for AML.",
    "EDD": "Enhanced Due Diligence — extra identity checks for high-risk customers like politicians.",
    "PEP": "Politically Exposed Person — senior politicians, judges, military officers, or their close associates.",
    "Unhosted Wallet": "A self-controlled crypto wallet (like MetaMask) not held by an exchange.",
    "Whitepaper": "Under MiCA, a legal disclosure document token issuers must publish before launch.",
    "OFAC": "US Treasury's sanctions list. Crypto businesses must screen users against it.",
    "CDD": "Customer Due Diligence — basic identity checks before opening an account.",
    "SAR": "Suspicious Activity Report — filed with the government when a transaction looks criminal.",
    "STR": "Suspicious Transaction Report — same as SAR, used in Singapore and UAE.",
    "BSA": "Bank Secrecy Act — the main US anti-money laundering law applying to crypto exchanges.",
    "ESMA": "European Securities and Markets Authority — maintains the EU CASP register.",
    "Reg D": "Regulation D — US exemption to sell security tokens to accredited investors without full SEC registration.",
    "Reg S": "Regulation S — US exemption for selling tokens to people outside the United States only.",
    "FATF": "Financial Action Task Force — global body setting anti-money laundering standards. 99 countries follow its rules.",
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
# CSS — Premium glassmorphism with aurora orbs, grid overlay, noise texture
# ═══════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500&family=JetBrains+Mono:wght@400;500&display=swap');

/* ══ RESET & BASE ══════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }
body, .gradio-container, .main, .wrap, .contain {
  background: #040d12 !important; color: #e8f4f1 !important;
  font-family: 'DM Sans', sans-serif !important;
}
.gradio-container { max-width: 900px !important; margin: 0 auto !important; position: relative; z-index: 1; }
h1,h2,h3,.prose h1,.prose h2,.prose h3 { font-family: 'Sora', sans-serif !important; color: #e8f4f1 !important; font-weight: 600 !important; }

/* ══ SCROLLBAR ═════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,201,167,0.25); border-radius: 10px; }

/* ══ AMBIENT CONTAINER — 3 aurora orbs + grid + noise ═════════════════ */
#amb {
  position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden;
  background: #040d12;
}
#amb .orb1 {
  position: absolute; top: -12%; right: -8%;
  width: 720px; height: 720px; border-radius: 50%;
  background: radial-gradient(circle, rgba(0,201,167,0.09) 0%, transparent 68%);
  animation: orb-drift-1 22s ease-in-out infinite;
}
#amb .orb2 {
  position: absolute; bottom: -8%; left: -6%;
  width: 580px; height: 580px; border-radius: 50%;
  background: radial-gradient(circle, rgba(0,201,167,0.06) 0%, transparent 68%);
  animation: orb-drift-2 28s ease-in-out infinite;
}
#amb .orb3 {
  position: absolute; top: 38%; left: 52%; transform: translate(-50%,-50%);
  width: 420px; height: 420px; border-radius: 50%;
  background: radial-gradient(circle, rgba(0,201,167,0.035) 0%, transparent 68%);
  animation: orb-drift-3 34s ease-in-out infinite;
}
@keyframes orb-drift-1 { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(-90px,55px) scale(1.05)} }
@keyframes orb-drift-2 { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(55px,-65px) scale(1.08)} }
@keyframes orb-drift-3 { 0%,100%{transform:translate(-50%,-50%) scale(1)} 50%{transform:translate(-50%,-50%) scale(1.18)} }

/* grid overlay */
#amb .grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(0,201,167,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,201,167,0.025) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 20%, transparent 100%);
  -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 20%, transparent 100%);
}

/* noise texture via inline SVG data URI */
#amb .noise {
  position: absolute; inset: 0; opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
  background-repeat: repeat;
}

/* ══ GLASS PANELS ══════════════════════════════════════════════════════ */
.glass, .gr-group, .gradio-group {
  background: rgba(0,201,167,0.025) !important;
  backdrop-filter: blur(24px) saturate(1.3) !important;
  -webkit-backdrop-filter: blur(24px) saturate(1.3) !important;
  border: 1px solid rgba(0,201,167,0.10) !important;
  border-radius: 16px !important;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.glass:hover, .gr-group:hover {
  border-color: rgba(0,201,167,0.22) !important;
  box-shadow: 0 8px 48px rgba(0,201,167,0.07), inset 0 1px 0 rgba(0,201,167,0.08) !important;
}

/* ══ INPUTS ════════════════════════════════════════════════════════════ */
.gr-panel, .gr-box, .gr-form { background: transparent !important; border: none !important; }
textarea, input[type="text"], .gr-textbox textarea {
  background: rgba(4,13,18,0.85) !important;
  border: 1px solid rgba(0,201,167,0.10) !important;
  border-radius: 12px !important;
  color: #e8f4f1 !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  padding: 14px 16px !important;
  line-height: 1.65 !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
textarea:focus, input[type="text"]:focus {
  border-color: #00C9A7 !important;
  box-shadow: 0 0 0 3px rgba(0,201,167,0.08), 0 0 24px rgba(0,201,167,0.06) !important;
  outline: none !important;
}
textarea::placeholder { color: rgba(232,244,241,0.2) !important; }

/* ══ LABELS ════════════════════════════════════════════════════════════ */
label, .gr-label, span.svelte-1gfkn6j {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  color: rgba(232,244,241,0.45) !important;
  letter-spacing: 0.5px !important;
  text-transform: uppercase !important;
}

/* ══ CHECKBOX PILLS — native checkbox hidden, pill with glow ═════════ */
.gr-check-radio, .gr-checkbox-group { display: flex !important; flex-wrap: wrap !important; gap: 8px !important; }
.gr-check-radio input[type="checkbox"], .gr-checkbox-group input[type="checkbox"] { display: none !important; }
.gr-check-radio label, .gr-checkbox-group label {
  background: rgba(4,13,18,0.85) !important;
  border: 1px solid rgba(0,201,167,0.10) !important;
  border-radius: 100px !important;
  padding: 8px 18px !important;
  cursor: pointer !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  color: rgba(232,244,241,0.55) !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
}
.gr-check-radio label:hover, .gr-checkbox-group label:hover {
  border-color: rgba(0,201,167,0.28) !important;
  background: rgba(0,201,167,0.05) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(0,201,167,0.06);
}
.gr-check-radio label:has(input:checked), .gr-checkbox-group label:has(input:checked) {
  background: rgba(0,201,167,0.10) !important;
  border-color: #00C9A7 !important;
  color: #00C9A7 !important;
  box-shadow: 0 0 18px rgba(0,201,167,0.14), inset 0 1px 0 rgba(0,201,167,0.10) !important;
}

/* ══ PRIMARY BUTTON — outlined CTA with glow on hover ════════════════ */
.gr-button-primary {
  background: #00C9A7 !important;
  border: none !important;
  color: #040d12 !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 15px !important;
  border-radius: 12px !important;
  padding: 16px 32px !important;
  letter-spacing: 0.3px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  cursor: pointer !important;
}
.gr-button-primary:hover {
  background: #00ddb8 !important;
  box-shadow: 0 6px 30px rgba(0,201,167,0.3), 0 2px 10px rgba(0,201,167,0.15) !important;
  transform: translateY(-2px) !important;
}
.gr-button-primary:active { transform: translateY(0) !important; box-shadow: 0 2px 10px rgba(0,201,167,0.2) !important; }

/* ══ ACCORDIONS ════════════════════════════════════════════════════════ */
.gr-accordion {
  background: rgba(0,201,167,0.02) !important;
  border: 1px solid rgba(0,201,167,0.08) !important;
  border-radius: 14px !important;
  margin-bottom: 8px !important;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.gr-accordion:hover {
  border-color: rgba(0,201,167,0.18) !important;
  box-shadow: 0 4px 24px rgba(0,201,167,0.04) !important;
}
.gr-accordion > .label-wrap, .gr-accordion .label-wrap {
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: rgba(232,244,241,0.85) !important;
  padding: 14px 18px !important;
}

/* ══ MARKDOWN ══════════════════════════════════════════════════════════ */
.prose, .md, .markdown-text { color: #e8f4f1 !important; font-family: 'DM Sans', sans-serif !important; line-height: 1.75 !important; }
.prose strong { color: #e8f4f1 !important; }
.prose table { border-collapse: collapse; width: 100%; margin: 12px 0; }
.prose th {
  background: rgba(0,201,167,0.06); color: #00C9A7; padding: 10px 14px; text-align: left;
  font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500;
  border-bottom: 1px solid rgba(0,201,167,0.15); text-transform: uppercase; letter-spacing: 0.5px;
}
.prose td { padding: 10px 14px; font-size: 13px; border-bottom: 1px solid rgba(0,201,167,0.05); }
.prose tr:hover td { background: rgba(0,201,167,0.02); }
.prose code {
  background: rgba(0,201,167,0.08); padding: 3px 8px; border-radius: 6px;
  color: #6ee7b0; font-family: 'JetBrains Mono', monospace; font-size: 12px;
  border: 1px solid rgba(0,201,167,0.08);
}

/* ══ TOOLTIPS — fade-up animation ═════════════════════════════════════ */
.tt { color: #6ee7b0; border-bottom: 1px dotted rgba(0,201,167,0.3); cursor: help; position: relative; }
.tt::after {
  content: attr(data-tip); position: absolute; bottom: calc(100% + 10px); left: 50%;
  transform: translateX(-50%) translateY(8px); opacity: 0;
  background: rgba(4,13,18,0.96);
  border: 1px solid rgba(0,201,167,0.18); color: #e8f4f1;
  font-size: 12px; font-family: 'DM Sans', sans-serif; line-height: 1.5;
  padding: 12px 16px; border-radius: 12px; width: 280px; z-index: 999;
  pointer-events: none; box-shadow: 0 14px 48px rgba(0,0,0,0.55), 0 0 24px rgba(0,201,167,0.06);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  transition: opacity 0.25s cubic-bezier(0.4,0,0.2,1), transform 0.25s cubic-bezier(0.4,0,0.2,1);
}
.tt:hover::after {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* ══ ANIMATIONS ════════════════════════════════════════════════════════ */
@keyframes breathe { 0%,100%{opacity:0.7;filter:drop-shadow(0 0 8px rgba(0,201,167,0.2))} 50%{opacity:1;filter:drop-shadow(0 0 18px rgba(0,201,167,0.45))} }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
@keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
@keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
@keyframes pulse-dot { 0%,100%{opacity:0.3;transform:scale(1)} 50%{opacity:1;transform:scale(1.4)} }
.pulse { display:inline-block;width:7px;height:7px;border-radius:50%;background:#00C9A7;animation:pulse-dot 1.4s ease-in-out infinite;margin-right:6px;vertical-align:middle; }

/* ══ RISK COLOURS ══════════════════════════════════════════════════════ */
.r-low{color:#34d399!important} .r-mod{color:#00C9A7!important} .r-high{color:#d4a942!important} .r-elev{color:#cf7b2e!important} .r-crit{color:#d94545!important;font-weight:700}

/* ══ AGENT CARDS ═══════════════════════════════════════════════════════ */
.ag {
  display:flex;align-items:center;gap:14px;padding:12px 16px;border-radius:12px;
  background:rgba(4,13,18,0.7);border:1px solid rgba(0,201,167,0.08);
  margin-bottom:6px;font-family:'DM Sans',sans-serif;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.ag:hover { border-color:rgba(0,201,167,0.18); background:rgba(0,201,167,0.03); }
.ag-n{font-weight:500;color:#e8f4f1;min-width:130px;font-size:13px}
.ag-t{color:rgba(232,244,241,0.3);flex:1;font-size:12px}
.ag .done{color:#34d399;font-size:11px;font-family:'JetBrains Mono',monospace}
.ag .work{color:#00C9A7;font-size:11px}
.ag .wait{color:rgba(232,244,241,0.2);font-size:11px}

/* ══ PROGRESS ══════════════════════════════════════════════════════════ */
.pbar{background:rgba(0,201,167,0.04);border:1px solid rgba(0,201,167,0.06);border-radius:100px;height:3px;overflow:hidden;margin-top:12px}
.pfill{height:100%;background:linear-gradient(90deg,#00C9A7,#6ee7b0);border-radius:100px;transition:width 1s cubic-bezier(0.4,0,0.2,1);
  box-shadow:0 0 8px rgba(0,201,167,0.3);
}

/* ══ SEPARATOR ═════════════════════════════════════════════════════════ */
.sep{height:1px;margin:32px 0;background:linear-gradient(90deg,transparent 5%,rgba(0,201,167,0.10) 50%,transparent 95%)}

/* ══ FILE UPLOAD ═══════════════════════════════════════════════════════ */
.gr-file{background:rgba(4,13,18,0.5)!important;border:1px solid rgba(0,201,167,0.08)!important;border-radius:10px!important;min-height:auto!important;max-height:52px!important}
.gr-file .wrap{min-height:auto!important;padding:8px!important}

/* ══ RESPONSIVE ════════════════════════════════════════════════════════ */
@media(max-width:768px){.tt:hover::after{width:200px;font-size:11px}}
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
Aegis by Arjit Mathur<br>
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
    block_background_fill="#0a1a1f",
    block_background_fill_dark="#0a1a1f",
    block_border_color="rgba(0,201,167,0.18)",
    block_border_color_dark="rgba(0,201,167,0.18)",
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
    input_background_fill="#060f14",
    input_background_fill_dark="#060f14",
    input_border_color="rgba(0,201,167,0.20)",
    input_border_color_dark="rgba(0,201,167,0.20)",
    input_border_color_focus="rgba(0,201,167,0.4)",
    input_border_color_focus_dark="rgba(0,201,167,0.4)",
    input_placeholder_color="rgba(232,244,241,0.25)",
    input_placeholder_color_dark="rgba(232,244,241,0.25)",
    input_radius="10px",
    input_shadow="none",
    input_shadow_dark="none",
    input_shadow_focus="0 0 0 3px rgba(0,201,167,0.08)",
    input_shadow_focus_dark="0 0 0 3px rgba(0,201,167,0.08)",

    # Buttons — solid teal fill so it's unmissable
    button_primary_background_fill="#00C9A7",
    button_primary_background_fill_dark="#00C9A7",
    button_primary_background_fill_hover="#00ddb8",
    button_primary_background_fill_hover_dark="#00ddb8",
    button_primary_text_color="#040d12",
    button_primary_text_color_dark="#040d12",
    button_primary_text_color_hover="#040d12",
    button_primary_text_color_hover_dark="#040d12",
    button_primary_border_color="#00C9A7",
    button_primary_border_color_dark="#00C9A7",
    button_primary_border_color_hover="#00ddb8",
    button_primary_border_color_hover_dark="#00ddb8",
    button_border_width="0px",
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

    summary = f"## Executive Summary\n\n{glossarise(r.get('summary', ''))}"

    fm = {"EU": "\U0001f1ea\U0001f1fa", "US": "\U0001f1fa\U0001f1f8", "SG": "\U0001f1f8\U0001f1ec", "UK": "\U0001f1ec\U0001f1e7", "AE": "\U0001f1e6\U0001f1ea"}
    jp = ["## Jurisdiction Analysis\n"]
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
            f"## Token Classification\n\n**Is your token a security?** {sw}\n\n"
            f"Howey Test: `{tc.get('us_classification','N/A')}` \u00b7 MiCA: `{tc.get('mica_type','N/A')}`\n\n"
            f"{tc.get('howey_result','')}\n\n"
            f"**Next steps:** Get a legal opinion \u00b7 "
            f"{'Register or secure Reg D/S exemption' if sec else 'Document classification analysis'} \u00b7 "
            f"Prepare MiCA whitepaper if targeting EU"
        )
    else:
        tc_md = ""

    aml = r.get("aml_analysis", {})
    ap = ["## AML & Identity Verification\n"]
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
    lp = ["## Licensing Roadmap\n"]
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
    cp = ["## Relevant Enforcement Cases\n"]
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
    axp = ["## Priority Action Plan\n"]
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
# HERO HTML — #amb aurora container + floating shield + brand
# ═══════════════════════════════════════════════════════════════════════════
HERO_HTML = """
<!-- AMBIENT BACKGROUND — visible aurora orbs + grid -->
<div style="position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden">
  <div style="position:absolute;top:-200px;right:-150px;width:800px;height:800px;border-radius:50%;
    background:radial-gradient(circle,rgba(0,201,167,0.15) 0%,rgba(0,201,167,0.03) 40%,transparent 70%);
    animation:od1 20s ease-in-out infinite"></div>
  <div style="position:absolute;bottom:-150px;left:-100px;width:650px;height:650px;border-radius:50%;
    background:radial-gradient(circle,rgba(0,180,150,0.10) 0%,transparent 70%);
    animation:od2 26s ease-in-out infinite"></div>
  <div style="position:absolute;top:30%;left:60%;width:400px;height:400px;border-radius:50%;
    background:radial-gradient(circle,rgba(0,201,167,0.06) 0%,transparent 60%);
    animation:od3 32s ease-in-out infinite"></div>
</div>
<style>
@keyframes od1{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-80px,60px) scale(1.08)}}
@keyframes od2{0%,100%{transform:translate(0,0)}50%{transform:translate(70px,-50px)}}
@keyframes od3{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-50px,40px) scale(1.12)}}
@keyframes hero-in{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
@keyframes shield-glow{0%,100%{filter:drop-shadow(0 0 12px rgba(0,201,167,0.3))}50%{filter:drop-shadow(0 0 28px rgba(0,201,167,0.6))}}
@keyframes shield-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
</style>

<!-- HERO CONTENT -->
<div style="text-align:center;padding:56px 20px 20px;position:relative;z-index:1;animation:hero-in 0.8s ease-out">

  <!-- Shield SVG — large, glowing, floating -->
  <div style="margin-bottom:20px;animation:shield-float 5s ease-in-out infinite">
    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" style="animation:shield-glow 3s ease-in-out infinite">
      <defs>
        <linearGradient id="shg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#00C9A7" stop-opacity="0.4"/>
          <stop offset="100%" stop-color="#00C9A7" stop-opacity="0.1"/>
        </linearGradient>
      </defs>
      <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"
            fill="url(#shg)" stroke="#00C9A7" stroke-width="1"/>
      <path d="M10 12l2 2 4-4" stroke="#00C9A7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </div>

  <!-- Brand name — big, white, Sora -->
  <div style="font-family:'Sora',sans-serif;font-weight:700;font-size:42px;color:#ffffff;letter-spacing:-1px;
    text-shadow:0 0 60px rgba(0,201,167,0.15)">
    Aegis
  </div>

  <!-- Tagline -->
  <div style="font-family:'DM Sans',sans-serif;font-weight:300;font-size:16px;color:#00C9A7;margin-top:6px;opacity:0.7">
    AI-powered regulatory intelligence for crypto businesses
  </div>

  <!-- Framework badges — visible, with real contrast -->
  <div style="display:flex;gap:8px;justify-content:center;margin-top:20px;flex-wrap:wrap">
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;color:#00C9A7;
      background:rgba(0,201,167,0.08);border:1px solid rgba(0,201,167,0.20);border-radius:100px;padding:5px 14px">MiCA</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;color:#00C9A7;
      background:rgba(0,201,167,0.08);border:1px solid rgba(0,201,167,0.20);border-radius:100px;padding:5px 14px">SEC</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;color:#00C9A7;
      background:rgba(0,201,167,0.08);border:1px solid rgba(0,201,167,0.20);border-radius:100px;padding:5px 14px">MAS</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;color:#00C9A7;
      background:rgba(0,201,167,0.08);border:1px solid rgba(0,201,167,0.20);border-radius:100px;padding:5px 14px">FCA</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;color:#00C9A7;
      background:rgba(0,201,167,0.08);border:1px solid rgba(0,201,167,0.20);border-radius:100px;padding:5px 14px">VARA</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;color:#00C9A7;
      background:rgba(0,201,167,0.08);border:1px solid rgba(0,201,167,0.20);border-radius:100px;padding:5px 14px">FATF</span>
  </div>

  <!-- Stat bar — shows scale at a glance -->
  <div style="display:flex;gap:24px;justify-content:center;margin-top:24px;flex-wrap:wrap">
    <div style="text-align:center">
      <div style="font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:#00C9A7">291</div>
      <div style="font-family:'DM Sans',sans-serif;font-size:11px;color:rgba(232,244,241,0.35);margin-top:2px">Regulations indexed</div>
    </div>
    <div style="width:1px;height:36px;background:rgba(0,201,167,0.15)"></div>
    <div style="text-align:center">
      <div style="font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:#00C9A7">5</div>
      <div style="font-family:'DM Sans',sans-serif;font-size:11px;color:rgba(232,244,241,0.35);margin-top:2px">Jurisdictions</div>
    </div>
    <div style="width:1px;height:36px;background:rgba(0,201,167,0.15)"></div>
    <div style="text-align:center">
      <div style="font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:#00C9A7">6</div>
      <div style="font-family:'DM Sans',sans-serif;font-size:11px;color:rgba(232,244,241,0.35);margin-top:2px">AI agents</div>
    </div>
    <div style="width:1px;height:36px;background:rgba(0,201,167,0.15)"></div>
    <div style="text-align:center">
      <div style="font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:#00C9A7">42</div>
      <div style="font-family:'DM Sans',sans-serif;font-size:11px;color:rgba(232,244,241,0.35);margin-top:2px">Enforcement cases</div>
    </div>
  </div>

  <!-- Divider -->
  <div style="height:1px;margin:32px auto 0;max-width:500px;
    background:linear-gradient(90deg,transparent,rgba(0,201,167,0.20),transparent)"></div>
</div>
"""

DEMO_BANNER_HTML = (
    '<div style="background:rgba(0,201,167,0.04);border:1px solid rgba(0,201,167,0.10);'
    'border-radius:12px;padding:12px 20px;margin:0 auto 20px;max-width:600px;'
    'color:rgba(232,244,241,0.55);font-size:13px;font-family:\'DM Sans\',sans-serif;text-align:center;'
    'backdrop-filter:blur(24px) saturate(1.3);-webkit-backdrop-filter:blur(24px) saturate(1.3);">'
    '<span style="color:#00C9A7;">Demo mode</span> \u2014 '
    'HF_TOKEN not set. Set it in Space settings for full AI-generated analysis.'
    '</div>'
)

# ═══════════════════════════════════════════════════════════════════════════
# BUILD UI
# ═══════════════════════════════════════════════════════════════════════════

with gr.Blocks(theme=THEME, css=CUSTOM_CSS, title="Aegis \u2014 Crypto Compliance Intelligence") as demo:

    # ── HERO ──
    gr.HTML(HERO_HTML)

    if DEMO_MODE:
        gr.HTML(DEMO_BANNER_HTML)

    # ── INPUT SECTION ──
    gr.HTML(
        '<div style="margin:20px 0 6px;">'
        '  <div style="font-family:\'Sora\',sans-serif;font-size:20px;font-weight:600;color:#e8f4f1;">'
        '    Tell us about your business</div>'
        '  <div style="font-family:\'DM Sans\',sans-serif;font-size:13px;'
        '    color:rgba(232,244,241,0.35);margin-top:4px;">'
        '    Describe what you do in plain language \u2014 no legal knowledge needed</div>'
        '</div>'
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
        '<div style="font-size:11px;color:rgba(232,244,241,0.20);margin-top:-2px;">'
        'Not sure? Select all \u2014 we\u2019ll tell you which apply.</div>'
    )
    act_in = gr.CheckboxGroup(label="What will your business do?", choices=ACTIVITY_CHOICES)

    # ── CTA BUTTON — solid teal, unmissable ──
    gr.HTML('<div style="height:8px"></div>')
    btn = gr.Button("Analyse my compliance requirements \u2192", variant="primary", size="lg")

    # ── DISCLAIMER — always visible, not hidden in accordion ──
    gr.HTML(
        '<div style="margin:20px 0 8px;padding:12px 16px;border-radius:10px;'
        'background:rgba(0,201,167,0.03);border:1px solid rgba(0,201,167,0.08);'
        'font-family:\'DM Sans\',sans-serif;font-size:11px;color:rgba(232,244,241,0.35);line-height:1.6;">'
        'This tool provides general regulatory information only and does not constitute legal advice. '
        'Always consult qualified legal counsel before making compliance decisions.'
        '</div>'
    )

    # ── ANALYSIS STATUS ──
    gr.HTML('<div class="sep"></div>')
    narr = gr.HTML("")
    agents = gr.HTML("")
    pbar = gr.HTML("")

    # ── RESULTS — all directly visible, no accordions ──
    risk_out = gr.HTML()

    gr.HTML('<div id="results-anchor"></div>')

    sum_out = gr.Markdown()

    gr.HTML('<div class="sep"></div>')
    jx_out = gr.Markdown()

    gr.HTML('<div class="sep"></div>')
    tok_out = gr.Markdown()

    gr.HTML('<div class="sep"></div>')
    aml_out = gr.Markdown()

    gr.HTML('<div class="sep"></div>')
    lic_out = gr.Markdown()

    gr.HTML('<div class="sep"></div>')
    act_out = gr.Markdown()

    gr.HTML('<div class="sep"></div>')
    case_out = gr.Markdown()

    pdf_out = gr.File(label="Download PDF Report", visible=True)

    with gr.Accordion("Full markdown report", open=False):
        full_out = gr.Markdown()

    # ── REFERENCE & ABOUT ──
    gr.HTML('<div class="sep" style="margin-top:40px;"></div>')
    with gr.Accordion("Quick reference \u2014 jurisdictions, thresholds, Howey Test", open=False):
        gr.Markdown(QUICK_REF)
    with gr.Accordion("About Aegis", open=False):
        gr.Markdown(ABOUT_MD)

    # ── FOOTER ──
    gr.HTML(
        '<div style="text-align:center;padding:48px 20px 32px;">'
        '  <div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:6px;">'
        '    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">'
        '      <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"'
        '            fill="none" stroke="rgba(0,201,167,0.3)" stroke-width="1.2"/>'
        '    </svg>'
        '    <span style="font-family:\'Sora\',sans-serif;font-weight:600;font-size:13px;color:rgba(232,244,241,0.4);">Aegis</span>'
        '  </div>'
        '  <div style="font-family:\'DM Sans\',sans-serif;font-size:11px;color:rgba(232,244,241,0.18);">'
        '    by Arjit Mathur</div>'
        '  <div style="font-family:\'JetBrains Mono\',monospace;font-size:9px;color:rgba(232,244,241,0.12);margin-top:6px;letter-spacing:1px;">'
        '    MiCA &middot; FATF &middot; SEC &middot; MAS &middot; FCA &middot; VARA</div>'
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
    is_spaces = os.environ.get("SPACE_ID") is not None
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=not is_spaces,  # share=True locally, False on HF Spaces (not needed there)
    )
