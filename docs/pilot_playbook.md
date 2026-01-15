# Crafta Revenue Control Room - Pilot Playbook

## Service Product Definition

### Service Name
**Crafta Revenue Control Room** - Phase 0/1 Supervised Invoice Automation

### Core Job-to-be-Done
Ensure customer contracts become correct invoices before entering the ERP, with AI-assisted drafting and human approval at every step.

### Scope of Pilot Service (Phase 0)

**Included:**
- Ingestion of up to 30 contracts (PDF/DOCX)
- AI-powered contract parsing and billing term extraction
- Work event/timesheet data integration
- Invoice draft generation with line-by-line explainability
- Controller review and approval workflow
- Exception flagging and resolution tracking
- CSV export of recovered/recoverable invoices
- Executive summary of findings
- 1x walkthrough session (30-60 min)

**Out of Scope:**
- Direct ERP write (manual export only in Phase 0)
- Ongoing automated monitoring
- Multi-currency handling (single currency per pilot)
- Custom integrations beyond CSV/PDF
- Historical audit reconciliation (forward-looking only)

### Pilot Deliverables
1. `recovered_invoices.csv` - All proposed invoice lines with amounts, confidence, explainability
2. `executive_summary.pdf` - One-page findings: total value, leakage reasons, recommendations
3. `audit_snapshot.pdf` - Signed audit evidence of the analysis
4. Walkthrough recording (Loom or live session)

### Monthly Supervised Service Deliverables (Phase 1)
1. Weekly contract intake and parsing
2. Weekly invoice draft generation
3. Approval queue management
4. Exception triage and resolution
5. Monthly reconciliation report
6. Monthly business review (30 min)
7. ERP export assistance (manual or semi-automated)

### Required Client Inputs
- Contract files (PDF, DOCX)
- Work event data (CSV from timesheet/billing system)
- Customer master list (for mapping)
- ERP customer IDs (for export)
- Designated approver contacts
- 1 hour onboarding session

### Human Roles

**Crafta Side:**
- Account Lead: Client relationship, onboarding, delivery
- Service Analyst: Contract parsing QA, exception resolution
- Product Support: Technical assistance, bug resolution

**Client Side:**
- CFO/Finance Director: Sponsor, final sign-off authority
- Controller: Primary approver, exception reviewer
- Billing Operations: Data provider, work event input
- ERP Admin: Export execution, system mapping

---

## User Personas and Primary Tasks

### Persona 1: CFO (Chief Financial Officer)

**Primary Goal:** Ensure revenue is fully captured and audit-defensible before financial close.

**Main Fears:**
- Revenue leakage going undetected
- Audit findings from improper billing
- Systems bypassing financial controls
- AI making decisions without oversight

**Key Tasks in Crafta:**
- View pilot dashboard and metrics
- Review executive summary
- Approve high-value/sensitive invoices (escalated)
- Access audit trail for compliance reviews

**Trust Evidence:**
- Complete audit trail with timestamps
- Human approval requirement clearly visible
- Confidence scores on all AI outputs
- Signed PDF snapshots of decisions

**Success Metrics:**
- Recovered revenue identified
- Zero audit exceptions from Crafta-processed invoices
- Reduced time to invoice

---

### Persona 2: Controller

**Primary Goal:** Approve accurate invoices efficiently while maintaining control.

**Main Fears:**
- Approving incorrect amounts
- Missing contract nuances
- Being held responsible for AI errors
- Losing control over billing accuracy

**Key Tasks in Crafta:**
- Review invoice draft queue daily
- Approve/reject individual invoice lines
- Review AI explanations and source clauses
- Handle exceptions requiring clarification
- Generate audit snapshots

**Trust Evidence:**
- Line-by-line explainability
- Source contract clause links
- Confidence indicators
- Editable fields before approval
- Clear "I confirm I reviewed this" acknowledgment

**Success Metrics:**
- Approval acceptance rate >95%
- Time per approval <5 minutes
- Exception resolution <24 hours

---

### Persona 3: Billing Operations Manager

**Primary Goal:** Get invoices out accurately and on time with minimal rework.

**Main Fears:**
- Data entry errors
- Missing billable events
- Duplicate invoices
- Delayed invoice cycles

**Key Tasks in Crafta:**
- Upload contracts and work events
- Review parsing results
- Flag missing data or discrepancies
- Prepare data for Controller review
- Export approved invoices to ERP

**Trust Evidence:**
- Upload confirmation and status tracking
- Parsing accuracy indicators
- Clear data validation feedback
- Export success confirmation

**Success Metrics:**
- Invoice cycle time reduced
- Manual data entry eliminated
- Fewer billing disputes

---

### Persona 4: ERP Administrator

**Primary Goal:** Ensure clean data enters the ERP system correctly.

**Main Fears:**
- Bad data corrupting ERP
- Failed imports
- Duplicate records
- Reconciliation nightmares

**Key Tasks in Crafta:**
- Configure ERP field mapping
- Review export payloads before push
- Execute ERP imports
- Verify successful posting
- Handle failed imports

**Trust Evidence:**
- Field mapping preview
- Validation before push
- Rollback procedures documented
- Import success/failure logs

**Success Metrics:**
- 100% successful ERP imports
- Zero manual corrections needed
- Clean audit trail to ERP

---

## End-to-End User Journey

### Step 1: Contract Upload

**System Action:** Accept file upload, validate format, store securely, initiate parsing job

**User Action:** Billing Ops uploads PDF/DOCX via drag-drop or file picker

**Data Artifacts:**
- Contract record (uploaded status)
- File stored with encryption
- Action log entry

**UI Component:** Contract Library with upload zone

**Failure Modes:**
- Invalid file format → Show error, accept only PDF/DOCX
- File too large → Show size limit error
- Duplicate upload → Warn user, allow override

**Resolution:** User corrects file and re-uploads

---

### Step 2: Contract Parsing & Rule Extraction

**System Action:** Run OCR if needed, extract text, identify billing clauses using AI/regex, assign confidence scores

**User Action:** Wait for parsing, review extracted terms, edit if needed

**Data Artifacts:**
- Contract record (parsed status)
- Clause/term records with confidence
- Action log entry

**UI Component:** Contract detail view with terms editor

**Failure Modes:**
- Low quality scan → Flag for manual review
- No terms extracted → Prompt user to check file
- Low confidence terms → Highlight for review

**Resolution:** User edits terms or uploads better file

---

### Step 3: Work Evidence / Milestone Input

**System Action:** Accept CSV upload, validate columns, link to contract

**User Action:** Billing Ops uploads timesheet/milestone data

**Data Artifacts:**
- Work event records
- Link to contract
- Action log entry

**UI Component:** Work events upload page with validation feedback

**Failure Modes:**
- Invalid CSV format → Show column requirements
- Missing required fields → Row-level errors
- Date parsing errors → Highlight problem rows

**Resolution:** User fixes CSV and re-uploads

---

### Step 4: AI Invoice Draft Generation

**System Action:** Match work events to contract clauses, calculate line amounts, generate explanations, flag exceptions

**User Action:** Trigger draft generation from contract view

**Data Artifacts:**
- Invoice draft record
- Line item records with explainability
- Exception flags if confidence <80%
- Action log entry

**UI Component:** Invoice generation button, progress indicator

**Failure Modes:**
- No matching clauses → Exception raised
- Missing work events → Warning shown
- Calculation discrepancy → Flag for review

**Resolution:** System generates what it can, exceptions handled separately

---

### Step 5: Human Review & Approval

**System Action:** Present draft for review, capture approval/rejection

**User Action:** Controller reviews lines, reads explanations, approves or rejects

**Data Artifacts:**
- Approval record with signature hash
- Updated invoice status
- Action log entry

**UI Component:** Invoice detail page, Approval Modal

**Failure Modes:**
- Reviewer disagrees with amount → Edit before approve
- Missing information → Reject with reason
- Timeout on approval → Escalation trigger

**Resolution:** Edit and re-approve, or reject for correction

---

### Step 6: Exception Handling

**System Action:** Route exceptions to appropriate reviewer, track resolution

**User Action:** Reviewer investigates, adds comments, resolves or escalates

**Data Artifacts:**
- Exception record with status
- Comment history
- Resolution record
- Action log entry

**UI Component:** Exception Center

**Failure Modes:**
- Unresolved exception blocking invoice → Escalation
- Incorrect resolution → Audit flag

**Resolution:** Escalate to senior reviewer, document resolution

---

### Step 7: ERP Export

**System Action:** Generate ERP-formatted payload, present for review

**User Action:** ERP Admin reviews mapping, executes export/push

**Data Artifacts:**
- ERP export batch record
- Export payload (JSON)
- Push confirmation
- Action log entry

**UI Component:** ERP Export Screen

**Failure Modes:**
- Missing customer mapping → Block until resolved
- ERP connection failure → Retry with backoff
- Validation failure → Show specific errors

**Resolution:** Fix mapping, retry connection, correct validation issues

---

### Step 8: Audit Trail Generation

**System Action:** Compile all actions into audit snapshot, generate signed PDF

**User Action:** Request audit export for specific entity or time range

**Data Artifacts:**
- Audit snapshot PDF
- Data hash for integrity
- Optional RSA signature

**UI Component:** Audit Timeline Viewer with export button

**Failure Modes:**
- Incomplete data → Warning on export
- PDF generation failure → Retry or export JSON

**Resolution:** System ensures complete data, fallback to JSON

---

### Step 9: Monthly Reporting

**System Action:** Generate monthly metrics and reconciliation report

**User Action:** CFO/Controller reviews report, discusses in monthly review

**Data Artifacts:**
- Monthly report PDF
- Metrics dashboard data
- Trend analysis

**UI Component:** Pilot Dashboard, Report generator

**Failure Modes:**
- Missing data for period → Warning shown
- Calculation errors → QA before release

**Resolution:** Manual verification before delivery

---

## Service Operations Workflow

### Pilot Timeline (Day 0-14)

#### Day 0: Kickoff
- **Crafta:** Send welcome email, schedule onboarding
- **Client:** Confirm receipt, identify data contacts
- **Artifact:** Pilot scope document signed

#### Day 1-2: Data Collection
- **Crafta:** Provide upload instructions, CSV templates
- **Client:** Upload contracts (up to 30), work events CSV
- **Artifact:** All contracts uploaded, status confirmed

#### Day 3-5: Processing
- **Crafta:** Run parsing, generate drafts, QA results
- **Client:** Available for clarification questions
- **Artifact:** Draft invoices generated, exceptions flagged

#### Day 6-7: Review Preparation
- **Crafta:** Prepare review queue, document exceptions
- **Client:** Clear approver calendar for review session
- **Artifact:** Review-ready invoice queue

#### Day 8-10: Approval Cycle
- **Crafta:** Support Controller through approvals
- **Client:** Controller reviews and approves/rejects lines
- **Artifact:** Approved invoices, resolved exceptions

#### Day 11-12: Export & Delivery
- **Crafta:** Generate CSV export, executive summary
- **Client:** ERP Admin receives export file
- **Artifact:** recovered_invoices.csv, executive_summary.pdf

#### Day 13-14: Wrap-up
- **Crafta:** Conduct walkthrough session, deliver audit snapshot
- **Client:** Acknowledge pilot completion
- **Artifact:** Walkthrough recording, audit_snapshot.pdf

#### Pilot Acceptance Criteria
- [ ] All uploaded contracts parsed
- [ ] Invoice drafts generated with >90% average confidence
- [ ] Controller approved or rejected all lines
- [ ] CSV export delivered
- [ ] Executive summary delivered
- [ ] Walkthrough completed

---

### Monthly Supervised Service

#### Weekly Cycle
- **Monday:** Client uploads new contracts and work events
- **Tuesday-Wednesday:** Crafta processes and QA's drafts
- **Thursday:** Controller reviews and approves
- **Friday:** Export and exception resolution

#### Monthly Cycle
- **Week 1-3:** Normal weekly cycles
- **Week 4:** Monthly reconciliation and reporting
- **End of Month:** Business review call (30 min)

#### Support Channels
- **Email:** support@crafta.ai (response <4 hours)
- **Slack:** Dedicated channel for pilot clients (response <1 hour)
- **Video call:** Scheduled via Calendly for complex issues

---

## SLA and Support Structure

### Response Times

| Severity | Description | Response Time | Resolution Target |
|----------|-------------|---------------|-------------------|
| Critical | System down, data loss | 1 hour | 4 hours |
| High | Blocking approval workflow | 4 hours | 24 hours |
| Medium | Feature issue, workaround exists | 24 hours | 72 hours |
| Low | Question, enhancement request | 48 hours | 1 week |

### Escalation Path
1. Service Analyst (first contact)
2. Account Lead (if unresolved in 24h)
3. Product Lead (if critical or SLA breach)

### Monthly Service Report Contents
- Contracts processed (count, value)
- Invoices generated and approved
- Average confidence score
- Exception rate and resolution time
- Time to approval metrics
- Recommendations for next month

### Service Credits
- SLA breach on Critical: 10% of monthly fee credit
- SLA breach on High (3+ occurrences): 5% credit
- Chronic underperformance: Pilot fee refund option

---

## Security, Trust, and Audit Requirements

### Access Control Model

| Role | Contracts | Invoices | Approvals | Audit | Settings |
|------|-----------|----------|-----------|-------|----------|
| Admin | Full | Full | Full | Full | Full |
| CFO | Read | Read | Approve (escalated) | Full | Read |
| Controller | Read | Full | Approve | Read | None |
| Billing Ops | Create/Read | Read | None | Limited | None |
| ERP Admin | None | Read | None | Read | ERP config |
| Viewer | Read | Read | None | Read | None |

### Data Retention
- Active data: Retained indefinitely
- Deleted contracts: Soft delete, recoverable for 90 days
- Audit logs: Immutable, retained 7 years minimum
- Uploaded files: Encrypted at rest, retained per contract lifecycle

### Audit Log Immutability
- All log entries are append-only
- Each entry includes timestamp, actor, action, payload hash
- Log exports include integrity hash
- Tampering detection via hash chain verification

### Approval Signature Capture
- Approver name and email (typed)
- Timestamp (system-generated)
- Invoice snapshot hash at approval time
- Approval method (UI, API)
- Optional 2FA verification

### Evidence Attachment Handling
- Source files linked to contract record
- Work event CSVs preserved
- All attachments encrypted at rest
- Integrity hash on all files

### Export Integrity
- All exports include generation timestamp
- Data hash included in export
- Audit trail link for traceability
- Optional RSA signature on PDFs

---

## Pricing Guidelines

### Pilot Pricing

| Pilot Tier | Contracts | Duration | Fee (USD) |
|------------|-----------|----------|-----------|
| Starter | Up to 15 | 10 days | $3,000 |
| Standard | Up to 30 | 14 days | $5,000 |
| Extended | Up to 50 | 21 days | $7,500 |

**Success Fee Option:** 20% of recovered revenue above $10,000 threshold

**Money-Back Guarantee:** If recoverable revenue identified is $0, pilot fee refunded (optional offer).

### Monthly Service Pricing

| Tier | Contracts/Month | Invoices/Month | Fee (USD/month) |
|------|-----------------|----------------|-----------------|
| Basic | Up to 20 | Up to 50 | $1,500 |
| Standard | Up to 50 | Up to 150 | $3,000 |
| Premium | Up to 100 | Up to 300 | $5,000 |
| Enterprise | Unlimited | Unlimited | Custom |

---

## First Client Engagement Checklist

### Before First Contact
- [ ] Pilot playbook ready
- [ ] Sample data templates available
- [ ] Demo environment accessible
- [ ] Pricing document approved

### Discovery Call
- [ ] Understand contract volume
- [ ] Identify pain points (leakage, speed, accuracy)
- [ ] Confirm ERP system
- [ ] Identify stakeholders (CFO, Controller, Billing Ops)

### Proposal
- [ ] Customize pilot scope
- [ ] Set expectations on deliverables
- [ ] Confirm pricing and timeline
- [ ] Send SOW for signature

### Kickoff
- [ ] Welcome email with data requirements
- [ ] Schedule onboarding call
- [ ] Provide upload instructions
- [ ] Set up communication channel

### Delivery
- [ ] Regular status updates
- [ ] Address questions promptly
- [ ] Deliver on timeline
- [ ] Conduct walkthrough
- [ ] Collect feedback

### Conversion to Monthly
- [ ] Present monthly service proposal
- [ ] Discuss ongoing cadence
- [ ] Sign service agreement
- [ ] Transition to standard support
