# Crafta Revenue Control Room

A production-grade MVP for contract-to-invoice automation with human-in-the-loop approval workflows.

## Overview

Crafta Revenue Control Room enables:
- **Contract Ingestion & Parsing**: Upload PDFs/DOCX, extract structured terms via AI/OCR
- **Invoice Draft Generation**: Auto-generate invoice lines from contracts + work events
- **Human-in-the-Loop Approval**: Controllers review and approve before ERP push
- **Audit Trail**: Complete versioned evidence for every action
- **ERP Integration**: Push approved invoices to QuickBooks, Xero, or NetSuite

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Contract │  │ Invoice  │  │ Exception│  │ Audit Timeline   │ │
│  │ Library  │  │ Queue    │  │ Center   │  │ & Approval Modal │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Backend API (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Contract │  │ Invoice  │  │ Approval │  │ Audit & Export   │ │
│  │ Service  │  │ Service  │  │ Service  │  │ Service          │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Pipeline (Python)                     │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │ parse_contract   │  │ derive_invoice_lines                 │ │
│  │ (OCR + LLM)      │  │ (Rule engine + explainability)       │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ERP Connectors                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │QuickBooks│  │   Xero   │  │ NetSuite │                       │
│  └──────────┘  └──────────┘  └──────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 14+ (or Supabase)
- Redis (optional, for job queues)

### Local Development

1. **Clone and install dependencies:**

```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Agents
cd ../agents
pip install -r requirements.txt
```

2. **Set up environment variables:**

```bash
# Copy example env files
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
```

3. **Configure environment variables:**

```bash
# backend/.env
DATABASE_URL=postgresql://user:pass@localhost:5432/crafta
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-32-byte-encryption-key
RSA_PRIVATE_KEY=your-rsa-private-key
OPENAI_API_KEY=your-openai-key  # For LLM parsing

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Initialize database:**

```bash
cd backend
alembic upgrade head
python scripts/seed_sample_data.py
```

5. **Start services:**

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Agent worker (optional)
cd agents
python worker.py
```

6. **Access the app:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Run End-to-End Pilot Simulation

```bash
# Generate pilot deliverables with sample data
cd backend
python scripts/run_pilot_simulation.py

# Outputs:
# - outputs/recovered_invoices.csv
# - outputs/executive_summary.pdf
# - outputs/audit_snapshot.pdf
```

## Phase Definitions

### Phase 0: Forensic (Manual-First)
- Manual/agent-assisted contract parsing
- Invoice reconstruction and gap analysis
- Deliverables: `recovered_invoices.csv`, executive summary
- Human validates all outputs

### Phase 1: Assisted Control Room
- Web UI with contract upload and parsing
- Generated invoice drafts with explainability
- Human approve/deny workflow
- Push to ERP (manual button only)
- Complete audit logging

## Key Features

### Human-in-the-Loop Controls

1. **No Auto-Post**: ERP push requires explicit human approval
2. **Confidence Thresholds**: Lines < 80% confidence flagged for review
3. **Rev-Rec Sensitivity**: Multi-element arrangements require CFO approval
4. **Audit Trail**: Every action logged with actor, timestamp, rationale

### Explainability

Each invoice line includes:
- Source contract clause reference
- Extraction reasoning (3-4 sentences)
- Confidence score
- Linked work events

### Audit Evidence

- Versioned snapshots of all decisions
- RSA-signed PDF artifacts
- Complete action log with payload hashes
- CFO/auditor-acceptable documentation

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/contracts/upload` | POST | Upload contract files |
| `/api/contracts/{id}` | GET | Get parsed contract |
| `/api/workevents/{contract_id}/upload` | POST | Upload work events |
| `/api/invoices/draft` | POST | Generate invoice draft |
| `/api/invoices/{id}` | GET | Get invoice draft |
| `/api/invoices/{id}/approve` | POST | Approve invoice |
| `/api/invoices/{id}/push` | POST | Push to ERP |
| `/api/audit/{entity_id}` | GET | Get audit trail |
| `/api/anonize/{contract_id}` | POST | Anonymize for case study |

## Deployment

### Docker

```bash
docker-compose up -d
```

### Cloud Deployment

See [docs/deployment.md](docs/deployment.md) for:
- AWS/GCP/Azure deployment guides
- Kubernetes configurations
- CI/CD pipeline setup

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
cd tests
pytest integration/ -v
```

## Pilot Pack

The pilot deliverables include:
- `recovered_invoices.csv` - All proposed recoverable invoices
- `executive_summary.pdf` - One-page CFO summary
- `audit_snapshot.pdf` - Signed audit evidence
- Demo script for Loom recording

## Documentation

- [API Reference](docs/api.md)
- [Data Schemas](docs/schemas.md)
- [Deployment Guide](docs/deployment.md)
- [Pilot SOW Template](docs/pilot_sow.md)
- [SOC2 Checklist](docs/soc2_checklist.md)
- [Runbook](docs/runbook.md)

## Security

- All data encrypted at rest (AES-256)
- TLS enforced for all connections
- Role-based access control
- Complete audit logging
- GDPR-compliant data retention

## License

Proprietary - Crafta Inc.

## Support

For pilot onboarding or support:
- Email: support@crafta.ai
- Documentation: https://docs.crafta.ai
