# EY Techathon 6 — Multi-Agent Orchestrator

**Submission for EY Techathon 6**

A modular, auditable multi-agent system centered on a **Master Agent** (LangGraph orchestrator) that decomposes strategic biomedical queries, routes tasks to specialized worker agents, and enforces a **"Rank & Verify"** anti-hallucination pipeline to surface provenance-anchored recommendations with confidence scoring.

---

## Table of Contents

- [Overview](#overview)
- [Architecture & Dataflow](#architecture--dataflow)
- [Agents](#agents)
  - [Master Agent (The Brain)](#master-agent-the-brain)
  - [Research Agent (PubMed)](#research-agent-pubmed)
  - [Internal Knowledge Agent](#internal-knowledge-agent)
  - [IQVIA Insights Agent](#iqvia-insights-agent)
  - [Clinical Trials Agent](#clinical-trials-agent)
  - [EXIM Trends Agent](#exim-trends-agent)
  - [Patent Landscape Agent](#patent-landscape-agent)
  - [Web Intelligence Agent (Tavily)](#web-intelligence-agent-tavily)
- [Rank & Verify (Anti-Hallucination)](#rank--verify-anti-hallucination)
- [Connectors & Data Sources](#connectors--data-sources)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Testing & Validation](#testing--validation)
- [Observability & Audit Logging](#observability--audit-logging)
- [Security & Compliance](#security--compliance)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Team & Contact](#team--contact)

---

## Overview

**EY Techathon 6** delivers an orchestrated decision-making platform for rapid biomedical opportunity assessment. A single Master Agent decomposes strategic queries and distributes sub-tasks to eight specialized Worker Agents covering literature, clinical trials, market intelligence, supply chain, patents, internal operations, and web trends. All evidence is ranked, cross-validated, and surfaced with full provenance to reduce hallucinations and support explainable, auditable recommendations.

### Key Features

- **Multi-agent orchestration** via LangGraph for parallel task execution
- **Rank & Verify pipeline** to minimize hallucinations and enforce consensus checks
- **Full provenance tracking** — every claim traces back to source documents
- **Confidence scoring** with human-in-the-loop gating for high-stakes decisions
- **RAG support** for private company data (internal knowledge)
- **Real-time web intelligence** via Tavily for competitive & clinical monitoring
- **Audit trail** with immutable evidence logging for compliance

### Use Cases

- **Drug repurposing** triage:  is this therapeutic indication viable?
- **Regulatory pathway** assessment: which pathway (505(b)(2), NDA, etc.) is most efficient?
- **Commercial viability** screening: market size, prescription trends, revenue potential
- **Supply chain risk** evaluation: API availability, geopolitical threats, import dependencies
- **IP & FTO** analysis: patent landscape, freedom-to-operate, exclusivity windows
- **Clinical precedence** search: existing trials, endpoints, regulatory history

---

## Architecture & Dataflow

**High-level flow:**

```
User Query
    ↓
Master Agent (Orchestrator)
    ↓
[Task Decomposition]
    ↓
Parallel Dispatch to Worker Agents: 
├─ Research Agent (PubMed)
├─ Internal Knowledge Agent
├─ IQVIA Insights Agent
├─ Clinical Trials Agent
├─ EXIM Trends Agent
├─ Patent Landscape Agent
└─ Web Intelligence Agent (Tavily)
    ↓
Evidence Aggregation
    ↓
Rank & Verify Pipeline
├─ Score & rank by source reliability
├─ Cross-agent verification
├─ Conflict detection & resolution
└─ Confidence thresholding
    ↓
Human-in-the-Loop Gating (if needed)
    ↓
Response + Audit Log
```

**Core Components:**

- **Master Agent** — LangGraph orchestrator; task decomposition, routing, aggregation, Rank & Verify orchestration
- **Worker Agents** — Domain-specific microservices (research, market, regulatory, supply, IP, web)
- **Vector DB** — Embeddings for RAG (Pinecone, Milvus, Weaviate, or self-hosted)
- **Document Store** — S3-compatible bucket for raw artifacts & PDFs
- **Secrets Manager** — Vault or AWS Secrets Manager for API keys
- **Audit Store** — Append-only log for evidence provenance
- **Observability** — Prometheus, Grafana, ELK for metrics & logs

---

## Agents

All agents return structured **evidence items** in JSON format: 

```json
{
  "id": "unique_id",
  "agent":  "agent_name",
  "score": 0.85,
  "confidence": "high",
  "sources": [
    {
      "title": "Source Title",
      "url": "https://...",
      "authority": "PubMed / Clinicaltrials.gov / Patent DB / .. .",
      "publication_date": "2025-01-15",
      "citation_count": 42
    }
  ],
  "extracted_facts": {
    "mechanism": ".. .",
    "evidence_level": "Phase III RCT",
    "risk_flag": false
  },
  "raw_excerpt": "...",
  "timestamp": "2025-12-09T10:30:00Z"
}
```

### Master Agent (The Brain)

**Role:** Orchestrator and decision engine

**Responsibilities:**
- Parse and decompose high-level queries into sub-tasks
- Route sub-tasks to appropriate worker agents via LangGraph
- Aggregate evidence from all agents
- Execute Rank & Verify pipeline (scoring, cross-checks, thresholding)
- Determine human-review gating (legal flags, low confidence, contradictions)
- Package final recommendation with provenance chain
- Log all steps to audit trail

**Key Algorithms:**
- Task decomposition:  use semantic understanding to infer required worker agents
- Evidence aggregation: merge results, deduplicate, preserve source metadata
- Rank & Verify:  apply weighted scoring, consensus checks, confidence thresholding

---

### Research Agent (PubMed)

**Role:** Biomedical literature scanning and mechanism extraction

**Capabilities:**
- Semantic search across PubMed and PubMed Central (NCBI E-utilities)
- Extract biological mechanisms (e.g., Blood-Brain Barrier permeability, receptor binding)
- Compute evidence-level metrics (RCT phase, citation count, H-index of authors)
- Identify disease-indication candidates and rank by clinical strength
- Detect contradictory findings and flag methodological concerns

**Data Sources:**
- PubMed/PMC via NCBI APIs
- MeSH (Medical Subject Headings) for indexing

**Confidence Scoring:**
- High: Phase III RCT, >100 citations, recent publication (< 2 years)
- Medium: Phase II, 10–100 citations
- Low:  Preclinical, <10 citations, older publications

---

### Internal Knowledge Agent

**Role:** RAG search over private company documents

**Capabilities:**
- Secure vector search on internal PDFs (meeting minutes, inventory, BOMs)
- Manufacturing feasibility checks (e.g., "Do we have API surplus?", "What is our production capacity?")
- Supply & logistics constraints
- Historical project data and lessons learned
- Competitive intelligence from internal sources

**Data Sources:**
- S3 bucket with company PDFs
- Vector embeddings (OpenAI, Anthropic, or self-hosted)

**Security:**
- Access controls per document classification
- Encrypted retrieval; raw PDFs never leaked in outputs
- Audit logging of all queries

---

### IQVIA Insights Agent

**Role:** Commercial viability assessment

**Capabilities:**
- Market sizing by indication (total addressable market, serviceable market)
- Prescription trends and prescriber patterns
- Competitor share and revenue forecasts
- Pricing benchmarks and reimbursement status
- Commercial risk metrics

**Data Sources:**
- IQVIA APIs (requires enterprise license)
- Public market reports & SEC filings
- Prescription databases (IQVIA, Veeva)

**Output:**
- Market opportunity score (e.g., 0–1.0)
- Competitive landscape summary
- Revenue forecast range (5-year)

---

### Clinical Trials Agent

**Role:** Registry analysis and regulatory pathway mapping

**Capabilities:**
- Search global trial registries (clinicaltrials.gov, EudraCT, ISRCTN)
- Identify precedent trials (same indication, same or similar drug)
- Extract trial endpoints, enrollment, phase, and regulatory status
- Map regulatory pathways (e.g., 505(b)(2), NDA, PDUFA timelines)
- Compute regulatory risk (e.g., efficacy concerns, safety signals)
- Timeline forecasting (when might approval occur?)

**Data Sources:**
- clinicaltrials.gov APIs
- EudraCT (Europe)
- ISRCTN (UK & international)
- FDA Orange Book for precedent & exclusivity

**Output:**
- List of relevant trials with links
- Regulatory pathway recommendation
- Approval timeline estimate

---

### EXIM Trends Agent

**Role:** Supply chain & trade flow monitoring

**Capabilities:**
- Global API (Active Pharmaceutical Ingredient) shipment data
- Export controls and sanctions (e.g., OFAC, EAR)
- Country-of-origin risk (geopolitical, embargoes)
- Import dependency ratios for critical materials
- Supplier diversification assessment
- Tariff & trade agreement implications

**Data Sources:**
- Trade databases (e.g., Panjiva, TradeKey)
- Sanctions lists (OFAC, BIS)
- Industry supply chain reports

**Output:**
- Supply security score (0–1.0)
- Risk flags (geopolitical, sanctions, single-source dependency)
- Sourcing recommendations

---

### Patent Landscape Agent

**Role:** Freedom-to-Operate (FTO) and patent cliff analysis

**Capabilities:**
- Prior art search (Google Patents, PATENTSCOPE, USPTO, EPO)
- Patent claim analysis and infringement risk scoring
- Filing family mapping (related patents across jurisdictions)
- Exclusivity windows and patent cliff detection
- Generic entry timeline forecasting
- FTO clearance summary

**Data Sources:**
- Google Patents API
- PATENTSCOPE (WIPO)
- USPTO & EPO databases
- Patent litigation databases (optional)

**Confidence Scoring:**
- High:  no blocking patents, clear FTO
- Medium: potentially blocking patents, detailed claim review required
- Low: high infringement risk, freedom-to-operate uncertain

---

### Web Intelligence Agent (Tavily)

**Role:** Real-time web scanning for competitive and clinical trends

**Capabilities:**
- Competitor news monitoring and sentiment analysis
- Clinical guideline updates (e.g., NCCN, ESC, ADA)
- Standard-of-care shifts and clinical practice changes
- Regulatory announcements (FDA, EMA)
- Conference presentations and trial disclosures
- Social media & news sentiment on indication

**Data Sources:**
- Tavily API for web search & scraping
- RSS feeds for regulatory agencies
- Google News alerts
- Clinical society publications

**Output:**
- Trending news summary
- Regulatory/guideline changes
- Competitive threats or opportunities
- Sentiment signal (bullish/bearish)

---

## Rank & Verify (Anti-Hallucination)

The **Rank & Verify** pipeline is the core safety mechanism that prevents unreliable claims from reaching decision-makers. 

### Rank Phase

For each evidence item returned by worker agents, compute a **composite score**:

```
Score = Σ (weight(source_authority) × relevance × recency_factor × citation_multiplier)
```

**Source Authority Weights (examples):**
- RCT in top-tier journal (Phase III): 1.0
- Published observational study:  0.7
- Internal company data (validated): 0.8
- Pre-print / preregistered trial: 0.5
- Web news / guidelines: 0.4
- Speculation or low-confidence retrieval: 0.2

**Recency Factor:**
- Publication < 1 year old: 1.0
- 1–2 years:  0.95
- 2–5 years: 0.85
- > 5 years (unless landmark): 0.6

**Citation Multiplier:**
- > 100 citations: 1.2
- 10–100 citations: 1.0
- < 10 citations: 0.8

### Verify Phase

**Cross-agent validation checks:**

1. **Consistency Check:** Does PubMed evidence align with clinicaltrials.gov trial results?  Flag contradictions. 
2. **Consensus Check:** Do ≥2 independent authoritative sources support the claim? 
3. **Temporal Check:** Is the evidence current, or superseded by newer data?
4. **Completeness Check:** Is the evidence sufficient, or are critical gaps?

**Example:**
- Claim: "Drug X shows efficacy in Disease Y"
- PubMed: Phase II study, 50 patients, statistically significant (score:  0.72)
- Clinical Trials: Phase III trial ongoing, interim analysis shows null efficacy (score: 0.3)
- **Verify result:** Contradiction detected.  Reduce overall confidence, flag for human review.

### Confidence Thresholding

**Confidence Levels & Actions:**

| Confidence | Score | Action |
|---|---|---|
| **High** | ≥ 0.80 | Proceed with recommendation |
| **Medium** | 0.60–0.79 | Proceed with caveats; recommend secondary review |
| **Low** | < 0.60 | **REQUIRE** human review before proceeding |
| **Conflicted** | Any score with contradictions | **REQUIRE** human review; present both sides |

### Chain of Evidence

Every final claim includes: 

```json
{
  "claim": "Drug X is viable for Disease Y via 505(b)(2) pathway",
  "confidence": "medium",
  "score": 0.72,
  "supporting_sources": [
    { "source": "PubMed NCT001234567", "contribution": 0.3 },
    { "source": "Clinicaltrials.gov active trial", "contribution": 0.25 },
    { "source":  "IQVIA market sizing", "contribution": 0.17 }
  ],
  "counter_evidence": [
    { "source": "Safety signal in EudraCT trial X", "concern": "hepatotoxicity" }
  ],
  "gaps": ["No Phase III efficacy data in target population"],
  "human_review_required": true,
  "reason_for_review": "conflicting efficacy data from Phase II vs.  Phase III"
}
```

---

## Connectors & Data Sources

### Required API Keys & Credentials

| Source | Type | Access Method | Cost |
|---|---|---|---|
| **PubMed/NCBI** | Literature | E-utilities API (email registration) | Free |
| **Clinicaltrials.gov** | Trials | Public API | Free |
| **IQVIA** | Market data | Enterprise API (contract) | Paid |
| **Google Patents** | Patents | Bulk export or API (limited free tier) | Free / Paid |
| **Tavily** | Web Intelligence | Tavily API | Paid (subscription) |
| **EudraCT** | Trials (EU) | Public scraping | Free |
| **S3 / Vector DB** | Internal docs | AWS / Pinecone / etc. | Infrastructure cost |

### Environment Variables

Create a `.env` file (never commit to repo):

```bash
# Master Agent
MASTER_API_KEY=sk_... 
LANGGRAPH_ENDPOINT=http://localhost:8000

# PubMed
PUBMED_EMAIL=your. email@company.com
PUBMED_API_KEY=...

# IQVIA (if available)
IQVIA_API_KEY=... 
IQVIA_BASE_URL=https://...

# Tavily
TAVILY_API_KEY=... 

# Internal RAG
S3_BUCKET=my-company-docs
S3_REGION=us-east-1
S3_ACCESS_KEY=...
S3_SECRET_KEY=...

# Vector DB
VECTOR_DB_URL=https://api.pinecone.io
VECTOR_DB_API_KEY=... 
VECTOR_DB_INDEX=ey-techathon-6

# Secrets Manager
VAULT_ADDR=https://vault.company.com
VAULT_TOKEN=... 

# Observability
PROMETHEUS_ENDPOINT=http://localhost:9090
ELK_ENDPOINT=http://localhost:9200
```

**Never store secrets in the repo. ** Use GitHub Secrets for CI/CD, and a proper secrets manager (Vault, AWS Secrets Manager) for runtime. 

---

## Local Development

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional, for local vector DB)
- Git

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/adityachanna/EY. git
   cd EY
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirement.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

5. **Start local vector DB (optional):**
   ```bash
   docker-compose up -d vectordb
   # Wait for service to be ready
   ```

6. **Run the Master Agent:**
   ```bash
   python -m agents.master. app
   ```
   
   The API should be available at `http://localhost:8000`.

7. **Run unit tests:**
   ```bash
   pytest tests/ -v
   ```

### Example API Usage

**Request:**
```bash
curl -X POST "http://localhost:8000/api/assess" \
  -H "Authorization: Bearer $MASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Assess repurposing of Drug X for Disease Y.  Is a 505(b)(2) pathway feasible?  What are commercial and supply chain risks?",
    "priority": "high",
    "required_agents": ["research", "clinical_trials", "iqvia", "exim_trends", "patent"]
  }'
```

**Response:**
```json
{
  "id": "assessment_uuid_12345",
  "question": "Assess repurposing.. .",
  "ranked_candidates": [
    {
      "candidate": "505(b)(2) pathway for Drug X → Disease Y",
      "score": 0.75,
      "confidence": "medium",
      "supporting_evidence": [... ],
      "risks": [
        {
          "type": "supply_chain",
          "severity": "medium",
          "description": "Single-source API supplier in geopolitically sensitive region"
        }
      ]
    }
  ],
  "summary": {
    "overall_viability": "medium",
    "key_risks": ["supply_chain", "patent_infringement_risk"],
    "recommended_next_steps": ["conduct FTO search", "engage regulatory affairs"]
  },
  "human_review_required": true,
  "review_reason": "supply_chain_risk AND conflicting_efficacy_data",
  "audit_log_id": "audit_12345",
  "timestamp": "2025-12-09T10:30:00Z"
}
```

---

## Deployment

### Docker Deployment

**Build image:**
```bash
docker build -t ey-techathon-6:latest .
```

**Run container:**
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  -v /path/to/config:/app/config \
  ey-techathon-6:latest
```

### Kubernetes Deployment

See `/infrastructure/k8s/` for sample manifests: 
- `master-agent-deployment.yaml` — Master Agent service
- `worker-agent-deployment.yaml` — Worker Agent replicas
- `vector-db-statefulset.yaml` — Vector DB (Milvus or Weaviate)
- `postgres-statefulset.yaml` — Audit log & metadata store

**Deploy:**
```bash
kubectl apply -f infrastructure/k8s/
```

---

## Testing & Validation

### Unit Tests

Test individual agent logic (fact extraction, scoring):

```bash
pytest tests/agents/ -v
```

### Integration Tests

Test orchestration and Rank & Verify flows (with mocked external APIs):

```bash
pytest tests/integration/ -v
```

### End-to-End Tests

Full system validation including audit logging:

```bash
pytest tests/e2e/ -v
```

### Code Quality

Run linting and security checks:

```bash
flake8 agents/ --max-line-length=120
black --check agents/
bandit -r agents/  # Security scanning
```

---

## Observability & Audit Logging

### Structured Logging

All requests are logged in JSON format with correlation IDs:

```json
{
  "timestamp": "2025-12-09T10:30:00Z",
  "correlation_id": "req_12345",
  "event": "task_dispatched",
  "agent": "research_agent",
  "status": "in_progress",
  "user": "admin@company.com"
}
```

### Metrics

Exposed via Prometheus endpoint (`/metrics`):
- `ey_requests_total` — Total requests by status
- `ey_latency_seconds` — Request latency histogram
- `ey_agent_success_rate` — Per-agent success rate
- `ey_verification_failures_total` — Number of Rank & Verify conflicts
- `ey_human_review_rate` — Percentage of assessments requiring human review

### Audit Trail

All evidence items, transformations, and final decisions are logged to an immutable append-only store:

```json
{
  "audit_id": "audit_12345",
  "request_id": "req_12345",
  "event_type": "evidence_scored",
  "agent": "research_agent",
  "claim": "Drug X shows efficacy in Disease Y",
  "score_before": null,
  "score_after":  0.72,
  "reason": "PubMed Phase II RCT",
  "timestamp": "2025-12-09T10:30:05Z",
  "operator_id": "langgraph_v1"
}
```

### Dashboards

See `/infrastructure/grafana/` for pre-built dashboards:
- **Agent Health:** Success rates, latency, error rates per agent
- **Rank & Verify:** Confidence distribution, verification failures, human review rate
- **Audit Trail:** Event timeline, evidence lifecycle

---

## Security & Compliance

### Data Protection

- **Encryption in transit:** All external API calls use TLS 1.3
- **Encryption at rest:** Document store encrypted with AWS KMS or equivalent
- **Access control:** RAG queries are scoped to user permissions; sensitive documents require approval

### PHI Handling

- Any patient or clinical data is treated as **Protected Health Information (PHI)**
- HIPAA compliance:  encrypted transport, audit logging, data minimization
- Never log raw patient data; use anonymized identifiers only

### Secrets Management

- **Never commit secrets** to the repository
- Use GitHub Secrets for CI/CD
- Use HashiCorp Vault or AWS Secrets Manager for runtime
- Rotate API keys quarterly

### Compliance Checklist

- [ ] HIPAA compliance (if handling PHI)
- [ ] FDA 21 CFR Part 11 (electronic records, if applicable)
- [ ] GDPR compliance (if EU data subjects)
- [ ] Legal review of patent and regulatory outputs
- [ ] Data retention policies defined

---

## Project Structure

```
EY/
├── agents/
│   ├── __init__.py
│   ├── master/
│   │   ├── app.py                 # Master Agent entry point
│   │   ├── orchestrator.py         # LangGraph task routing logic
│   │   ├── rank_verify.py          # Scoring & verification pipeline
│   │   └── README.md
│   ├── research_pubmed/
│   │   ├── agent.py
│   │   ├── retriever.py            # PubMed API client
│   │   ├── scoring.py
│   │   └── README. md
│   ├── internal_knowledge/
│   │   ├── agent. py
│   │   ├── rag_search.py           # Vector DB queries
│   │   └── README.md
│   ├── iqvia/
│   │   ├── agent.py
│   │   ├── market_data.py
│   │   └── README.md
│   ├── clinical_trials/
│   │   ├── agent. py
│   │   ├── registry_search.py
│   │   └── README.md
│   ├── exim_trends/
│   │   ├── agent.py
│   │   ├── supply_chain.py
│   │   └── README.md
│   ├── patent_landscape/
│   │   ├── agent.py
│   │   ├── fto_search.py
│   │   └── README.md
│   ├── web_intel/
│   │   ├── agent.py
│   │   ├── tavily_client.py
│   │   └── README.md
│   └── shared/
│       ├── schemas.py              # Evidence item schemas
│       ├── logging.py
│       └── config.py
├── tests/
│   ├── unit/                       # Unit tests per agent
│   ├── integration/                # Orchestration tests
│   └── e2e/                        # End-to-end scenarios
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── k8s/
│   │   ├── master-agent-deployment.yaml
│   │   ├── worker-agent-deployment. yaml
│   │   └── vectordb-statefulset.yaml
│   └── grafana/
│       └── dashboards/
├── scripts/
│   ├── ingest_documents.py         # RAG document ingestion
│   ├── compute_embeddings.py
│   └── migrate_audit_logs.py
├── docs/
│   ├── architecture.md
│   ├── agent_api_spec.md
│   └── deployment_guide.md
├── . env.example
├── .gitignore
├── requirement.txt
├── README.md                       # This file
└── steps.md                        # Implementation steps
```

---

## Contributing

### Branch Naming

- Feature:  `feature/agent-name-capability`
- Bug fix: `fix/issue-number-short-desc`
- Experiment: `exp/hypothesis-name`

Example:  `feature/patent-agent-fto-search`, `fix/123-rank-verify-timeout`

### Pull Request Process

1. Create a feature branch from `main`
2. Add tests for new functionality
3. Update relevant READMEs
4. Add a changelog entry (see below)
5. Open PR with clear description of changes
6. Ensure CI passes (tests, linting, security checks)
7. Request review from team
8. Merge after approval

### Changelog

Add entries to `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [Unreleased]

### Added
- Patent Landscape Agent now supports EPC prior art searches

### Fixed
- Tavily timeout issue when scraping large news archives
```

### Adding a New Agent

1. Create agent directory:  `agents/<agent_name>/`
2. Implement: 
   - `agent.py` — Main agent logic
   - `retriever.py` or `client.py` — External API integration
   - `scoring.py` — Evidence scoring logic
   - `__init__.py`
3. Add tests in `tests/unit/<agent_name>/`
4. Add `README.md` with:
   - External API requirements
   - Evidence item schema
   - Example outputs
   - Scoring methodology
5. Register agent in Master Agent's `orchestrator.py`
6. Update this README's Agents section

---

## Team & Contact

**Project:** EY Techathon 6 Multi-Agent Orchestrator  
**Maintainer:** Aditya Channa  
**GitHub:** https://github.com/adityachanna/EY  
**Email:** aditya. channa@... 

### Support & Questions

For technical issues, API integration questions, or deployment assistance:
1. Open an issue on GitHub
2. Check existing documentation in `/docs/`
3. Review agent-specific READMEs in `/agents/`

### Acknowledgments

- LangGraph for orchestration framework
- NCBI PubMed for biomedical literature access
- Tavily for web intelligence
- Open-source community for embeddings & vector DB tools

---

**Thank you for using EY Techathon 6! **

This README is the single source of truth for architecture, agents, and operational guidance. Keep it current as the system evolves. 

For questions or suggestions, reach out to the team via GitHub Issues. 
