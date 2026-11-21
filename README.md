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

To run the complete test suite across all Level 1 and Level 2 modules (including Case-Centric Workflows):
```powershell
python manage.py test
```

---

## 🔍 Case-Centric AI Extraction & Deduplication Architecture

### 1. Case-First Principle
In real-world criminal investigations, an intelligence system should never produce orphan entities floating in isolation without case context. CrimeLink AI implements **Case-Centric AI Extraction**:
- Document analysis (`FIR`, `PDF`, `TXT`) first identifies the **Investigation Case** (FIR number, title, description, crime classification, incident location).
- Entities (Persons, Vehicles, Organizations, Locations, Phone Calls) and explicit relationships are structured **under** that specific case.
- Extracted data is held in an intermediate staging model (`ExtractedCase` and `ExtractedEntity`) with `review_status = 'pending'`.
- **Zero Orphan Guarantee**: No database records are created in permanent entity tables until an investigator reviews and approves the staged case.
- Rejection discards the staged extraction cleanly without polluting the core database.

### 2. Atomic Database Commit & Entity Deduplication
When the investigator clicks **Approve & Commit to Database**, the entire operation runs inside a single database transaction (`transaction.atomic()`):
1. **Case Resolution**: Either creates a new `Case` record or merges the extracted data into an existing case selected by the investigator.
2. **Entity Deduplication & Linking**:
   - **Persons**: Matches existing records by case-insensitive `full_name`. If found, links the existing person to the case (`person.cases.add(case)`); if new, creates the person and links them.
   - **Vehicles**: Matches existing records by normalized `registration_number`. Links to `vehicle.related_cases.add(case)`.
   - **Organizations**: Matches existing records by case-insensitive `name`. Links to `org.cases.add(case)`.
   - **Locations**: Matches existing records by `location_name`. Links to `loc.cases.add(case)`.
   - **Phone Records**: Avoids duplicate entries matching `caller_number`, `receiver_number`, `call_date`, and `call_time`. Associates record directly with the case.
3. **Explicit Relationship Registration**: Creates verified `EntityRelationship` entries linking persons to vehicles ("owns"), persons to organizations ("associated_with"), etc., and incorporates these into the NetworkX graph.

---

## 📊 Network Analysis & Viva Q&A (BTech CSE Capstone)

### Network Centrality Metrics Explained

| Metric | Definition | Crime Intelligence Application |
| :--- | :--- | :--- |
| **Degree Centrality** | Fraction of direct edges connected to a node: $C_D(v) = \frac{\text{deg}(v)}{N - 1}$ | Highlights **Direct Connectors** who communicate with or link the highest number of other entities. |
| **Betweenness Centrality** | Frequency with which a node falls on the shortest path between all pairs: $C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$ | Identifies **Network Bridges / Middlemen** who control information or resource flow between disparate criminal cells. |
| **PageRank** | Eigenvector-based centrality measuring influence transitively: $PR(v) = \frac{1-d}{N} + d \sum_{u \in M(v)} \frac{PR(u)}{L(u)}$ | Identifies **Influential Kingpins / Key Hubs** connected to other well-connected entities, not just high quantity of contacts. |
| **Connected Components** | Disjoint subgraphs where all nodes are reachable to one another | Segregates independent criminal syndicates or cells operating without mutual communication. |

### Common Viva & Interview Questions

> **Q1: Why did you use `NetworkX` on the backend and `Cytoscape.js` on the frontend?**
> **Answer**: `NetworkX` is a powerful Python graph-theory library optimized for computing complex mathematical algorithms (centrality scores, paths, clustering) server-side. `Cytoscape.js` is a dedicated, GPU-accelerated client-side visualization library that provides interactive layout engines (e.g., CoSE physics, concentric), smooth zooming, panning, and dynamic node styling without re-rendering the whole page.

> **Q2: Why use Many-to-Many relationships for Vehicles and Persons across Cases?**
> **Answer**: In real-world policing, a suspect or a getaway car is frequently involved in multiple offenses across jurisdictions. A `ForeignKey` would improperly constrain a vehicle to only one crime, leading to duplicate records or lost intelligence links. A `ManyToManyField` allows a single vehicle or person to connect multiple investigation cases, enabling cross-case link analysis.

> **Q3: How does the system prevent AI hallucinations and false accusations?**
> **Answer**: The system uses a strict **Human-in-the-Loop** model. AI extraction and anomaly detection never commit records directly as truth. Instead, they present confidence scores and evidence citations for investigator review. High centrality is neutrally labeled (e.g., *"Key Network Bridge"*, *"Highly Connected Node"*) rather than *"Mastermind"*, ensuring investigative objectivity.
