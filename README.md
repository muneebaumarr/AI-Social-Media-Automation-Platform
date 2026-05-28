# AI Social Media Automation Platform

A full-stack SaaS web application that helps users create draft content and repurpose it for different social media platforms using AI. The platform generates captions, hashtags, and platform-specific content based on trends.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python FastAPI |
| Database | MySQL 8.0 |
| ORM | SQLAlchemy |
| Templates | Jinja2 + Bootstrap 5 |
| AI | Google Gemini 1.5 Flash |
| Auth | JWT Tokens + bcrypt |
| Email | smtplib (Gmail) |
| Deployment | Railway.app |

---

## Project Structure

```
AI-Social-Media-Automation-Platform/
│
├── main.py                   ← FastAPI app entry point
├── .env                      ← Secret keys (never commit)
├── requirements.txt          ← Package list
├── venv/                     ← Virtual environment
│
├── Data/                     ← CSV files (synthetic data)
├── Database/                 ← schema.sql, validation.sql
├── Docs/                     ← Normalization, dataflow docs
│
└── app/
    ├── __init__.py
    ├── database.py           ← MySQL connection
    ├── config.py             ← Settings and env variables
    │
    ├── routers/              ← URL routes
    │   ├── __init__.py
    │   ├── auth.py           ← /login /register /logout
    │   ├── drafts.py         ← /drafts /drafts/new
    │   ├── posts.py          ← /posts
    │   ├── approvals.py      ← /approve /reject
    │   └── analytics.py      ← /analytics
    │
    ├── models/               ← Database query functions
    │   ├── __init__.py
    │   ├── user.py
    │   ├── draft.py
    │   └── post.py
    │
    ├── services/             ← Business logic
    │   ├── __init__.py
    │   ├── ai_service.py     ← Gemini API calls
    │   ├── email_service.py  ← Email notifications
    │   └── auth_service.py   ← Password hashing + JWT
    │
    ├── templates/            ← HTML pages (Jinja2)
    │   ├── base.html         ← Shared layout + navbar
    │   ├── auth/
    │   │   ├── login.html
    │   │   └── register.html
    │   └── dashboard/
    │       ├── dashboard.html
    │       ├── drafts.html
    │       ├── new_draft.html
    │       ├── posts.html
    │       ├── manager.html
    │       └── analytics.html
    │
    └── static/
        ├── css/
        │   └── style.css
        └── js/
            └── main.js
```

---

## Database Schema

11 tables designed and normalized to 3NF:

| Table | Purpose |
|---|---|
| `users` | Writers, managers, admins |
| `clients` | Brand profiles |
| `social_accounts` | Connected social media accounts |
| `content_drafts` | Original content written by writers |
| `posts` | AI-repurposed platform-specific posts |
| `ai_generations` | Prompt and response audit trail |
| `approvals` | Manager review decisions |
| `scheduled_posts` | Scheduling records |
| `analytics_logs` | Post performance metrics |
| `content_recommendations` | AI weekly content suggestions |
| `audit_logs` | System-wide action history |

---

## User Roles

| Role | Access |
|---|---|
| **Writer** | Create drafts, trigger AI repurposing, view post status |
| **Manager** | Approve, reject, or request edits on posts |
| **Admin** | Full access to everything |

---

## Workflow

```
Writer creates draft
        ↓
AI repurposes for selected platforms
        ↓
Manager receives email notification
        ↓
Manager approves or rejects each post
        ↓
Writer schedules approved posts
        ↓
Analytics tracked per post
        ↓
AI generates weekly recommendations
```

---

## Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/muneebaumarr/AI-Social-Media-Automation-Platform.git
cd AI-Social-Media-Automation-Platform
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root folder:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=ai_social_media_db
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-key
EMAIL_ADDRESS=your-gmail@gmail.com
EMAIL_PASSWORD=your-app-password
```

### 5. Set up the database
```bash
mysql -u root -p < Database/schema.sql
```

### 6. Run the development server
```bash
uvicorn main:app --reload
```

Open `http://localhost:8000`

API documentation available at `http://localhost:8000/docs`

---

## Milestones

| Milestone | Status |
|---|---|
| M1 — ERD and database design | ✅ Done |
| M2 — Normalization 1NF to 3NF | ✅ Done |
| M3 — Synthetic data and dataflow | ✅ Done |
| M4 — DDL scripts and constraints | ✅ Done |
| M5 — Data population and validation | ✅ Done |
| M6 — FastAPI backend | 🔄 In progress |
| M7 — Frontend templates | ⬜ Pending |
| M8 — Deployment on Railway | ⬜ Pending |

---
