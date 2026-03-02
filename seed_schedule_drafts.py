"""Seed events and drafts for NAYAM Phase 2."""
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.event import Event, EventType, EventStatus, EventPriority
from app.models.draft import Draft, DraftType, DraftStatus
from app.models.user import User

db = SessionLocal()
admin = db.query(User).first()
uid = admin.id if admin else None
now = datetime.now(timezone.utc)

# ── Seed Events ──────────────────────────────────
events_data = [
    dict(title="Ward Development Committee Meeting",
         description="Monthly review of ongoing projects in Wards 1-5. Agenda: road repair budget, drainage status, citizen grievances.",
         event_type=EventType.MEETING, status=EventStatus.SCHEDULED, priority=EventPriority.HIGH,
         start_time=now + timedelta(days=1, hours=2), end_time=now + timedelta(days=1, hours=4),
         location="Municipal Hall, Room 201", attendees="DM Singh, SDO Verma, Ward Members 1-5",
         department="Public Works", ward="Ward 3", created_by=uid),
    dict(title="Water Supply Review",
         description="Review current water distribution schedule and address citizen complaints about irregular supply.",
         event_type=EventType.REVIEW, status=EventStatus.SCHEDULED, priority=EventPriority.HIGH,
         start_time=now + timedelta(days=2, hours=3), end_time=now + timedelta(days=2, hours=5),
         location="Water Department Office", attendees="JE Water Supply, Ward Engineers",
         department="Water Supply Department", ward="Ward 4", created_by=uid),
    dict(title="Public Hearing - New Market Construction",
         description="Public hearing for proposed commercial market in Ward 7. All stakeholders invited.",
         event_type=EventType.HEARING, status=EventStatus.SCHEDULED, priority=EventPriority.MEDIUM,
         start_time=now + timedelta(days=3, hours=1), end_time=now + timedelta(days=3, hours=3),
         location="Community Center, Ward 7", attendees="Public, Ward Councillor, Revenue Officer",
         department="Revenue Department", ward="Ward 7", created_by=uid),
    dict(title="Bridge Construction Site Visit",
         description="Inspection of under-construction bridge near Gandhi Nagar.",
         event_type=EventType.SITE_VISIT, status=EventStatus.SCHEDULED, priority=EventPriority.MEDIUM,
         start_time=now + timedelta(days=4, hours=0), end_time=now + timedelta(days=4, hours=2),
         location="Gandhi Nagar Bridge Site", attendees="Executive Engineer, Contractor Rep",
         department="Public Works", ward="Ward 2", created_by=uid),
    dict(title="Budget Submission Deadline",
         description="Final date for departmental budget proposals for FY 2026-27.",
         event_type=EventType.DEADLINE, status=EventStatus.SCHEDULED, priority=EventPriority.HIGH,
         start_time=now + timedelta(days=5), end_time=now + timedelta(days=5, hours=1),
         location="Online Portal", attendees="All Department Heads",
         department="Finance Department", is_all_day=True, created_by=uid),
    dict(title="Independence Day Celebration Planning",
         description="Plan cultural programs, security arrangements, and VIP seating for 15 August.",
         event_type=EventType.PUBLIC_EVENT, status=EventStatus.SCHEDULED, priority=EventPriority.MEDIUM,
         start_time=now + timedelta(days=7, hours=2), end_time=now + timedelta(days=7, hours=4),
         location="District Stadium", attendees="Cultural Officer, Police SP, Protocol Officer",
         department="General Administration", created_by=uid),
    dict(title="Sanitation Drive - Ward 1",
         description="Mega cleanliness campaign. Deploy 3 teams for complete ward coverage.",
         event_type=EventType.PUBLIC_EVENT, status=EventStatus.SCHEDULED, priority=EventPriority.LOW,
         start_time=now + timedelta(days=6, hours=1), end_time=now + timedelta(days=6, hours=6),
         location="Ward 1 - All sectors", attendees="Sanitation Inspector, 30 field workers",
         department="Sanitation Department", ward="Ward 1", created_by=uid),
    dict(title="Staff Performance Review",
         description="Quarterly KPI review for administrative staff.",
         event_type=EventType.REVIEW, status=EventStatus.SCHEDULED, priority=EventPriority.LOW,
         start_time=now + timedelta(days=8, hours=3), end_time=now + timedelta(days=8, hours=5),
         location="Conference Room B", attendees="HR Head, Section Officers",
         department="General Administration", created_by=uid),
    dict(title="Road Repair Inspection (completed)",
         description="Final inspection of NH-44 pothole repair completed.",
         event_type=EventType.SITE_VISIT, status=EventStatus.COMPLETED, priority=EventPriority.HIGH,
         start_time=now - timedelta(days=2, hours=3), end_time=now - timedelta(days=2, hours=1),
         location="NH-44 Km 23-25", attendees="PWD Engineer, Contractor",
         department="Public Works", ward="Ward 5", created_by=uid),
    dict(title="Monsoon Preparedness Meeting (completed)",
         description="Pre-monsoon planning meeting completed. All departments briefed.",
         event_type=EventType.MEETING, status=EventStatus.COMPLETED, priority=EventPriority.HIGH,
         start_time=now - timedelta(days=5, hours=4), end_time=now - timedelta(days=5, hours=2),
         location="Collectorate Conference Hall", attendees="All Department Heads",
         department="Disaster Management", created_by=uid),
]

for ed in events_data:
    db.add(Event(**ed))
db.commit()
print(f"Seeded {len(events_data)} events")

# ── Seed Drafts ──────────────────────────────────
SPEECH_CONTENT = """# Independence Day Address 2026

Respected dignitaries, fellow officers, and dear citizens of our district,

On this 80th Independence Day, as we hoist our Tricolour, I am reminded of the immense responsibility we carry -- to serve the people of this district with integrity, efficiency, and compassion.

## Our Achievements This Year

Over the past twelve months, our administration has:

1. **Resolved 847 citizen grievances** through the NAYAM governance platform -- a 40% improvement over last year.
2. **Completed 12 infrastructure projects** including the Gandhi Nagar bridge, Ward 3 drainage overhaul, and the new community health center.
3. **Digitized 95% of land records**, making them accessible to citizens online within minutes.

## Challenges Ahead

We must honestly acknowledge the work that remains. Water supply irregularities in Wards 4 and 6, the pending market construction in Ward 7, and the need for better sanitation coverage demand our urgent attention.

## Our Commitment

I pledge that this administration will:
- Launch the Ward Mission 2027 program for comprehensive development
- Implement AI-assisted decision-making through NAYAM for faster response times
- Ensure 100% grievance resolution within 30 days

Let us move forward together. Jai Hind, Jai Bharat!

Thank you."""

RESPONSE_CONTENT = """# Official Response

**Reference:** WS/2026/0342
**Date:** 28 February 2026
**Subject:** Irregular Water Supply in Sector 12, Ward 4

Dear Residents of Sector 12,

This is in response to your collective representation dated 20 February 2026 regarding irregular water supply in Sector 12, Ward 4.

The Water Supply Department has investigated the matter and identified two root causes:

1. **Pipeline deterioration** on the Sector 12 main line (installed 2008, beyond service life)
2. **Pump station capacity** insufficient for the expanded population

## Actions Being Taken

- **Immediate:** Tanker supply arranged twice daily (6 AM and 5 PM) starting 1 March 2026
- **Short-term (2 weeks):** Repair of critical pipeline sections
- **Long-term (3 months):** Replacement of entire Sector 12 main line under Ward Development Fund

The estimated cost of Rs 4.2 Lakhs has been sanctioned from the emergency maintenance budget.

We regret the inconvenience and assure you of our commitment to resolving this permanently.

Yours faithfully,
**District Administration**"""

PRESS_CONTENT = """# FOR IMMEDIATE RELEASE

**District Administration Launches AI-Powered Governance Platform "NAYAM"**

*First-of-its-kind AI Co-Pilot for public administration in the state*

The District Administration today announced the launch of NAYAM, an AI-powered governance intelligence platform that will transform how public services are delivered.

NAYAM integrates speech-to-text processing, document summarization, predictive analytics, and multi-agent AI to assist leaders and administrators in making faster, data-driven decisions.

## Key Features
- Voice-to-text issue logging in Hindi and English
- AI-generated risk assessments per ward
- Automated speech and document drafting
- Real-time dashboards with anomaly detection
- Schedule management for administrative workflows

The platform has already processed over 130 citizen issues and 60 citizen profiles during its pilot phase.

**Media Contact:** PRO, District Administration
**Email:** pro@district.gov.in"""

POLICY_CONTENT = """# Policy Brief: Ward-Level Predictive Risk Scoring

## Executive Summary
This brief proposes the adoption of AI-driven predictive risk scoring across all wards to enable proactive resource allocation and early intervention.

## Background
Traditionally, government response to civic issues has been reactive. NAYAM analytics engine can now predict which wards are likely to experience escalation based on historical patterns, seasonal factors, and real-time data feeds.

## Key Findings
- Wards with >15 open issues have a 73% probability of citizen escalation within 2 weeks
- Water and sanitation issues account for 62% of high-priority complaints
- Seasonal peaks (monsoon, summer) are predictable with 85% accuracy

## Policy Options
1. **Status Quo** -- Continue reactive approach (not recommended)
2. **Pilot Program** -- Deploy predictive scoring in 3 high-risk wards for 6 months
3. **Full Rollout** -- Implement across all wards with monthly review cycles

## Recommendation
Option 2 (Pilot Program) is recommended with Ward 3, Ward 4, and Ward 7 as pilot locations based on current risk metrics from NAYAM dashboard."""

drafts_data = [
    dict(title="Speech: Independence Day Address 2026",
         draft_type=DraftType.SPEECH, status=DraftStatus.DRAFT,
         content=SPEECH_CONTENT,
         prompt_context="Independence Day speech highlighting district achievements and future plans",
         tone="Formal", audience="Citizens, Officials, Media",
         department="General Administration", version=1,
         extra_metadata={"word_count": 210, "ai_generated": False},
         created_by=uid),
    dict(title="Official Response: Water Supply Complaint - Ward 4",
         draft_type=DraftType.OFFICIAL_RESPONSE, status=DraftStatus.APPROVED,
         content=RESPONSE_CONTENT,
         prompt_context="Response to water supply complaints from Ward 4 residents",
         tone="Empathetic", audience="Ward 4 Residents",
         department="Water Supply Department", version=2,
         extra_metadata={"word_count": 185, "ai_generated": True},
         created_by=uid),
    dict(title="Press Release: NAYAM AI Governance Platform Launch",
         draft_type=DraftType.PRESS_RELEASE, status=DraftStatus.PUBLISHED,
         content=PRESS_CONTENT,
         prompt_context="Press release for NAYAM platform launch",
         tone="Professional", audience="Media, General Public",
         department="General Administration", version=1,
         extra_metadata={"word_count": 195, "ai_generated": True},
         created_by=uid),
    dict(title="Policy Brief: Ward-Level Predictive Risk Scoring",
         draft_type=DraftType.POLICY_BRIEF, status=DraftStatus.UNDER_REVIEW,
         content=POLICY_CONTENT,
         prompt_context="Policy brief on using AI predictive analytics for ward risk management",
         tone="Analytical", audience="Senior Administration, Policy Committee",
         department="Planning Department", version=1,
         extra_metadata={"word_count": 190, "ai_generated": True},
         created_by=uid),
]

for dd in drafts_data:
    db.add(Draft(**dd))
db.commit()
print(f"Seeded {len(drafts_data)} drafts")
db.close()
print("Done!")
