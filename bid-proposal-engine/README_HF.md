---
title: Bid Proposal Engine API
emoji: "\U0001F4CA"
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Bid & Proposal Response Engine API

AI-powered RFP analysis, compliance checking, and proposal generation.

## API Endpoints

- `POST /upload-rfp` — Upload RFP document
- `POST /extract-requirements` — Extract requirements from RFP
- `POST /retrieve-capabilities` — RAG capability matching
- `POST /compliance-check` — Compliance scoring
- `POST /score` — Win probability calculation
- `POST /generate-proposal` — Full proposal generation
- `GET /health` — Health check
- `GET /llm-stats` — LLM service statistics
