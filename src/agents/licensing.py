"""Licensing Advisor Agent — recommends licences, costs, timelines, and sequencing.

This agent takes the outputs of the Regulatory Analysis and Token Classification
agents and produces actionable licensing recommendations with real-world cost
estimates, timelines, prerequisites, and optimal sequencing.
"""

from src.agents.regulatory import JURISDICTION_FRAMEWORKS

# Real licence data — costs, timelines, and prerequisites
LICENCE_DATABASE = {
    "US": {
        "MSB (FinCEN)": {
            "regulator": "FinCEN (Financial Crimes Enforcement Network)",
            "timeline_months": "0.5-1",
            "estimated_cost_usd": "0 (registration fee)",
            "total_cost_range": "$5,000 - $25,000 (legal + compliance setup)",
            "prerequisites": [
                "Designate BSA compliance officer",
                "Develop written AML programme",
                "Implement CIP/CDD procedures",
                "Conduct initial BSA/AML risk assessment",
            ],
            "notes": "Registration only — does not include state MTL costs. "
                     "Form 107 filing is free but must be renewed every 2 years.",
        },
        "State MTL (per state)": {
            "regulator": "State banking/financial regulators",
            "timeline_months": "3-12 (varies by state)",
            "estimated_cost_usd": "5,000 - 100,000 per state",
            "total_cost_range": "$50,000 - $1,000,000+ (all 50 states)",
            "prerequisites": [
                "FinCEN MSB registration",
                "Surety bond (amount varies by state, typically $25K-$500K)",
                "Minimum net worth requirements (varies by state)",
                "Background checks for all control persons",
                "Audited financial statements",
                "Comprehensive business plan",
            ],
            "notes": "NY BitLicense is the most expensive and complex ($5K fee, "
                     "12-18 month timeline, extensive capital requirements). "
                     "Consider NMLS multi-state licensing for efficiency.",
        },
        "SEC Reg D Filing": {
            "regulator": "SEC",
            "timeline_months": "0.5 (Form D filing within 15 days of first sale)",
            "estimated_cost_usd": "0 (SEC filing fee)",
            "total_cost_range": "$25,000 - $100,000 (legal + offering docs)",
            "prerequisites": [
                "Qualified legal counsel opinion on Reg D applicability",
                "Offering memorandum / PPM preparation",
                "Investor accreditation verification procedures (506c)",
                "Blue sky compliance in each state",
            ],
            "notes": "Reg D 506(b) allows up to 35 non-accredited investors. "
                     "Reg D 506(c) permits general solicitation but requires "
                     "verification of accredited investor status.",
        },
    },
    "EU": {
        "CASP (MiCA)": {
            "regulator": "National Competent Authority (home Member State)",
            "timeline_months": "3-6",
            "estimated_cost_usd": "50,000 - 150,000",
            "total_cost_range": "€50,000 - €150,000 (legal + application + compliance setup)",
            "prerequisites": [
                "Legal entity established in an EU Member State",
                "Minimum own funds (€50K-€150K depending on services)",
                "Fit-and-proper assessment of management body",
                "Written AML/CFT programme compliant with AMLD",
                "Governance framework with three lines of defence",
                "ICT security arrangements compliant with DORA",
                "Client asset segregation procedures",
                "Complaint handling procedures",
                "Business continuity plan",
                "Crypto-asset white paper (if issuing)",
            ],
            "notes": "Authorisation in one Member State enables passporting across "
                     "all 27 EU/EEA states. France (AMF) and Ireland (CBI) are "
                     "popular home states. Assessment takes 40 working days for "
                     "complete application. Consider grandfathering provisions "
                     "for firms already operating in EU.",
        },
    },
    "UK": {
        "FCA MLR Registration": {
            "regulator": "Financial Conduct Authority (FCA)",
            "timeline_months": "3-6",
            "estimated_cost_usd": "3,000 - 15,000",
            "total_cost_range": "£2,000 - £10,000 (FCA fees) + £20,000 - £80,000 (legal/compliance)",
            "prerequisites": [
                "Company registered in the UK or with UK establishment",
                "Designated MLRO with adequate qualifications",
                "Written AML/CFT policies and procedures",
                "Business-wide ML/TF risk assessment",
                "Fit-and-proper assessment of key individuals",
                "Adequate financial resources",
                "Technology and cyber risk assessment",
            ],
            "notes": "FCA has an approximately 15-20% approval rate for crypto "
                     "registrations. Common rejection reasons: inadequate AML "
                     "controls, unqualified MLROs, insufficient transaction "
                     "monitoring. Registration ≠ FCA authorisation — separate "
                     "regime under FSMA 2023 coming for full authorisation.",
        },
    },
    "SG": {
        "MAS SPI Licence": {
            "regulator": "Monetary Authority of Singapore (MAS)",
            "timeline_months": "6-12",
            "estimated_cost_usd": "80,000 - 200,000",
            "total_cost_range": "SGD 100,000 - SGD 300,000 (capital + legal + compliance)",
            "prerequisites": [
                "Company incorporated in Singapore",
                "Minimum base capital of SGD 100,000",
                "Application fee of SGD 1,000",
                "Designated compliance officer",
                "AML/CFT programme compliant with PSN02",
                "Technology risk management framework",
                "Business plan demonstrating viability",
                "Fit-and-proper assessment of directors and CEO",
            ],
            "notes": "SPI licence for DPT services processing <SGD 3M/month. "
                     "MAS approval rate is approximately 11% — extremely selective. "
                     "Common rejection: inadequate AML, insufficient tech risk controls.",
        },
        "MAS MPI Licence": {
            "regulator": "Monetary Authority of Singapore (MAS)",
            "timeline_months": "6-12",
            "estimated_cost_usd": "200,000 - 500,000",
            "total_cost_range": "SGD 250,000 - SGD 750,000 (capital + legal + compliance)",
            "prerequisites": [
                "Company incorporated in Singapore",
                "Minimum base capital of SGD 250,000",
                "Application fee of SGD 1,500",
                "All SPI prerequisites plus enhanced requirements",
                "Security deposit with MAS",
                "Enhanced technology and cybersecurity controls",
                "Business continuity and disaster recovery plan",
            ],
            "notes": "MPI licence required if DPT services exceed SGD 3M/month "
                     "or SGD 6M/month across all payment services. Higher ongoing "
                     "compliance costs and reporting obligations.",
        },
    },
    "AE": {
        "VARA VASP Licence (Advisory)": {
            "regulator": "Virtual Assets Regulatory Authority (VARA)",
            "timeline_months": "6-12",
            "estimated_cost_usd": "50,000 - 150,000",
            "total_cost_range": "AED 200,000 - AED 600,000 (capital + fees + setup)",
            "prerequisites": [
                "Company established in Dubai (excluding DIFC)",
                "Minimum capital of AED 500,000",
                "Compliance officer and MLRO",
                "AML/CFT programme compliant with VARA Rulebook",
                "Technology governance framework",
                "Professional indemnity insurance",
            ],
            "notes": "Advisory is the lightest VARA licence category. "
                     "Multi-stage licensing process: initial assessment → "
                     "full application → preparatory licence → operational licence.",
        },
        "VARA VASP Licence (Exchange)": {
            "regulator": "Virtual Assets Regulatory Authority (VARA)",
            "timeline_months": "6-12",
            "estimated_cost_usd": "500,000 - 1,500,000",
            "total_cost_range": "AED 2,000,000 - AED 6,000,000 (capital + fees + setup)",
            "prerequisites": [
                "Company established in Dubai (excluding DIFC)",
                "Minimum capital of AED 15,000,000 (~USD 4.1M)",
                "All Advisory prerequisites plus:",
                "Market surveillance systems",
                "Matching engine with proven reliability",
                "Proof-of-reserves capability",
                "Insurance coverage for custody operations",
                "Independent security audit",
            ],
            "notes": "Exchange licence has the highest capital requirement. "
                     "VARA is extremely thorough — expect multiple rounds of "
                     "queries and supplementary information requests.",
        },
        "VARA VASP Licence (Custody)": {
            "regulator": "Virtual Assets Regulatory Authority (VARA)",
            "timeline_months": "6-12",
            "estimated_cost_usd": "200,000 - 600,000",
            "total_cost_range": "AED 800,000 - AED 2,500,000 (capital + fees + setup)",
            "prerequisites": [
                "Company established in Dubai (excluding DIFC)",
                "Minimum capital of AED 5,000,000 (~USD 1.36M)",
                "HSM-based key management infrastructure",
                "Multi-signature or threshold signature schemes",
                "80%+ cold storage requirement",
                "Crime and professional indemnity insurance",
                "Annual independent custody audit",
            ],
            "notes": "Custody licence requires significant infrastructure "
                     "investment in key management and cold storage.",
        },
    },
}

# Optimal sequencing rules
SEQUENCING_RULES = {
    "US_first_if_security": (
        "If the token may be a security, resolve US classification first — "
        "SEC enforcement has global reach and the highest penalties"
    ),
    "EU_passport_advantage": (
        "EU CASP authorisation provides passporting across 27 Member States — "
        "consider obtaining this early to maximise market access"
    ),
    "SG_selective": (
        "Singapore MAS has an ~11% approval rate — begin the application early "
        "and invest heavily in AML/compliance infrastructure before applying"
    ),
    "UK_registration_first": (
        "UK FCA MLR registration is relatively quick and inexpensive — "
        "obtain early to demonstrate regulatory credibility"
    ),
    "AE_parallel": (
        "VARA licensing can proceed in parallel with EU/UK applications — "
        "the multi-stage process allows operations to begin under preparatory licence"
    ),
}


class LicensingAdvisorAgent:
    """Recommends licensing strategies, costs, timelines, and optimal sequencing.

    This agent takes the outputs of the Regulatory Analysis and Token Classification
    agents and produces actionable licensing recommendations with real-world cost
    and timeline estimates based on actual regulatory fee schedules and industry
    experience data.

    Attributes:
        None (stateless agent — all state passed via method arguments).
    """

    def advise(
        self,
        regulatory_analysis: dict,
        token_classification: dict,
        jurisdictions: list[str],
    ) -> dict:
        """Generate licensing recommendations based on regulatory analysis.

        Args:
            regulatory_analysis: Output from RegulatoryAnalysisAgent.analyze().
            token_classification: Output from TokenClassificationAgent.classify().
            jurisdictions: List of target jurisdiction codes.

        Returns:
            Dict containing:
                - required_licences: list of licence recommendation dicts
                - exemptions_available: list of potential exemptions
                - sequencing: list of ordered sequencing recommendations
                - total_estimated_cost: dict with low/high ranges by jurisdiction
        """
        required_licences = []
        exemptions = []
        total_cost = {}

        for jx in jurisdictions:
            jx_analysis = regulatory_analysis.get(jx, {})
            reg_required = jx_analysis.get("registration_required", {})

            jx_licences = self._get_required_licences(jx, reg_required, token_classification)
            required_licences.extend(jx_licences)

            jx_exemptions = self._check_exemptions(jx, token_classification)
            exemptions.extend(jx_exemptions)

            # Calculate costs for this jurisdiction
            low_cost = 0
            high_cost = 0
            for lic in jx_licences:
                low_cost += lic.get("estimated_cost_low_usd", 0)
                high_cost += lic.get("estimated_cost_high_usd", 0)

            total_cost[jx] = {
                "low_usd": low_cost,
                "high_usd": high_cost,
                "display": f"${low_cost:,} - ${high_cost:,}",
            }

        # Generate sequencing recommendations
        sequencing = self._recommend_sequencing(
            jurisdictions, token_classification, required_licences,
        )

        return {
            "required_licences": required_licences,
            "exemptions_available": exemptions,
            "sequencing": sequencing,
            "total_estimated_cost": total_cost,
        }

    def _get_required_licences(
        self,
        jx: str,
        reg_required: dict,
        token_classification: dict,
    ) -> list[dict]:
        """Get the specific licences required in a jurisdiction."""
        licences = []
        jx_db = LICENCE_DATABASE.get(jx, {})

        for licence_type, info in reg_required.items():
            if not info.get("required"):
                continue

            # Find matching licence in database
            licence_data = jx_db.get(licence_type, {})
            if not licence_data:
                # Try partial match
                for db_type, db_data in jx_db.items():
                    if licence_type.lower() in db_type.lower() or db_type.lower() in licence_type.lower():
                        licence_data = db_data
                        licence_type = db_type
                        break

            if licence_data:
                # Parse cost range
                cost_range = licence_data.get("total_cost_range", "$0")
                low, high = self._parse_cost_range(cost_range)

                licences.append({
                    "jurisdiction": jx,
                    "jurisdiction_name": JURISDICTION_FRAMEWORKS.get(jx, {}).get("name", jx),
                    "licence_type": licence_type,
                    "regulator": licence_data.get("regulator", ""),
                    "timeline_months": licence_data.get("timeline_months", "Unknown"),
                    "estimated_cost_usd": licence_data.get("estimated_cost_usd", "Unknown"),
                    "estimated_cost_low_usd": low,
                    "estimated_cost_high_usd": high,
                    "total_cost_range": cost_range,
                    "prerequisites": licence_data.get("prerequisites", []),
                    "notes": licence_data.get("notes", ""),
                    "triggers": info.get("triggers", []),
                })

        # Add special cases based on token classification
        is_security = token_classification.get("is_security", False)
        if is_security and jx == "US":
            # Check if SEC registration already in the list
            has_sec = any(l["licence_type"] == "SEC Reg D Filing" for l in licences)
            if not has_sec and "SEC Reg D Filing" in jx_db:
                sec_data = jx_db["SEC Reg D Filing"]
                low, high = self._parse_cost_range(sec_data.get("total_cost_range", "$0"))
                licences.append({
                    "jurisdiction": "US",
                    "jurisdiction_name": "United States",
                    "licence_type": "SEC Reg D Filing",
                    "regulator": sec_data["regulator"],
                    "timeline_months": sec_data["timeline_months"],
                    "estimated_cost_usd": sec_data["estimated_cost_usd"],
                    "estimated_cost_low_usd": low,
                    "estimated_cost_high_usd": high,
                    "total_cost_range": sec_data["total_cost_range"],
                    "prerequisites": sec_data["prerequisites"],
                    "notes": sec_data["notes"],
                    "triggers": ["Token classified as security under Howey Test"],
                })

        return licences

    def _check_exemptions(self, jx: str, token_classification: dict) -> list[dict]:
        """Check for available regulatory exemptions."""
        exemptions = []

        if jx == "US":
            exemptions.append({
                "jurisdiction": "US",
                "exemption": "Regulation D 506(b) / 506(c)",
                "description": "Private placement to accredited investors. "
                               "506(b): no general solicitation, up to 35 non-accredited. "
                               "506(c): general solicitation permitted, verified accredited only.",
                "applicable_if": "Token is classified as a security",
            })
            exemptions.append({
                "jurisdiction": "US",
                "exemption": "Regulation S",
                "description": "Offshore offering safe harbour — no registration required "
                               "for offers and sales outside the US to non-US persons.",
                "applicable_if": "Token offering excludes US persons with adequate geo-blocking",
            })

        if jx == "EU":
            mica_type = token_classification.get("mica_type", "")
            if mica_type == "utility token":
                exemptions.append({
                    "jurisdiction": "EU",
                    "exemption": "MiCA Article 14 — White Paper Exemptions",
                    "description": "White paper not required if: token offered for free, "
                                   "mining/staking reward, utility token for existing service, "
                                   "offering <€1M over 12 months, or offered only to qualified investors.",
                    "applicable_if": "Token meets specific Article 14 exemption criteria",
                })

        return exemptions

    def _recommend_sequencing(
        self,
        jurisdictions: list[str],
        token_classification: dict,
        required_licences: list[dict],
    ) -> list[str]:
        """Recommend optimal licensing sequencing."""
        sequencing = []
        is_security = token_classification.get("is_security", False)

        # Priority 1: Resolve US classification if security risk
        if is_security and "US" in jurisdictions:
            sequencing.append(
                "1. [IMMEDIATE] Resolve US token classification — obtain formal legal "
                "opinion and file Reg D/S if token is a security. SEC enforcement has "
                "global reach and the highest penalties."
            )

        # Priority 2: Quick wins
        if "UK" in jurisdictions:
            sequencing.append(
                f"{'2' if sequencing else '1'}. [MONTH 1-3] Apply for FCA MLR registration "
                "— relatively quick and affordable, demonstrates regulatory credibility "
                "to other jurisdictions."
            )

        # Priority 3: EU passport
        if "EU" in jurisdictions:
            step_num = len(sequencing) + 1
            sequencing.append(
                f"{step_num}. [MONTH 1-6] Apply for EU CASP authorisation under MiCA — "
                "single licence provides passporting across all 27 EU/EEA Member States. "
                "Choose home state strategically (France, Ireland, or Lithuania common)."
            )

        # Priority 4: VARA (can run in parallel)
        if "AE" in jurisdictions:
            step_num = len(sequencing) + 1
            sequencing.append(
                f"{step_num}. [MONTH 1-6] Begin VARA licensing process in parallel — "
                "multi-stage process allows operations under preparatory licence while "
                "full licence is processed."
            )

        # Priority 5: Singapore (longest, most selective)
        if "SG" in jurisdictions:
            step_num = len(sequencing) + 1
            sequencing.append(
                f"{step_num}. [MONTH 1-12] Apply for MAS PSP licence — start early as "
                "MAS has ~11% approval rate and 6-12 month timeline. Invest heavily in "
                "AML/compliance infrastructure before applying."
            )

        # Priority 6: US state licences (long tail)
        if "US" in jurisdictions:
            step_num = len(sequencing) + 1
            sequencing.append(
                f"{step_num}. [MONTH 3-18] Begin state money transmitter licence applications "
                "via NMLS. Prioritise high-value states (NY, CA, TX, FL) first. NY BitLicense "
                "takes 12-18 months — start immediately."
            )

        if not sequencing:
            sequencing.append(
                "1. Engage qualified legal counsel in each target jurisdiction "
                "to confirm licensing requirements."
            )

        return sequencing

    def _parse_cost_range(self, cost_str: str) -> tuple[int, int]:
        """Parse a cost range string into (low, high) integers."""
        import re
        numbers = re.findall(r'[\d,]+', cost_str.replace(",", ""))
        if len(numbers) >= 2:
            try:
                return int(numbers[0].replace(",", "")), int(numbers[1].replace(",", ""))
            except ValueError:
                pass
        elif len(numbers) == 1:
            try:
                val = int(numbers[0].replace(",", ""))
                return val, val
            except ValueError:
                pass
        return 0, 0
