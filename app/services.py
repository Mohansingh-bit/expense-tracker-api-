from datetime import datetime, timezone
from collections import defaultdict
from extensions import db
from models import Expense, BudgetLimit, User
from auth import hash_password


class UserService:

    @staticmethod
    def create_user(username: str, email: str, password: str) -> User:
        user = User(
            username=username,
            email=email,
            password=hash_password(password)
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email.lower(), is_active=True).first()

    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        return User.query.filter_by(id=user_id, is_active=True).first()


class ExpenseService:

    @staticmethod
    def add_expense(user_id: int, data: dict) -> Expense:
        expense = Expense(
            user_id=user_id,
            title=data["title"],
            amount=data["amount"],
            category=data["category"],
            date=data["date"],
            note=data.get("note")
        )
        db.session.add(expense)
        db.session.commit()
        return expense

    @staticmethod
    def get_all_expenses(user_id: int, category: str = None,
                         page: int = 1, per_page: int = 20) -> dict:
        """
        Returns paginated expenses.
        Only returns non-deleted expenses.
        """
        query = Expense.query.filter_by(user_id=user_id, is_deleted=False)
        if category:
            query = query.filter_by(category=category.lower())

        query = query.order_by(Expense.date.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "expenses": [e.to_dict() for e in paginated.items],
            "pagination": {
                "page": paginated.page,
                "per_page": paginated.per_page,
                "total": paginated.total,
                "pages": paginated.pages,
                "has_next": paginated.has_next,
                "has_prev": paginated.has_prev
            }
        }

    @staticmethod
    def get_expense_by_id(user_id: int, expense_id: int) -> Expense | None:
        return Expense.query.filter_by(
            id=expense_id, user_id=user_id, is_deleted=False
        ).first()

    @staticmethod
    def update_expense(user_id: int, expense_id: int, data: dict) -> Expense | None:
        """Partial update — only updates fields provided in data."""
        expense = Expense.query.filter_by(
            id=expense_id, user_id=user_id, is_deleted=False
        ).first()
        if not expense:
            return None

        for field, value in data.items():
            setattr(expense, field, value)

        expense.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return expense

    @staticmethod
    def delete_expense(user_id: int, expense_id: int) -> bool:
        """Soft delete — marks as deleted, does not remove from DB."""
        expense = Expense.query.filter_by(
            id=expense_id, user_id=user_id, is_deleted=False
        ).first()
        if not expense:
            return False
        expense.is_deleted = True
        expense.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return True

    @staticmethod
    def get_monthly_summary(user_id: int, year: int, month: int) -> dict:
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.is_deleted == False,
            db.extract("year", Expense.date) == year,
            db.extract("month", Expense.date) == month
        ).all()

        if not expenses:
            return {
                "year": year, "month": month,
                "total": 0, "count": 0,
                "by_category": {}, "budget_alerts": []
            }

        total = sum(float(e.amount) for e in expenses)
        by_category = defaultdict(lambda: {"total": 0, "count": 0, "expenses": []})

        for e in expenses:
            by_category[e.category]["total"] += float(e.amount)
            by_category[e.category]["count"] += 1
            by_category[e.category]["expenses"].append(e.to_dict())

        for cat in by_category:
            by_category[cat]["total"] = round(by_category[cat]["total"], 2)
            by_category[cat]["percentage"] = round(
                (by_category[cat]["total"] / total) * 100, 2
            )

        alerts = BudgetService.check_alerts(user_id, dict(by_category))

        return {
            "year": year,
            "month": month,
            "total": round(total, 2),
            "count": len(expenses),
            "by_category": {k: dict(v) for k, v in by_category.items()},
            "budget_alerts": alerts
        }


class BudgetService:

    @staticmethod
    def set_limit(user_id: int, data: dict) -> BudgetLimit:
        existing = BudgetLimit.query.filter_by(
            user_id=user_id, category=data["category"]
        ).first()
        if existing:
            existing.monthly_limit = data["monthly_limit"]
            existing.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return existing

        limit = BudgetLimit(
            user_id=user_id,
            category=data["category"],
            monthly_limit=data["monthly_limit"]
        )
        db.session.add(limit)
        db.session.commit()
        return limit

    @staticmethod
    def get_limits(user_id: int) -> list:
        return BudgetLimit.query.filter_by(user_id=user_id).all()

    @staticmethod
    def delete_limit(user_id: int, category: str) -> bool:
        limit = BudgetLimit.query.filter_by(
            user_id=user_id, category=category.lower()
        ).first()
        if not limit:
            return False
        db.session.delete(limit)
        db.session.commit()
        return True

    @staticmethod
    def check_alerts(user_id: int, by_category: dict) -> list:
        limits = BudgetLimit.query.filter_by(user_id=user_id).all()
        alerts = []
        for bl in limits:
            cat_data = by_category.get(bl.category)
            if not cat_data:
                continue
            spent = cat_data["total"]
            percent_used = round((spent / float(bl.monthly_limit)) * 100, 2)
            if percent_used >= 100:
                status = "exceeded"
            elif percent_used >= 80:
                status = "warning"
            else:
                continue
            alerts.append({
                "category": bl.category,
                "limit": float(bl.monthly_limit),
                "spent": round(spent, 2),
                "percent_used": percent_used,
                "status": status
            })
        return alerts
