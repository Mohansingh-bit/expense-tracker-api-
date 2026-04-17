# Expense Tracker API — v2

A production-ready REST API for tracking personal expenses.
Built with Flask, SQLAlchemy, JWT authentication, and clean layered architecture.

---

## What's New vs v1

| Area | v1 | v2 |
|---|---|---|
| Auth | API key (no expiry) | JWT with access + refresh tokens |
| Password | None | bcrypt hashed |
| Database | SQLite only | PostgreSQL (SQLite for dev/test) |
| Money type | Float (rounding errors) | Decimal (exact) |
| CRUD | No update | Full CRUD with PATCH |
| Delete | Hard delete | Soft delete (audit trail) |
| Pagination | None (dumps all records) | Page + per_page on all list endpoints |
| Categories | Free text | Fixed validated list |
| Rate limiting | None | Per-endpoint limits |
| Config | Hardcoded | Dev / Prod / Test configs via .env |
| Logging | None | Structured logging |
| API versioning | /api/ | /api/v1/ |
| Error handling | Partial | Global handlers for 404, 405, 429, 500 |

---

## Project Structure

```
expense_tracker_api/
├── app/
│   ├── app.py          # App factory with logging + error handlers
│   ├── config.py       # Dev / Prod / Test config classes
│   ├── models.py       # ORM models with Decimal types + soft delete
│   ├── services.py     # All business logic
│   ├── routes.py       # Thin HTTP layer, versioned under /api/v1
│   ├── validators.py   # Input validation including PATCH validator
│   ├── auth.py         # bcrypt + JWT token helpers
│   └── extensions.py   # db, jwt, limiter instances
├── tests/
│   └── test_api.py     # 30+ tests covering all endpoints
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

```bash
git clone <repo>
cd expense_tracker_api

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your DB URL and JWT secret

cd app
python app.py
```

Server runs at `http://127.0.0.1:5000`

---

## Authentication

This API uses **JWT (JSON Web Tokens)**.

1. Register → get `access_token` + `refresh_token`
2. Send `access_token` in every request header:
   ```
   Authorization: Bearer <access_token>
   ```
3. Access tokens expire in **1 hour**. Use `/api/v1/refresh` with your refresh token to get a new one without logging in again.

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/register` | Create account → returns tokens |
| POST | `/api/v1/login` | Login → returns tokens |
| POST | `/api/v1/refresh` | Get new access token (send refresh token) |

### Expenses

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/expenses` | Add expense |
| GET | `/api/v1/expenses` | List expenses (paginated, filterable) |
| GET | `/api/v1/expenses/<id>` | Get single expense |
| PATCH | `/api/v1/expenses/<id>` | Update expense (any fields) |
| DELETE | `/api/v1/expenses/<id>` | Soft delete expense |
| GET | `/api/v1/expenses/summary` | Monthly summary + budget alerts |

### Budgets

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/budgets` | Set or update budget limit |
| GET | `/api/v1/budgets` | List all budget limits |
| DELETE | `/api/v1/budgets/<category>` | Remove budget limit |

---

## Valid Categories

`food` · `transport` · `housing` · `health` · `entertainment` · `education` · `shopping` · `other`

---

## Pagination

All list endpoints support:
```
GET /api/v1/expenses?page=1&per_page=20
```

Response includes:
```json
{
  "expenses": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 85,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Running Tests

```bash
cd expense_tracker_api
python -m pytest tests/test_api.py -v --cov=app
```

---

## Tech Stack

- **Flask** — web framework
- **Flask-SQLAlchemy** — ORM
- **Flask-JWT-Extended** — JWT auth
- **Flask-Limiter** — rate limiting
- **bcrypt** — password hashing
- **PostgreSQL** — production database
- **SQLite** — development/testing
- **pytest** — testing
