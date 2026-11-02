# CrimeLink AI

> An AI-powered Criminal Network Analysis System for police and investigation teams.

---

## Tech Stack

- **Backend**: Python 3 · Django 4.x · SQLite
- **Frontend**: Bootstrap 5.3 · Bootstrap Icons · Chart.js · Google Fonts (Inter)
- **Security**: python-dotenv (env-based config)

---

## Run Guide

### 1. Clone the repository
```bash
git clone https://github.com/SUVIGYA-RAI/CrimeLink-AI.git
cd CrimeLink-AI
```

### 2. Create and activate virtual environment
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

### 4. Set up environment variables
```bash
# Copy the example file and fill in your own secret key
cp .env.example .env
```
Edit `.env` and set:
```
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Load sample data
```bash
python manage.py load_sample_data
```

### 7. Start the server
```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/** in your browser.
