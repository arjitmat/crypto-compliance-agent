"""Regulatory Analysis Agent — jurisdiction-by-jurisdiction compliance assessment.

This agent analyses a described business against the regulatory framework of each
target jurisdiction, retrieves relevant regulatory text, identifies key requirements,
and flags compliance gaps.
"""

from src.rag.retriever import Retriever

# Framework identifiers by jurisdiction
JURISDICTION_FRAMEWORKS = {
    "US": {
        "name": "United States",
        "framework": "SEC / FinCEN / CFTC / State",
        "regulator": "SEC, CFTC, FinCEN, State Regulators (NY DFS)",
        "key_laws": [
            "Securities Act of 1933",
            "Securities Exchange Act of 1934",
            "Bank Secrecy Act (BSA)",
            "Commodity Exchange Act (CEA)",
            "NY BitLicense (23 NYCRR Part 200)",
        ],
    },
    "EU": {
        "name": "European Union",
        "framework": "MiCA (Regulation EU 2023/1114)",
        "regulator": "National Competent Authorities, ESMA, EBA",
        "key_laws": [
            "Markets in Crypto-Assets Regulation (MiCA)",
            "Transfer of Funds Regulation (TFR) 2023/1113",
            "Anti-Money Laundering Directive (AMLD5/6)",
            "MiFID II (for security tokens)",
        ],
    },
    "UK": {
        "name": "United Kingdom",
        "framework": "FCA / FSMA",
        "regulator": "Financial Conduct Authority (FCA)",
        "key_laws": [
            "Financial Services and Markets Act 2000 (FSMA)",
            "Financial Services and Markets Act 2023",
            "Money Laundering Regulations 2017 (MLR)",
            "Financial Promotions Order (SI 2023/612)",
        ],
    },
    "SG": {
        "name": "Singapore",
        "framework": "MAS Payment Services Act",
        "regulator": "Monetary Authority of Singapore (MAS)",
        "key_laws": [
            "Payment Services Act 2019 (amended 2021)",
            "Securities and Futures Act (SFA)",
            "Financial Advisers Act (FAA)",
            "MAS Notice PSN02 (AML/CFT)",
        ],
    },
    "AE": {
        "name": "United Arab Emirates (Dubai)",
        "framework": "VARA",
        "regulator": "Virtual Assets Regulatory Authority (VARA)",
        "key_laws": [
            "Dubai Law No. 4 of 2022",
            "VARA Virtual Assets Regulations 2023",
            "VARA AML/CFT Rulebook",
            "UAE Federal AML Law (Decree-Law No. 20 of 2018)",
        ],
    },
}

# Activities that trigger registration/licensing by jurisdiction
REGISTRATION_TRIGGERS = {
    "US": {
        "MSB (FinCEN)": [
            "exchange", "trading", "transfer", "transmission", "custody",
            "bitcoin atm", "otc", "broker",
        ],
        "SEC Registration": [
            "security token", "securities", "investment contract",
            "exchange for securities", "broker-dealer",
        ],
        "State MTL": [
            "exchange", "transmission", "money transfer",
        ],
    },
    "EU": {
        "CASP (MiCA)": [
            "exchange", "trading", "custody", "transfer", "broker",
            "advice", "portfolio management", "placing",
        ],
    },
    "UK": {
        "FCA MLR Registration": [
            "exchange", "custody", "wallet",
        ],
    },
    "SG": {
        "MAS PSP Licence": [
            "exchange", "trading", "custody", "transfer", "dealing",
            "digital payment token",
        ],
    },
    "AE": {
        "VARA VASP Licence": [
            "exchange", "trading", "custody", "lending", "broker",
            "advisory", "transfer", "management",
        ],
    },
}


class RegulatoryAnalysisAgent:
    """Analyses regulatory requirements for crypto businesses across jurisdictions.

    This agent evaluates a business description against each target jurisdiction's
    regulatory framework, retrieves relevant regulatory text from the knowledge
    base, identifies applicable requirements, and flags compliance gaps.

    Attributes:
        None (stateless agent — all state passed via method arguments).
    """

    def analyze(
        self,
        business_desc: str,
        jurisdictions: list[str],
        activities: list[str],
        retriever: Retriever,
    ) -> dict:
        """Perform jurisdiction-by-jurisdiction regulatory analysis.

        Args:
            business_desc: Natural language description of the business.
            jurisdictions: List of jurisdiction codes to analyse.
            activities: List of business activities performed.
            retriever: Retriever instance for regulatory text retrieval.

        Returns:
            Dict mapping each jurisdiction code to:
                - applies: bool — whether the jurisdiction's framework applies
                - framework: str — name of the applicable framework
                - regulator: str — primary regulator
                - key_requirements: list — specific requirements for this business
                - registration_required: dict — which registrations/licences needed
                - gaps: list — compliance gaps identified
                - retrieved_chunks: list — retrieved regulatory text dicts
        """
        desc_lower = business_desc.lower()
        activities_lower = [a.lower() for a in activities]
        combined_text = f"{desc_lower} {' '.join(activities_lower)}"

        result = {}

        for jx in jurisdictions:
            jx_info = JURISDICTION_FRAMEWORKS.get(jx, {})
            if not jx_info:
                result[jx] = {
                    "applies": False,
                    "framework": "Unknown",
                    "regulator": "Unknown",
                    "key_requirements": [],
                    "registration_required": {},
                    "gaps": [f"Jurisdiction {jx} not in knowledge base"],
                    "retrieved_chunks": [],
                }
                continue

            # Determine if jurisdiction applies
            applies = self._jurisdiction_applies(jx, combined_text)

            # Determine required registrations
            reg_required = self._check_registrations(jx, combined_text)

            # Retrieve relevant regulatory chunks
            retrieved = self._retrieve_regulations(
                business_desc, jx, activities, retriever,
            )

            # Extract key requirements
            key_reqs = self._extract_requirements(jx, combined_text, reg_required)

            # Identify gaps
            gaps = self._identify_gaps(jx, combined_text, reg_required, key_reqs)

            # Format retrieved context
            retrieved_dicts = []
            for doc in retrieved:
                retrieved_dicts.append({
                    "id": doc.id,
                    "text": doc.text[:500],
                    "jurisdiction": doc.jurisdiction,
                    "category": doc.category,
                    "score": doc.score,
                    "tags": doc.tags,
                })

            result[jx] = {
                "applies": applies,
                "framework": jx_info.get("framework", ""),
                "regulator": jx_info.get("regulator", ""),
                "key_laws": jx_info.get("key_laws", []),
                "key_requirements": key_reqs,
                "registration_required": reg_required,
                "gaps": gaps,
                "retrieved_chunks": retrieved_dicts,
            }

        return result

    def _jurisdiction_applies(self, jx: str, combined_text: str) -> bool:
        """Determine if a jurisdiction's regulatory framework applies."""
        # Check for explicit jurisdiction mentions
        jx_keywords = {
            "US": ["united states", "us", "usa", "american", "new york", "delaware"],
            "EU": ["europe", "european", "eu", "germany", "france", "netherlands", "ireland"],
            "UK": ["united kingdom", "uk", "england", "london", "britain"],
            "SG": ["singapore"],
            "AE": ["uae", "dubai", "abu dhabi", "emirates"],
        }

        keywords = jx_keywords.get(jx, [])
        for kw in keywords:
            if kw in combined_text:
                return True

        # If the jurisdiction is in the target list, it applies by default
        return True

    def _check_registrations(self, jx: str, combined_text: str) -> dict:
        """Check which registrations/licences are required in a jurisdiction."""
        triggers = REGISTRATION_TRIGGERS.get(jx, {})
        required = {}

        for licence_type, keywords in triggers.items():
            matched = [kw for kw in keywords if kw in combined_text]
            required[licence_type] = {
                "required": len(matched) > 0,
                "triggers": matched,
            }

        return required

    def _retrieve_regulations(
        self,
        business_desc: str,
        jurisdiction: str,
        activities: list[str],
        retriever: Retriever,
    ) -> list:
        """Retrieve top regulatory documents for a specific jurisdiction."""
        query = f"{business_desc} {' '.join(activities)} regulatory requirements"
        return retriever.retrieve(query, k=8, jurisdiction_filter=[jurisdiction])

    def _extract_requirements(
        self,
        jx: str,
        combined_text: str,
        reg_required: dict,
    ) -> list[str]:
        """Extract key requirements for the business in this jurisdiction."""
        requirements = []

        if jx == "US":
            if reg_required.get("MSB (FinCEN)", {}).get("required"):
                requirements.extend([
                    "Register as Money Services Business with FinCEN (Form 107)",
                    "Implement BSA/AML compliance programme with designated compliance officer",
                    "File CTRs for cash transactions exceeding $10,000",
                    "File SARs for suspicious transactions of $2,000 or more",
                    "Comply with Travel Rule for transfers of $3,000 or more",
                    "Obtain state money transmitter licences in each state of operation",
                ])
            if reg_required.get("SEC Registration", {}).get("required"):
                requirements.extend([
                    "Register securities offering with SEC or qualify for exemption (Reg D/S/A+)",
                    "If operating an exchange: register as national securities exchange or ATS",
                    "If providing advice: register as investment adviser under IAA",
                ])

        elif jx == "EU":
            if reg_required.get("CASP (MiCA)", {}).get("required"):
                requirements.extend([
                    "Obtain CASP authorisation from home Member State competent authority",
                    "Prepare and notify crypto-asset white paper (Article 6/19)",
                    "Meet minimum own funds requirements (€50K-€150K depending on services)",
                    "Implement governance framework with fit-and-proper management body",
                    "Comply with conduct-of-business rules (Article 66)",
                    "Implement client asset segregation (Article 75)",
                    "Comply with Transfer of Funds Regulation for ALL transfers (zero threshold)",
                    "Register with ESMA CASP register",
                ])

        elif jx == "UK":
            if reg_required.get("FCA MLR Registration", {}).get("required"):
                requirements.extend([
                    "Register with FCA under Money Laundering Regulations 2017",
                    "Appoint Money Laundering Reporting Officer (MLRO)",
                    "Comply with financial promotions regime (s.21 FSMA) from Oct 2023",
                    "Include prescribed risk warnings on all crypto promotions",
                    "Implement 24-hour cooling-off period for first-time retail investors",
                    "Conduct appropriateness assessments under COBS 10",
                    "Comply with UK Travel Rule (£1,000 threshold) from Sep 2023",
                    "Comply with Consumer Duty (PS22/9)",
                ])

        elif jx == "SG":
            if reg_required.get("MAS PSP Licence", {}).get("required"):
                requirements.extend([
                    "Obtain MAS Payment Services licence (SPI or MPI based on volume)",
                    "Meet minimum capital requirements (SGD 100K SPI / SGD 250K MPI)",
                    "Comply with MAS Notice PSN02 AML/CFT requirements",
                    "Implement Travel Rule for transfers ≥SGD 1,500",
                    "Comply with retail marketing restrictions (PS-G02) — no public advertising",
                    "Implement customer asset safeguarding under Part 4A",
                    "Comply with technology risk management (TRM Guidelines)",
                ])

        elif jx == "AE":
            if reg_required.get("VARA VASP Licence", {}).get("required"):
                requirements.extend([
                    "Obtain VARA VASP licence for each activity category",
                    "Meet capital requirements (AED 500K to AED 15M depending on activity)",
                    "Comply with VARA AML/CFT Rulebook",
                    "Implement Travel Rule for ALL transfers (zero threshold)",
                    "Comply with Marketing and Promotions Rulebook",
                    "Implement Technology Governance requirements",
                    "Comply with Consumer Protection Rulebook",
                    "Appoint Chief Compliance Officer reporting to board",
                ])

        return requirements

    def _identify_gaps(
        self,
        jx: str,
        combined_text: str,
        reg_required: dict,
        key_reqs: list[str],
    ) -> list[str]:
        """Identify compliance gaps for this jurisdiction."""
        gaps = []

        # Check if any required registration is not mentioned as obtained
        for licence_type, info in reg_required.items():
            if info.get("required"):
                licence_keywords = ["licensed", "registered", "authorised", "authorized", "approved"]
                has_licence = any(kw in combined_text for kw in licence_keywords)
                if not has_licence:
                    gaps.append(
                        f"{licence_type} appears required but no indication of "
                        f"existing registration or licence"
                    )

        # Jurisdiction-specific gap checks
        if jx == "EU" and "white paper" not in combined_text and "whitepaper" not in combined_text:
            if reg_required.get("CASP (MiCA)", {}).get("required"):
                gaps.append("MiCA crypto-asset white paper not mentioned — required before offering")

        if jx == "UK" and "risk warning" not in combined_text:
            if reg_required.get("FCA MLR Registration", {}).get("required"):
                gaps.append("FCA prescribed risk warnings not mentioned — mandatory on all promotions")

        if jx == "SG" and "retail" in combined_text:
            if "marketing restriction" not in combined_text and "advertising" not in combined_text:
                gaps.append(
                    "MAS retail marketing restrictions (PS-G02) not addressed — "
                    "crypto advertising to the general public is prohibited in Singapore"
                )

        return gaps
