# FastAPI HR Contact & Cold Email System

This project is a backend service built with **FastAPI** to manage HR/recruiter contacts and send personalized cold emails.
It is designed as an **internal/admin backend** and secured using **API key–based authorization**.

---

## Features

### 1. Import HR Contacts from PDF
- Upload a PDF file containing HR or recruiter information
- Extracts name, email, title, and company
- Stores extracted contacts in a PostgreSQL database
- Skips invalid or malformed rows

**Endpoint**
```
POST /hr-contacts/import
```

---

### 2. Add HR / Company Details Manually
- Add HR contact details using a JSON API
- Input validation using Pydantic schemas

**Endpoint**
```
POST /company/add-company-details
```

---

### 3. Send Cold Emails
- Sends personalized cold emails to all stored HR contacts
- Uses **Jinja2** templates for dynamic email content
- Attaches a resume (PDF) from local storage
- Supports testing with dummy HR data

**Endpoint**
```
POST /email/send
```

---

### 4. Email Templating
- Email content is rendered using a `.j2` template
- Dynamic placeholders include:
  - HR name
  - Job position
  - Experience
  - Skills
  - Contact details
- Each email is rendered separately for personalization

---

### 5. API Key Authorization
- All sensitive APIs are protected using a **global API key**
- The key must be sent in request headers

**Header**
```
Key-Secret: <your_api_key>
```

---

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy (Async)
- PostgreSQL
- Jinja2
- SMTP (Gmail)
- pdfplumber
- python-dotenv

---

## Project Structure

```
app/
├── api/
│   ├── email.py
│   ├── company.py
│   └── hr_contacts_imports.py
│
├── core/
│   ├── config.py
│   └── security.py
│
├── services/
│   ├── cold_email_service.py
│   ├── company_service.py
│   └── hr_contacts_import_service.py
│
├── database/
│   ├── database.py
│   └── repositories.py
│
├── models/
│   └── models.py
│
├── templates/
│   └── cold_email.j2
│
├── resumes/
│   └── Saurabh_Amrutkar_Resume.pdf
│
├── main.py
└── .env
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

ADMIN_KEY=your_api_key_here

SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_email_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

> ⚠️ API keys must be ASCII-only (avoid special characters).

---

## Running the Project

### Install dependencies
```bash
pip install -r requirements.txt
```

### Start the server
```bash
uvicorn app.main:app --reload
```

---

## Security Notes

- Uses **header-based API key (shared secret) authorization**
- No user login or session management
- Intended for internal/admin usage

---

## Current Limitations

- No email scheduling
- No rate limiting enabled by default
- Single global API key
- Backend only (no UI)

---

## Future Enhancements

- Email scheduling
- Rate limiting
- Distributor-specific API keys
- Email delivery logs
- Admin dashboard UI

---

## Author

**Saurabh Sunil Amrutkar**  
Python Backend Developer  
FastAPI | SQLAlchemy | Jinja2
