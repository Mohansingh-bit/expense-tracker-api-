from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import limiter
from auth import check_password, generate_tokens, get_current_user
from services import ExpenseService, BudgetService, UserService
from validators import (
    validate_register_input,
    validate_expense_input,
    validate_expense_update,
    validate_budget_input,
    ValidationError
)

api = Blueprint("api", __name__)


# ─── AUTH ────────────────────────────────────────────────────────────────────

@api.route("/register", methods=["POST"])
@limiter.limit("10 per hour")   # Rate limit — prevents spam registration
def register():
    """Register a new user. Returns JWT access + refresh tokens."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        clean = validate_register_input(data)
    except ValidationError as e:
        return jsonify({"error": e.message}), 422

    from models import User
    if User.query.filter_by(username=clean["username"]).first():
        return jsonify({"error": "Username already taken."}), 409
    if User.query.filter_by(email=clean["email"]).first():
        return jsonify({"error": "Email already registered."}), 409

    user = UserService.create_user(clean["username"], clean["email"], clean["password"])
    tokens = generate_tokens(user.id)

    return jsonify({
        "message": "Account created.",
        "user": user.to_dict(),
        **tokens
    }), 201


@api.route("/login", methods=["POST"])
@limiter.limit("20 per hour")
def login():
    """Login with email + password. Returns JWT tokens."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = UserService.get_by_email(email)

    # Same error for wrong email or wrong password — prevents user enumeration
    if not user or not check_password(password, user.password):
        return jsonify({"error": "Invalid email or password."}), 401

    tokens = generate_tokens(user.id)
    return jsonify({"message": "Login successful.", **tokens}), 200


@api.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    """Use refresh token to get a new access token without re-logging in."""
    user_id = get_jwt_identity()
    from flask_jwt_extended import create_access_token
    new_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_token}), 200


# ─── EXPENSES ────────────────────────────────────────────────────────────────

@api.route("/expenses", methods=["POST"])
@jwt_required()
def add_expense():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        clean = validate_expense_input(data)
    except ValidationError as e:
        return jsonify({"error": e.message}), 422

    user = get_current_user()
    expense = ExpenseService.add_expense(user.id, clean)
    return jsonify({"message": "Expense added.", "expense": expense.to_dict()}), 201


@api.route("/expenses", methods=["GET"])
@jwt_required()
def get_expenses():
    """
    Get expenses with pagination and optional category filter.
    Query params: ?category=food&page=1&per_page=20
    """
    user = get_current_user()
    category = request.args.get("category")

    try:
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)  # cap at 100
    except ValueError:
        return jsonify({"error": "'page' and 'per_page' must be integers."}), 400

    result = ExpenseService.get_all_expenses(user.id, category, page, per_page)
    return jsonify(result), 200


@api.route("/expenses/<int:expense_id>", methods=["GET"])
@jwt_required()
def get_expense(expense_id):
    user = get_current_user()
    expense = ExpenseService.get_expense_by_id(user.id, expense_id)
    if not expense:
        return jsonify({"error": f"Expense {expense_id} not found."}), 404
    return jsonify(expense.to_dict()), 200


@api.route("/expenses/<int:expense_id>", methods=["PATCH"])
@jwt_required()
def update_expense(expense_id):
    """Partially update an expense. Only send the fields you want to change."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        clean = validate_expense_update(data)
    except ValidationError as e:
        return jsonify({"error": e.message}), 422

    user = get_current_user()
    expense = ExpenseService.update_expense(user.id, expense_id, clean)
    if not expense:
        return jsonify({"error": f"Expense {expense_id} not found."}), 404
    return jsonify({"message": "Expense updated.", "expense": expense.to_dict()}), 200


@api.route("/expenses/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_expense(expense_id):
    """Soft delete — expense is hidden but kept in DB for audit history."""
    user = get_current_user()
    deleted = ExpenseService.delete_expense(user.id, expense_id)
    if not deleted:
        return jsonify({"error": f"Expense {expense_id} not found."}), 404
    return jsonify({"message": f"Expense {expense_id} deleted."}), 200


# ─── SUMMARY ─────────────────────────────────────────────────────────────────

@api.route("/expenses/summary", methods=["GET"])
@jwt_required()
def monthly_summary():
    from datetime import date
    today = date.today()

    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
    except ValueError:
        return jsonify({"error": "'year' and 'month' must be integers."}), 400

    if not (1 <= month <= 12):
        return jsonify({"error": "'month' must be between 1 and 12."}), 400

    user = get_current_user()
    summary = ExpenseService.get_monthly_summary(user.id, year, month)
    return jsonify(summary), 200


# ─── BUDGET LIMITS ───────────────────────────────────────────────────────────

@api.route("/budgets", methods=["POST"])
@jwt_required()
def set_budget():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        clean = validate_budget_input(data)
    except ValidationError as e:
        return jsonify({"error": e.message}), 422

    user = get_current_user()
    limit = BudgetService.set_limit(user.id, clean)
    return jsonify({"message": "Budget limit set.", "budget": limit.to_dict()}), 201


@api.route("/budgets", methods=["GET"])
@jwt_required()
def get_budgets():
    user = get_current_user()
    limits = BudgetService.get_limits(user.id)
    return jsonify({"budgets": [b.to_dict() for b in limits]}), 200


@api.route("/budgets/<string:category>", methods=["DELETE"])
@jwt_required()
def delete_budget(category):
    user = get_current_user()
    deleted = BudgetService.delete_limit(user.id, category)
    if not deleted:
        return jsonify({"error": f"No budget limit found for '{category}'."}), 404
    return jsonify({"message": f"Budget limit for '{category}' deleted."}), 200
