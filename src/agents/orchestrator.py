"""Compliance Orchestrator — coordinates all specialist agents in sequence.

This is the top-level entry point for the multi-agent compliance analysis system.
It initialises all components, manages the analysis pipeline, handles caching,
and returns the final structured result for the Gradio UI.
"""

import json
import os
import time

from src.agents.aml_kyc import AMLKYCAgent
from src.agents.licensing import LicensingAdvisorAgent
from src.agents.regulatory import RegulatoryAnalysisAgent
from src.agents.synthesis import SynthesisAgent
from src.agents.token_classifier import TokenClassificationAgent
from src.rag.index_builder import IndexBuilder
from src.rag.retriever import Retriever
from src.utils.cache import ResponseCache
from src.utils.llm_client import HFInferenceClient
from src.utils.report_builder import ReportBuilder
from src.utils.risk_scorer import RiskScorer

# Path to knowledge base JSON files
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")

# Path to 2025 regulatory updates (HIGH PRIORITY — loaded first)
UPDATES_FILE = os.path.join(KNOWLEDGE_DIR, "updates", "regulatory_updates_2025.json")


def _load_2025_updates() -> list[dict]:
    """Load 2025 regulatory updates that override older knowledge base entries."""
    if not os.path.exists(UPDATES_FILE):
        return []
    try:
        with open(UPDATES_FILE, "r", encoding="utf-8") as f:
            updates = json.load(f)
        return updates if isinstance(updates, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def _get_relevant_updates(jurisdictions: list[str], updates: list[dict]) -> list[dict]:
    """Filter 2025 updates relevant to the given jurisdictions."""
    relevant = []
    for update in updates:
        uj = update.get("jurisdiction", "")
        if uj == "GLOBAL" or uj in jurisdictions:
            relevant.append(update)
    return relevant


def _format_updates_context(updates: list[dict]) -> str:
    """Format 2025 updates as high-priority context string for agent prompts."""
    if not updates:
        return ""
    parts = ["[CRITICAL 2025 REGULATORY UPDATES — these override older information]\n"]
    for u in updates:
        parts.append(
            f"• [{u.get('jurisdiction', '??')}] {u.get('title', '')} "
            f"({u.get('date', '')}): {u.get('summary', '')}"
        )
    return "\n".join(parts)

# Quick summary templates for demo mode
QUICK_SUMMARIES = {
    "exchange": {
        "US": (
            "A crypto exchange operating in the US must register as a Money Services Business "
            "(MSB) with FinCEN, implement a full BSA/AML compliance programme, and obtain "
            "state money transmitter licences in each state of operation. The NY BitLicense "
            "is particularly demanding (12-18 months, significant capital requirements). If "
            "the exchange lists tokens that are securities under the Howey Test, it may need "
            "to register as a national securities exchange or ATS with the SEC. Travel Rule "
            "compliance is required for transfers of $3,000+. Key risk: SEC enforcement "
            "actions against Coinbase and Binance demonstrate that major exchanges face "
            "existential regulatory risk if they list unregistered securities."
        ),
        "EU": (
            "Under MiCA (effective December 2024), a crypto exchange must obtain CASP "
            "authorisation from a national competent authority in its home Member State. "
            "This provides passporting across all 27 EU/EEA states. Minimum own funds: "
            "€150,000 for trading platform operators. The Transfer of Funds Regulation "
            "requires Travel Rule compliance for ALL transfers (zero threshold). The "
            "exchange must implement client asset segregation, conduct-of-business rules, "
            "and market abuse surveillance systems. Estimated timeline: 3-6 months. "
            "Estimated cost: €50,000-€150,000 for application and compliance setup."
        ),
        "UK": (
            "A crypto exchange must register with the FCA under the Money Laundering "
            "Regulations 2017. The FCA has an approximately 15-20% approval rate — most "
            "rejections are due to inadequate AML controls. From October 2023, all crypto "
            "promotions must comply with the financial promotions regime: prescribed risk "
            "warnings, 24-hour cooling-off for first-time investors, and appropriateness "
            "assessments. The UK Travel Rule applies from September 2023 (£1,000 threshold). "
            "The Consumer Duty (PS22/9) requires firms to deliver good outcomes for retail "
            "customers. A broader FCA authorisation regime under FSMA 2023 is forthcoming."
        ),
        "SG": (
            "A crypto exchange must obtain a Major Payment Institution (MPI) licence from "
            "MAS under the Payment Services Act 2019. MAS has an approximately 11% approval "
            "rate — the most selective crypto licensing regime globally. Minimum capital: "
            "SGD 250,000. Timeline: 6-12 months. MAS Notice PSN02 mandates comprehensive "
            "AML/CFT controls. The Travel Rule applies for transfers ≥SGD 1,500. Critical: "
            "MAS guidelines (PS-G02) prohibit advertising DPT services to the general public "
            "in Singapore. No social media marketing, no influencer promotions, no sign-up "
            "bonuses. Retail access restrictions are among the strictest globally."
        ),
        "AE": (
            "A crypto exchange must obtain a VARA Exchange Services VASP licence in Dubai. "
            "This is the highest-tier VARA licence with minimum capital of AED 15,000,000 "
            "(~USD 4.1M). The multi-stage licensing process takes 6-12 months. VARA requires "
            "market surveillance systems, matching engine reliability standards, and "
            "proof-of-reserves capability. The VARA AML/CFT Rulebook mandates Travel Rule "
            "compliance for ALL transfers (zero threshold). Marketing must comply with the "
            "VARA Marketing and Promotions Rulebook. Note: VARA jurisdiction covers Dubai "
            "only (excluding DIFC). Abu Dhabi has a separate framework under ADGM/FSRA."
        ),
    },
    "stablecoin": {
        "US": (
            "Stablecoin issuers in the US face a complex regulatory landscape. If the "
            "stablecoin references a single fiat currency, it may be classified as e-money "
            "or a money transmission instrument under state law. FinCEN MSB registration "
            "is required. The SEC may assert jurisdiction if the stablecoin has investment "
            "characteristics (see Bitfinex/Tether $59.5M settlement). Key obligations: "
            "accurate and transparent reserve disclosure, regular independent attestation, "
            "and compliance with state money transmission laws. The Bitfinex/Tether "
            "enforcement action demonstrated that misrepresenting reserve backing carries "
            "severe penalties from both CFTC ($41M) and state regulators (NYAG $18.5M)."
        ),
        "EU": (
            "Under MiCA, a stablecoin pegged to a single currency is an E-Money Token (EMT) "
            "regulated under Articles 48-58. The issuer must be authorised as a credit "
            "institution or e-money institution. EMTs must be issued and redeemable at par "
            "value. No interest may be paid on EMTs. Reserve assets: at least 30% deposited "
            "at credit institutions (60% for significant EMTs). A stablecoin referencing "
            "multiple assets is an Asset-Referenced Token (ART) under Articles 16-47, "
            "requiring separate authorisation, own funds of €350,000 or 2% of reserves, "
            "and comprehensive reserve management. Significant ART/EMT issuers face EBA "
            "supervision and enhanced requirements."
        ),
    },
    "defi": {
        "US": (
            "DeFi protocols face significant US regulatory uncertainty. FinCEN guidance "
            "(FIN-2019-G001) states that DApp developers are generally not money transmitters "
            "if the DApp merely facilitates peer-to-peer transactions. However, the SEC has "
            "asserted that DeFi protocols facilitating securities trading may be unregistered "
            "exchanges. The CFTC has brought enforcement actions against DeFi platforms for "
            "offering unregistered derivatives. Key risks: governance token holders may face "
            "liability if the DAO effectively controls operations. The Tornado Cash OFAC "
            "designation (2022) demonstrated that privacy protocols face extreme sanctions "
            "risk. DAOs holding diversified treasuries may trigger Investment Company Act "
            "registration requirements."
        ),
        "EU": (
            "MiCA does not comprehensively address fully decentralised DeFi protocols. "
            "Recital 22 states that crypto-asset services provided in a fully decentralised "
            "manner without any intermediary should not fall within MiCA's scope. However, "
            "the determination of 'fully decentralised' is fact-specific — protocols with "
            "identifiable teams, governance token holders with significant control, or "
            "fee-collecting mechanisms may still be considered CASPs. The AML framework "
            "applies through the FATF guidance that protocol owners/operators with control "
            "or sufficient influence are VASPs. DeFi front-ends serving EU users likely "
            "fall within MiCA scope even if the underlying protocol is decentralised."
        ),
    },
    "nft": {
        "US": (
            "NFTs face SEC scrutiny when marketed as investments. The SEC brought enforcement "
            "actions against Impact Theory ($6.1M settlement) and Stoner Cats ($1M settlement) "
            "in 2023 for selling NFTs as unregistered securities. Key factors: marketing "
            "NFTs for price appreciation, tiered collections suggesting investment levels, "
            "and tying value to the issuer's ongoing efforts. Purely artistic or collectible "
            "NFTs with no investment marketing are less likely to be securities, but there is "
            "no formal safe harbour. Fractionalised NFTs that pool ownership almost certainly "
            "constitute securities. NFT marketplaces may need to register as exchanges if "
            "they list NFTs classified as securities."
        ),
    },
}


class ComplianceOrchestrator:
    """Top-level orchestrator coordinating all compliance analysis agents.

    Initialises all components (agents, RAG pipeline, LLM client, utilities),
    manages the analysis pipeline, handles caching, and returns structured
    results for the Gradio UI.

    Attributes:
        token_agent: TokenClassificationAgent instance.
        aml_agent: AMLKYCAgent instance.
        regulatory_agent: RegulatoryAnalysisAgent instance.
        licensing_agent: LicensingAdvisorAgent instance.
        synthesis_agent: SynthesisAgent instance.
        retriever: Retriever instance for knowledge base queries.
        llm_client: HFInferenceClient for LLM generation.
        risk_scorer: RiskScorer for risk calculation.
        report_builder: ReportBuilder for markdown/PDF output.
        cache: ResponseCache for query result caching.
    """

    def __init__(self):
        print("[Orchestrator] Initialising CryptoComply compliance system...")

        # Load 2025 regulatory updates FIRST (high priority)
        self._updates_2025 = _load_2025_updates()
        print(f"[Orchestrator] Loaded {len(self._updates_2025)} critical 2025 regulatory updates")

        # Initialise specialist agents
        print("[Orchestrator] Loading specialist agents...")
        self.token_agent = TokenClassificationAgent()
        self.aml_agent = AMLKYCAgent()
        self.regulatory_agent = RegulatoryAnalysisAgent()
        self.licensing_agent = LicensingAdvisorAgent()
        self.synthesis_agent = SynthesisAgent()

        # Build or load FAISS index
        knowledge_path = os.path.abspath(KNOWLEDGE_DIR)
        print(f"[Orchestrator] Knowledge base path: {knowledge_path}")
        index, documents = IndexBuilder.load_or_build(knowledge_path)
        print(f"[Orchestrator] Index ready: {index.ntotal} vectors, {len(documents)} documents")

        # Initialise retriever
        self.retriever = Retriever()
        # Force load since index was just built
        self.retriever._index = index
        self.retriever._documents = documents
        from src.rag.embedder import Embedder
        self.retriever._embedder = Embedder()

        # Initialise utilities
        print("[Orchestrator] Initialising LLM client...")
        self.llm_client = HFInferenceClient()
        self.risk_scorer = RiskScorer()
        self.report_builder = ReportBuilder()
        self.cache = ResponseCache()

        # Print index stats
        stats = self.retriever.get_stats()
        print(f"[Orchestrator] Knowledge base stats:")
        print(f"  Total documents: {stats['total_documents']}")
        print(f"  By jurisdiction: {stats['by_jurisdiction']}")
        print(f"  By category: {stats['by_category']}")

        print("[Orchestrator] System ready.")

    def run(
        self,
        business_description: str,
        jurisdictions: list[str],
        activities: list[str],
        token_description: str = "",
    ) -> dict:
        """Run the full compliance analysis pipeline.

        Args:
            business_description: Natural language description of the business.
            jurisdictions: List of jurisdiction codes (e.g. ["US", "EU", "SG"]).
            activities: List of business activities (e.g. ["exchange", "custody"]).
            token_description: Optional description of a specific token being
                issued or traded.

        Returns:
            Complete result dict containing:
                - summary: str (executive summary text)
                - risk_scores: dict (overall + sub-scores)
                - risk_label: str ("Low"/"Medium"/"High"/"Critical")
                - jurisdiction_analysis: list of jurisdiction dicts
                - token_analysis: dict (Howey + MiCA analysis)
                - aml_analysis: dict (AML/KYC assessment)
                - licensing: dict (licence recommendations)
                - enforcement_cases: list of relevant cases
                - action_plan: list of prioritised actions
                - markdown_report: str (full markdown report)
                - pdf_path: str (path to generated PDF)
                - metadata: dict (jurisdictions, processing time)
        """
        start_time = time.time()

        # 1. Check cache
        cache_key = ResponseCache.make_key(
            business_description, str(sorted(jurisdictions)),
            str(sorted(activities)), token_description,
        )
        cached = self.cache.get(cache_key)
        if cached:
            print("[Orchestrator] Returning cached result")
            return cached

        print("[Orchestrator] Starting compliance analysis...")
        print(f"  Jurisdictions: {jurisdictions}")
        print(f"  Activities: {activities}")
        print(f"  Token: {'Yes' if token_description else 'No'}")

        # 2. Run Token Classification Agent
        token_result = {}
        if token_description:
            print("[Orchestrator] Running Token Classification Agent...")
            token_result = self.token_agent.classify(
                description=token_description,
                jurisdictions=jurisdictions,
                retriever=self.retriever,
            )
            print(f"  US classification: {token_result.get('us_classification')}")
            print(f"  MiCA type: {token_result.get('mica_type')}")
            print(f"  Is security: {token_result.get('is_security')}")
        else:
            print("[Orchestrator] No token description — skipping token classification")

        # 3. Run AML/KYC Agent
        print("[Orchestrator] Running AML/KYC Agent...")
        aml_result = self.aml_agent.analyze(
            business_desc=business_description,
            activities=activities,
            jurisdictions=jurisdictions,
            retriever=self.retriever,
        )
        print(f"  VASP status: {aml_result.get('vasp_status')}")
        print(f"  Travel Rule applies: {aml_result.get('travel_rule_applies')}")
        print(f"  Gaps found: {len(aml_result.get('gaps', []))}")

        # 4. Run Regulatory Analysis Agent
        print("[Orchestrator] Running Regulatory Analysis Agent...")
        reg_result = self.regulatory_agent.analyze(
            business_desc=business_description,
            jurisdictions=jurisdictions,
            activities=activities,
            retriever=self.retriever,
        )
        for jx, analysis in reg_result.items():
            req_count = len(analysis.get("key_requirements", []))
            gap_count = len(analysis.get("gaps", []))
            print(f"  {jx}: {req_count} requirements, {gap_count} gaps")

        # 5. Run Licensing Advisor Agent
        print("[Orchestrator] Running Licensing Advisor Agent...")
        licensing_result = self.licensing_agent.advise(
            regulatory_analysis=reg_result,
            token_classification=token_result,
            jurisdictions=jurisdictions,
        )
        lic_count = len(licensing_result.get("required_licences", []))
        print(f"  Required licences: {lic_count}")
        for lic in licensing_result.get("required_licences", []):
            print(f"    - {lic.get('jurisdiction')}: {lic.get('licence_type')} "
                  f"({lic.get('timeline_months')} months)")

        # 6. Retrieve enforcement cases
        print("[Orchestrator] Retrieving enforcement case analogies...")
        enforcement_cases = self.retriever.retrieve_cases(business_description, k=5)
        case_dicts = []
        for case in enforcement_cases:
            case_dicts.append({
                "case_name": case.metadata.get("case_name", case.metadata.get("title", "")),
                "jurisdiction": case.jurisdiction,
                "outcome": case.metadata.get("outcome", ""),
                "key_lesson": case.metadata.get("key_lesson", ""),
                "score": case.score,
                "title": case.metadata.get("title", case.metadata.get("case_name", "")),
            })
        print(f"  Found {len(case_dicts)} analogous cases")

        # 7. Inject 2025 regulatory updates as high-priority context
        relevant_updates = _get_relevant_updates(jurisdictions, self._updates_2025)
        updates_context = _format_updates_context(relevant_updates)
        if relevant_updates:
            print(f"[Orchestrator] Injecting {len(relevant_updates)} critical 2025 updates")

        # 8. Run Synthesis Agent
        print("[Orchestrator] Running Synthesis Agent...")
        all_outputs = {
            "token_classification": token_result,
            "aml_kyc": aml_result,
            "regulatory": reg_result,
            "licensing": licensing_result,
            "regulatory_updates_2025": relevant_updates,
            "updates_context": updates_context,
        }
        user_inputs = {
            "business_description": business_description,
            "token_description": token_description,
            "activities": activities,
            "jurisdictions": jurisdictions,
        }
        synthesis_result = self.synthesis_agent.synthesize(
            all_agent_outputs=all_outputs,
            user_inputs=user_inputs,
            llm_client=self.llm_client,
            retriever=self.retriever,
        )

        # Inject enforcement cases into synthesis result
        synthesis_result["enforcement_cases"] = case_dicts

        # 8. Build markdown report
        print("[Orchestrator] Building reports...")
        markdown_report = self.report_builder.build_markdown(synthesis_result)

        # 9. Build PDF report
        pdf_path = "/tmp/report.pdf"
        try:
            pdf_bytes = self.report_builder.build_pdf(synthesis_result)
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            print(f"  PDF saved to {pdf_path} ({len(pdf_bytes):,} bytes)")
        except Exception as e:
            import traceback as _tb
            print(f"  PDF generation failed: {e}")
            _tb.print_exc()
            pdf_path = ""

        # 10. Assemble final result
        processing_time = time.time() - start_time
        risk_scores = synthesis_result.get("risk_scores", {})
        overall_score = risk_scores.get("overall", 0)

        result = {
            "summary": synthesis_result.get("business_summary", ""),
            "risk_scores": risk_scores,
            "risk_label": self.risk_scorer.risk_label(overall_score),
            "jurisdiction_analysis": synthesis_result.get("jurisdictions", []),
            "token_analysis": synthesis_result.get("token_classification", {}),
            "aml_analysis": synthesis_result.get("aml_requirements", {}),
            "licensing": licensing_result,
            "enforcement_cases": case_dicts,
            "action_plan": synthesis_result.get("priority_actions", []),
            "markdown_report": markdown_report,
            "pdf_path": pdf_path,
            "metadata": {
                "jurisdictions": jurisdictions,
                "activities": activities,
                "processing_time_s": round(processing_time, 2),
                "token_analyzed": bool(token_description),
                "cached": False,
            },
        }

        # 11. Cache result
        self.cache.set(cache_key, result, ttl_seconds=3600)

        print(f"[Orchestrator] Analysis complete in {processing_time:.1f}s")
        print(f"  Overall risk: {overall_score}/100 ({result['risk_label']})")
        print(f"  Actions: {len(result['action_plan'])}")

        return result

    def get_quick_summary(self, business_type: str, jurisdiction: str) -> str:
        """Return an instant template-based summary for demo mode.

        No LLM call, no agent pipeline — pure template lookup for common
        business type + jurisdiction combinations.

        Args:
            business_type: One of "exchange", "stablecoin", "defi", "nft",
                "lending", "custody", "payment".
            jurisdiction: Single jurisdiction code (e.g. "US", "EU").

        Returns:
            Formatted summary string. Returns a generic message if the
            combination is not in the template database.
        """
        bt = business_type.lower().strip()
        jx = jurisdiction.upper().strip()

        templates = QUICK_SUMMARIES.get(bt, {})
        if jx in templates:
            return templates[jx]

        # Generic fallback
        jx_names = {
            "US": "United States (SEC/FinCEN/CFTC)",
            "EU": "European Union (MiCA)",
            "UK": "United Kingdom (FCA)",
            "SG": "Singapore (MAS)",
            "AE": "UAE/Dubai (VARA)",
        }
        jx_name = jx_names.get(jx, jx)

        return (
            f"A {bt} business operating in {jx_name} is subject to the jurisdiction's "
            f"crypto-asset regulatory framework. Key requirements typically include: "
            f"obtaining the appropriate licence or registration, implementing a comprehensive "
            f"AML/CFT programme with designated compliance officer, conducting KYC/CDD on all "
            f"customers, complying with Travel Rule requirements for cross-border transfers, "
            f"screening against applicable sanctions lists, and maintaining adequate capital "
            f"reserves. For a detailed analysis with specific requirements, risk scoring, "
            f"and action plan, use the full compliance analysis mode above."
        )

    def get_index_stats(self) -> dict:
        """Return knowledge base index statistics for the UI."""
        return self.retriever.get_stats()
