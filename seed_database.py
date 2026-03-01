"""
NAYAM (नयम्) — Heavy Database Seed Script

Populates the database with rich, realistic sample data:
  • 60 citizens across 8 wards
  • 150+ issues with varied statuses, priorities, and departments
  • 5 governance documents with full RAG indexing

Run: python seed_database.py
Requires the backend to be running on http://localhost:8000
"""

import requests
import random
import sys
import os
import time

BASE = "http://localhost:8000/api/v1"

# ── Sample Data ──────────────────────────────────────────────────────

WARDS = ["Ward-1", "Ward-2", "Ward-3", "Ward-4", "Ward-5", "Ward-6", "Ward-7", "Ward-8"]

CITIZENS = [
    # Ward-1 (8 citizens)
    {"name": "Aarav Sharma", "contact_number": "9876543210", "ward": "Ward-1"},
    {"name": "Ananya Gupta", "contact_number": "9876543215", "ward": "Ward-1"},
    {"name": "Neha Agarwal", "contact_number": "9876543225", "ward": "Ward-1"},
    {"name": "Suresh Malhotra", "contact_number": "9876543230", "ward": "Ward-1"},
    {"name": "Kiran Bala", "contact_number": "9876543231", "ward": "Ward-1"},
    {"name": "Pankaj Srivastava", "contact_number": "9876543232", "ward": "Ward-1"},
    {"name": "Rekha Jain", "contact_number": "9876543233", "ward": "Ward-1"},
    {"name": "Vivek Kohli", "contact_number": "9876543234", "ward": "Ward-1"},
    # Ward-2 (8 citizens)
    {"name": "Priya Patel", "contact_number": "9876543211", "ward": "Ward-2"},
    {"name": "Rajesh Kumar", "contact_number": "9876543216", "ward": "Ward-2"},
    {"name": "Sita Ram", "contact_number": "9876543227", "ward": "Ward-2"},
    {"name": "Harpreet Kaur", "contact_number": "9876543235", "ward": "Ward-2"},
    {"name": "Mohan Lal", "contact_number": "9876543236", "ward": "Ward-2"},
    {"name": "Anjali Saxena", "contact_number": "9876543237", "ward": "Ward-2"},
    {"name": "Dinesh Prasad", "contact_number": "9876543238", "ward": "Ward-2"},
    {"name": "Shobha Rani", "contact_number": "9876543239", "ward": "Ward-2"},
    # Ward-3 (8 citizens)
    {"name": "Rohit Verma", "contact_number": "9876543212", "ward": "Ward-3"},
    {"name": "Meena Kumari", "contact_number": "9876543217", "ward": "Ward-3"},
    {"name": "Manoj Dubey", "contact_number": "9876543228", "ward": "Ward-3"},
    {"name": "Sarita Devi", "contact_number": "9876543240", "ward": "Ward-3"},
    {"name": "Ramesh Chandra", "contact_number": "9876543241", "ward": "Ward-3"},
    {"name": "Pooja Mishra", "contact_number": "9876543242", "ward": "Ward-3"},
    {"name": "Anil Kumar Pal", "contact_number": "9876543243", "ward": "Ward-3"},
    {"name": "Usha Tiwari", "contact_number": "9876543244", "ward": "Ward-3"},
    # Ward-4 (8 citizens)
    {"name": "Sunita Devi", "contact_number": "9876543213", "ward": "Ward-4"},
    {"name": "Arjun Reddy", "contact_number": "9876543220", "ward": "Ward-4"},
    {"name": "Geeta Thakur", "contact_number": "9876543229", "ward": "Ward-4"},
    {"name": "Balram Singh", "contact_number": "9876543245", "ward": "Ward-4"},
    {"name": "Nirmala Pathak", "contact_number": "9876543246", "ward": "Ward-4"},
    {"name": "Yogesh Bhatt", "contact_number": "9876543247", "ward": "Ward-4"},
    {"name": "Kamla Devi", "contact_number": "9876543248", "ward": "Ward-4"},
    {"name": "Sunil Rawat", "contact_number": "9876543249", "ward": "Ward-4"},
    # Ward-5 (7 citizens)
    {"name": "Vikram Singh", "contact_number": "9876543214", "ward": "Ward-5"},
    {"name": "Lakshmi Nair", "contact_number": "9876543221", "ward": "Ward-5"},
    {"name": "Prakash Jha", "contact_number": "9876543250", "ward": "Ward-5"},
    {"name": "Savitri Devi", "contact_number": "9876543251", "ward": "Ward-5"},
    {"name": "Raghav Bansal", "contact_number": "9876543252", "ward": "Ward-5"},
    {"name": "Padma Iyer", "contact_number": "9876543253", "ward": "Ward-5"},
    {"name": "Arun Kapoor", "contact_number": "9876543254", "ward": "Ward-5"},
    # Ward-6 (7 citizens)
    {"name": "Deepak Yadav", "contact_number": "9876543218", "ward": "Ward-6"},
    {"name": "Pooja Chauhan", "contact_number": "9876543223", "ward": "Ward-6"},
    {"name": "Santosh Mehta", "contact_number": "9876543255", "ward": "Ward-6"},
    {"name": "Radha Krishna", "contact_number": "9876543256", "ward": "Ward-6"},
    {"name": "Vijay Pandey", "contact_number": "9876543257", "ward": "Ward-6"},
    {"name": "Lata Mangeshkar", "contact_number": "9876543258", "ward": "Ward-6"},
    {"name": "Hemant Khurana", "contact_number": "9876543259", "ward": "Ward-6"},
    # Ward-7 (7 citizens)
    {"name": "Kavita Mishra", "contact_number": "9876543219", "ward": "Ward-7"},
    {"name": "Amit Tiwari", "contact_number": "9876543224", "ward": "Ward-7"},
    {"name": "Sudha Sharma", "contact_number": "9876543260", "ward": "Ward-7"},
    {"name": "Girish Karnad", "contact_number": "9876543261", "ward": "Ward-7"},
    {"name": "Asha Bhonsle", "contact_number": "9876543262", "ward": "Ward-7"},
    {"name": "Mukesh Ambani", "contact_number": "9876543263", "ward": "Ward-7"},
    {"name": "Preeti Zinta", "contact_number": "9876543264", "ward": "Ward-7"},
    # Ward-8 (7 citizens)
    {"name": "Sanjay Joshi", "contact_number": "9876543222", "ward": "Ward-8"},
    {"name": "Ravi Pandey", "contact_number": "9876543226", "ward": "Ward-8"},
    {"name": "Nandini Verma", "contact_number": "9876543265", "ward": "Ward-8"},
    {"name": "Sudhir Choudhary", "contact_number": "9876543266", "ward": "Ward-8"},
    {"name": "Madhuri Dixit", "contact_number": "9876543267", "ward": "Ward-8"},
    {"name": "Tarun Gogoi", "contact_number": "9876543268", "ward": "Ward-8"},
    {"name": "Bhavna Solanki", "contact_number": "9876543269", "ward": "Ward-8"},
]

DEPARTMENTS = [
    "Water Supply", "Roads & Infrastructure", "Sanitation",
    "Public Health", "Education", "Electricity",
    "Housing", "Revenue", "Social Welfare", "Transport",
]

ISSUE_TEMPLATES = [
    # Water Supply (20 issues)
    ("Broken water pipeline causing flooding on main road", "Water Supply", "High"),
    ("Drainage overflow during recent rainfall in colony area", "Water Supply", "High"),
    ("Water contamination reported in bore well supply", "Water Supply", "High"),
    ("Fire hydrant not functional near commercial zone", "Water Supply", "High"),
    ("Request for additional water tanker supply in summer", "Water Supply", "Low"),
    ("Low water pressure in residential apartments since 2 weeks", "Water Supply", "Medium"),
    ("Sewage mixing with drinking water in pipeline junction", "Water Supply", "High"),
    ("Water meter malfunction showing inflated readings", "Water Supply", "Medium"),
    ("Underground water tank leaking in community park", "Water Supply", "Medium"),
    ("Bore well dried up, need alternative water source", "Water Supply", "High"),
    ("Water tanker not arriving on schedule for 3 days", "Water Supply", "Medium"),
    ("Rusty water supply from old iron pipes", "Water Supply", "Medium"),
    ("Request for new water connection for newly built house", "Water Supply", "Low"),
    ("Overhead tank overflowing daily wasting water", "Water Supply", "Low"),
    ("Flooding in basement due to water main burst", "Water Supply", "High"),
    ("Water supply timing irregular, no fixed schedule", "Water Supply", "Medium"),
    ("Illegal water tapping diverting supply from main line", "Water Supply", "High"),
    ("Handpump broken in slum area, no alternative source", "Water Supply", "High"),
    ("Water purification plant not functioning properly", "Water Supply", "High"),
    ("Stagnant water collecting near water tank breeding mosquitoes", "Water Supply", "Medium"),
    # Roads & Infrastructure (20 issues)
    ("Pothole on highway near school zone creating hazard", "Roads & Infrastructure", "High"),
    ("Road resurfacing needed after monsoon damage", "Roads & Infrastructure", "Medium"),
    ("New housing colony lacks proper road connectivity", "Roads & Infrastructure", "Medium"),
    ("Tree fell blocking road during storm", "Roads & Infrastructure", "High"),
    ("Bridge inspection needed after flood damage report", "Roads & Infrastructure", "High"),
    ("Speed breaker needed near hospital entrance", "Roads & Infrastructure", "Medium"),
    ("Road divider broken after truck accident last week", "Roads & Infrastructure", "Medium"),
    ("Footpath encroachment making pedestrians walk on road", "Roads & Infrastructure", "Medium"),
    ("Road caving in due to underground pipe leak", "Roads & Infrastructure", "High"),
    ("Missing manhole cover on main road extremely dangerous", "Roads & Infrastructure", "High"),
    ("Street name boards faded and unreadable in old town", "Roads & Infrastructure", "Low"),
    ("Railway crossing gate malfunctioning causing traffic jams", "Roads & Infrastructure", "High"),
    ("Flyover construction causing extended road closures", "Roads & Infrastructure", "Medium"),
    ("Waterlogged road after every rain for 3 months", "Roads & Infrastructure", "High"),
    ("Unpaved road in newly developed residential area", "Roads & Infrastructure", "Medium"),
    ("Road marking completely faded at busy intersection", "Roads & Infrastructure", "Medium"),
    ("Narrow bridge causing bottleneck during peak hours", "Roads & Infrastructure", "Medium"),
    ("Construction debris dumped on public road for weeks", "Roads & Infrastructure", "Medium"),
    ("Retaining wall collapse risk on hillside road", "Roads & Infrastructure", "High"),
    ("Pedestrian crossing signal not working at market area", "Roads & Infrastructure", "High"),
    # Sanitation (18 issues)
    ("Garbage not collected for 5 days in residential area", "Sanitation", "Medium"),
    ("Public toilet facility needs urgent repair", "Sanitation", "High"),
    ("Sewage line blockage causing hygiene concerns", "Sanitation", "High"),
    ("Open drain overflowing near school compound", "Sanitation", "High"),
    ("Dumping ground overflow causing foul smell in locality", "Sanitation", "High"),
    ("No dustbins available at bus stand area", "Sanitation", "Low"),
    ("Stray dogs scattering garbage from open collection point", "Sanitation", "Medium"),
    ("Bio-medical waste found mixed in municipal garbage", "Sanitation", "High"),
    ("Community toilet block locked and unusable", "Sanitation", "Medium"),
    ("Waste segregation not being followed by garbage collectors", "Sanitation", "Medium"),
    ("Drain cleaning not done before monsoon season", "Sanitation", "High"),
    ("Plastic waste burning in open area causing pollution", "Sanitation", "Medium"),
    ("Septic tank overflowing in residential colony", "Sanitation", "High"),
    ("Night sweeping not happening in market area", "Sanitation", "Low"),
    ("Construction waste blocking drainage channel", "Sanitation", "Medium"),
    ("Dead animal carcass not removed from roadside for days", "Sanitation", "Medium"),
    ("Public urination wall needs proper signage and cleaning", "Sanitation", "Low"),
    ("Composting facility at community garden not maintained", "Sanitation", "Low"),
    # Electricity (15 issues)
    ("Streetlights not functioning in Ward since last week", "Electricity", "Medium"),
    ("Power outages lasting 6+ hours daily in summer", "Electricity", "High"),
    ("Solar streetlight installation request for new colony", "Electricity", "Medium"),
    ("Electric pole leaning dangerously after storm", "Electricity", "High"),
    ("Transformer explosion risk due to overloading", "Electricity", "High"),
    ("Low voltage issue affecting entire residential block", "Electricity", "Medium"),
    ("Street light timer malfunction, lights on during daytime", "Electricity", "Low"),
    ("Exposed electric wires hanging low near playground", "Electricity", "High"),
    ("Power theft by illegal connections in slum area", "Electricity", "High"),
    ("UPS backup needed for community water pump", "Electricity", "Medium"),
    ("Frequent power fluctuations damaging home appliances", "Electricity", "Medium"),
    ("New electricity connection pending for 4 months", "Electricity", "Medium"),
    ("Solar panel installation on community hall not working", "Electricity", "Low"),
    ("Substation humming noise disturbing nearby residents", "Electricity", "Low"),
    ("Emergency generator at hospital not functional", "Electricity", "High"),
    # Public Health (12 issues)
    ("Stray animal menace near marketplace area", "Public Health", "Medium"),
    ("Mosquito fogging needed to prevent dengue outbreak", "Public Health", "High"),
    ("Noise pollution from construction site at night", "Public Health", "Low"),
    ("Food safety inspection needed at street food zone", "Public Health", "Medium"),
    ("Dengue cases rising, need vector control measures", "Public Health", "High"),
    ("Air quality deteriorating due to factory emissions", "Public Health", "High"),
    ("Stagnant water breeding grounds for malaria mosquitoes", "Public Health", "High"),
    ("Community health centre understaffed for 6 months", "Public Health", "Medium"),
    ("Expired medicines found at government dispensary", "Public Health", "High"),
    ("Dog bite incidents increasing in Ward, need vaccination drive", "Public Health", "High"),
    ("Contaminated meat sold at unlicensed butcher shop", "Public Health", "High"),
    ("Lack of ambulance service in peripheral areas", "Public Health", "Medium"),
    # Education (10 issues)
    ("School building roof leaking in monsoon season", "Education", "Medium"),
    ("Playground equipment broken and unsafe for children", "Education", "Medium"),
    ("Mid-day meal quality complaints from multiple parents", "Education", "High"),
    ("Government school toilet facilities in deplorable condition", "Education", "High"),
    ("Teacher vacancy not filled for 8 months", "Education", "Medium"),
    ("Computer lab equipment outdated and non-functional", "Education", "Medium"),
    ("School boundary wall collapsed, security concern", "Education", "High"),
    ("Drinking water facility not working in primary school", "Education", "High"),
    ("Library books not updated since 5 years", "Education", "Low"),
    ("School bus route not covering new residential area", "Education", "Medium"),
    # Housing (8 issues)
    ("Illegal construction blocking public walkway", "Housing", "Low"),
    ("Street vendor relocation request for market area", "Housing", "Low"),
    ("Unauthorized encroachment on government land", "Housing", "Medium"),
    ("Building permission pending for 6 months", "Housing", "Medium"),
    ("Dilapidated building risk assessment needed urgently", "Housing", "High"),
    ("Affordable housing scheme applications stuck in backlog", "Housing", "Medium"),
    ("Park land being used for unauthorized parking", "Housing", "Medium"),
    ("Heritage building restoration work stalled", "Housing", "Low"),
    # Revenue (7 issues)
    ("Property tax assessment dispute for residential plot", "Revenue", "Low"),
    ("Birth certificate issuance delayed by 3 weeks", "Revenue", "Medium"),
    ("Land records digitization error affecting property", "Revenue", "High"),
    ("Shop license renewal process taking too long", "Revenue", "Medium"),
    ("Incorrect property valuation in municipal records", "Revenue", "Medium"),
    ("Market fee collection irregular and disputed", "Revenue", "Low"),
    ("Trade license not issued despite complete documentation", "Revenue", "Medium"),
    # Social Welfare (10 issues)
    ("Pension disbursement delayed for 3 months", "Social Welfare", "High"),
    ("Widow pension application pending for 6 months", "Social Welfare", "High"),
    ("Community hall booking system not working properly", "Social Welfare", "Low"),
    ("Disability pension not received for current quarter", "Social Welfare", "High"),
    ("Scholarship application portal down for 2 weeks", "Social Welfare", "Medium"),
    ("Old age home maintenance and hygiene complaints", "Social Welfare", "Medium"),
    ("Anganwadi centre not providing nutritional supplements", "Social Welfare", "High"),
    ("Ration card address update not processed for months", "Social Welfare", "Medium"),
    ("Self-help group loan application rejected without reason", "Social Welfare", "Medium"),
    ("Night shelter facility overcrowded, needs expansion", "Social Welfare", "Medium"),
    # Transport (10 issues)
    ("Traffic signal malfunction at major intersection", "Transport", "High"),
    ("Bus stop shelter damaged and needs replacement", "Transport", "Low"),
    ("Auto-rickshaw overcharging complaints from commuters", "Transport", "Low"),
    ("No public transport connectivity to industrial area", "Transport", "Medium"),
    ("Parking lot at market full, vehicles parked on road", "Transport", "Medium"),
    ("City bus frequency reduced causing overcrowding", "Transport", "Medium"),
    ("School zone speed limit signs missing or damaged", "Transport", "High"),
    ("Footover bridge at railway station in poor condition", "Transport", "High"),
    ("Cycle lane encroached by vendors and parked vehicles", "Transport", "Medium"),
    ("Traffic congestion due to no left-turn signal at junction", "Transport", "Medium"),
]

# ── Sample Governance Documents ──────────────────────────────────────

SAMPLE_DOCUMENTS = {
    "Municipal Water Supply Policy 2024.txt": """Municipal Water Supply Policy — 2024 Revision

Section 1: Objectives
The primary objective of this policy is to ensure 24x7 potable water supply to all residents within the municipal jurisdiction. The policy targets:
1. Universal access to clean drinking water by 2025
2. Reducing non-revenue water losses to below 15%
3. Implementing smart water metering across all wards
4. Ensuring water quality compliance with BIS 10500:2012 standards

Section 2: Supply Standards
Each household shall receive a minimum of 135 litres per capita per day (LPCD) as per CPHEEO norms.
Commercial establishments: 45 LPCD per employee.
Industrial units: As per consent-to-operate conditions from State Pollution Control Board.

Section 3: Infrastructure Investment
A total budget of Rs. 180 crores has been allocated for the FY 2024-25 under the AMRUT 2.0 scheme for:
- Replacement of aging pipeline infrastructure (Rs. 65 crores)
- New overhead tank construction in Ward-3, Ward-5, Ward-7 (Rs. 45 crores)
- Smart metering pilot in Ward-1 and Ward-2 (Rs. 30 crores)
- Water treatment plant upgradation (Rs. 40 crores)

Section 4: Emergency Response
In case of pipeline burst or water contamination:
1. The affected ward councillor must be notified within 1 hour
2. Alternative water tanker supply must be arranged within 4 hours
3. Water quality testing must be conducted within 6 hours
4. Full restoration of supply within 24 hours for minor incidents, 72 hours for major incidents

Section 5: Citizen Grievance Mechanism
All water-related complaints must be resolved within:
- Urgent (contamination/flooding): 12 hours
- High priority (no supply): 24 hours
- Medium priority (low pressure): 48 hours
- Low priority (new connection): 15 working days

Section 6: Financial Provisions
Water charges revised effective April 2024:
- Domestic: Rs. 5 per kilolitre (first 20 KL), Rs. 12 per KL (20-40 KL), Rs. 25 per KL (above 40 KL)
- Commercial: Rs. 30 per KL flat rate
- Industrial: Rs. 45 per KL flat rate
- BPL households: Free up to 20 KL per month

Approved by: Municipal Commissioner, Order No. MC/WS/2024/001
Date of Effect: 1st April 2024
""",

    "Ward Development Plan FY2024-25.txt": """Ward-wise Development Plan — Financial Year 2024-25

Executive Summary:
This document outlines the comprehensive development plan for all 8 wards under the municipal corporation jurisdiction. Total planned expenditure: Rs. 320 crores across infrastructure, public health, education, and social welfare sectors.

Ward-1 (Population: 45,000):
Priority Projects:
- Smart water metering pilot project (Rs. 15 crores) — Status: In Progress
- Road resurfacing of 12 km stretch on MG Road (Rs. 8 crores) — Status: Tendered
- New community health centre construction (Rs. 5 crores) — Status: Planning
Key Issues: Water pressure complaints (High), Pothole hazards on main road (High)
Risk Level: Medium — Active management needed for infrastructure degradation

Ward-2 (Population: 52,000):
Priority Projects:
- Sewage treatment plant expansion (Rs. 22 crores) — Status: Under Construction
- Primary school renovation for 3 schools (Rs. 4 crores) — Status: In Progress
- LED streetlight installation on all main roads (Rs. 3 crores) — Status: Completed
Key Issues: Sewage overflow near residential areas (Critical), School building conditions (High)
Risk Level: High — Sewage infrastructure requires immediate attention

Ward-3 (Population: 38,000):
Priority Projects:
- New overhead water tank (Rs. 12 crores) — Status: Approved
- Waste segregation processing unit (Rs. 7 crores) — Status: Planning
- Park and recreation area development (Rs. 3 crores) — Status: Tendered
Key Issues: Waste management concerns (Medium), Water supply intermittent (Medium)
Risk Level: Medium — Projects on track

Ward-4 (Population: 41,000):
Priority Projects:
- Bridge repair and strengthening (Rs. 18 crores) — Status: In Progress
- Pension disbursement digitization (Rs. 2 crores) — Status: Testing
- Market area pedestrianization (Rs. 6 crores) — Status: Public Consultation
Key Issues: Bridge structural concerns (Critical), Pension delays (High)
Risk Level: High — Bridge safety is critical priority

Ward-5 (Population: 35,000):
Priority Projects:
- New overhead water tank (Rs. 14 crores) — Status: Approved
- Traffic signal modernization (Rs. 4 crores) — Status: Procurement
- Affordable housing 200 units (Rs. 40 crores) — Status: Land Acquired
Key Issues: Water scarcity in summer (High), Traffic management (Medium)
Risk Level: Medium — Water infrastructure timeline critical

Ward-6 (Population: 48,000):
Priority Projects:
- Industrial area access road (Rs. 15 crores) — Status: Under Construction
- Community toilet complex renovation (Rs. 3 crores) — Status: Completed
- Solar power installation on public buildings (Rs. 5 crores) — Status: In Progress
Key Issues: Road connectivity to industrial belt (High), Power supply issues (Medium)
Risk Level: Medium — Road project on schedule

Ward-7 (Population: 42,000):
Priority Projects:
- Dengue prevention vector control program (Rs. 2 crores) — Status: Active
- School computer lab modernization (Rs. 3 crores) — Status: Procurement
- Drainage system overhaul (Rs. 10 crores) — Status: DPR Prepared
Key Issues: Health concerns — dengue cases rising (Critical), Education infrastructure (Medium)
Risk Level: High — Public health emergency requires resources

Ward-8 (Population: 36,000):
Priority Projects:
- Heritage building restoration (Rs. 8 crores) — Status: Planning
- Bus route extension (Rs. 5 crores) — Status: Survey Complete
- Night shelter expansion (Rs. 2 crores) — Status: Under Construction
Key Issues: Public transport gaps (Medium), Housing for vulnerable populations (Medium)
Risk Level: Low — No critical infrastructure gaps

Budget Summary:
Total Approved: Rs. 320 crores
Central Grants (AMRUT, Smart City): Rs. 180 crores
State Share: Rs. 80 crores
Municipal Revenue: Rs. 60 crores

Monitoring: Monthly progress review by Municipal Commissioner
Next Review Date: 15th of each month
""",

    "Citizen Grievance Redressal Guidelines.txt": """Citizen Grievance Redressal Guidelines — Municipal Corporation

Chapter 1: Introduction
These guidelines establish a standardized framework for receiving, processing, and resolving citizen grievances across all departments of the Municipal Corporation. The guidelines are aligned with the Right to Public Services Act and the Centralized Public Grievance Redress and Monitoring System (CPGRAMS).

Chapter 2: Grievance Categories & Response Times

Category A — Emergency (Response: 4 hours, Resolution: 24 hours):
- Water contamination
- Gas leaks
- Building collapse risk
- Fire hazard
- Road cave-in
- Exposed electrical wires

Category B — Urgent (Response: 12 hours, Resolution: 48 hours):
- Complete water supply failure
- Major road blockage
- Sewage overflow
- Missing manhole covers
- Broken traffic signals at major intersections

Category C — Priority (Response: 24 hours, Resolution: 7 days):
- Partial water supply issues
- Garbage collection failure (>3 days)
- Streetlight outage
- Public toilet malfunction
- Stray animal complaints

Category D — Standard (Response: 48 hours, Resolution: 15 days):
- New connection requests
- Property tax queries
- License renewals
- Certificate issuance
- General maintenance

Category E — Long-term (Response: 72 hours, Resolution: 30 days):
- Policy suggestions
- Infrastructure development requests
- Budget allocation queries
- Land use change requests

Chapter 3: Escalation Matrix
Level 1: Ward Officer (0-2 days)
Level 2: Zonal Officer (2-5 days)
Level 3: Department Head (5-10 days)
Level 4: Additional Commissioner (10-15 days)
Level 5: Municipal Commissioner (>15 days)

If a grievance is not resolved within the stipulated time, it automatically escalates to the next level. The citizen must be informed of each escalation via SMS notification.

Chapter 4: Performance Metrics
Each department's performance is measured on:
1. Average Resolution Time (target: <70% of stipulated time)
2. First Contact Resolution Rate (target: >40%)
3. Citizen Satisfaction Score (target: >3.5/5.0)
4. Escalation Rate (target: <15%)
5. Reopening Rate (target: <5%)

Chapter 5: Digital Integration
All grievances must be logged in the NAYAM platform. Manual/verbal complaints received at ward offices must be digitized within 2 hours. The platform provides:
- Automatic acknowledgment SMS to citizen
- Real-time status tracking via portal
- Automated escalation triggers
- Dashboard analytics for decision-makers
- Predictive issue identification using AI agents

Chapter 6: Accountability
Officers failing to meet response/resolution targets for more than 20% of assigned cases in a quarter will:
1. First instance: Written warning
2. Second instance: Mandatory training
3. Third instance: Performance review impact
4. Persistent failure: Departmental inquiry

Effective Date: 1st January 2024
Approved by: Municipal Commissioner
Order No: MC/GRG/2024/004
""",

    "Annual Budget Summary FY2024-25.txt": """Municipal Corporation Annual Budget Summary — FY 2024-25

Revenue Receipts (Total: Rs. 450 crores):

1. Tax Revenue (Rs. 220 crores):
   - Property Tax: Rs. 120 crores (27% of total)
   - Water Tax: Rs. 35 crores
   - Advertisement Tax: Rs. 15 crores
   - Market Fees: Rs. 25 crores
   - Other Taxes: Rs. 25 crores

2. Non-Tax Revenue (Rs. 80 crores):
   - User Charges: Rs. 30 crores
   - Rental Income: Rs. 20 crores
   - License/Permit Fees: Rs. 15 crores
   - Other Receipts: Rs. 15 crores

3. Government Grants (Rs. 150 crores):
   - Central Grants (AMRUT, Smart City, SBM): Rs. 90 crores
   - State Finance Commission: Rs. 40 crores
   - Special Purpose Grants: Rs. 20 crores

Expenditure Allocation (Total: Rs. 430 crores):

Department-wise Allocation:
1. Water Supply & Sewerage: Rs. 95 crores (22%)
   - New infrastructure: Rs. 45 crores
   - Maintenance: Rs. 30 crores
   - Water treatment: Rs. 20 crores

2. Roads & Infrastructure: Rs. 80 crores (19%)
   - Road construction/repair: Rs. 50 crores
   - Bridges & flyovers: Rs. 20 crores
   - Street lighting: Rs. 10 crores

3. Sanitation & Waste: Rs. 55 crores (13%)
   - Solid waste management: Rs. 30 crores
   - Drain maintenance: Rs. 15 crores
   - Public toilets: Rs. 10 crores

4. Public Health: Rs. 40 crores (9%)
   - Health centres: Rs. 20 crores
   - Vector control: Rs. 10 crores
   - Emergency services: Rs. 10 crores

5. Education: Rs. 35 crores (8%)
   - School infrastructure: Rs. 20 crores
   - Mid-day meals: Rs. 10 crores
   - Digital education: Rs. 5 crores

6. Social Welfare: Rs. 30 crores (7%)
   - Pensions: Rs. 15 crores
   - Housing assistance: Rs. 10 crores
   - Night shelters: Rs. 5 crores

7. Transport: Rs. 25 crores (6%)
   - Traffic management: Rs. 15 crores
   - Bus services: Rs. 10 crores

8. Administration & IT: Rs. 40 crores (9%)
   - Staff salaries: Rs. 25 crores
   - IT systems (NAYAM platform): Rs. 10 crores
   - Office operations: Rs. 5 crores

9. Revenue Department: Rs. 15 crores (3%)
10. Housing: Rs. 15 crores (3%)

Capital vs Revenue Split:
- Capital expenditure: Rs. 250 crores (58%)
- Revenue expenditure: Rs. 180 crores (42%)

Ward-wise Capital Allocation:
- Ward-1: Rs. 35 crores (Smart metering + roads)
- Ward-2: Rs. 45 crores (Sewage plant — highest allocation)
- Ward-3: Rs. 25 crores (Water tank + waste processing)
- Ward-4: Rs. 35 crores (Bridge repair + pension digitization)
- Ward-5: Rs. 30 crores (Water tank + housing)
- Ward-6: Rs. 28 crores (Industrial road + solar)
- Ward-7: Rs. 22 crores (Health + drainage)
- Ward-8: Rs. 20 crores (Heritage + transport)
Unallocated reserve: Rs. 10 crores

Key Financial Indicators:
- Revenue surplus: Rs. 20 crores
- Debt service ratio: 8% (within 25% limit)
- Property tax collection efficiency: 78% (target: 85%)
- Grant utilization rate: 82% (target: 90%)

Approved by Municipal Council Resolution No. 2024/BUD/001
Date: 28th March 2024
""",

    "Public Health Emergency Protocol.txt": """Public Health Emergency Response Protocol — Municipal Corporation

Document Classification: CRITICAL
Version: 3.0 (Updated January 2024)

Section 1: Scope and Applicability
This protocol governs the municipal corporation's response to public health emergencies including:
- Epidemic/Pandemic outbreaks (Dengue, Malaria, COVID, Cholera)
- Water contamination events
- Air quality emergencies (AQI > 400)
- Food safety incidents
- Industrial chemical spills
- Natural disaster health response

Section 2: Alert Levels

GREEN (Normal): Routine surveillance, regular fogging schedule, standard health services
YELLOW (Watch): 10% increase in disease cases above seasonal baseline. Enhanced surveillance, increased fogging frequency, public awareness campaigns.
ORANGE (Warning): 25% increase or cluster of cases in single ward. Activate ward-level emergency teams, daily situation reports, resource pre-positioning.
RED (Emergency): 50% increase or multi-ward outbreak. Full emergency operations centre activation, all-department coordination, state/central assistance request.

Section 3: Dengue/Vector-Borne Disease Protocol
Current Status: Ward-7 is at ORANGE alert level (15 confirmed cases in last 2 weeks)

Immediate Actions:
1. Door-to-door larval survey in affected areas (Ward-7 priority, then Ward-6, Ward-5)
2. Fogging operations: Daily for Red zones, alternate days for Orange, weekly for Yellow
3. Hospital preparedness: Ensure 50 dengue-ready beds across municipal hospitals
4. Blood bank: Maintain platelet reserve of 200 units
5. Diagnostic: Free dengue NS1 and IgM testing at all health centres

Resource Requirements:
- Fogging machines: 15 (current: 10, shortfall: 5)
- Malathion stock: 500 litres per week (current stock: 800 litres)
- Temephos for larval control: 200 kg (current stock: 150 kg)
- Health workers for survey: 120 (current deployed: 85)

Section 4: Water Contamination Protocol
Trigger: Any positive coliform test result or citizen illness cluster linked to water supply

Response Timeline:
Hour 0: Lab confirms contamination → Alert Municipal Commissioner
Hour 1: Shut down affected supply line, notify ward councillor
Hour 2: Deploy water tanker to affected area
Hour 4: Door-to-door health advisory distribution
Hour 6: Complete water quality audit of connected lines
Hour 12: Identify contamination source
Hour 24: Begin remediation
Hour 48: Clearance testing
Hour 72: Supply restoration

Section 5: Inter-Department Coordination
The Health Department serves as the nodal agency. Required coordination:
- Water Supply: Contamination events, chlorination levels
- Sanitation: Waste management, drain cleaning for vector control
- Education: School closure decisions, awareness programs
- Revenue: Emergency fund disbursement
- Transport: Ambulance services, material movement

Section 6: Budget Provisions
Emergency health fund: Rs. 5 crores (revolving fund)
Per-event spending authority: Rs. 50 lakhs (Ward Officer), Rs. 2 crores (Health Officer)
Central assistance trigger: Expenditure exceeding Rs. 5 crores

Contact Directory:
Chief Medical Officer: Dr. Priya Sharma — 9876500001
Epidemic Response Team Lead: Dr. Rahul Mehra — 9876500002
Vector Control Officer: Shri Manoj Kumar — 9876500003
Emergency Operations Centre: 1800-xxx-xxxx (24x7)

Review Frequency: Monthly (normal), Weekly (elevated), Daily (emergency)
Next Review: 1st of next month or upon alert level change
""",
}


def main():
    print("=" * 60)
    print("  NAYAM — Heavy Database Seed Script")
    print("=" * 60)
    print()

    # ── Step 1: Login ────────────────────────────────────────────
    print("[1/5] Logging in...")
    try:
        resp = requests.post(f"{BASE}/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        if resp.status_code != 200:
            print("  ⚠  Default user not found. Creating one...")
            resp = requests.post(f"{BASE}/auth/register", json={
                "name": "Admin User",
                "email": "admin@nayam.gov.in",
                "password": "admin12345",
                "role": "Leader",
            })
            if resp.status_code not in (200, 201):
                print(f"  ✗ Registration failed: {resp.status_code} — {resp.text}")
                sys.exit(1)
        token = resp.json()["access_token"]
        print(f"  ✓ Authenticated (token: {token[:20]}...)")
    except requests.ConnectionError:
        print("  ✗ Cannot connect to backend. Is it running on http://localhost:8000?")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    # ── Step 2: Create Citizens ──────────────────────────────────
    print()
    print(f"[2/5] Creating {len(CITIZENS)} citizens...")
    citizen_ids = []
    created = 0
    skipped = 0
    for c in CITIZENS:
        resp = requests.post(f"{BASE}/citizens/", json=c, headers=headers)
        if resp.status_code == 201:
            cid = resp.json()["id"]
            citizen_ids.append(cid)
            created += 1
        elif resp.status_code == 400 and "already" in resp.text.lower():
            # Try to find existing citizen
            skipped += 1
        else:
            print(f"  ✗ {c['name']} — {resp.status_code}: {resp.text[:80]}")

    # Also fetch existing citizens
    resp = requests.get(f"{BASE}/citizens/", params={"limit": 500}, headers=headers)
    if resp.status_code == 200:
        existing = resp.json().get("citizens", [])
        existing_ids = [c["id"] for c in existing]
        # Merge — ensure we have all IDs
        for eid in existing_ids:
            if eid not in citizen_ids:
                citizen_ids.append(eid)

    print(f"  ✓ Created: {created}, Skipped: {skipped}, Total available: {len(citizen_ids)}")

    if not citizen_ids:
        print("  ✗ No citizens available. Aborting.")
        sys.exit(1)

    # ── Step 3: Create Issues ────────────────────────────────────
    print()
    print(f"[3/5] Creating {len(ISSUE_TEMPLATES)} issues...")
    issue_created = 0
    issue_failed = 0
    status_choices = ["Open", "Open", "Open", "In Progress", "In Progress", "Closed"]

    for desc, dept, priority in ISSUE_TEMPLATES:
        citizen_id = random.choice(citizen_ids)
        payload = {
            "citizen_id": citizen_id,
            "department": dept,
            "description": desc,
            "priority": priority,
        }
        resp = requests.post(f"{BASE}/issues/", json=payload, headers=headers)
        if resp.status_code == 201:
            issue_created += 1
            # Randomly update some issues to "In Progress" or "Closed"
            chosen_status = random.choice(status_choices)
            if chosen_status != "Open":
                iid = resp.json()["id"]
                requests.put(
                    f"{BASE}/issues/{iid}",
                    json={"status": chosen_status},
                    headers=headers,
                )
        else:
            issue_failed += 1

    print(f"  ✓ Created: {issue_created}, Failed: {issue_failed}")

    # ── Step 4: Upload Documents ─────────────────────────────────
    print()
    print(f"[4/5] Uploading {len(SAMPLE_DOCUMENTS)} governance documents...")
    doc_created = 0
    temp_dir = os.path.join(os.path.dirname(__file__), "_seed_temp")
    os.makedirs(temp_dir, exist_ok=True)

    for filename, content in SAMPLE_DOCUMENTS.items():
        # Write temp file
        temp_path = os.path.join(temp_dir, filename)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Upload via API
        with open(temp_path, "rb") as f:
            resp = requests.post(
                f"{BASE}/documents/upload",
                data={"title": filename.replace(".txt", "")},
                files={"file": (filename, f, "text/plain")},
                headers=headers,
            )
            if resp.status_code == 201:
                doc_created += 1
                doc_id = resp.json().get("id", "?")
                print(f"  ✓ {filename} — {str(doc_id)[:8]}...")
            else:
                print(f"  ✗ {filename} — {resp.status_code}: {resp.text[:80]}")

    # Clean up temp files
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    # ── Step 5: Summary ──────────────────────────────────────────
    print()

    # Fetch final counts
    resp_c = requests.get(f"{BASE}/citizens/", params={"limit": 1}, headers=headers)
    resp_i = requests.get(f"{BASE}/issues/", params={"limit": 1}, headers=headers)
    resp_d = requests.get(f"{BASE}/documents/", params={"limit": 1}, headers=headers)

    total_citizens = resp_c.json().get("total", "?") if resp_c.status_code == 200 else "?"
    total_issues = resp_i.json().get("total", "?") if resp_i.status_code == 200 else "?"
    total_docs = resp_d.json().get("total", "?") if resp_d.status_code == 200 else "?"

    print("=" * 60)
    print(f"  ✓ Seed complete!")
    print(f"    Citizens:  {total_citizens}")
    print(f"    Issues:    {total_issues}")
    print(f"    Documents: {total_docs}")
    print()
    print("  Login credentials:")
    print("    Email:    test@example.com")
    print("    Password: password123")
    print()
    print("  Recommended documents to upload for RAG:")
    print("    • Municipal policies & regulations")
    print("    • Ward development plans")
    print("    • Budget reports & allocation documents")
    print("    • Public health advisories")
    print("    • Citizen grievance guidelines")
    print("    • Department performance reports")
    print("=" * 60)


if __name__ == "__main__":
    main()
