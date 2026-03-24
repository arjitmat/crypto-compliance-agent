---
title: Aegis - Crypto Compliance Intelligence
emoji: 🛡️
colorFrom: green
colorTo: gray
sdk: gradio
sdk_version: 4.44.0
python_version: "3.11"
app_file: app.py
pinned: false
license: mit
---

# Crypto Compliance Intelligence Agent

Multi-agent AI system for institutional-grade crypto regulatory compliance analysis.

**Jurisdictions:** EU (MiCA) · US (SEC) · Singapore (MAS) · UK (FCA) · UAE (VARA)

**Powered by:** Mistral-7B-Instruct via HF Inference API · FAISS semantic retrieval · Real regulatory texts

## What It Does

- Classifies your token/activity under each jurisdiction's framework
- Applies Howey Test (US) and MiCA asset-type classification (EU)
- Checks AML/KYC obligations including FATF Travel Rule thresholds
- Retrieves relevant real enforcement cases as precedent
- Produces a risk-scored gap analysis with prioritised action items
- Generates a downloadable compliance report

## Not Legal Advice

This tool provides general regulatory information only. Always consult qualified legal counsel.
