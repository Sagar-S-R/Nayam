"""Add more seed data for events and drafts to enrich the demo."""
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.event import Event, EventType, EventStatus, EventPriority
from app.models.draft import Draft, DraftType, DraftStatus
from app.models.user import User

db = SessionLocal()
admin = db.query(User).first()
uid = admin.id if admin else None
now = datetime.now(timezone.utc)

# ── MORE EVENTS ──────────────────────────────────────────────────────
extra_events = [
    dict(title="RTI Response Deadline - Case 2026/117",
         description="Final date to respond to RTI query regarding road construction contracts in Ward 5. All relevant documents must be compiled.",
         event_type=EventType.DEADLINE, status=EventStatus.SCHEDULED, priority=EventPriority.HIGH,
         start_time=now + timedelta(days=2, hours=5), end_time=now + timedelta(days=2, hours=6),
         location="RTI Cell, Collectorate", attendees="PIO, APIO, Legal Advisor",
         department="General Administration", ward="Ward 5", created_by=uid),

    dict(title="Gram Sabha - Ward 6",
         description="Quarterly Gram Sabha meeting. Agenda: review of MGNREGA works, new BPL list verification, village road repair priorities.",
         event_type=EventType.MEETING, status=EventStatus.SCHEDULED, priority=EventPriority.MEDIUM,
         start_time=now + timedelta(days=3, hours=2), end_time=now + timedelta(days=3, hours=5),
         location="Panchayat Bhawan, Ward 6", attendees="Sarpanch, Gram Sachiv, Ward Members, Citizens",
         department="Panchayati Raj", ward="Ward 6", created_by=uid),

    dict(title="Electricity Department Coordination",
         description="Coordinate with state electricity board on transformer replacement schedule for Wards 2 and 3. Frequent outages reported.",
         event_type=EventType.MEETING, status=EventStatus.SCHEDULED, priority=EventPriority.HIGH,
         start_time=now + timedelta(days=1, hours=5), end_time=now + timedelta(days=1, hours=7),
         location="SDM Office", attendees="SDM, XEN Electricity, JE Ward 2, JE Ward 3",
         department="Electricity Department", ward="Ward 2", created_by=uid),

    dict(title="School Building Safety Inspection",
         description="Annual structural safety audit of government schools in Wards 1-3. Priority check on buildings older than 20 years.",
         event_type=EventType.SITE_VISIT, status=EventStatus.SCHEDULED, priority=EventPriority.HIGH,
         start_time=now + timedelta(days=5, hours=1), end_time=now + timedelta(days=5, hours=6),
         location="Govt. Primary School, Ward 1 (start)", attendees="BEO, PWD Engineer, School Principals",
         department="Education Department", ward="Ward 1", created_by=uid),

    dict(title="Weekly Law & Order Review",
         description="Regular weekly review with police on law and order situation, pending cases, and upcoming festivals security planning.",
         event_type=EventType.REVIEW, status=EventStatus.SCHEDULED, priority=EventPriority.MEDIUM,
         start_time=now + timedelta(days=1, hours=0), end_time=now + timedelta(days=1, hours=1),
         location="SP Office", attendees="DM, SP, DSP, SHOs",
         department="Police", created_by=uid),

    dict(title="Ration Distribution Drive - Ward 4",
         description="Special ration distribution for flood-affected families in Ward 4, Sector 8. 200 families identified for relief.",
         event_type=EventType.PUBLIC_EVENT, status=EventStatus.SCHEDULED, priority=EventPriority.HIGH,
         start_time=now + timedelta(days=2, hours=1), end_time=now + timedelta(days=2, hours=8),
         location="Community Hall, Sector 8, Ward 4", attendees="Supply Inspector, 10 Volunteers, Ward Councillor",
         department="Food & Civil Supplies", ward="Ward 4", created_by=uid),

    dict(title="Vaccination Camp Planning",
         description="Plan for pulse polio and routine immunization camp across all wards. Coordinate with PHC staff.",
         event_type=EventType.MEETING, status=EventStatus.SCHEDULED, priority=EventPriority.MEDIUM,
         start_time=now + timedelta(days=9, hours=3), end_time=now + timedelta(days=9, hours=5),
         location="CMO Office", attendees="CMO, PHC Doctors, ASHA Workers Coordinator",
         department="Health Department", created_by=uid),

    dict(title="Revenue Court Hearing - Land Dispute",
         description="Hearing for land dispute case No. 45/2025 between parties in Ward 7. Both parties summoned with documents.",
         event_type=EventType.HEARING, status=EventStatus.SCHEDULED, priority=EventPriority.MEDIUM,
         start_time=now + timedelta(days=4, hours=3), end_time=now + timedelta(days=4, hours=5),
         location="Revenue Court, Tehsil Office", attendees="SDM (Presiding), Patwari, Both Parties",
         department="Revenue Department", ward="Ward 7", created_by=uid),

    dict(title="CANCELLED: Contractor Meeting (postponed)",
         description="Meeting with road contractors for NH-44 widening project postponed due to state-level review.",
         event_type=EventType.MEETING, status=EventStatus.CANCELLED, priority=EventPriority.MEDIUM,
         start_time=now - timedelta(days=1, hours=2), end_time=now - timedelta(days=1),
         location="PWD Office", attendees="EE PWD, Contractors",
         department="Public Works", created_by=uid),

    dict(title="Completed: Flood Damage Assessment - Ward 4",
         description="Field assessment of flood damage in Ward 4 completed. 47 houses partially damaged, 8 fully damaged. Report submitted.",
         event_type=EventType.SITE_VISIT, status=EventStatus.COMPLETED, priority=EventPriority.HIGH,
         start_time=now - timedelta(days=3, hours=5), end_time=now - timedelta(days=3, hours=1),
         location="Ward 4, Sectors 6-9", attendees="Tehsildar, Patwari, Revenue Inspector",
         department="Revenue Department", ward="Ward 4", created_by=uid),

    dict(title="Completed: District Development Committee",
         description="Quarterly DDC meeting completed. Approved 5 new projects, reviewed 12 ongoing schemes. Minutes circulated.",
         event_type=EventType.MEETING, status=EventStatus.COMPLETED, priority=EventPriority.HIGH,
         start_time=now - timedelta(days=7, hours=4), end_time=now - timedelta(days=7, hours=1),
         location="Collectorate Conference Hall", attendees="DM, CDO, All BDOs, MPs/MLAs Representatives",
         department="Planning Department", created_by=uid),

    dict(title="IN PROGRESS: Road Resurfacing - Ward 3",
         description="Road resurfacing work on Main Market Road, Ward 3 currently underway. Expected completion: 3 days.",
         event_type=EventType.SITE_VISIT, status=EventStatus.IN_PROGRESS, priority=EventPriority.MEDIUM,
         start_time=now - timedelta(hours=6), end_time=now + timedelta(days=3),
         location="Main Market Road, Ward 3", attendees="JE PWD, Contractor Foreman",
         department="Public Works", ward="Ward 3", created_by=uid),
]

for ed in extra_events:
    db.add(Event(**ed))
db.commit()
print(f"Added {len(extra_events)} more events (total: {db.query(Event).count()})")


# ── MORE DRAFTS ──────────────────────────────────────────────────────

MEETING_AGENDA_CONTENT = """# Ward Development Committee Meeting Agenda

**Date:** 5 March 2026, 10:00 AM
**Venue:** Municipal Hall, Room 201
**Chaired by:** District Magistrate

---

## 1. Call to Order & Attendance (10:00 - 10:10)
- Roll call of Ward Members 1-5
- Confirmation of quorum

## 2. Approval of Previous Minutes (10:10 - 10:20)
- Review minutes of meeting held on 5 February 2026
- Motion for approval

## 3. Road Repair Budget Review (10:20 - 10:50)
- Current allocation: Rs 12.5 Lakhs
- Expenditure to date: Rs 8.3 Lakhs (66.4%)
- Pending works: Ward 2 internal roads, Ward 5 NH-44 access road
- **Decision needed:** Supplementary allocation request of Rs 4 Lakhs

## 4. Drainage Status Update (10:50 - 11:20)
- Ward 3 main drain desilting: 85% complete
- Ward 4 Sector 12 waterlogging: New pipeline approved
- Monsoon preparedness checklist review

## 5. Citizen Grievance Review (11:20 - 11:50)
- Total pending grievances: 23 (down from 41 last month)
- High-priority cases requiring immediate action: 5
- NAYAM platform performance metrics

## 6. New Business (11:50 - 12:00)
- Ward Mission 2027 program proposal
- Next meeting date confirmation

## 7. Adjournment

---
*Secretary: SDO Verma | Minutes to be circulated within 48 hours*"""

PUBLIC_NOTICE_CONTENT = """# PUBLIC NOTICE

## Regarding: Road Closure for Resurfacing Work — Main Market Road, Ward 3

**Notice No.:** PWD/2026/RC-045
**Date:** 3 March 2026

---

To all residents and commuters,

It is hereby notified for general information that **Main Market Road in Ward 3** will remain closed for vehicular traffic from **4 March 2026 to 7 March 2026** due to road resurfacing work under the Annual Road Maintenance Program.

### Alternative Routes:
1. **Light vehicles:** Use Nehru Marg via Sector 4 crossing
2. **Heavy vehicles:** Divert via Ring Road (NH-44 bypass)
3. **Emergency vehicles:** Will be provided escort through work zone

### Timings:
- Work hours: 7:00 AM to 6:00 PM daily
- Road will be open for pedestrians with safety barriers

### Contact for Queries:
- **Control Room:** 1800-XXX-XXXX (toll free)
- **JE PWD Ward 3:** 98XXX-XXXXX

Citizens are requested to cooperate and plan their travel accordingly. Inconvenience caused is deeply regretted.

**By Order,**
**Executive Engineer, Public Works Department**
**District Administration**"""

FORMAL_LETTER_CONTENT = """# OFFICE OF THE DISTRICT MAGISTRATE

**Ref No.:** DM/2026/WS-087
**Date:** 3 March 2026

To,
The Chief Engineer,
State Water Supply & Sewerage Board,
State Capital

**Subject: Urgent Request for Emergency Pipeline Replacement — Sector 12, Ward 4**

Sir/Madam,

I am writing to bring to your urgent attention the critical water supply situation in Sector 12, Ward 4 of our district.

**Background:**
The main water supply pipeline serving Sector 12 (installed in 2008) has deteriorated beyond repair. Over the past 3 months, we have recorded 14 major leakages and the supply has become highly irregular, affecting approximately 5,000 residents.

**Current Situation:**
1. Daily water supply reduced to 2 hours (from standard 6 hours)
2. 342 written complaints received from residents
3. Emergency tanker deployment costing Rs 15,000/day from district funds
4. Risk of water contamination due to pipe corrosion

**Request:**
I request your kind office to:
1. **Sanction emergency pipeline replacement** under the State Water Infrastructure Fund
2. **Estimated cost:** Rs 42 Lakhs (detailed estimate enclosed)
3. **Deploy a technical team** for survey within 7 working days

The matter has been flagged as HIGH priority on our NAYAM governance platform and is being monitored at the DM level.

I shall be grateful for your early and favorable consideration.

Yours faithfully,

**District Magistrate**
**[District Name]**

Encl: (1) Detailed Cost Estimate (2) Pipeline Survey Report (3) Citizen Complaint Summary"""

RTI_RESPONSE_CONTENT = """# RIGHT TO INFORMATION ACT, 2005
## Response to RTI Application

**RTI Reference No.:** RTI/2026/0117
**Date of Application:** 15 February 2026
**Date of Response:** 3 March 2026
**PIO:** Assistant Collector (Administration)

---

**Applicant:** [Name withheld for privacy]
**Subject:** Information regarding road construction contracts in Ward 5

---

Dear Applicant,

With reference to your RTI application dated 15 February 2026 seeking information about road construction contracts awarded in Ward 5 during FY 2025-26, the following information is provided:

### Point-wise Response:

**Q1: Total number of road construction contracts awarded in Ward 5 in FY 2025-26**
**A1:** A total of **7 contracts** were awarded during the period April 2025 to February 2026.

**Q2: Names of contractors and contract values**
**A2:**
| S.No. | Contractor | Work Description | Contract Value (Rs) |
|-------|-----------|-----------------|-------------------|
| 1 | ABC Constructions | Internal roads Sector 3 | 8,50,000 |
| 2 | XYZ Infra Pvt Ltd | Main road resurfacing | 12,30,000 |
| 3 | PQR Builders | Drain-cum-road Sector 7 | 6,75,000 |
| 4 | LMN Associates | Footpath construction | 3,20,000 |
| 5 | DEF Contractors | Road patching (annual) | 4,50,000 |
| 6 | GHI Works | Bridge approach road | 9,80,000 |
| 7 | JKL Infrastructure | Colony road Sector 11 | 5,60,000 |

**Q3: Completion status of each contract**
**A3:** 4 contracts completed, 2 in progress, 1 not yet started.

**Q4: Quality inspection reports**
**A4:** Copies of inspection reports for completed works are enclosed (47 pages).

### Appeal Information:
If you are not satisfied with this response, you may file a First Appeal with the **First Appellate Authority (Additional District Magistrate)** within 30 days.

**Public Information Officer**
**District Administration**"""

GOVT_CIRCULAR_CONTENT = """# GOVERNMENT CIRCULAR

**Circular No.:** DM/GC/2026/012
**Date:** 3 March 2026

**To:** All Department Heads, Sub-Divisional Officers, Block Development Officers, and Tehsildars

**Subject: Implementation of NAYAM AI Governance Platform — Mandatory Adoption Directive**

---

In continuation of the District Administration's digital governance initiative, the following directions are issued for immediate compliance:

## 1. Platform Adoption (Effective Immediately)

All departmental offices under the district administration shall:
- Ensure **100% of officers** (Grade B and above) complete NAYAM platform registration by **15 March 2026**
- Log all citizen grievances received (in-person, written, or telephonic) on the NAYAM platform within **24 hours** of receipt
- Upload relevant documents (inspection reports, meeting minutes, field visit notes) to the NAYAM document repository

## 2. Weekly Compliance Reporting

- Every Monday by 11:00 AM, each department head shall submit a **weekly digital compliance report** through NAYAM
- The report shall include: grievances received, resolved, pending; documents uploaded; platform usage metrics
- Non-compliance will be noted in the officer's Annual Performance Appraisal

## 3. Training Schedule

| Batch | Date | Time | Venue |
|-------|------|------|-------|
| Batch 1 (Revenue, PWD, Water) | 8 March 2026 | 10 AM - 1 PM | Collectorate Hall |
| Batch 2 (Education, Health, Police) | 9 March 2026 | 10 AM - 1 PM | Collectorate Hall |
| Batch 3 (Panchayati Raj, Food, Electricity) | 10 March 2026 | 10 AM - 1 PM | Collectorate Hall |

## 4. Nodal Officers

Each department shall designate one **NAYAM Nodal Officer** responsible for:
- Ensuring data quality and timely updates
- Coordinating with the IT Cell for technical issues
- Reporting platform adoption metrics

## 5. Review Mechanism

The District Magistrate will review platform adoption progress in the **weekly coordination meeting** every Wednesday.

This circular supersedes all previous instructions on the subject.

**By Order of the District Magistrate**

*Distribution: All concerned*
*Copy to: State IT Department for information*"""

extra_drafts = [
    dict(title="Meeting Agenda: Ward Development Committee - 5 March",
         draft_type=DraftType.MEETING_AGENDA, status=DraftStatus.APPROVED,
         content=MEETING_AGENDA_CONTENT,
         prompt_context="Prepare agenda for monthly ward development committee meeting covering road repairs, drainage, and grievances",
         tone="Professional", audience="Ward Committee Members, Department Officers",
         department="General Administration", version=1,
         extra_metadata={"word_count": 280, "ai_generated": True},
         created_by=uid),

    dict(title="Public Notice: Road Closure - Ward 3 Main Market Road",
         draft_type=DraftType.PUBLIC_NOTICE, status=DraftStatus.PUBLISHED,
         content=PUBLIC_NOTICE_CONTENT,
         prompt_context="Public notice about road closure for resurfacing work on Main Market Road in Ward 3",
         tone="Informative", audience="General Public, Commuters",
         department="Public Works", version=1,
         extra_metadata={"word_count": 220, "ai_generated": True},
         created_by=uid),

    dict(title="Formal Letter: Emergency Pipeline Replacement Request to State Board",
         draft_type=DraftType.LETTER, status=DraftStatus.UNDER_REVIEW,
         content=FORMAL_LETTER_CONTENT,
         prompt_context="Letter to State Water Board requesting emergency pipeline replacement for Sector 12, Ward 4",
         tone="Formal", audience="State Government Officials",
         department="Water Supply Department", version=2,
         extra_metadata={"word_count": 260, "ai_generated": True},
         created_by=uid),

    dict(title="RTI Response: Road Construction Contracts - Ward 5",
         draft_type=DraftType.RTI_RESPONSE, status=DraftStatus.APPROVED,
         content=RTI_RESPONSE_CONTENT,
         prompt_context="RTI response about road construction contracts awarded in Ward 5 during FY 2025-26",
         tone="Formal", audience="RTI Applicant",
         department="General Administration", version=1,
         extra_metadata={"word_count": 320, "ai_generated": False},
         created_by=uid),

    dict(title="Government Circular: NAYAM Platform Mandatory Adoption",
         draft_type=DraftType.CIRCULAR, status=DraftStatus.PUBLISHED,
         content=GOVT_CIRCULAR_CONTENT,
         prompt_context="Circular directing all departments to adopt NAYAM governance platform with training schedule and compliance requirements",
         tone="Authoritative", audience="Department Heads, All Officers",
         department="General Administration", version=1,
         extra_metadata={"word_count": 350, "ai_generated": True},
         created_by=uid),
]

for dd in extra_drafts:
    db.add(Draft(**dd))
db.commit()
print(f"Added {len(extra_drafts)} more drafts (total: {db.query(Draft).count()})")
db.close()
print("Done! Database now has rich demo data for both Schedules and Drafts.")
