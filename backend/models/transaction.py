from datetime import datetime
from app import db

class Transaction(db.Model):
    """Transaction model for storing transaction data"""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    transaction_type = db.Column(db.String(20), nullable=False)  # income, expense, transfer
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    merchant = db.Column(db.String(100))
    location = db.Column(db.String(100))
    is_recurring = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Return a dict representation of the transaction"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'transaction_type': self.transaction_type,
            'transaction_date': self.transaction_date.isoformat(),
            'merchant': self.merchant,
            'location': self.location,
            'is_recurring': self.is_recurring,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f"<Transaction {self.id}: {self.amount} - {self.category}>"