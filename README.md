# Ghana Grid Project — CS 112 Final Course Project

Integrated data science + software engineering project (Summer 2026):

1. **National Electricity Grid Network Analysis** (`data-science/`) — cleaning,
   EDA, network analysis, geospatial visualization, and a Streamlit dashboard
   built on a synthetic dataset grounded in Ghana's grid (ECG, NEDCo, GRIDCo, VRA).
2. **GridCare-Lite** (`gridcare-lite/`) — a Tkinter/SQLite outage and
   maintenance management system for engineers, technicians, admins, and
   customer-service staff.

## Team

| Member | Role |
| --- | --- |
| 1 | Data Engineer — cleaning, integration, network analysis (Task 2.1) |
| 2 | Data Analyst — EDA, business intelligence, reliability analysis |
| 3 | Visualization Specialist — geospatial analysis, dashboards, charts |
| 4 | Software Engineer — GridCare-Lite build, DB schema, auth, testing |

## Setup

```bash
cd data-science
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python generate_dataset.py      # produces utilities.csv, substations.csv, lines.csv
python task1_1_clean_data.py    # cleans + validates, writes *_clean.csv
```

## Status

- [x] Dataset generated (seed 42 — reproducible across the team)
- [x] Task 1.1: Data cleaning and validation
- [x] Task 1.2: EDA (Member 2)
- [ ] Task 1.3: Data integration (Member 1)
- [ ] Task 2.1: Network analysis (Member 1)
- [ ] Task 2.2: Geospatial analysis (Member 3)
- [ ] Task 2.3: Business intelligence (Member 2)
- [ ] Task 3.1: Dashboard (all)
- [ ] Task 3.2: Advanced visualizations (Member 3)
- [ ] GridCare-Lite (Member 4)
