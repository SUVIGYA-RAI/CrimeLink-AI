# CrimeLink AI

> **An AI-powered Criminal Network Analysis System for police and investigation teams.**  
> Built with Django, Bootstrap 5, and Chart.js — featuring a sleek "Midnight Intelligence" dark-navy UI.

---

## Features

| Feature | Details |
|---|---|
| **Authentication** | Login, logout, registration with role-based access (Admin / Investigator) |
| **Dashboard** | Real-time statistics from SQLite — total cases, open/closed counts, entity totals, Chart.js bar chart |
| **Case Management** | Full CRUD: add, view, edit, delete cases with status, priority, and case-type filters |
| **Entity Management** | Full CRUD for Persons, Vehicles, Organizations, Locations, and Phone Records |
| **Search & Filters** | Live search and dropdown filters on every list page |
| **Admin Panel** | Django admin fully configured for all models |
| **Role-Based Access** | Admin-only Users list; investigators see their own scope |
| **Form Validation** | Django ModelForm validation with inline error messages |

---

## Tech Stack

- **Backend**: Python 3 · Django 4.x · SQLite
- **Frontend**: Bootstrap 5.3 · Bootstrap Icons · Chart.js · Google Fonts (Inter)
- **Testing**: Django TestCase (60 unit + integration tests)

---

## Setup Instructions

### Prerequisites
- Python 3.10+ installed
- `pip` available

### 1. Clone / Open the project
```bash
# The project is at:
cd C:\Users\raisu\OneDrive\Desktop\CrimeLinkAI
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run database migrations
```bash
python manage.py migrate
```

### 5. Load sample data (demo users + 5 cases + entities)
```bash
python manage.py load_sample_data
```

### 6. Start the development server
```bash
python manage.py runserver
```

Open your browser to: **http://127.0.0.1:8000/**

---

## Demo Login Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Investigator | `investigator1` | `inv123` |

### Django Admin Panel
Visit **http://127.0.0.1:8000/admin/** and log in with the admin credentials.

---

## Running Tests

```bash
python manage.py test accounts cases entities --verbosity=2
```

Expected output: **60 tests · 0 failures · 0 errors**

---

## Project Structure

```
CrimeLinkAI/
├── accounts/          # Authentication, user profiles, role management
│   ├── models.py      # UserProfile (Admin / Investigator roles)
│   ├── views.py       # Login, logout, register, profile, user list
│   └── tests.py       # 17 tests – auth, registration, dashboard access
├── cases/             # Case management CRUD
│   ├── models.py      # Case (number, title, type, status, priority)
│   ├── views.py       # List/detail/create/edit/delete + search/filter
│   └── tests.py       # 16 tests – CRUD, search, filter, auth guards
├── entities/          # Entity CRUD (Persons, Vehicles, Orgs, Locations, Phones)
│   ├── models.py      # Person, Vehicle, Organization, Location, PhoneRecord
│   ├── views.py       # CRUD views for all 5 entity types
│   └── tests.py       # 27 tests – all entity list/create/detail/delete views
├── dashboard/         # Analytics dashboard
│   └── views.py       # ORM stats + Chart.js data for the dashboard
├── templates/         # Project-wide HTML templates
│   ├── base.html      # Sidebar + navbar layout (Midnight Intelligence theme)
│   ├── accounts/      # login, register, profile, user_list templates
│   ├── cases/         # list, detail, form, confirm_delete templates
│   ├── entities/      # 16 templates for all entity types
│   └── dashboard/     # home.html with stat cards and Chart.js
├── static/
│   ├── css/style.css  # Midnight Intelligence dark-navy theme
│   └── js/script.js   # Bootstrap alert auto-dismiss + UI helpers
├── cases/management/
│   └── commands/
│       └── load_sample_data.py  # Synthetic demo data loader
├── manage.py
├── requirements.txt
└── README.md
```

---

## Level 1 Completion Checklist

- [x] Django server starts without errors
- [x] Registration and login work
- [x] Admin and investigator roles work
- [x] Dashboard displays real SQLite data
- [x] Case CRUD works (add, view, edit, delete)
- [x] All five entity types have working CRUD
- [x] Search and filters work
- [x] Forms validate incorrect inputs
- [x] Data remains saved after restarting the server
- [x] All pages are responsive and visually consistent
- [x] Django migrations and tests pass (60/60)
- [x] README contains setup and run commands

---

## Screenshots

| Page | Description |
|---|---|
| Login | Dark-navy card with CrimeLink AI branding |
| Dashboard | Stat cards + Bar chart of case types |
| Cases List | Searchable, filterable table with badge-color status/priority |
| Person Detail | Full profile card with linked cases |

---

*CrimeLink AI — Intelligence System | Built with Django & Bootstrap 5*
