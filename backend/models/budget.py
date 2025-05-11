from datetime import datetime
from app import db

class Budget(db.Model):
    """Budget model for storing budget data"""
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Return a dict representation of the budget"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'amount': self.amount,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f"<Budget {self.id}: {self.category} - {self.amount}>"


class InvestmentProfile(db.Model):
    """Investment profile model for storing investment preferences"""
    __tablename__ = 'investment_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    risk_tolerance = db.Column(db.String(20), default='moderate')  # low, moderate, high
    investment_horizon = db.Column(db.Integer)  # in years
    investment_goal = db.Column(db.String(100))
    target_amount = db.Column(db.Float)
    monthly_contribution = db.Column(db.Float, default=0.0)
    preferred_sectors = db.Column(db.String(255))  # comma-separated sectors
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Return a dict representation of the investment profile"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'risk_tolerance': self.risk_tolerance,
            'investment_horizon': self.investment_horizon,
            'investment_goal': self.investment_goal,
            'target_amount': self.target_amount,
            'monthly_contribution': self.monthly_contribution,
            'preferred_sectors': self.preferred_sectors.split(',') if self.preferred_sectors else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f"<InvestmentProfile {self.id}: {self.risk_tolerance}>"