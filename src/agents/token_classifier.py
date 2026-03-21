"""Token Classification Agent — analyses digital assets under Howey Test and MiCA framework.

This agent evaluates a described token or digital asset against US securities law
(Howey Test, SEC Framework 2019) and EU MiCA classification criteria. It retrieves
relevant regulatory text and enforcement precedents to support the analysis.
"""

from src.rag.retriever import Retriever

# Keywords indicating each Howey prong is likely satisfied
HOWEY_PRONG_INDICATORS = {
    "investment_of_money": [
        "purchase", "buy", "invest", "contribute", "fund", "pay", "exchange",
        "sale", "offering", "raise capital", "ICO", "IDO", "token sale",
    ],
    "common_enterprise": [
        "pool", "treasury", "fund development", "project fund", "shared",
        "collective", "dao", "protocol revenue", "community fund",
    ],
    "expectation_of_profit": [
        "return", "yield", "appreciation", "profit", "gain", "reward",
        "staking reward", "earn", "apy", "apr", "dividend", "revenue share",
        "buyback", "burn", "deflationary", "price increase", "moon",
        "investment", "secondary market", "listing", "exchange listing",
    ],
    "efforts_of_others": [
        "team", "founder", "developer", "company", "roadmap", "build",
        "develop", "manage", "operate", "governance by team",
        "centralized", "core team", "foundation",
    ],
}

# Keywords indicating the prong may NOT be satisfied
HOWEY_PRONG_NEGATORS = {
    "investment_of_money": [
        "airdrop", "free", "mining reward", "no cost",
    ],
    "common_enterprise": [
        "independent", "no pooling", "individual",
    ],
    "expectation_of_profit": [
        "consumptive", "use only", "access", "utility", "service",
        "no secondary market", "fixed price", "non-transferable",
    ],
    "efforts_of_others": [
        "decentralized", "community governed", "dao governed",
        "fully decentralized", "no central team", "open source",
        "permissionless", "validator operated",
    ],
}

# MiCA classification keywords
MICA_INDICATORS = {
    "e-money token": [
        "pegged to one currency", "single fiat", "backed by euro",
        "backed by usd", "backed by dollar", "stablecoin single currency",
        "redeemable at par", "fiat-backed single",
    ],
    "asset-reference token": [
        "basket", "multiple currencies", "commodity backed", "gold backed",
        "multi-asset", "algorithmic stable", "reserve of assets",
        "stable value", "pegged to basket",
    ],
    "utility token": [
        "access", "service", "platform use", "functionality",
        "consumptive", "in-app", "use token", "membership",
        "governance", "voting rights",
    ],
}


class TokenClassificationAgent:
    """Classifies digital tokens under US securities law and EU MiCA framework.

    This agent performs a structured analysis of a token's characteristics against
    the Howey Test (US), SEC Framework for Investment Contract Analysis (2019),
    and MiCA asset classification criteria (EU). It does NOT call the LLM directly —
    it returns structured data for the Synthesis Agent to compile.

    Attributes:
        None (stateless agent — all state passed via method arguments).
    """

    def classify(
        self,
        description: str,
        jurisdictions: list[str],
        retriever: Retriever,
    ) -> dict:
        """Classify a token based on its description and target jurisdictions.

        Args:
            description: Natural language description of the token, its
                mechanics, distribution, and intended use.
            jurisdictions: List of jurisdiction codes (e.g. ["US", "EU", "SG"]).
            retriever: Retriever instance for fetching regulatory context.

        Returns:
            Dict containing:
                - us_classification: "security" | "commodity" | "utility" | "undetermined"
                - eu_classification: MiCA type or "not applicable"
                - howey_analysis: dict with prong-by-prong assessment
                - mica_type: specific MiCA classification
                - is_security: bool indicating if token is likely a security in any jurisdiction
                - risks: list of classification risk factors
                - retrieved_context: list of retrieved Document dicts for synthesis
        """
        desc_lower = description.lower()

        # 1. Howey Test analysis
        howey = self._analyze_howey(desc_lower)

        # 2. MiCA classification
        mica_type = self._classify_mica(desc_lower)

        # 3. US classification determination
        us_class = self._determine_us_classification(howey, desc_lower)

        # 4. EU classification
        eu_class = mica_type if "EU" in jurisdictions else "not applicable"

        # 5. Retrieve relevant regulatory context
        retrieved_context = self._retrieve_context(description, jurisdictions, retriever)

        # 6. Retrieve enforcement case analogies
        case_context = retriever.retrieve_cases(description, k=5)

        # 7. Identify risks
        risks = self._identify_risks(howey, mica_type, us_class, jurisdictions)

        # 8. Determine if security in any jurisdiction
        is_security = us_class == "security"

        # Combine all retrieved context
        all_context = []
        for doc in retrieved_context:
            all_context.append({
                "id": doc.id,
                "text": doc.text[:500],
                "jurisdiction": doc.jurisdiction,
                "category": doc.category,
                "score": doc.score,
            })
        for doc in case_context:
            all_context.append({
                "id": doc.id,
                "text": doc.text[:500],
                "jurisdiction": doc.jurisdiction,
                "category": doc.category,
                "score": doc.score,
            })

        return {
            "us_classification": us_class,
            "eu_classification": eu_class,
            "howey_analysis": howey,
            "mica_type": mica_type,
            "is_security": is_security,
            "risks": risks,
            "retrieved_context": all_context,
        }

    def _analyze_howey(self, desc_lower: str) -> dict:
        """Evaluate all four prongs of the Howey Test.

        Returns a dict with each prong's assessment:
            {prong_name: {"likely_met": bool, "indicators": list, "negators": list, "assessment": str}}
        """
        howey = {}

        prong_names = {
            "investment_of_money": "Investment of Money",
            "common_enterprise": "Common Enterprise",
            "expectation_of_profit": "Reasonable Expectation of Profits",
            "efforts_of_others": "Derived from Efforts of Others",
        }

        for prong_key, display_name in prong_names.items():
            indicators_found = [
                kw for kw in HOWEY_PRONG_INDICATORS[prong_key]
                if kw in desc_lower
            ]
            negators_found = [
                kw for kw in HOWEY_PRONG_NEGATORS[prong_key]
                if kw in desc_lower
            ]

            # Determine if prong is likely met
            indicator_score = len(indicators_found)
            negator_score = len(negators_found)

            if indicator_score > 0 and negator_score == 0:
                likely_met = True
                assessment = f"Likely satisfied — indicators: {', '.join(indicators_found)}"
            elif indicator_score > negator_score:
                likely_met = True
                assessment = (
                    f"Probably satisfied — indicators ({indicator_score}) outweigh "
                    f"negators ({negator_score})"
                )
            elif negator_score > 0 and indicator_score == 0:
                likely_met = False
                assessment = f"Likely NOT satisfied — negators: {', '.join(negators_found)}"
            elif negator_score >= indicator_score and negator_score > 0:
                likely_met = False
                assessment = (
                    f"Probably NOT satisfied — negators ({negator_score}) outweigh "
                    f"indicators ({indicator_score})"
                )
            else:
                likely_met = True  # Conservative: assume met if unclear
                assessment = "Undetermined — insufficient information, assuming satisfied (conservative)"

            howey[prong_key] = {
                "display_name": display_name,
                "likely_met": likely_met,
                "indicators": indicators_found,
                "negators": negators_found,
                "assessment": assessment,
            }

        return howey

    def _classify_mica(self, desc_lower: str) -> str:
        """Classify the token under MiCA categories.

        Returns one of: "e-money token", "asset-reference token",
        "utility token", "other crypto-asset".
        """
        scores = {}
        for mica_type, keywords in MICA_INDICATORS.items():
            matches = sum(1 for kw in keywords if kw in desc_lower)
            scores[mica_type] = matches

        # Return highest scoring type, defaulting to "other crypto-asset"
        best_type = max(scores, key=scores.get)
        if scores[best_type] > 0:
            return best_type

        return "other crypto-asset"

    def _determine_us_classification(self, howey: dict, desc_lower: str) -> str:
        """Determine US classification based on Howey analysis.

        Returns: "security", "commodity", "utility", or "undetermined".
        """
        prongs_met = sum(1 for p in howey.values() if p["likely_met"])

        if prongs_met == 4:
            return "security"
        elif prongs_met >= 3:
            # 3 out of 4 prongs met — high risk of security classification
            return "security"

        # Check for commodity indicators (Bitcoin, Ether-like)
        commodity_keywords = [
            "bitcoin", "btc", "ether", "eth", "commodity",
            "decentralized", "no central issuer", "proof of work",
            "proof of stake", "mining",
        ]
        commodity_matches = sum(1 for kw in commodity_keywords if kw in desc_lower)

        if commodity_matches >= 2 and prongs_met <= 1:
            return "commodity"

        # Check for pure utility
        if prongs_met <= 1:
            return "utility"

        return "undetermined"

    def _retrieve_context(
        self,
        description: str,
        jurisdictions: list[str],
        retriever: Retriever,
    ) -> list:
        """Retrieve relevant regulatory documents for the classification analysis."""
        # Build query combining token description with classification-focused terms
        query = f"token classification securities test {description}"

        # Retrieve with jurisdiction filter if specified
        if jurisdictions:
            docs = retriever.retrieve(query, k=8, jurisdiction_filter=jurisdictions)
        else:
            docs = retriever.retrieve(query, k=8)

        return docs

    def _identify_risks(
        self,
        howey: dict,
        mica_type: str,
        us_class: str,
        jurisdictions: list[str],
    ) -> list[str]:
        """Identify classification-related compliance risks."""
        risks = []

        # US risks
        if us_class == "security":
            risks.append(
                "Token likely qualifies as a security under US law (Howey Test). "
                "Registration under Securities Act Section 5 or a valid exemption "
                "(Reg D, Reg S, Reg A+) is required before any offer or sale."
            )

        if us_class == "undetermined":
            risks.append(
                "Token classification under US law is uncertain. SEC may assert "
                "jurisdiction. Obtain a formal legal opinion from qualified US "
                "securities counsel before proceeding."
            )

        # Specific prong risks
        if howey.get("efforts_of_others", {}).get("likely_met"):
            risks.append(
                "Reliance on core team efforts is a strong indicator of security "
                "classification. Consider whether the network can achieve 'sufficient "
                "decentralization' (per Hinman Speech 2018) before token distribution."
            )

        if howey.get("expectation_of_profit", {}).get("likely_met"):
            risks.append(
                "Profit expectation indicators detected in token description. Review "
                "all marketing materials to remove investment-oriented language. "
                "SEC LBRY case (2022) confirmed that utility does not preclude "
                "security classification if marketed as investment."
            )

        # EU/MiCA risks
        if "EU" in jurisdictions:
            if mica_type == "asset-reference token":
                risks.append(
                    "Token may be classified as an Asset-Referenced Token (ART) under "
                    "MiCA. ART issuers must obtain authorisation (Article 16), maintain "
                    "reserve assets (Article 36), and meet own funds requirements of "
                    "€350,000 or 2% of reserves (Article 22)."
                )
            elif mica_type == "e-money token":
                risks.append(
                    "Token may be classified as an E-Money Token (EMT) under MiCA. "
                    "Issuer must be authorised as a credit institution or e-money "
                    "institution. EMTs must be redeemable at par at all times (Article 49)."
                )

        # Cross-jurisdiction risk
        if len(jurisdictions) > 1:
            risks.append(
                f"Token is targeting {len(jurisdictions)} jurisdictions. Classification "
                f"may differ across jurisdictions — a token classified as a utility token "
                f"in one jurisdiction may be a security in another. Obtain legal opinions "
                f"in each target jurisdiction."
            )

        return risks
