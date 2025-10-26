
# Academic Insights — Agentic Prototype

<div style="display:flex;align-items:flex-start;gap:24px;">

**What this is**

- A lightweight multi-agent prototype that extracts, normalizes, and analyzes student report-card data.
- Built for rapid iteration: a small custom agentic architecture (controller → service → utils) that is easy to prototype and deploy.

</div>


## Architecture (agentic overview)

```
[Client] -> [Orchestrator] -> { Extraction Agent -> Normalization Agent -> Insights Agent }
								 │
								 └-> Health / routing and retry logic
```

- Orchestrator: routes uploaded documents, calls agents, and aggregates results.
- Extraction Agent: OCR (Tesseract) + PDF/image processing → raw text & structured fields.
- Normalization Agent: translates (OpenAI LLM) and formats the extracted text into a strict JSON ReportCard via prompt engineering and schema validation.
- Insights Agent: analytics, scoring, and recommendations built on normalized data.

---

## Why a custom agentic architecture?

- Speed to prototype: a small, explicit controller → service → utils pattern avoids heavy framework lock-in and is easier to iterate locally and in CI.
- Transparency: each agent has a single responsibility and simple, testable boundaries.
- Extensibility: add parallel workers, caching, or replace LLM/OCR components with minimal changes.

---

## Capabilities

- OCR of PDFs/images to extract free text and tabular grades (Tesseract + pdf2image).
- Language-agnostic translation to English using an LLM for higher fidelity across noisy OCR results.
- Prompt-engineered normalization: converts messy text into a validated ReportCard JSON schema.
- Lightweight orchestration for multi-step pipelines and retries.

---

## Technology stack

- Python 3.11, FastAPI, uvicorn
- OCR: Tesseract (pytesseract + pdf2image + Pillow) — robust for scanned documents and PDFs
- LLM: OpenAI (gpt-4o-mini by default in this project) — used for translation and deterministic JSON formatting via prompt engineering
- HTTP client: httpx
- Containers: Docker Compose for local orchestration

---

## Quick start (Windows PowerShell)

1) Build & run (from repo root):

```powershell

docker compose -f "academicInsights\docker-compose.yml" up -d --build
```

2) Health check (example):

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/health
```

---

## Roles of each agent

- Extraction Agent: ingest PDF/image, run OCR (Tesseract), and extract raw text + simple heuristics to find grade tables and metadata.
- Normalization Agent: translate extracted text to English (OpenAI LLM) and run a prompt that returns strictly formatted JSON validated against a Pydantic ReportCard model.
- Orchestrator: handles uploads, calls extraction + normalization, performs retries/timeouts, and returns the normalized payload to the client.
- Insights Agent: consumes normalized ReportCard objects to compute metrics, recommendations, and produce analytics.

---

## OCR & LLM details

- OCR: Tesseract (via pytesseract). We rasterize PDFs with pdf2image at a configurable DPI for better recognition of scanned documents.
- LLM: OpenAI's API (gpt-4o-mini default). We use the LLM for two reasons:
	1. Translation — robustly translate noisy OCR outputs from any language to English.
	2. Formatting — prompt-engineered JSON output reduces brittle handwritten parsing and produces a validated schema in one step.

---

## Metrics & cost (rough estimates)

- Time per document (end-to-end, typical scanned report card): ~30 seconds (this varies with OCR size, image DPI, and LLM latency).
- Cost per OpenAI API call: depends on model and tokens used. For budgeting, assume roughly $0.03 per normalization call on a compact model (this is a ballpark; check your tenant pricing and tokens consumed per request).

---

## Usage tips & next steps

- For scale, convert LLM calls to async/pooled workers and add caching for repeated documents.
- Add retries and exponential backoff for transient HTTP/LLM failures (the orchestrator already has timeouts and error handling patterns).
- Keep prompts versioned in `normalization_agent/prompts/report_prompt.json` so you can iterate on formatting without code changes.

---

If you'd like, I can:
- run a quick end-to-end sample to show real output from your current OpenAI key,
- convert the normalization calls to fully async clients (if you prefer native asyncio LLM client), or
- add a tiny dashboard demo that shows raw vs normalized output side-by-side.

