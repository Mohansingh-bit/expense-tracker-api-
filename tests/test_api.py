import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
from app import create_app
from config import TestingConfig
from extensions import db as _db


# ─── FIXTURES ────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register and login a user, return JWT auth headers."""
    client.post("/api/v1/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    res = client.post("/api/v1/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_expense(client, auth_headers):
    """Add one expense and return it."""
    res = client.post("/api/v1/expenses", json={
        "title": "Lunch", "amount": 150.0,
        "category": "food", "date": "2025-06-15"
    }, headers=auth_headers)
    return res.get_json()["expense"]


# ─── REGISTER ────────────────────────────────────────────────────────────────

def test_register_success(client):
    res = client.post("/api/v1/register", json={
        "username": "mohan", "email": "mohan@example.com", "password": "secret123"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "mohan"


def test_register_duplicate_username(client):
    client.post("/api/v1/register", json={
        "username": "mohan", "email": "mohan@example.com", "password": "secret123"
    })
    res = client.post("/api/v1/register", json={
        "username": "mohan", "email": "other@example.com", "password": "secret123"
    })
    assert res.status_code == 409


def test_register_duplicate_email(client):
    client.post("/api/v1/register", json={
        "username": "mohan", "email": "mohan@example.com", "password": "secret123"
    })
    res = client.post("/api/v1/register", json={
        "username": "mohan2", "email": "mohan@example.com", "password": "secret123"
    })
    assert res.status_code == 409


def test_register_weak_password(client):
    res = client.post("/api/v1/register", json={
        "username": "mohan", "email": "mohan@example.com", "password": "abc"
    })
    assert res.status_code == 422


def test_register_missing_fields(client):
    res = client.post("/api/v1/register", json={"username": "mohan"})
    assert res.status_code == 422


# ─── LOGIN ───────────────────────────────────────────────────────────────────

def test_login_success(client):
    client.post("/api/v1/register", json={
        "username": "mohan", "email": "mohan@example.com", "password": "secret123"
    })
    res = client.post("/api/v1/login", json={
        "email": "mohan@example.com", "password": "secret123"
    })
    assert res.status_code == 200
    assert "access_token" in res.get_json()


def test_login_wrong_password(client):
    client.post("/api/v1/register", json={
        "username": "mohan", "email": "mohan@example.com", "password": "secret123"
    })
    res = client.post("/api/v1/login", json={
        "email": "mohan@example.com", "password": "wrongpass"
    })
    assert res.status_code == 401


def test_login_wrong_email(client):
    res = client.post("/api/v1/login", json={
        "email": "nobody@example.com", "password": "secret123"
    })
    assert res.status_code == 401


# ─── AUTH GUARD ──────────────────────────────────────────────────────────────

def test_no_token_returns_401(client):
    res = client.get("/api/v1/expenses")
    assert res.status_code == 401


def test_invalid_token_returns_401(client):
    res = client.get("/api/v1/expenses", headers={"Authorization": "Bearer faketoken"})
    assert res.status_code == 422  # JWT returns 422 for malformed tokens


# ─── ADD EXPENSE ─────────────────────────────────────────────────────────────

def test_add_expense_success(client, auth_headers):
    res = client.post("/api/v1/expenses", json={
        "title": "Lunch", "amount": 150.0,
        "category": "food", "date": "2025-06-15"
    }, headers=auth_headers)
    assert res.status_code == 201
    assert res.get_json()["expense"]["amount"] == 150.0


def test_add_expense_invalid_category(client, auth_headers):
    res = client.post("/api/v1/expenses", json={
        "title": "Lunch", "amount": 150.0,
        "category": "xyz_invalid", "date": "2025-06-15"
    }, headers=auth_headers)
    assert res.status_code == 422


def test_add_expense_negative_amount(client, auth_headers):
    res = client.post("/api/v1/expenses", json={
        "title": "Lunch", "amount": -50,
        "category": "food", "date": "2025-06-15"
    }, headers=auth_headers)
    assert res.status_code == 422


def test_add_expense_bad_date(client, auth_headers):
    res = client.post("/api/v1/expenses", json={
        "title": "Lunch", "amount": 100,
        "category": "food", "date": "15-06-2025"
    }, headers=auth_headers)
    assert res.status_code == 422


# ─── UPDATE EXPENSE ──────────────────────────────────────────────────────────

def test_update_expense_success(client, auth_headers, sample_expense):
    res = client.patch(f"/api/v1/expenses/{sample_expense['id']}",
                       json={"amount": 200.0}, headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["expense"]["amount"] == 200.0


def test_update_expense_empty_body(client, auth_headers, sample_expense):
    res = client.patch(f"/api/v1/expenses/{sample_expense['id']}",
                       json={}, headers=auth_headers)
    assert res.status_code == 422


def test_update_expense_not_found(client, auth_headers):
    res = client.patch("/api/v1/expenses/9999",
                       json={"amount": 200.0}, headers=auth_headers)
    assert res.status_code == 404


# ─── GET EXPENSES ────────────────────────────────────────────────────────────

def test_get_all_expenses_paginated(client, auth_headers):
    for i in range(5):
        client.post("/api/v1/expenses", json={
            "title": f"Expense {i}", "amount": 100,
            "category": "food", "date": "2025-06-10"
        }, headers=auth_headers)

    res = client.get("/api/v1/expenses?page=1&per_page=3", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["expenses"]) == 3
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["has_next"] is True


def test_filter_by_category(client, auth_headers):
    client.post("/api/v1/expenses", json={
        "title": "Bus", "amount": 20, "category": "transport", "date": "2025-06-10"
    }, headers=auth_headers)
    client.post("/api/v1/expenses", json={
        "title": "Pizza", "amount": 200, "category": "food", "date": "2025-06-10"
    }, headers=auth_headers)
    res = client.get("/api/v1/expenses?category=food", headers=auth_headers)
    assert res.get_json()["pagination"]["total"] == 1


# ─── DELETE EXPENSE ──────────────────────────────────────────────────────────

def test_delete_expense_soft_delete(client, auth_headers, sample_expense):
    """After delete, expense should not appear in GET but still exist in DB."""
    res = client.delete(f"/api/v1/expenses/{sample_expense['id']}", headers=auth_headers)
    assert res.status_code == 200

    res = client.get(f"/api/v1/expenses/{sample_expense['id']}", headers=auth_headers)
    assert res.status_code == 404


def test_delete_nonexistent_expense(client, auth_headers):
    res = client.delete("/api/v1/expenses/9999", headers=auth_headers)
    assert res.status_code == 404


# ─── MONTHLY SUMMARY ─────────────────────────────────────────────────────────

def test_monthly_summary(client, auth_headers):
    client.post("/api/v1/expenses", json={
        "title": "Rent", "amount": 10000, "category": "housing", "date": "2025-06-01"
    }, headers=auth_headers)
    client.post("/api/v1/expenses", json={
        "title": "Food", "amount": 3000, "category": "food", "date": "2025-06-15"
    }, headers=auth_headers)

    res = client.get("/api/v1/expenses/summary?year=2025&month=6", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 13000
    assert data["by_category"]["food"]["percentage"] == round((3000 / 13000) * 100, 2)


def test_monthly_summary_empty(client, auth_headers):
    res = client.get("/api/v1/expenses/summary?year=2020&month=1", headers=auth_headers)
    assert res.get_json()["total"] == 0


# ─── BUDGET ──────────────────────────────────────────────────────────────────

def test_set_budget(client, auth_headers):
    res = client.post("/api/v1/budgets", json={
        "category": "food", "monthly_limit": 5000
    }, headers=auth_headers)
    assert res.status_code == 201


def test_budget_alert_exceeded(client, auth_headers):
    client.post("/api/v1/budgets", json={
        "category": "food", "monthly_limit": 100
    }, headers=auth_headers)
    client.post("/api/v1/expenses", json={
        "title": "Dinner", "amount": 110,
        "category": "food", "date": "2025-06-10"
    }, headers=auth_headers)
    res = client.get("/api/v1/expenses/summary?year=2025&month=6", headers=auth_headers)
    alerts = res.get_json()["budget_alerts"]
    assert len(alerts) == 1
    assert alerts[0]["status"] == "exceeded"


def test_budget_invalid_category(client, auth_headers):
    res = client.post("/api/v1/budgets", json={
        "category": "xyz_fake", "monthly_limit": 5000
    }, headers=auth_headers)
    assert res.status_code == 422


def test_delete_budget(client, auth_headers):
    client.post("/api/v1/budgets", json={
        "category": "food", "monthly_limit": 5000
    }, headers=auth_headers)
    res = client.delete("/api/v1/budgets/food", headers=auth_headers)
    assert res.status_code == 200


# ─── DATA ISOLATION ──────────────────────────────────────────────────────────

def test_data_isolation(client):
    """User A cannot see User B's expenses."""
    client.post("/api/v1/register", json={
        "username": "user_a", "email": "a@example.com", "password": "password123"
    })
    res_a = client.post("/api/v1/login", json={
        "email": "a@example.com", "password": "password123"
    })
    token_a = res_a.get_json()["access_token"]

    client.post("/api/v1/register", json={
        "username": "user_b", "email": "b@example.com", "password": "password123"
    })
    res_b = client.post("/api/v1/login", json={
        "email": "b@example.com", "password": "password123"
    })
    token_b = res_b.get_json()["access_token"]

    # User A adds an expense
    client.post("/api/v1/expenses", json={
        "title": "Secret expense", "amount": 999,
        "category": "other", "date": "2025-06-01"
    }, headers={"Authorization": f"Bearer {token_a}"})

    # User B should see 0 expenses
    res = client.get("/api/v1/expenses", headers={"Authorization": f"Bearer {token_b}"})
    assert res.get_json()["pagination"]["total"] == 0
