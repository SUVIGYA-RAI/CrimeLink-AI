# CrimeLink AI – Intelligence & Criminal Network Analysis System

> An AI-powered Criminal Network Analysis and Intelligence System designed for investigation teams, police departments, and academic study (BTech CSE Capstone Project).

---

## 🚀 Overview

CrimeLink AI is built in two distinct architectural levels:

### Level 1: Core Case & Entity Management
- **Case Management**: Register, track, search, and update criminal cases with status and priority tags.
- **Entity Management**: Persons, Vehicles, Organizations, Locations, and Phone Records with relational mappings.
- **Role-based Authentication**: Secure user management with investigator and admin roles.
- **Midnight Intelligence UI**: Dark cyber-defense themed dashboard with responsive Bootstrap 5 and Chart.js metrics.

### Level 2: AI Entity Extraction, Network Analysis & Pattern Detection
1. **Data Management & Document Upload**:
   - Upload FIR documents (PDF / TXT) and synthetic CSV datasets (Call Detail Records, Financial Transactions).
   - Text extraction using `pdfplumber` and structured validation with `pandas`.
2. **AI Entity Extraction (NLP)**:
   - Named Entity Recognition (NER) powered by `spaCy` (`en_core_web_sm`) identifying Persons, Organizations, Locations, and Dates.
   - Regex fallback extractors for Indian mobile numbers (`+91/0` format) and vehicle registration plates.
   - Human-in-the-loop review workflow (`Pending Review`, `Approved`, `Rejected`).
3. **Entity Relationship Mapping**:
   - Explicit relationships (`Associated With`, `Communicated With`, `Owns`, `Member Of`) linked with evidence citations and confidence scores.
4. **Network Analysis (NetworkX)**:
   - Centrality metric computations: **Degree Centrality**, **Betweenness Centrality**, **PageRank**, and **Connected Components**.
   - Neutral investigative labeling (e.g. *Highly Connected Entity*, *Network Bridge*).
5. **Interactive Network Graph (Cytoscape.js)**:
   - Interactive nodes with color coding by entity type (Person = Cyan, Case = Blue, Org = Purple, Vehicle = Amber, Location = Emerald).
   - Real-time zoom, pan, node search, and neighborhood highlighting.
6. **Explainable Suspicious Pattern Detection**:
   - Unusually frequent communication between identical phone numbers.
   - Large or rapid financial transactions relative to dataset thresholds.
   - Clear investigative disclaimers (anomalies serve as investigative leads, not proof of guilt).
7. **Comprehensive AI Analysis Dashboard**:
   - Real-time metrics on documents processed, pending reviews, active alerts, and network nodes.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.13 / Django 4.2
- **Database**: SQLite (via Django ORM)
- **AI & NLP**: `spaCy` (`en_core_web_sm`), Regular Expressions
- **Data Processing**: `Pandas`, `pdfplumber`
- **Network Graph Analysis**: `NetworkX`
- **Visualization**: `Cytoscape.js`, `Chart.js`
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Inter font

---

## 📂 Project Architecture

```text
CrimeLink-AI/
├── crimelink/            # Project configuration (settings, root URLs, WSGI)
├── accounts/             # Authentication & user profiles
├── cases/                # Case records & investigator tracking
├── entities/             # Level 1 Entities (Person, Vehicle, Org, Location, Phone)
├── dashboard/            # Intelligence Dashboard (Level 1 + Level 2 overview)
├── data_management/      # Level 2 Document Upload & CSV Processing
│   └── services/         # pdf_extractor.py, csv_processor.py
├── ai_analysis/          # Level 2 NLP Entity Extraction & Anomaly Detection
│   └── services/         # entity_extractor.py, anomaly_detector.py
├── network_analysis/     # Level 2 Graph Building, Metrics & Cytoscape.js
│   └── services/         # graph_builder.py, graph_metrics.py
├── sample_data/          # Synthetic sample FIRs, call records, and transactions
├── static/               # Midnight Intelligence CSS & JavaScript
└── templates/            # Django HTML templates
```

---

## ⚡ Quick Start Guide

### 1. Activate the Virtual Environment
```powershell
# Windows PowerShell
.\venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Run Database Migrations
```powershell
python manage.py migrate
```

### 4. Start the Application Server
```powershell
python manage.py runserver
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🧪 Running Automated Tests

To run the complete test suite across all Level 1 and Level 2 modules:
```powershell
python manage.py test
```
