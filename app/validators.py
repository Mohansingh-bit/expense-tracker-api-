from datetime import datetime
from models import VALID_CATEGORIES


class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def validate_register_input(data: dict) -> dict:
    errors = []

    username = data.get("username", "").strip()
    if not username:
        errors.append("'username' is required.")
    elif len(username) < 3:
        errors.append("'username' must be at least 3 characters.")
    elif len(username) > 80:
        errors.append("'username' cannot exceed 80 characters.")

    email = data.get("email", "").strip().lower()
    if not email:
        errors.append("'email' is required.")
    elif "@" not in email or "." not in email.split("@")[-1]:
        errors.append("'email' is not valid.")
    elif len(email) > 120:
        errors.append("'email' cannot exceed 120 characters.")

    password = data.get("password", "")
    if not password:
        errors.append("'password' is required.")
    elif len(password) < 8:
        errors.append("'password' must be at least 8 characters.")

    if errors:
        raise ValidationError("; ".join(errors))

    return {"username": username, "email": email, "password": password}


def validate_expense_input(data: dict) -> dict:
    errors = []

    # title — required, max 120 chars
    title = data.get("title", "").strip()
    if not title:
        errors.append("'title' is required.")
    elif len(title) > 120:
        errors.append("'title' cannot exceed 120 characters.")

    # amount — positive decimal
    try:
        amount = float(data.get("amount"))
        if amount <= 0:
            errors.append("'amount' must be a positive number.")
        if amount > 10_000_000:
            errors.append("'amount' seems unrealistically large.")
    except (TypeError, ValueError):
        errors.append("'amount' must be a valid number.")
        amount = None

    # category — must be from fixed list
    category = data.get("category", "").strip().lower()
    if not category:
        errors.append("'category' is required.")
    elif category not in VALID_CATEGORIES:
        errors.append(f"'category' must be one of: {', '.join(VALID_CATEGORIES)}.")

    # date — YYYY-MM-DD
    date_str = data.get("date", "").strip()
    parsed_date = None
    if not date_str:
        errors.append("'date' is required (format: YYYY-MM-DD).")
    else:
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append("'date' must be in YYYY-MM-DD format.")

    # note — optional, max 500 chars
    note = data.get("note", "").strip() or None
    if note and len(note) > 500:
        errors.append("'note' cannot exceed 500 characters.")

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "title": title,
        "amount": amount,
        "category": category,
        "date": parsed_date,
        "note": note
    }


def validate_expense_update(data: dict) -> dict:
    """For PATCH — all fields optional, but at least one must be provided."""
    allowed = {"title", "amount", "category", "date", "note"}
    provided = {k: v for k, v in data.items() if k in allowed}

    if not provided:
        raise ValidationError("At least one field must be provided to update.")

    errors = []
    clean = {}

    if "title" in provided:
        title = provided["title"].strip()
        if not title:
            errors.append("'title' cannot be empty.")
        elif len(title) > 120:
            errors.append("'title' cannot exceed 120 characters.")
        else:
            clean["title"] = title

    if "amount" in provided:
        try:
            amount = float(provided["amount"])
            if amount <= 0:
                errors.append("'amount' must be positive.")
            else:
                clean["amount"] = amount
        except (TypeError, ValueError):
            errors.append("'amount' must be a valid number.")

    if "category" in provided:
        category = provided["category"].strip().lower()
        if category not in VALID_CATEGORIES:
            errors.append(f"'category' must be one of: {', '.join(VALID_CATEGORIES)}.")
        else:
            clean["category"] = category

    if "date" in provided:
        try:
            clean["date"] = datetime.strptime(provided["date"].strip(), "%Y-%m-%d").date()
        except ValueError:
            errors.append("'date' must be in YYYY-MM-DD format.")

    if "note" in provided:
        note = provided["note"].strip() or None
        if note and len(note) > 500:
            errors.append("'note' cannot exceed 500 characters.")
        else:
            clean["note"] = note

    if errors:
        raise ValidationError("; ".join(errors))

    return clean


def validate_budget_input(data: dict) -> dict:
    errors = []

    category = data.get("category", "").strip().lower()
    if not category:
        errors.append("'category' is required.")
    elif category not in VALID_CATEGORIES:
        errors.append(f"'category' must be one of: {', '.join(VALID_CATEGORIES)}.")

    try:
        limit = float(data.get("monthly_limit"))
        if limit <= 0:
            errors.append("'monthly_limit' must be a positive number.")
    except (TypeError, ValueError):
        errors.append("'monthly_limit' must be a valid number.")
        limit = None

    if errors:
        raise ValidationError("; ".join(errors))

    return {"category": category, "monthly_limit": limit}
