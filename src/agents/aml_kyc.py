"""AML/KYC Analysis Agent — evaluates anti-money laundering and KYC obligations.

This agent determines whether a described business qualifies as a VASP/MSB
under each jurisdiction, identifies applicable Travel Rule thresholds,
KYC requirements, and AML programme obligations. It retrieves relevant
SOP documents and regulatory text to support the analysis.
"""

from src.rag.retriever import Retriever

# Travel Rule thresholds by jurisdiction
TRAVEL_RULE_THRESHOLDS = {
    "US": {"amount": "$3,000", "basis": "31 CFR 1010.410(f)", "note": "FinCEN proposed lowering to $250 for CVC (not finalized)"},
    "EU": {"amount": "€0 (all transfers)", "basis": "TFR Regulation 2023/1113", "note": "No de minimis threshold — stricter than FATF"},
    "UK": {"amount": "£1,000", "basis": "MLR 2017 (Amendment) 2022", "note": "Effective September 2023"},
    "SG": {"amount": "SGD 1,500", "basis": "MAS Notice PSN02 Para. 13A", "note": "Aligned with FATF threshold"},
    "AE": {"amount": "AED 0 (all transfers)", "basis": "VARA AML/CFT Rulebook Ch. 5", "note": "Zero threshold — all transfers require compliance"},
}

# Activities that make a business a VASP/MSB by jurisdiction
VASP_ACTIVITIES = {
    "US": [
        "exchange of virtual currency for fiat",
        "exchange of virtual currency for other virtual currency",
        "transmission of virtual currency",
        "custody of virtual currency",
        "operating a crypto exchange",
        "operating a bitcoin atm",
    ],
    "EU": [
        "custody and administration of crypto-assets",
        "operation of a trading platform",
        "exchange of crypto-assets for funds",
        "exchange of crypto-assets for other crypto-assets",
        "execution of orders",
        "placing of crypto-assets",
        "providing advice on crypto-assets",
        "portfolio management of crypto-assets",
        "transfer services for crypto-assets",
    ],
    "UK": [
        "exchange of cryptoassets for money",
        "exchange of money for cryptoassets",
        "exchange of one cryptoasset for another",
        "safeguarding or administering cryptoassets",
    ],
    "SG": [
        "dealing in digital payment tokens",
        "facilitating exchange of digital payment tokens",
        "facilitating transmission of digital payment tokens",
    ],
    "AE": [
        "exchange services",
        "broker-dealer services",
        "custody services",
        "lending and borrowing services",
        "management and investment services",
        "transfer and settlement services",
        "advisory services",
    ],
}

# High-risk indicators for enhanced due diligence
HIGH_RISK_INDICATORS = [
    "privacy coins",
    "monero",
    "zcash",
    "mixing",
    "tumbling",
    "tornado cash",
    "pep",
    "politically exposed",
    "sanctioned jurisdiction",
    "iran",
    "north korea",
    "syria",
    "cuba",
    "crimea",
    "high value transaction",
    "anonymous",
    "unhosted wallet",
    "self-custodial",
    "peer-to-peer",
    "otc",
    "over the counter",
    "no kyc",
    "darknet",
    "ransomware",
]


class AMLKYCAgent:
    """Analyzes AML/KYC compliance obligations for crypto businesses.

    This agent evaluates whether a business qualifies as a VASP or MSB,
    determines Travel Rule applicability and thresholds, identifies KYC
    requirements and AML programme needs, and flags high-risk factors
    that trigger enhanced due diligence.

    Attributes:
        None (stateless agent — all state passed via method arguments).
    """

    def analyze(
        self,
        business_desc: str,
        activities: list[str],
        jurisdictions: list[str],
        retriever: Retriever,
    ) -> dict:
        """Analyze AML/KYC obligations for the described business.

        Args:
            business_desc: Natural language description of the business
                and its operations.
            activities: List of specific activities the business performs
                (e.g. ["exchange", "custody", "lending"]).
            jurisdictions: List of jurisdiction codes where the business
                operates or plans to operate.
            retriever: Retriever instance for fetching SOP and regulatory context.

        Returns:
            Dict containing:
                - vasp_status: dict per jurisdiction, whether business is a VASP/MSB
                - travel_rule_applies: bool
                - travel_rule_thresholds: dict of thresholds by jurisdiction
                - kyc_requirements: list of required KYC procedures
                - aml_program_required: bool
                - edd_triggers: list of conditions triggering enhanced due diligence
                - high_risk_factors: list of identified high-risk factors
                - gaps: list of compliance gaps identified
                - retrieved_sops: list of retrieved SOP document dicts
        """
        desc_lower = business_desc.lower()
        activities_lower = [a.lower() for a in activities]
        combined_text = f"{desc_lower} {' '.join(activities_lower)}"

        # 1. VASP/MSB classification per jurisdiction
        vasp_status = self._classify_vasp(combined_text, activities_lower, jurisdictions)

        # 2. Travel Rule assessment
        travel_rule_applies = any(vasp_status.values())
        travel_rule_thresholds = self._get_travel_rule_thresholds(jurisdictions)

        # 3. KYC requirements
        kyc_requirements = self._determine_kyc_requirements(vasp_status, jurisdictions)

        # 4. AML programme assessment
        aml_program_required = any(vasp_status.values())

        # 5. EDD triggers
        edd_triggers = self._identify_edd_triggers(combined_text, jurisdictions)

        # 6. High-risk factors
        high_risk_factors = self._identify_high_risk_factors(combined_text)

        # 7. Retrieve relevant SOPs
        retrieved_sops = self._retrieve_sops(business_desc, activities, retriever)

        # 8. Retrieve regulatory context
        retrieved_regs = self._retrieve_aml_regulations(business_desc, jurisdictions, retriever)

        # 9. Identify gaps
        gaps = self._identify_gaps(
            vasp_status, travel_rule_applies, aml_program_required,
            combined_text, jurisdictions,
        )

        # Combine retrieved context
        all_retrieved = []
        for doc in retrieved_sops:
            all_retrieved.append({
                "id": doc.id,
                "text": doc.text[:500],
                "jurisdiction": doc.jurisdiction,
                "category": doc.category,
                "score": doc.score,
            })
        for doc in retrieved_regs:
            all_retrieved.append({
                "id": doc.id,
                "text": doc.text[:500],
                "jurisdiction": doc.jurisdiction,
                "category": doc.category,
                "score": doc.score,
            })

        return {
            "vasp_status": vasp_status,
            "travel_rule_applies": travel_rule_applies,
            "travel_rule_thresholds": travel_rule_thresholds,
            "kyc_requirements": kyc_requirements,
            "aml_program_required": aml_program_required,
            "edd_triggers": edd_triggers,
            "high_risk_factors": high_risk_factors,
            "gaps": gaps,
            "retrieved_sops": all_retrieved,
        }

    def _classify_vasp(
        self,
        combined_text: str,
        activities: list[str],
        jurisdictions: list[str],
    ) -> dict:
        """Determine if the business qualifies as a VASP/MSB in each jurisdiction.

        Returns dict mapping jurisdiction code to bool.
        """
        result = {}

        for jx in jurisdictions:
            vasp_activities = VASP_ACTIVITIES.get(jx, [])
            is_vasp = False

            for va in vasp_activities:
                if va in combined_text:
                    is_vasp = True
                    break

            # Also check generic activity keywords
            generic_vasp_keywords = [
                "exchange", "trading platform", "custody", "wallet",
                "transfer", "broker", "lending", "staking",
            ]
            if not is_vasp:
                for kw in generic_vasp_keywords:
                    if kw in combined_text:
                        is_vasp = True
                        break

            result[jx] = is_vasp

        return result

    def _get_travel_rule_thresholds(self, jurisdictions: list[str]) -> dict:
        """Return applicable Travel Rule thresholds for each jurisdiction."""
        thresholds = {}
        for jx in jurisdictions:
            if jx in TRAVEL_RULE_THRESHOLDS:
                thresholds[jx] = TRAVEL_RULE_THRESHOLDS[jx]
            else:
                thresholds[jx] = {
                    "amount": "FATF default: $1,000/€1,000",
                    "basis": "FATF Recommendation 16",
                    "note": "Jurisdiction-specific threshold not mapped",
                }
        return thresholds

    def _determine_kyc_requirements(
        self,
        vasp_status: dict,
        jurisdictions: list[str],
    ) -> list[str]:
        """Determine KYC requirements based on VASP status and jurisdictions."""
        requirements = []

        if any(vasp_status.values()):
            # Core CDD requirements (universal)
            requirements.extend([
                "Customer Identification Programme (CIP) — collect and verify name, "
                "date of birth, address, and government-issued ID for all individuals",
                "Beneficial Ownership identification — identify and verify all UBOs "
                "with 25%+ ownership or control of legal entity customers",
                "Sanctions screening — screen all customers against OFAC SDN, "
                "EU Consolidated List, UN Sanctions List, and applicable local lists",
                "PEP screening — screen customers and beneficial owners against "
                "PEP databases and apply EDD where PEP status is identified",
                "Ongoing transaction monitoring — implement rule-based and "
                "blockchain analytics monitoring for suspicious activity",
                "SAR/STR filing — file suspicious activity reports with the "
                "relevant FIU when suspicion is identified",
                "Record keeping — maintain all CDD records for minimum 5 years "
                "(8 years in UAE) after end of business relationship",
            ])

            # Jurisdiction-specific requirements
            if vasp_status.get("US"):
                requirements.append(
                    "US: Register as MSB with FinCEN (Form 107). Implement BSA "
                    "compliance programme. File CTRs for cash transactions >$10,000. "
                    "File SARs for suspicious transactions >$2,000."
                )

            if vasp_status.get("EU"):
                requirements.append(
                    "EU: Comply with AMLD5/6 as an obliged entity. Implement "
                    "risk-based CDD. Apply Transfer of Funds Regulation to ALL "
                    "crypto-asset transfers (zero threshold)."
                )

            if vasp_status.get("UK"):
                requirements.append(
                    "UK: Register with FCA under MLR 2017. Appoint MLRO. "
                    "File SARs with NCA. Comply with UK Travel Rule (£1,000 threshold)."
                )

            if vasp_status.get("SG"):
                requirements.append(
                    "SG: Comply with MAS Notice PSN02. Implement Travel Rule "
                    "for transfers ≥SGD 1,500. File STRs with STRO."
                )

            if vasp_status.get("AE"):
                requirements.append(
                    "AE: Comply with VARA AML/CFT Rulebook. Appoint MLRO. "
                    "Implement Travel Rule for ALL transfers (zero threshold). "
                    "Maintain records for 8 years."
                )

        # Crypto-specific requirements
        requirements.append(
            "Wallet address screening — screen all deposit and withdrawal addresses "
            "against blockchain analytics databases for sanctions, darknet, "
            "ransomware, and mixer exposure"
        )

        return requirements

    def _identify_edd_triggers(self, combined_text: str, jurisdictions: list[str]) -> list[str]:
        """Identify conditions that would trigger Enhanced Due Diligence."""
        triggers = [
            "Customer identified as a Politically Exposed Person (PEP) or close associate",
            "Customer resident in or connected to FATF grey-list or black-list jurisdiction",
            "Complex or opaque corporate ownership structure",
            "Transaction patterns inconsistent with customer's stated purpose or profile",
            "Correspondent VASP relationships with entities in high-risk jurisdictions",
        ]

        if any(kw in combined_text for kw in ["privacy coin", "monero", "zcash"]):
            triggers.append(
                "Transactions involving privacy-enhanced cryptocurrencies (Monero, Zcash) — "
                "enhanced source of funds verification required"
            )

        if any(kw in combined_text for kw in ["mixing", "tumbling", "tornado"]):
            triggers.append(
                "Customer funds with exposure to mixing/tumbling services — "
                "mandatory enhanced investigation and MLRO review"
            )

        if any(kw in combined_text for kw in ["unhosted", "self-custodial", "non-custodial"]):
            triggers.append(
                "Transfers to/from unhosted wallets — risk assessment required, "
                "ownership verification recommended (EU TFR: mandatory for >€1,000)"
            )

        return triggers

    def _identify_high_risk_factors(self, combined_text: str) -> list[str]:
        """Identify high-risk factors present in the business description."""
        factors = []
        for indicator in HIGH_RISK_INDICATORS:
            if indicator in combined_text:
                factor_descriptions = {
                    "privacy coins": "Business involves privacy-enhanced cryptocurrencies",
                    "monero": "Monero (XMR) transactions — limited blockchain traceability",
                    "zcash": "Zcash (ZEC) transactions — shielded transactions not auditable",
                    "mixing": "Mixing/tumbling service involvement detected",
                    "tumbling": "Tumbling service involvement detected",
                    "tornado cash": "Tornado Cash interaction — OFAC-sanctioned protocol",
                    "pep": "Politically Exposed Person involvement",
                    "politically exposed": "Politically Exposed Person involvement",
                    "sanctioned jurisdiction": "Operations in or connected to sanctioned jurisdiction",
                    "iran": "Connection to Iran — comprehensive OFAC sanctions apply",
                    "north korea": "Connection to North Korea — comprehensive sanctions apply",
                    "syria": "Connection to Syria — comprehensive OFAC sanctions apply",
                    "cuba": "Connection to Cuba — comprehensive OFAC sanctions apply",
                    "crimea": "Connection to Crimea region — sanctions apply",
                    "anonymous": "Anonymous or pseudonymous customer interaction",
                    "unhosted wallet": "Unhosted wallet transfers — no counterparty VASP for Travel Rule",
                    "self-custodial": "Self-custodial wallet interaction",
                    "peer-to-peer": "Peer-to-peer transactions — heightened AML risk",
                    "otc": "OTC (over-the-counter) trading — higher ML risk",
                    "over the counter": "OTC trading operations",
                    "no kyc": "Operations described as no-KYC — non-compliant",
                    "darknet": "Darknet marketplace connection",
                    "ransomware": "Ransomware connection",
                }
                desc = factor_descriptions.get(indicator, f"High-risk indicator: {indicator}")
                if desc not in factors:
                    factors.append(desc)

        return factors

    def _identify_gaps(
        self,
        vasp_status: dict,
        travel_rule_applies: bool,
        aml_program_required: bool,
        combined_text: str,
        jurisdictions: list[str],
    ) -> list[str]:
        """Identify compliance gaps based on the analysis."""
        gaps = []

        if aml_program_required:
            aml_keywords = ["aml program", "aml policy", "anti-money laundering", "compliance program"]
            has_aml = any(kw in combined_text for kw in aml_keywords)
            if not has_aml:
                gaps.append(
                    "No AML/CFT programme mentioned — a comprehensive programme with "
                    "designated MLRO is required in all jurisdictions where the business "
                    "qualifies as a VASP/MSB"
                )

        if travel_rule_applies:
            travel_keywords = ["travel rule", "originator information", "beneficiary information"]
            has_travel = any(kw in combined_text for kw in travel_keywords)
            if not has_travel:
                gaps.append(
                    "Travel Rule compliance not addressed — implementation of a Travel "
                    "Rule protocol (TRISA, Notabene, Sygna) is required for transfers "
                    "above applicable thresholds"
                )

        kyc_keywords = ["kyc", "know your customer", "identity verification", "customer due diligence"]
        has_kyc = any(kw in combined_text for kw in kyc_keywords)
        if not has_kyc and any(vasp_status.values()):
            gaps.append(
                "KYC/CDD procedures not described — customer identification and "
                "verification is a fundamental requirement for all VASPs/MSBs"
            )

        sanctions_keywords = ["sanctions", "ofac", "sdn", "screening"]
        has_sanctions = any(kw in combined_text for kw in sanctions_keywords)
        if not has_sanctions and any(vasp_status.values()):
            gaps.append(
                "Sanctions screening not mentioned — screening against OFAC SDN, "
                "EU, UN, and UK sanctions lists is mandatory and operates on strict "
                "liability in the US"
            )

        monitoring_keywords = ["monitoring", "transaction monitoring", "blockchain analytics"]
        has_monitoring = any(kw in combined_text for kw in monitoring_keywords)
        if not has_monitoring and any(vasp_status.values()):
            gaps.append(
                "Transaction monitoring not described — ongoing monitoring with "
                "blockchain analytics is required to detect suspicious activity "
                "and meet SAR filing obligations"
            )

        return gaps

    def _retrieve_sops(
        self,
        business_desc: str,
        activities: list[str],
        retriever: Retriever,
    ) -> list:
        """Retrieve relevant SOP documents."""
        query = f"AML KYC compliance procedures {' '.join(activities)} {business_desc}"
        return retriever.retrieve_sop(query, k=6)

    def _retrieve_aml_regulations(
        self,
        business_desc: str,
        jurisdictions: list[str],
        retriever: Retriever,
    ) -> list:
        """Retrieve relevant AML regulatory documents."""
        query = f"AML CFT requirements VASP money laundering {business_desc}"
        return retriever.retrieve(query, k=6, jurisdiction_filter=jurisdictions)
