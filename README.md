# Expense Tracker API

A REST API for tracking personal expenses built with Flask and SQLAlchemy.

---

## Features

- JWT authentication with access + refresh tokens
- bcrypt password hashing
- Add, view, update, and delete expenses
- Soft delete with audit trail
- Category-based budget limits with warning and exceeded alerts
- Monthly summary with percentage breakdown per category
- Pagination on all list endpoints
- Input validation with meaningful error messages
- Per-user data isolation
- Global error handlers

---

## Tech Stack

- **Flask** — web framework
- **Flask-SQLAlchemy** — ORM
- **Flask-JWT-Extended** — JWT authentication
- **Flask-Limiter** — rate limiting
- **bcrypt** — password hashing
- **SQLite** — development database
- **PostgreSQL** — production database
- **pytest** — 28 tests

---

## Project Structure

```
expense_tracker/
├── app/
│   ├── app.py          # App factory, config, error handlers
│   ├── config.py       # Dev / Prod / Test config classes
│   ├── models.py       # User, Expense, BudgetLimit models
│   ├── services.py     # Business logic layer
│   ├── routes.py       # API endpoints
│   ├── validators.py   # Input validation
│   ├── auth.py         # JWT + bcrypt helpers
│   └── extensions.py   # db, jwt, limiter instances
├── tests/
│   └── test_api.py     # 28 pytest tests
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

```bash
git clone https://github.com/Mohansingh-bit/expense-tracker-api-
cd expense-tracker-api-

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your JWT secret

cd app
python app.py
```

Server runs at `http://127.0.0.1:5000`

---

## Authentication

Register to get a JWT token, then send it in every request header:

```
Authorization: Bearer <access_token>
```

Access tokens expire in 1 hour. Use `/api/v1/refresh` with your refresh token to get a new one.

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/register` | Create account, returns tokens |
| POST | `/api/v1/login` | Login, returns tokens |
| POST | `/api/v1/refresh` | Get new access token |

### Expenses

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/expenses` | Add expense |
| GET | `/api/v1/expenses` | List expenses (paginated) |
| GET | `/api/v1/expenses/<id>` | Get single expense |
| PATCH | `/api/v1/expenses/<id>` | Update expense |
| DELETE | `/api/v1/expenses/<id>` | Soft delete expense |
| GET | `/api/v1/expenses/summary` | Monthly summary + budget alerts |

### Budgets

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/budgets` | Set budget limit for a category |
| GET | `/api/v1/budgets` | List all budget limits |
| DELETE | `/api/v1/budgets/<category>` | Remove budget limit |

---

## Valid Categories

`food` · `transport` · `housing` · `health` · `entertainment` · `education` · `shopping` · `other`

---

## Running Tests

```bash
python -m pytest tests/test_api.py -v
```

---

## Author

**Mohan Singh**
- GitHub: [github.com/Mohansingh-bit](https://github.com/Mohansingh-bit)
- LinkedIn: [linkedin.com/in/mohansingh-8b8a612a6](https://linkedin.com/in/mohansingh-8b8a612a6)
- Portfolio: [portfolio-c68g.onrender.com](https://portfolio-c68g.onrender.com)