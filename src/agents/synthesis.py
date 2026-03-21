"""Synthesis Agent — combines all agent outputs into a coherent compliance report.

This is the final agent in the pipeline. It takes the structured outputs from
all specialist agents, builds a prompt for the LLM to generate narrative
analysis, and assembles the complete result dict for the ReportBuilder.
If the LLM is unavailable, it falls back to template-based synthesis.
"""

from src.rag.retriever import Retriever
from src.utils.llm_client import HFInferenceClient
from src.utils.risk_scorer import RiskScorer


class SynthesisAgent:
    """Combines all agent outputs into a unified compliance analysis report.

    This agent is the final stage of the multi-agent pipeline. It:
    1. Collects structured outputs from Token Classifier, AML/KYC, Regulatory,
       and Licensing agents
    2. Builds a context-rich prompt for the LLM
    3. Generates narrative executive summary and jurisdiction assessments
    4. Assembles the final result dict consumed by ReportBuilder

    If the LLM is unavailable or returns an empty response, the agent falls
    back to deterministic template-based synthesis that requires no LLM.

    Attributes:
        risk_scorer: RiskScorer instance for calculating risk scores.
    """

    def __init__(self):
        self.risk_scorer = RiskScorer()

    def synthesize(
        self,
        all_agent_outputs: dict,
        user_inputs: dict,
        llm_client: HFInferenceClient,
        retriever: Retriever,
    ) -> dict:
        """Synthesize all agent outputs into a final compliance report structure.

        Args:
            all_agent_outputs: Dict containing outputs from all agents:
                - token_classification: from TokenClassificationAgent
                - aml_kyc: from AMLKYCAgent
                - regulatory: from RegulatoryAnalysisAgent
                - licensing: from LicensingAdvisorAgent
            user_inputs: Dict with user-provided information:
                - business_description: str
                - token_description: str (optional)
                - activities: list[str]
                - jurisdictions: list[str]
            llm_client: HFInferenceClient for generating narrative text.
            retriever: Retriever for fetching additional context if needed.

        Returns:
            Complete result dict ready for ReportBuilder, containing all
            sections needed for the markdown and PDF reports.
        """
        token_data = all_agent_outputs.get("token_classification", {})
        aml_data = all_agent_outputs.get("aml_kyc", {})
        reg_data = all_agent_outputs.get("regulatory", {})
        licensing_data = all_agent_outputs.get("licensing", {})
        jurisdictions = user_inputs.get("jurisdictions", [])

        # 1. Calculate risk scores
        risk_input = self._build_risk_input(token_data, aml_data, reg_data, jurisdictions)
        risk_scores = self.risk_scorer.score(risk_input)

        # 2. Generate priority actions
        priority_actions = self.risk_scorer.priority_actions(risk_scores, jurisdictions)

        # 3. Identify top risks
        top_risks = self._extract_top_risks(token_data, aml_data, reg_data, risk_scores)

        # 4. Build jurisdiction analysis for report
        jurisdiction_analysis = self._build_jurisdiction_analysis(reg_data, jurisdictions)

        # 5. Build enforcement cases section
        enforcement_cases = self._extract_enforcement_cases(token_data, aml_data)

        # 6. Build AML requirements section
        aml_requirements = self._build_aml_section(aml_data)

        # 7. Build licensing roadmap
        licensing_roadmap = self._build_licensing_roadmap(licensing_data)

        # 8. Build token classification section
        token_section = self._build_token_section(token_data)

        # 9. Generate narrative summary via LLM (or fallback)
        business_summary = self._generate_summary(
            all_agent_outputs, user_inputs, risk_scores, llm_client,
        )

        # 10. Assemble final result
        return {
            "risk_scores": risk_scores,
            "business_summary": business_summary,
            "top_risks": top_risks,
            "jurisdictions": jurisdiction_analysis,
            "token_classification": token_section,
            "aml_requirements": aml_requirements,
            "licensing_roadmap": licensing_roadmap,
            "enforcement_cases": enforcement_cases,
            "priority_actions": priority_actions,
            "query": user_inputs.get("business_description", ""),
        }

    def _build_risk_input(
        self,
        token_data: dict,
        aml_data: dict,
        reg_data: dict,
        jurisdictions: list[str],
    ) -> dict:
        """Build the input dict for the RiskScorer."""
        # Count unlicensed jurisdictions
        unlicensed = []
        for jx, analysis in reg_data.items():
            reg_required = analysis.get("registration_required", {})
            for licence_type, info in reg_required.items():
                if info.get("required"):
                    unlicensed.append(jx)
                    break

        return {
            "unlicensed_jurisdictions": unlicensed,
            "has_aml_program": aml_data.get("aml_program_required", False)
                              and len(aml_data.get("gaps", [])) == 0,
            "is_security_token": token_data.get("is_security", False),
            "is_registered": False,  # Conservative: assume not registered
            "travel_rule_compliant": aml_data.get("travel_rule_applies", False)
                                    and "Travel Rule" not in str(aml_data.get("gaps", [])),
            "has_whitepaper": False,  # Conservative: assume not prepared
            "mica_applies": "EU" in jurisdictions,
            "enforcement_analogies": len(
                [c for c in token_data.get("retrieved_context", [])
                 if c.get("category") in ("enforcement", "precedent")]
            ),
            "has_kyc_procedures": "KYC" not in str(aml_data.get("gaps", [])),
            "has_sanctions_screening": "sanctions" not in str(aml_data.get("gaps", [])).lower(),
            "has_transaction_monitoring": "monitoring" not in str(aml_data.get("gaps", [])).lower(),
            "target_jurisdictions": jurisdictions,
        }

    def _extract_top_risks(
        self,
        token_data: dict,
        aml_data: dict,
        reg_data: dict,
        risk_scores: dict,
    ) -> list[str]:
        """Extract the top 5 risks from all agent outputs."""
        all_risks = []

        # Token classification risks
        for risk in token_data.get("risks", []):
            all_risks.append(risk)

        # AML gaps as risks
        for gap in aml_data.get("gaps", []):
            all_risks.append(gap)

        # Regulatory gaps as risks
        for jx, analysis in reg_data.items():
            for gap in analysis.get("gaps", []):
                all_risks.append(f"[{jx}] {gap}")

        # High-risk factors
        for factor in aml_data.get("high_risk_factors", []):
            all_risks.append(f"High-risk factor: {factor}")

        # Return top 5, prioritising token and licensing risks
        return all_risks[:5] if all_risks else ["No significant risks identified"]

    def _build_jurisdiction_analysis(
        self,
        reg_data: dict,
        jurisdictions: list[str],
    ) -> list[dict]:
        """Build jurisdiction analysis entries for the report."""
        analysis = []

        for jx in jurisdictions:
            jx_data = reg_data.get(jx, {})
            reqs = jx_data.get("key_requirements", [])
            gaps = jx_data.get("gaps", [])
            reg_required = jx_data.get("registration_required", {})

            # Determine status
            has_gaps = len(gaps) > 0
            required_count = sum(
                1 for r in reg_required.values() if r.get("required")
            )

            if required_count > 0 and has_gaps:
                status = "Non-compliant"
            elif required_count > 0:
                status = "Action required"
            else:
                status = "Monitoring"

            # Build detail text
            detail_parts = []
            if jx_data.get("framework"):
                detail_parts.append(f"Framework: {jx_data['framework']}")
            if jx_data.get("regulator"):
                detail_parts.append(f"Regulator: {jx_data['regulator']}")
            if reqs:
                detail_parts.append(f"Key requirements: {'; '.join(reqs[:3])}")
            if gaps:
                detail_parts.append(f"Gaps identified: {'; '.join(gaps)}")

            analysis.append({
                "code": jx,
                "name": jx_data.get("framework", jx),
                "status": status,
                "key_requirements": "; ".join(reqs[:2]) if reqs else "See detailed analysis",
                "gaps": "; ".join(gaps[:2]) if gaps else "None identified",
                "detail": "\n".join(detail_parts),
            })

        return analysis

    def _extract_enforcement_cases(
        self,
        token_data: dict,
        aml_data: dict,
    ) -> list[dict]:
        """Extract enforcement case context from agent outputs."""
        cases = []
        seen_ids = set()

        for ctx in token_data.get("retrieved_context", []):
            if ctx.get("category") in ("enforcement", "precedent"):
                if ctx["id"] not in seen_ids:
                    cases.append(ctx)
                    seen_ids.add(ctx["id"])

        return cases[:5]

    def _build_aml_section(self, aml_data: dict) -> dict:
        """Build the AML/KYC requirements section."""
        return {
            "needed": aml_data.get("kyc_requirements", []),
            "missing": aml_data.get("gaps", []),
            "travel_rule_applies": aml_data.get("travel_rule_applies", False),
            "travel_rule_thresholds": aml_data.get("travel_rule_thresholds", {}),
            "high_risk_factors": aml_data.get("high_risk_factors", []),
            "edd_triggers": aml_data.get("edd_triggers", []),
        }

    def _build_licensing_roadmap(self, licensing_data: dict) -> list[dict]:
        """Build the licensing roadmap section."""
        roadmap = []
        for lic in licensing_data.get("required_licences", []):
            roadmap.append({
                "action": f"Obtain {lic.get('licence_type', 'licence')}",
                "jurisdiction": lic.get("jurisdiction_name", lic.get("jurisdiction", "")),
                "timeline": f"{lic.get('timeline_months', 'TBD')} months",
                "cost": lic.get("total_cost_range", "TBD"),
            })
        return roadmap

    def _build_token_section(self, token_data: dict) -> dict:
        """Build the token classification section."""
        howey = token_data.get("howey_analysis", {})

        # Summarise Howey result
        prongs_met = sum(1 for p in howey.values() if p.get("likely_met"))
        if prongs_met == 4:
            howey_result = "All 4 prongs likely satisfied — HIGH probability of security classification"
        elif prongs_met == 3:
            howey_result = f"{prongs_met}/4 prongs likely satisfied — ELEVATED risk of security classification"
        elif prongs_met == 2:
            howey_result = f"{prongs_met}/4 prongs likely satisfied — MODERATE risk"
        else:
            howey_result = f"{prongs_met}/4 prongs likely satisfied — LOWER risk of security classification"

        # Build implications
        implications_parts = []
        if token_data.get("is_security"):
            implications_parts.append(
                "Token is likely a security under US law. Must register with SEC or "
                "qualify for exemption (Reg D, Reg S, Reg A+) before any offer or sale."
            )
        mica_type = token_data.get("mica_type", "")
        if mica_type:
            implications_parts.append(
                f"Under MiCA, token classified as: {mica_type}. "
                f"Applicable MiCA requirements must be met."
            )

        return {
            "howey_result": howey_result,
            "howey_prongs": howey,
            "mica_type": token_data.get("mica_type", "Not assessed"),
            "us_classification": token_data.get("us_classification", "Not assessed"),
            "eu_classification": token_data.get("eu_classification", "Not assessed"),
            "is_security": token_data.get("is_security", False),
            "implications": " ".join(implications_parts) if implications_parts else "N/A",
            "risks": token_data.get("risks", []),
        }

    def _generate_summary(
        self,
        all_agent_outputs: dict,
        user_inputs: dict,
        risk_scores: dict,
        llm_client: HFInferenceClient,
    ) -> str:
        """Generate an executive summary using the LLM, with template fallback.

        Builds a structured prompt with all agent outputs and asks the LLM
        to generate a narrative summary. If the LLM fails, falls back to
        a deterministic template.
        """
        prompt = self._build_llm_prompt(all_agent_outputs, user_inputs, risk_scores)

        # Attempt LLM generation
        llm_output = llm_client.generate(prompt, max_tokens=1024, temperature=0.1)

        if llm_output and len(llm_output) > 50:
            return llm_output

        # Fallback: template-based synthesis
        return self._template_summary(all_agent_outputs, user_inputs, risk_scores)

    def _build_llm_prompt(
        self,
        all_agent_outputs: dict,
        user_inputs: dict,
        risk_scores: dict,
    ) -> str:
        """Build the structured prompt for the LLM."""
        token_data = all_agent_outputs.get("token_classification", {})
        aml_data = all_agent_outputs.get("aml_kyc", {})
        reg_data = all_agent_outputs.get("regulatory", {})
        licensing_data = all_agent_outputs.get("licensing", {})

        jurisdictions = user_inputs.get("jurisdictions", [])
        overall = risk_scores.get("overall", 0)
        label = self.risk_scorer.risk_label(overall)

        # Build context sections
        context_parts = []

        # Inject 2025 regulatory updates as TOP PRIORITY context
        updates_ctx = all_agent_outputs.get("updates_context", "")
        if updates_ctx:
            context_parts.append(updates_ctx)

        context_parts.append(
            f"BUSINESS DESCRIPTION:\n{user_inputs.get('business_description', 'N/A')}"
        )

        context_parts.append(
            f"RISK SCORES:\n"
            f"Overall: {overall}/100 ({label})\n"
            f"Licensing: {risk_scores.get('licensing', 0)}/100\n"
            f"AML: {risk_scores.get('aml', 0)}/100\n"
            f"Token: {risk_scores.get('token', 0)}/100\n"
            f"Disclosure: {risk_scores.get('disclosure', 0)}/100\n"
            f"Operational: {risk_scores.get('operational', 0)}/100"
        )

        context_parts.append(
            f"TOKEN CLASSIFICATION:\n"
            f"US: {token_data.get('us_classification', 'N/A')}\n"
            f"EU (MiCA): {token_data.get('mica_type', 'N/A')}\n"
            f"Is Security: {token_data.get('is_security', False)}"
        )

        if aml_data.get("gaps"):
            context_parts.append(
                f"AML/KYC GAPS:\n" + "\n".join(f"- {g}" for g in aml_data["gaps"])
            )

        jx_summaries = []
        for jx in jurisdictions:
            jx_info = reg_data.get(jx, {})
            gaps = jx_info.get("gaps", [])
            reqs_count = len(jx_info.get("key_requirements", []))
            jx_summaries.append(f"- {jx}: {reqs_count} requirements, {len(gaps)} gaps")

        if jx_summaries:
            context_parts.append(
                f"JURISDICTION SUMMARY:\n" + "\n".join(jx_summaries)
            )

        required_lics = licensing_data.get("required_licences", [])
        if required_lics:
            lic_strs = [
                f"- {l['jurisdiction']}: {l['licence_type']} ({l.get('timeline_months', '?')} months)"
                for l in required_lics[:5]
            ]
            context_parts.append(
                f"REQUIRED LICENCES:\n" + "\n".join(lic_strs)
            )

        context = "\n\n".join(context_parts)

        prompt = (
            "You are a senior crypto compliance analyst. Based on the following analysis data, "
            "write a professional compliance assessment.\n\n"
            f"{context}\n\n"
            "Write:\n"
            "1. An executive summary (2 paragraphs) describing the business's compliance posture\n"
            "2. The top 5 compliance risks in order of severity (numbered list)\n"
            "3. For each jurisdiction, one paragraph assessment of requirements and gaps\n"
            "4. A recommended 30/60/90 day action plan\n\n"
            "Be specific, cite regulations by name, and prioritise actionable recommendations. "
            "Use professional but accessible language."
        )

        return prompt

    def _template_summary(
        self,
        all_agent_outputs: dict,
        user_inputs: dict,
        risk_scores: dict,
    ) -> str:
        """Fallback template-based summary when LLM is unavailable."""
        token_data = all_agent_outputs.get("token_classification", {})
        aml_data = all_agent_outputs.get("aml_kyc", {})
        reg_data = all_agent_outputs.get("regulatory", {})
        licensing_data = all_agent_outputs.get("licensing", {})

        overall = risk_scores.get("overall", 0)
        label = self.risk_scorer.risk_label(overall)
        jurisdictions = user_inputs.get("jurisdictions", [])

        parts = []

        # Executive summary paragraph 1
        parts.append(
            f"This compliance assessment evaluates the described business across "
            f"{len(jurisdictions)} jurisdiction{'s' if len(jurisdictions) != 1 else ''} "
            f"({', '.join(jurisdictions)}). The overall compliance risk score is "
            f"{overall}/100 ({label}). "
        )

        if token_data.get("is_security"):
            parts.append(
                "The token has been assessed as likely constituting a security under US law "
                "(Howey Test), which triggers registration requirements under the Securities "
                "Act of 1933. "
            )

        gap_count = len(aml_data.get("gaps", []))
        if gap_count > 0:
            parts.append(
                f"{gap_count} AML/KYC compliance gap{'s were' if gap_count != 1 else ' was'} "
                f"identified, requiring immediate attention. "
            )

        # Executive summary paragraph 2
        lic_count = len(licensing_data.get("required_licences", []))
        if lic_count > 0:
            total_cost = licensing_data.get("total_estimated_cost", {})
            cost_parts = []
            for jx, cost in total_cost.items():
                if cost.get("display"):
                    cost_parts.append(f"{jx}: {cost['display']}")

            parts.append(
                f"\n\n{lic_count} licence{'s are' if lic_count != 1 else ' is'} required "
                f"across the target jurisdictions. "
            )
            if cost_parts:
                parts.append(
                    f"Estimated total licensing costs: {'; '.join(cost_parts)}. "
                )

        # Jurisdiction-specific notes
        for jx in jurisdictions:
            jx_info = reg_data.get(jx, {})
            gaps = jx_info.get("gaps", [])
            framework = jx_info.get("framework", jx)
            if gaps:
                parts.append(
                    f"In {jx} ({framework}), {len(gaps)} compliance "
                    f"gap{'s were' if len(gaps) != 1 else ' was'} identified. "
                )

        return "".join(parts)
