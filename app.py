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
# FONTS
# ═══════════════════════════════════════════════════════════════════════════
FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700'
    '&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500'
    '&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
)

# ═══════════════════════════════════════════════════════════════════════════
# CSS — Deep forest glassmorphism with sage-teal accents
# ═══════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = r"""
:root{
  --bg:#060e0b;--s1:#0a1610;--s2:#0f1f17;
  --g:rgba(62,178,127,.05);--gb:rgba(62,178,127,.14);--gh:rgba(62,178,127,.26);
  --a:#3eb27f;--ad:#276b4e;--al:#6ee7b0;
  --gold:#d4a942;--amber:#cf7b2e;--red:#d94545;--green:#34d399;
  --t1:#dceee5;--t2:rgba(220,238,229,.50);--t3:rgba(220,238,229,.25);
  --mono:'JetBrains Mono',monospace;--head:'Sora',system-ui,sans-serif;--body:'DM Sans',system-ui,sans-serif;
}

/* ── BASE ── */
body,.gradio-container,.main,.wrap,.contain{background:var(--bg)!important;color:var(--t1)!important;font-family:var(--body)!important}
.gradio-container{max-width:860px!important;margin:0 auto!important;position:relative}
/* aurora */
.gradio-container::before,.gradio-container::after{content:'';position:fixed;border-radius:50%;pointer-events:none;z-index:0;filter:blur(150px);opacity:.08}
.gradio-container::before{width:800px;height:800px;background:radial-gradient(circle,#3eb27f,transparent 70%);top:-280px;right:-220px;animation:dr 80s ease-in-out infinite alternate}
.gradio-container::after{width:600px;height:600px;background:radial-gradient(circle,#1a5c3a,transparent 70%);bottom:-180px;left:-180px;animation:dr 80s ease-in-out infinite alternate-reverse}
@keyframes dr{0%{transform:translate(0,0)}100%{transform:translate(60px,-40px)}}

/* ── GLASS ── */
.glass{background:rgba(62,178,127,.04)!important;backdrop-filter:blur(20px)!important;-webkit-backdrop-filter:blur(20px)!important;border:1px solid var(--gb)!important;border-radius:16px!important;transition:border-color .3s,box-shadow .3s}
.glass:hover{border-color:var(--gh)!important;box-shadow:0 0 30px rgba(62,178,127,.05)}

/* ── INPUTS ── */
.gr-panel,.gr-box,.gr-form{background:transparent!important;border:none!important}
textarea,input[type="text"],.gr-textbox textarea{
  background:rgba(10,22,16,.7)!important;border:1px solid var(--gb)!important;border-radius:12px!important;
  color:var(--t1)!important;font-family:var(--body)!important;font-size:15px!important;
  padding:14px 16px!important;line-height:1.55!important;
}
textarea:focus,input[type="text"]:focus{border-color:var(--a)!important;box-shadow:0 0 0 3px rgba(62,178,127,.12)!important;outline:none!important}
textarea::placeholder{color:var(--t3)!important}
label,span.svelte-1gfkn6j{color:var(--t2)!important;font-family:var(--body)!important;font-weight:500!important;font-size:13px!important}

/* ── CHECKBOXES — hide native box, pill style ── */
.gr-check-radio{display:flex!important;flex-wrap:wrap!important;gap:7px!important}
.gr-check-radio label{background:rgba(10,22,16,.6)!important;border:1px solid var(--gb)!important;border-radius:100px!important;padding:8px 18px!important;font-size:13px!important;cursor:pointer;transition:all .25s!important}
.gr-check-radio label:hover{border-color:var(--gh)!important;background:rgba(62,178,127,.06)!important}
.gr-check-radio label:has(input:checked){background:rgba(62,178,127,.15)!important;border-color:var(--a)!important;color:var(--al)!important;box-shadow:0 0 12px rgba(62,178,127,.10)}
.gr-check-radio input[type="checkbox"]{display:none!important}

/* ── BUTTON — outlined, not filled ── */
.cta-btn,.gr-button-primary{
  background:transparent!important;color:var(--a)!important;
  font-family:var(--body)!important;font-weight:600!important;font-size:15px!important;
  border:1.5px solid var(--a)!important;border-radius:12px!important;
  padding:14px 32px!important;cursor:pointer;letter-spacing:.02em;transition:all .3s!important;
}
.cta-btn:hover,.gr-button-primary:hover{
  background:var(--a)!important;color:var(--bg)!important;
  box-shadow:0 6px 30px rgba(62,178,127,.22)!important;transform:translateY(-1px)!important;
}

/* ── ACCORDION ── */
.gr-accordion{background:rgba(10,22,16,.4)!important;border:1px solid rgba(62,178,127,.10)!important;border-radius:14px!important;overflow:hidden;margin-bottom:8px!important}
.gr-accordion .label-wrap{color:var(--t1)!important;font-family:var(--body)!important;font-size:14px!important}

/* ── MARKDOWN ── */
.prose,.md,.markdown-text{color:var(--t1)!important;font-family:var(--body)!important;line-height:1.7!important}
.prose h1,.prose h2,.prose h3,.md h1,.md h2,.md h3{font-family:var(--head)!important;color:var(--t1)!important;font-weight:600!important}
.prose strong{color:var(--t1)!important}
.prose table{border-collapse:collapse;width:100%}
.prose th{background:rgba(62,178,127,.06);color:var(--a);padding:9px 12px;text-align:left;font-size:12px;font-weight:500;border-bottom:1px solid var(--gb)}
.prose td{padding:9px 12px;border-bottom:1px solid rgba(62,178,127,.05);font-size:13px}
.prose code{background:rgba(62,178,127,.07);padding:2px 7px;border-radius:5px;color:var(--al);font-family:var(--mono);font-size:12px}

/* ── TOOLTIPS ── */
.tt{color:var(--al);border-bottom:1px dotted rgba(62,178,127,.25);cursor:help;position:relative}
.tt:hover::after{content:attr(data-tip);position:absolute;bottom:calc(100% + 10px);left:50%;transform:translateX(-50%);background:#091a12;border:1px solid var(--gb);color:var(--t1);font-size:12px;font-family:var(--body);line-height:1.5;padding:11px 14px;border-radius:11px;width:270px;z-index:999;pointer-events:none;box-shadow:0 10px 40px rgba(0,0,0,.6)}

/* ── ANIMATIONS ── */
@keyframes su{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
@keyframes pd{0%,100%{opacity:.3;transform:scale(1)}50%{opacity:1;transform:scale(1.4)}}
.pulse{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--a);animation:pd 1.4s ease-in-out infinite;margin-right:6px;vertical-align:middle}

/* ── RISK ── */
.r-low{color:var(--green)!important}.r-mod{color:var(--a)!important}.r-high{color:var(--gold)!important}.r-elev{color:var(--amber)!important}.r-crit{color:var(--red)!important;font-weight:700}

/* ── AGENT CARDS ── */
.ag{display:flex;align-items:center;gap:12px;padding:10px 14px;border-radius:10px;background:rgba(10,22,16,.5);border:1px solid rgba(62,178,127,.08);margin-bottom:5px;font-size:13px}
.ag-n{font-weight:500;color:var(--t1);min-width:130px;font-size:13px}
.ag-t{color:var(--t3);flex:1;font-size:12px}
.ag .done{color:var(--green);font-size:11px}.ag .work{color:var(--a);font-size:11px}.ag .wait{color:var(--t3);font-size:11px}

/* ── PROGRESS ── */
.pbar{background:rgba(62,178,127,.06);border:1px solid rgba(62,178,127,.08);border-radius:100px;height:4px;overflow:hidden;margin-top:10px}
.pfill{height:100%;background:var(--a);border-radius:100px;transition:width .8s ease}

/* ── DIVIDER ── */
.divider{height:1px;margin:28px 0;background:linear-gradient(90deg,transparent,rgba(62,178,127,.12),transparent)}

/* ── FILE UPLOAD — compact ── */
.gr-file{background:rgba(10,22,16,.4)!important;border:1px solid rgba(62,178,127,.10)!important;border-radius:12px!important;min-height:auto!important;max-height:60px!important}
.gr-file .wrap{min-height:auto!important;padding:10px!important}

/* ── HERO ── */
.hero{text-align:center;padding:44px 20px 10px}
.hero-mark{font-family:var(--head);font-weight:700;font-size:2.2em;color:var(--t1);display:flex;align-items:center;gap:12px;justify-content:center}
.hero-mark .dot{width:36px;height:36px;border-radius:9px;background:linear-gradient(135deg,var(--a),#4cc990);display:inline-flex;align-items:center;justify-content:center;font-size:17px;color:var(--bg);box-shadow:0 3px 16px rgba(62,178,127,.20)}
.hero-tag{font-family:var(--body);font-weight:300;font-size:.95em;color:var(--ad);margin-top:5px}
.hero-frame{font-family:var(--mono);font-size:.72em;color:var(--t3);margin-top:6px;letter-spacing:.04em}

/* ── RESPONSIVE ── */
@media(max-width:768px){.hero-mark{font-size:1.6em}.tt:hover::after{width:200px;font-size:11px}}
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
# BUILD UI
# ═══════════════════════════════════════════════════════════════════════════

with gr.Blocks(theme=gr.themes.Base(), css=CUSTOM_CSS, title="CryptoComply") as demo:
    gr.HTML(FONT_LINK)

    # ── HERO ──
    gr.HTML(
        '<div class="hero">'
        '  <div class="hero-mark"><span class="dot">\u26e8</span>CryptoComply</div>'
        '  <div class="hero-tag">Regulatory intelligence for crypto businesses</div>'
        '  <div class="hero-frame">MiCA \u00b7 SEC \u00b7 MAS \u00b7 FCA \u00b7 VARA \u00b7 FATF</div>'
        '</div>'
        '<div class="divider"></div>'
    )

    if DEMO_MODE:
        gr.HTML(
            '<div style="background:rgba(62,178,127,.05);border:1px solid rgba(62,178,127,.15);'
            'border-radius:14px;padding:14px 20px;margin:0 auto 18px;max-width:680px;'
            'color:var(--accent-d);font-size:13px;text-align:center">'
            '\u26a0\ufe0f <strong>Demo mode</strong> \u2014 HF_TOKEN not set. '
            'Summaries use templates. Set HF_TOKEN in Space settings for full AI analysis.'
            '</div>'
        )

    with gr.Accordion("\u24d8 Disclaimer", open=False, elem_classes=["glass"]):
        gr.Markdown(DISCLAIMER)

    # ── INPUT ──
    gr.HTML('<div style="height:16px"></div>')
    gr.HTML(
        '<div style="font-family:var(--head);font-size:1.35em;font-weight:600;margin-bottom:2px">'
        'Tell us about your business</div>'
        '<div style="color:var(--txt2);font-size:14px;margin-bottom:16px">'
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
    jx_in = gr.CheckboxGroup(label="Where do you want to operate?", choices=JURISDICTION_CHOICES, value=["European Union", "United States"])
    gr.HTML('<div style="color:var(--txt3);font-size:12px;margin-top:-4px">Not sure? Select all \u2014 we\u2019ll tell you which apply.</div>')

    act_in = gr.CheckboxGroup(label="What will your business do?", choices=ACTIVITY_CHOICES)

    btn = gr.Button("Analyse my compliance requirements \u2192", variant="primary", size="lg", elem_classes=["cta-btn"])

    # ── ANALYSIS STATUS (compact) ──
    gr.HTML('<div class="divider"></div>')
    narr = gr.HTML('<span style="color:var(--t3);font-size:13px">&nbsp;</span>')
    agents = gr.HTML("")
    pbar = gr.HTML("")

    # ── RESULTS ──
    risk_out = gr.HTML()

    with gr.Accordion("Executive summary", open=True, elem_classes=["glass"]):
        sum_out = gr.Markdown()
    with gr.Accordion("Jurisdiction analysis", open=False, elem_classes=["glass"]):
        jx_out = gr.Markdown()
    with gr.Accordion("Token classification", open=False, elem_classes=["glass"]):
        tok_out = gr.Markdown()
    with gr.Accordion("AML and identity verification", open=False, elem_classes=["glass"]):
        aml_out = gr.Markdown()
    with gr.Accordion("Your licensing journey", open=False, elem_classes=["glass"]):
        lic_out = gr.Markdown()
    with gr.Accordion("What to do next", open=False, elem_classes=["glass"]):
        act_out = gr.Markdown()
    with gr.Accordion("Similar enforcement cases", open=False, elem_classes=["glass"]):
        case_out = gr.Markdown()

    pdf_out = gr.File(label="PDF Report", visible=True)

    with gr.Accordion("Full markdown report", open=False, elem_classes=["glass"]):
        full_out = gr.Markdown()

    # ── REFERENCE & ABOUT ──
    gr.HTML('<div class="divider" style="margin-top:48px"></div>')
    with gr.Accordion("Quick reference \u2014 jurisdictions, thresholds, Howey Test", open=False, elem_classes=["glass"]):
        gr.Markdown(QUICK_REF)
    with gr.Accordion("About CryptoComply", open=False, elem_classes=["glass"]):
        gr.Markdown(ABOUT_MD)

    # ── FOOTER ──
    gr.HTML(
        '<div style="text-align:center;padding:44px 20px 28px;color:var(--txt3);font-size:12px">'
        '<span style="font-family:var(--head);font-weight:600;color:var(--txt2)">\u26e8 CryptoComply</span> by Arjit Mathur<br>'
        'MiCA \u00b7 FATF 2025 \u00b7 SEC Project Crypto \u00b7 MAS DTSP 2025 \u00b7 FCA \u00b7 VARA'
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
