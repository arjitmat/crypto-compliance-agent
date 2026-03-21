"""Risk scoring engine for compliance gap analysis."""


class RiskScorer:
    """Scores compliance risk across multiple dimensions."""

    # Score thresholds for risk labels
    THRESHOLDS = {
        "Low": (0, 25),
        "Medium": (26, 50),
        "High": (51, 75),
        "Critical": (76, 100),
    }

    def score(self, analysis_data: dict) -> dict:
        """Calculate risk scores across all dimensions.

        Args:
            analysis_data: Dict with keys like:
                - unlicensed_jurisdictions: list of jurisdiction codes
                - has_aml_program: bool
                - is_security_token: bool
                - is_registered: bool
                - travel_rule_compliant: bool
                - has_whitepaper: bool
                - mica_applies: bool
                - enforcement_analogies: int (number of similar enforcement cases)
                - has_kyc_procedures: bool
                - has_sanctions_screening: bool
                - has_transaction_monitoring: bool
                - target_jurisdictions: list of jurisdiction codes

        Returns:
            Dict with overall score and sub-scores, all 0-100.
        """
        aml_score = self._score_aml(analysis_data)
        licensing_score = self._score_licensing(analysis_data)
        disclosure_score = self._score_disclosure(analysis_data)
        token_score = self._score_token(analysis_data)
        operational_score = self._score_operational(analysis_data)

        # Overall is weighted average
        overall = min(100, int(
            licensing_score * 0.30
            + aml_score * 0.25
            + token_score * 0.20
            + disclosure_score * 0.15
            + operational_score * 0.10
        ))

        return {
            "overall": overall,
            "aml": aml_score,
            "licensing": licensing_score,
            "disclosure": disclosure_score,
            "token": token_score,
            "operational": operational_score,
        }

    def _score_licensing(self, data: dict) -> int:
        """Score licensing risk."""
        score = 0

        unlicensed = data.get("unlicensed_jurisdictions", [])
        score += len(unlicensed) * 20

        # Security token without registration is severe
        if data.get("is_security_token") and not data.get("is_registered"):
            score += 30

        return min(100, score)

    def _score_aml(self, data: dict) -> int:
        """Score AML/KYC risk."""
        score = 0

        if not data.get("has_aml_program"):
            score += 25

        if not data.get("has_kyc_procedures"):
            score += 20

        if not data.get("has_sanctions_screening"):
            score += 20

        if not data.get("travel_rule_compliant"):
            score += 15

        if not data.get("has_transaction_monitoring"):
            score += 15

        return min(100, score)

    def _score_disclosure(self, data: dict) -> int:
        """Score disclosure/whitepaper risk."""
        score = 0

        if data.get("mica_applies") and not data.get("has_whitepaper"):
            score += 10

        # Missing whitepaper in any jurisdiction that requires it
        target_jx = data.get("target_jurisdictions", [])
        whitepaper_required_jx = {"EU", "UK", "AE"}
        for jx in target_jx:
            if jx in whitepaper_required_jx and not data.get("has_whitepaper"):
                score += 10

        # Marketing compliance issues
        if not data.get("marketing_compliant"):
            score += 15

        return min(100, score)

    def _score_token(self, data: dict) -> int:
        """Score token classification risk."""
        score = 0

        if data.get("is_security_token") and not data.get("is_registered"):
            score += 30

        # Enforcement analogies — each one adds risk signal
        analogies = min(data.get("enforcement_analogies", 0), 4)
        score += analogies * 5

        # No legal opinion obtained
        if not data.get("has_legal_opinion"):
            score += 20

        return min(100, score)

    def _score_operational(self, data: dict) -> int:
        """Score operational risk."""
        score = 0

        if not data.get("has_smart_contract_audit"):
            score += 15

        if not data.get("has_custody_controls"):
            score += 15

        if not data.get("has_incident_response"):
            score += 10

        if not data.get("has_business_continuity"):
            score += 10

        return min(100, score)

    def risk_label(self, score: int) -> str:
        """Return human-readable risk label for a numeric score."""
        for label, (low, high) in self.THRESHOLDS.items():
            if low <= score <= high:
                return label
        return "Critical"

    def priority_actions(self, scores: dict, jurisdictions: list[str]) -> list[str]:
        """Generate an ordered list of priority compliance actions.

        Actions are ordered by urgency (highest risk sub-score first).
        """
        actions = []

        # Sort sub-scores by severity (descending), exclude 'overall'
        sub_scores = {k: v for k, v in scores.items() if k != "overall"}
        sorted_areas = sorted(sub_scores.items(), key=lambda x: x[1], reverse=True)

        for area, area_score in sorted_areas:
            if area_score <= 25:
                continue

            if area == "licensing" and area_score > 25:
                for jx in jurisdictions:
                    jx_names = {
                        "US": "SEC/FinCEN registration",
                        "EU": "MiCA CASP authorisation",
                        "UK": "FCA MLR registration",
                        "SG": "MAS PS Act licence (SPI/MPI)",
                        "AE": "VARA VASP licence",
                    }
                    name = jx_names.get(jx, f"{jx} licence")
                    actions.append(f"[CRITICAL] Obtain {name} before operating in {jx}")

            if area == "aml" and area_score > 25:
                if area_score >= 50:
                    actions.append("[URGENT] Implement comprehensive AML/CFT programme with designated MLRO")
                    actions.append("[URGENT] Deploy sanctions screening (OFAC, EU, UN, UK) for all customers and transactions")
                    actions.append("[URGENT] Implement KYC/CDD procedures for customer onboarding")
                actions.append("[HIGH] Implement Travel Rule compliance for cross-border transfers")
                actions.append("[HIGH] Establish transaction monitoring with blockchain analytics")
                actions.append("[MEDIUM] Implement SAR/STR filing procedures and train compliance staff")

            if area == "token" and area_score > 25:
                actions.append("[CRITICAL] Obtain legal opinion on token classification in all target jurisdictions")
                if area_score >= 50:
                    actions.append("[CRITICAL] If token is a security: register offering or secure exemption (Reg D/S) before any sales")
                actions.append("[HIGH] Conduct Howey Test self-assessment with qualified US securities counsel")
                actions.append("[HIGH] Prepare MiCA classification analysis if EU market is targeted")

            if area == "disclosure" and area_score > 25:
                actions.append("[HIGH] Prepare crypto-asset white paper compliant with MiCA Article 6 requirements")
                actions.append("[MEDIUM] Review all marketing materials for compliance with FCA PS23/6 and MAS PS-G02")
                actions.append("[MEDIUM] Implement risk warnings on all customer-facing materials")

            if area == "operational" and area_score > 25:
                actions.append("[MEDIUM] Commission independent smart contract security audit before deployment")
                actions.append("[MEDIUM] Implement custody controls with key segregation and cold storage")
                actions.append("[LOW] Establish incident response and business continuity plans")

        # Deduplicate while preserving order
        seen = set()
        unique_actions = []
        for action in actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)

        return unique_actions
