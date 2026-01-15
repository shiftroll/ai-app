# Statement of Work: Crafta Revenue Control Room Pilot

## PILOT AGREEMENT

**Client:** [Client Company Name]
**Crafta Entity:** Crafta Inc.
**Effective Date:** [Date]
**Pilot Duration:** 14 calendar days from data receipt

---

## 1. SCOPE OF SERVICES

Crafta will provide a Revenue Control Room pilot engagement consisting of:

### 1.1 Contract Analysis
- Ingestion of up to **30 customer contracts** (PDF or DOCX format)
- AI-powered extraction of billing terms, rate cards, milestones, and payment clauses
- Human quality assurance on extracted terms

### 1.2 Invoice Draft Generation
- Matching of provided work events/timesheets to contract terms
- Generation of invoice line items with amounts, explanations, and confidence scores
- Exception flagging for low-confidence or unusual items

### 1.3 Approval Workflow Support
- Presentation of invoice drafts in Crafta Control Room interface
- Controller review and approval workflow
- Exception resolution assistance

### 1.4 Deliverables
- `recovered_invoices.csv` — All proposed invoice lines with amounts and explainability
- `executive_summary.pdf` — One-page summary of findings, total value, recommendations
- `audit_snapshot.pdf` — Signed audit evidence of the analysis process
- **1x walkthrough session** (30-60 minutes, recorded for future reference)

---

## 2. CLIENT RESPONSIBILITIES

Client agrees to provide:

### 2.1 Required Data (within 3 business days of kickoff)
- Contract files (PDF or DOCX) — up to 30 contracts
- Work events/timesheet data (CSV format)
- Customer list with ERP identifiers (if available)

### 2.2 Personnel Access
- Designated Controller for approval workflow (minimum 2 hours availability in Week 2)
- Point of contact for data clarification questions

### 2.3 Communication
- Response to clarification requests within 24 business hours
- Participation in walkthrough session

---

## 3. TIMELINE

| Phase | Days | Activities |
|-------|------|------------|
| Data Collection | Day 1-3 | Client uploads contracts and work events |
| Processing | Day 4-7 | Crafta parses contracts, generates drafts |
| Review | Day 8-11 | Controller reviews and approves/rejects |
| Delivery | Day 12-14 | Crafta delivers final artifacts, walkthrough |

---

## 4. PRICING

### 4.1 Pilot Fee
- **Standard Pilot (up to 30 contracts):** $5,000 USD
- Payment due: 50% upon signing, 50% upon delivery

### 4.2 Success Fee (Optional)
- 20% of total recovered/recoverable invoice value identified above $10,000 threshold
- Payable within 30 days of pilot completion if applicable

### 4.3 Money-Back Guarantee
If Crafta identifies $0 in recoverable invoice value, the pilot fee will be refunded in full upon Client request.

---

## 5. ACCEPTANCE CRITERIA

The pilot is considered complete when:

- [ ] All uploaded contracts have been parsed
- [ ] Invoice drafts generated for all applicable work events
- [ ] Controller has reviewed 100% of invoice lines
- [ ] `recovered_invoices.csv` delivered
- [ ] `executive_summary.pdf` delivered
- [ ] Walkthrough session completed

---

## 6. CONFIDENTIALITY

Crafta agrees to:
- Treat all Client data as confidential
- Use data solely for the purpose of this pilot engagement
- Delete or return Client data within 30 days of pilot completion upon request
- Not share Client data with third parties without written consent

---

## 7. LIMITATION OF LIABILITY

Crafta's total liability under this pilot agreement shall not exceed the pilot fee paid by Client.

Crafta does not guarantee any specific amount of recovered revenue. The pilot is an analysis service; actual revenue recovery depends on Client action.

---

## 8. ACCEPTANCE

**Client:**

Name: _________________________
Title: _________________________
Date: _________________________
Signature: _____________________

**Crafta Inc.:**

Name: _________________________
Title: _________________________
Date: _________________________
Signature: _____________________

---

## APPENDIX A: Data Requirements

### Contract Files
- Format: PDF or DOCX
- Readable text (not scanned images if possible)
- Include rate cards, SOWs, amendments

### Work Events CSV
Required columns:
```
event_id,date,description,units,unit_type,amount,external_ref
```

Example:
```csv
we_001,2025-12-12,Consulting hours,10,hour,2000,PO-778
```

### Customer List (Optional)
```
customer_name,customer_id,erp_customer_ref
```

---

## APPENDIX B: Sample Executive Summary Structure

1. **Total Recoverable Amount**
2. **Breakdown by Category** (T&M, Milestones, Expenses)
3. **Top 3 Findings** (Leakage reasons, contract gaps)
4. **Confidence Analysis** (High/Medium/Low confidence line distribution)
5. **Recommended Actions**
6. **Next Steps**
