"""Compliance report builder — markdown and PDF output."""

import io
from datetime import datetime

from fpdf import FPDF

# Header colour: dark purple RGB(45, 20, 105)
HEADER_R, HEADER_G, HEADER_B = 45, 20, 105
ACCENT_R, ACCENT_G, ACCENT_B = 0, 201, 167  # Teal accent


class ReportBuilder:
    """Generates compliance reports in markdown and PDF formats."""

    def build_markdown(self, result: dict) -> str:
        """Build a full compliance report in markdown format.

        Args:
            result: Analysis result dict containing:
                - risk_scores: dict with overall + sub-scores
                - business_summary: str
                - jurisdictions: list of dicts with analysis per jurisdiction
                - token_classification: dict
                - aml_requirements: dict
                - licensing_roadmap: list of steps
                - enforcement_cases: list of case dicts
                - priority_actions: list of action strings
                - query: original user query
        """
        scores = result.get("risk_scores", {})
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        sections = []

        # Title
        sections.append("# Crypto Compliance Intelligence Report")
        sections.append(f"*Generated: {now}*\n")

        # 1. Executive Summary
        sections.append("## 1. Executive Summary")
        overall = scores.get("overall", 0)
        label = self._risk_label(overall)
        sections.append(f"**Overall Risk Score: {overall}/100 ({label})**\n")
        sections.append(self._risk_gauge(overall))
        sections.append("")

        # Top risks
        top_risks = result.get("top_risks", [])
        if top_risks:
            sections.append("**Top Risks:**")
            for i, risk in enumerate(top_risks[:3], 1):
                sections.append(f"{i}. {risk}")
            sections.append("")

        # Sub-scores table
        sections.append("| Risk Area | Score | Level |")
        sections.append("|-----------|-------|-------|")
        for area in ["licensing", "aml", "token", "disclosure", "operational"]:
            s = scores.get(area, 0)
            sections.append(f"| {area.title()} | {s}/100 | {self._risk_label(s)} |")
        sections.append("")

        # 2. Business Activity Assessment
        sections.append("## 2. Business Activity Assessment")
        sections.append(result.get("business_summary", "*No business summary available.*"))
        sections.append("")

        # 3. Jurisdiction-by-Jurisdiction Analysis
        sections.append("## 3. Jurisdiction-by-Jurisdiction Analysis")
        jurisdictions = result.get("jurisdictions", [])
        if jurisdictions:
            sections.append("| Jurisdiction | Status | Key Requirements | Gaps |")
            sections.append("|-------------|--------|-----------------|------|")
            for jx in jurisdictions:
                name = jx.get("name", "")
                status = jx.get("status", "")
                reqs = jx.get("key_requirements", "")
                gaps = jx.get("gaps", "")
                sections.append(f"| {name} | {status} | {reqs} | {gaps} |")
            sections.append("")

            for jx in jurisdictions:
                if jx.get("detail"):
                    sections.append(f"### {jx.get('name', '')}")
                    sections.append(jx["detail"])
                    sections.append("")

        # 4. Token Classification
        sections.append("## 4. Token Classification")
        tc = result.get("token_classification", {})
        if tc:
            sections.append(f"**Howey Test Assessment:** {tc.get('howey_result', 'Not assessed')}")
            sections.append(f"**MiCA Classification:** {tc.get('mica_type', 'Not assessed')}")
            sections.append(f"**Implications:** {tc.get('implications', 'N/A')}")
        else:
            sections.append("*Token classification not assessed.*")
        sections.append("")

        # 5. AML/KYC Requirements
        sections.append("## 5. AML/KYC Requirements")
        aml = result.get("aml_requirements", {})
        if aml:
            needed = aml.get("needed", [])
            missing = aml.get("missing", [])
            if needed:
                sections.append("**Required:**")
                for item in needed:
                    sections.append(f"- {item}")
            if missing:
                sections.append("\n**Gaps Identified:**")
                for item in missing:
                    sections.append(f"- {item}")
        else:
            sections.append("*AML/KYC assessment not available.*")
        sections.append("")

        # 6. Licensing Roadmap
        sections.append("## 6. Licensing Roadmap")
        roadmap = result.get("licensing_roadmap", [])
        if roadmap:
            sections.append("| # | Action | Jurisdiction | Timeline | Est. Cost |")
            sections.append("|---|--------|-------------|----------|-----------|")
            for i, step in enumerate(roadmap, 1):
                sections.append(
                    f"| {i} | {step.get('action', '')} | "
                    f"{step.get('jurisdiction', '')} | "
                    f"{step.get('timeline', '')} | "
                    f"{step.get('cost', '')} |"
                )
        else:
            sections.append("*No licensing roadmap generated.*")
        sections.append("")

        # 7. Relevant Enforcement Cases
        sections.append("## 7. Relevant Enforcement Cases")
        cases = result.get("enforcement_cases", [])
        if cases:
            for case in cases[:5]:
                name = case.get("case_name", case.get("title", ""))
                sections.append(f"### {name}")
                if case.get("outcome"):
                    sections.append(f"**Outcome:** {case['outcome']}")
                if case.get("key_lesson"):
                    sections.append(f"**Lesson:** {case['key_lesson']}")
                sections.append("")
        else:
            sections.append("*No analogous enforcement cases identified.*")
        sections.append("")

        # 8. Priority Action Plan
        sections.append("## 8. Priority Action Plan")
        actions = result.get("priority_actions", [])
        if actions:
            # Group by urgency
            immediate = [a for a in actions if "[CRITICAL]" in a]
            thirty_day = [a for a in actions if "[URGENT]" in a or "[HIGH]" in a]
            sixty_day = [a for a in actions if "[MEDIUM]" in a]
            ninety_day = [a for a in actions if "[LOW]" in a]

            if immediate:
                sections.append("**Immediate (0-30 days):**")
                for a in immediate:
                    sections.append(f"- {a}")
            if thirty_day:
                sections.append("\n**30-60 days:**")
                for a in thirty_day:
                    sections.append(f"- {a}")
            if sixty_day:
                sections.append("\n**60-90 days:**")
                for a in sixty_day:
                    sections.append(f"- {a}")
            if ninety_day:
                sections.append("\n**90+ days:**")
                for a in ninety_day:
                    sections.append(f"- {a}")
        else:
            sections.append("*No action items generated.*")
        sections.append("")

        # 9. Disclaimer
        sections.append("## 9. Disclaimer")
        sections.append(
            "This report is generated by an AI system and provides general regulatory "
            "information only. It does not constitute legal advice and should not be "
            "relied upon as such. The analysis is based on publicly available regulatory "
            "texts and may not reflect the most recent amendments or interpretive guidance. "
            "Always consult qualified legal counsel in each relevant jurisdiction before "
            "making compliance decisions. Regulatory requirements change frequently and "
            "the applicability of any requirement depends on specific facts and circumstances "
            "that cannot be fully assessed by an automated system."
        )

        return "\n".join(sections)

    def build_pdf(self, result: dict) -> bytes:
        """Build a professional PDF compliance report.

        Returns PDF as bytes.
        """
        pdf = _CompliancePDF()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()

        scores = result.get("risk_scores", {})
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(HEADER_R, HEADER_G, HEADER_B)
        pdf.cell(0, 12, "Crypto Compliance Intelligence Report", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, f"Generated: {now}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # 1. Executive Summary
        pdf._section_heading("1. Executive Summary")
        overall = scores.get("overall", 0)
        label = self._risk_label(overall)

        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Overall Risk Score: {overall}/100 ({label})", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # Sub-scores
        for area in ["licensing", "aml", "token", "disclosure", "operational"]:
            s = scores.get(area, 0)
            pdf._body_text(f"{area.title()}: {s}/100 ({self._risk_label(s)})")
        pdf.ln(2)

        # Top risks
        top_risks = result.get("top_risks", [])
        if top_risks:
            pdf._body_bold("Top Risks:")
            for risk in top_risks[:3]:
                pdf._body_bullet(risk)
            pdf.ln(2)

        # 2. Business Activity Assessment
        pdf._section_heading("2. Business Activity Assessment")
        pdf._body_text(result.get("business_summary", "No business summary available."))

        # 3. Jurisdiction Analysis
        pdf._section_heading("3. Jurisdiction-by-Jurisdiction Analysis")
        jurisdictions = result.get("jurisdictions", [])
        if jurisdictions:
            for jx in jurisdictions:
                name = jx.get("name", "Unknown")
                status = jx.get("status", "")
                pdf._body_bold(f"{name} - {status}")
                if jx.get("key_requirements"):
                    pdf._body_text(f"Requirements: {jx['key_requirements'][:200]}")
                if jx.get("gaps"):
                    pdf._body_text(f"Gaps: {jx['gaps'][:200]}")
                if jx.get("detail"):
                    pdf._body_text(jx["detail"][:500])
        else:
            pdf._body_text("No jurisdiction analysis available.")

        # 4. Token Classification
        pdf._section_heading("4. Token Classification")
        tc = result.get("token_classification", {})
        if tc:
            pdf._body_text(f"Howey Test: {tc.get('howey_result', 'Not assessed')}")
            pdf._body_text(f"MiCA Type: {tc.get('mica_type', 'Not assessed')}")
            pdf._body_text(f"Implications: {tc.get('implications', 'N/A')}")
        else:
            pdf._body_text("Token classification not assessed.")

        # 5. AML/KYC Requirements
        pdf._section_heading("5. AML/KYC Requirements")
        aml = result.get("aml_requirements", {})
        if aml:
            needed = aml.get("needed", [])
            missing = aml.get("missing", [])
            if needed:
                pdf._body_bold("Required:")
                for item in needed:
                    pdf._body_bullet(item)
            if missing:
                pdf._body_bold("Gaps Identified:")
                for item in missing:
                    pdf._body_bullet(item)
        else:
            pdf._body_text("AML/KYC assessment not available.")

        # 6. Licensing Roadmap
        pdf._section_heading("6. Licensing Roadmap")
        roadmap = result.get("licensing_roadmap", [])
        if roadmap:
            for i, step in enumerate(roadmap, 1):
                pdf._body_bold(f"{i}. {step.get('action', '')} - {step.get('jurisdiction', '')}")
                pdf._body_text(f"Timeline: {step.get('timeline', 'TBD')} | Cost: {step.get('cost', 'TBD')}")
        else:
            pdf._body_text("No licensing roadmap generated.")

        # 7. Enforcement Cases
        pdf._section_heading("7. Relevant Enforcement Cases")
        cases = result.get("enforcement_cases", [])
        if cases:
            for case in cases[:5]:
                name = case.get("case_name", case.get("title", ""))
                pdf._body_bold(name)
                if case.get("outcome"):
                    pdf._body_text(f"Outcome: {case['outcome']}")
                if case.get("key_lesson"):
                    pdf._body_text(f"Lesson: {case['key_lesson']}")
                pdf.ln(2)
        else:
            pdf._body_text("No analogous enforcement cases identified.")

        # 8. Priority Action Plan
        pdf._section_heading("8. Priority Action Plan")
        actions = result.get("priority_actions", [])
        if actions:
            for action in actions:
                pdf._body_bullet(action)
        else:
            pdf._body_text("No action items generated.")

        # 9. Disclaimer
        pdf._section_heading("9. Disclaimer")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(
            0, 4,
            pdf._safe(
                "This report is generated by an AI system and provides general regulatory "
                "information only. It does not constitute legal advice and should not be "
                "relied upon as such. Always consult qualified legal counsel in each relevant "
                "jurisdiction before making compliance decisions."
            ),
        )

        # Return PDF bytes
        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    def _risk_label(self, score: int) -> str:
        if score <= 25:
            return "Low"
        elif score <= 50:
            return "Medium"
        elif score <= 75:
            return "High"
        return "Critical"

    def _risk_gauge(self, score: int) -> str:
        """Simple text-based risk gauge for markdown."""
        filled = score // 5
        empty = 20 - filled
        bar = "█" * filled + "░" * empty
        return f"`[{bar}]` {score}/100"


class _CompliancePDF(FPDF):
    """Custom PDF class with header, footer, and helper methods."""

    def header(self):
        # Purple header bar
        self.set_fill_color(HEADER_R, HEADER_G, HEADER_B)
        self.rect(0, 0, 210, 8, "F")

        # Teal accent line
        self.set_fill_color(ACCENT_R, ACCENT_G, ACCENT_B)
        self.rect(0, 8, 210, 1, "F")

        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"CryptoComply Report  |  Page {self.page_no()}/{{nb}}", align="C")

    def _section_heading(self, text: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(HEADER_R, HEADER_G, HEADER_B)
        self.cell(0, 8, self._safe(text), new_x="LMARGIN", new_y="NEXT")

        # Teal underline
        self.set_draw_color(ACCENT_R, ACCENT_G, ACCENT_B)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    @staticmethod
    def _safe(text: str) -> str:
        """Strip non-latin-1 characters so Helvetica can render them."""
        return text.encode("latin-1", "replace").decode("latin-1")

    def _body_text(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.set_x(10)
        self.multi_cell(0, 5, self._safe(text))
        self.ln(2)

    def _body_bold(self, text: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(40, 40, 40)
        self.set_x(10)
        self.cell(0, 6, self._safe(text), new_x="LMARGIN", new_y="NEXT")

    def _body_bullet(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.set_x(10)  # reset to left margin
        safe = self._safe(f"- {text}")
        if len(safe) > 400:
            safe = safe[:400] + "..."
        self.multi_cell(0, 5, safe)

    def _table_header(self, columns: list[str]):
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(HEADER_R, HEADER_G, HEADER_B)
        self.set_text_color(255, 255, 255)

        col_width = (210 - 20) / len(columns)
        for col in columns:
            self.cell(col_width, 7, self._safe(col), border=1, fill=True, align="C")
        self.ln()

    def _table_row(self, cells: list[str]):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(40, 40, 40)
        self.set_fill_color(245, 245, 250)

        col_width = (210 - 20) / len(cells)
        max_chars = max(8, int(col_width / 2))  # ~2pt per char
        for cell_text in cells:
            # Sanitise: remove non-latin1 chars, truncate
            safe = cell_text[:max_chars].encode("latin-1", "replace").decode("latin-1")
            self.cell(col_width, 6, safe, border=1, align="L")
        self.ln()
