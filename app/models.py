from datetime import datetime, timezone
from decimal import Decimal
from extensions import db


# Fixed list of allowed categories — prevents "Food", "food", "fod" mess
VALID_CATEGORIES = [
    "food", "transport", "housing", "health",
    "entertainment", "education", "shopping", "other"
]


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)          # bcrypt hash
    is_active  = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    expenses     = db.relationship("Expense", backref="owner", lazy=True, cascade="all, delete-orphan")
    budget_limits = db.relationship("BudgetLimit", backref="owner", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title      = db.Column(db.String(120), nullable=False)
    amount     = db.Column(db.Numeric(10, 2), nullable=False)        # Decimal, not Float
    category   = db.Column(db.String(80), nullable=False)
    date       = db.Column(db.Date, nullable=False)
    note       = db.Column(db.String(500), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False) # Soft delete
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "amount": float(self.amount),   # serialize Decimal as float for JSON
            "category": self.category,
            "date": self.date.isoformat(),
            "note": self.note,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def __repr__(self):
        return f"<Expense {self.title} - {self.amount}>"


class BudgetLimit(db.Model):
    __tablename__ = "budget_limits"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category      = db.Column(db.String(80), nullable=False)
    monthly_limit = db.Column(db.Numeric(10, 2), nullable=False)     # Decimal, not Float
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                              onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("user_id", "category", name="unique_user_category_limit"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "monthly_limit": float(self.monthly_limit)
        }

    def __repr__(self):
        return f"<BudgetLimit {self.category} - {self.monthly_limit}>"
