import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import joblib
import logging
import os

logger = logging.getLogger(__name__)

class FinancialDataPreprocessor:
    """Preprocessing for financial data to be used in ML models"""
    
    def __init__(self, scaler_path='models/preprocessing/feature_scaler.pkl', 
                 encoder_path='models/preprocessing/category_encoder.pkl'):
        self.scaler_path = scaler_path
        self.encoder_path = encoder_path
        self.scaler = None
        self.category_encoder = None
        self._load_or_create_transformers()
        
        # Common transaction categories
        self.common_categories = [
            'groceries', 'dining', 'utilities', 'rent', 'mortgage', 
            'transportation', 'entertainment', 'shopping', 'travel',
            'healthcare', 'education', 'income', 'investments', 'savings',
            'other'
        ]
    
    def _load_or_create_transformers(self):
        """Load existing preprocessors or create new ones"""
        try:
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded existing feature scaler")
            else:
                self.scaler = StandardScaler()
                logger.info("Created new feature scaler")
                
            if os.path.exists(self.encoder_path):
                self.category_encoder = joblib.load(self.encoder_path)
                logger.info("Loaded existing category encoder")
            else:
                self.category_encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
                # Fit with common categories
                self.category_encoder.fit(np.array(self.common_categories).reshape(-1, 1))
                logger.info("Created new category encoder")
                
        except Exception as e:
            logger.error(f"Error loading preprocessors: {str(e)}")
            self.scaler = StandardScaler()
            self.category_encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
            self.category_encoder.fit(np.array(self.common_categories).reshape(-1, 1))
    
    def save_transformers(self):
        """Save the trained preprocessors"""
        os.makedirs(os.path.dirname(self.scaler_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.encoder_path), exist_ok=True)
        joblib.dump(self.scaler, self.scaler_path)
        joblib.dump(self.category_encoder, self.encoder_path)
        logger.info("Saved preprocessors to disk")
    
    def prepare_user_transactions(self, transactions, time_window=90):
        """
        Process user transactions for time-series analysis
        
        Args:
            transactions: List of transaction objects
            time_window: Number of days to analyze
            
        Returns:
            Processed transaction features and aggregated statistics
        """
        if not transactions:
            return None, None
        
        # Convert to DataFrame for easier manipulation
        trans_data = []
        for t in transactions:
            trans_data.append({
                'amount': t.amount,
                'category': t.category.lower(),
                'transaction_type': t.transaction_type,
                'date': t.transaction_date,
                'is_recurring': t.is_recurring
            })
        
        df = pd.DataFrame(trans_data)
        
        # Filter for time window
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_window)
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        if df.empty:
            return None, None
        
        # Process transaction types
        df['amount_mod'] = df.apply(
            lambda x: x['amount'] if x['transaction_type'] == 'income' else -x['amount'], 
            axis=1
        )
        
        # Encode categories
        categories = np.array(df['category'].tolist()).reshape(-1, 1)
        encoded_categories = self.category_encoder.transform(categories)
        
        # Feature engineering - daily aggregates
        df['date_day'] = df['date'].dt.date
        daily_features = []
        
        date_range = pd.date_range(start=start_date.date(), end=end_date.date())
        
        for date in date_range:
            day_df = df[df['date_day'] == date.date()]
            
            # Daily aggregates
            income = day_df[day_df['transaction_type'] == 'income']['amount'].sum()
            expenses = day_df[day_df['transaction_type'] == 'expense']['amount'].sum()
            net = income - expenses
            transaction_count = len(day_df)
            
            # Category breakdown (simplified for top categories)
            category_totals = {cat: 0 for cat in self.common_categories[:5]}  # Use just top 5 categories
            
            for _, row in day_df.iterrows():
                cat = row['category']
                if cat in category_totals:
                    if row['transaction_type'] == 'expense':
                        category_totals[cat] += row['amount']
            
            feature_vector = [
                date.day / 31.0,  # Normalized day of month
                date.weekday() / 6.0,  # Normalized day of week
                income,
                expenses,
                net,
                transaction_count
            ]
            
            # Add category totals
            feature_vector.extend(list(category_totals.values()))
            
            daily_features.append(feature_vector)
        
        # Create time series data
        X_timeseries = np.array(daily_features)
        
        # Scale numerical features
        if len(X_timeseries) > 0:
            numerical_features = X_timeseries[:, 2:]  # Skip date features
            numerical_features_scaled = self.scaler.fit_transform(numerical_features)
            
            # Combine back with date features
            X_timeseries = np.concatenate([
                X_timeseries[:, :2],  # Date features
                numerical_features_scaled
            ], axis=1)
        
        # Calculate aggregated statistics
        stats = self._calculate_transaction_statistics(df)
        
        return X_timeseries, stats
    
    def _calculate_transaction_statistics(self, df):
        """Calculate aggregated transaction statistics"""
        if df.empty:
            return {}
            
        stats = {
            'total_income': df[df['transaction_type'] == 'income']['amount'].sum(),
            'total_expenses': df[df['transaction_type'] == 'expense']['amount'].sum(),
            'net_cashflow': df[df['transaction_type'] == 'income']['amount'].sum() - 
                           df[df['transaction_type'] == 'expense']['amount'].sum(),
            'transaction_count': len(df),
            'avg_transaction_size': df['amount'].mean(),
            'recurring_expenses': df[(df['is_recurring']) & 
                                    (df['transaction_type'] == 'expense')]['amount'].sum(),
            'largest_expense': df[df['transaction_type'] == 'expense']['amount'].max() 
                              if not df[df['transaction_type'] == 'expense'].empty else 0,
            'expense_categories': {}
        }
        
        # Calculate category breakdown
        expense_df = df[df['transaction_type'] == 'expense']
        category_totals = expense_df.groupby('category')['amount'].sum().to_dict()
        
        for category, amount in category_totals.items():
            stats['expense_categories'][category] = amount
            
        # Calculate spending trends
        if len(df) >= 14:  # At least 2 weeks of data
            df = df.sort_values('date')
            half_point = len(df) // 2
            
            first_half = df.iloc[:half_point]
            second_half = df.iloc[half_point:]
            
            first_expenses = first_half[first_half['transaction_type'] == 'expense']['amount'].sum()
            second_expenses = second_half[second_half['transaction_type'] == 'expense']['amount'].sum()
            
            if first_expenses > 0:
                expense_trend = (second_expenses - first_expenses) / first_expenses
                stats['expense_trend'] = expense_trend
        
        return stats
    
    def prepare_user_profile(self, user, investment_profile=None, budget=None):
        """
        Process user profile data
        
        Args:
            user: User object
            investment_profile: Investment profile object
            budget: User's budget data
            
        Returns:
            User profile features
        """
        # Map categorical features
        risk_map = {'low': 0.0, 'moderate': 0.5, 'high': 1.0}
        risk_value = risk_map.get(user.risk_tolerance, 0.5)
        
        # Calculate age
        age = 30.0  # Default
        if user.date_of_birth:
            today = datetime.utcnow()
            age = (today - user.date_of_birth).days / 365.25
        
        # Investment horizon
        investment_horizon = 5.0  # Default
        if investment_profile and investment_profile.investment_horizon:
            investment_horizon = investment_profile.investment_horizon
        
        # Monthly income to annual
        annual_income = (user.monthly_income or 0) * 12
        
        # Budget utilization
        budget_utilization = 0.0
        if budget:
            # Calculate budget vs actual spending
            # This would need actual implementation based on your budget model
            budget_utilization = 0.7  # Placeholder
        
        # Assemble feature vector
        features = np.array([
            annual_income,
            age,
            risk_value,
            investment_horizon,
            budget_utilization,
            float(bool(investment_profile)),  # Has investment profile
            user.monthly_income or 0,
            # Additional features can be added
        ]).reshape(1, -1)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        return scaled_features
    
    def identify_spending_patterns(self, transactions, time_window=90):
        """
        Identify recurring transactions and spending patterns
        
        Args:
            transactions: List of transaction objects
            time_window: Days to analyze
            
        Returns:
            Dictionary of spending patterns
        """
        if not transactions:
            return {}
            
        # Convert to DataFrame
        trans_data = []
        for t in transactions:
            trans_data.append({
                'amount': t.amount,
                'category': t.category.lower(),
                'transaction_type': t.transaction_type,
                'date': t.transaction_date,
                'merchant': t.merchant,
                'description': t.description
            })
        
        df = pd.DataFrame(trans_data)
        
        # Filter for time window
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_window)
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        if df.empty:
            return {}
            
        # Identify potential recurring transactions by grouping similar amounts and merchants
        potential_recurring = {}
        
        # Group by merchant and rounded amount
        df['rounded_amount'] = df['amount'].round(2)
        merchant_amount_groups = df[df['transaction_type'] == 'expense'].groupby(['merchant', 'rounded_amount'])
        
        for (merchant, amount), group in merchant_amount_groups:
            if len(group) >= 2:  # At least 2 occurrences
                dates = group['date'].tolist()
                # Check if dates are roughly periodic
                if self._check_periodicity(dates):
                    key = f"{merchant}_{amount}"
                    potential_recurring[key] = {
                        'merchant': merchant,
                        'amount': amount,
                        'category': group['category'].iloc[0],
                        'frequency': self._estimate_frequency(dates),
                        'occurrences': len(group),
                        'dates': [d.strftime('%Y-%m-%d') for d in dates]
                    }
        
        # Identify category spending trends
        category_trends = {}
        if not df.empty:
            # Get monthly spending by category
            df['month'] = df['date'].dt.to_period('M')
            monthly_category = df[df['transaction_type'] == 'expense'].groupby(['month', 'category'])['amount'].sum().reset_index()
            
            # Convert period to datetime for easier handling
            monthly_category['month'] = monthly_category['month'].dt.to_timestamp()
            
            # Get list of months and categories
            months = sorted(monthly_category['month'].unique())
            categories = df['category'].unique()
            
            # Calculate trend for each category
            for category in categories:
                cat_data = monthly_category[monthly_category['category'] == category]
                if len(cat_data) >= 2:
                    # Simple linear trend (could be improved with proper regression)
                    first_month = cat_data.iloc[0]
                    last_month = cat_data.iloc[-1]
                    
                    if first_month['amount'] > 0:
                        trend = (last_month['amount'] - first_month['amount']) / first_month['amount']
                        category_trends[category] = {
                            'trend': trend,
                            'first_month': first_month['month'].strftime('%Y-%m'),
                            'last_month': last_month['month'].strftime('%Y-%m'),
                            'first_amount': float(first_month['amount']),
                            'last_amount': float(last_month['amount'])
                        }
        
        return {
            'recurring_transactions': list(potential_recurring.values()),
            'category_trends': category_trends
        }
    
    def _check_periodicity(self, dates, tolerance=5):
        """Check if dates follow a periodic pattern"""
        if len(dates) < 2:
            return False
            
        # Sort dates
        dates = sorted(dates)
        
        # Calculate intervals between consecutive dates
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        
        if len(intervals) < 1:
            return False
            
        # Check if intervals are consistent within tolerance
        avg_interval = sum(intervals) / len(intervals)
        
        consistent = True
        for interval in intervals:
            if abs(interval - avg_interval) > tolerance:
                consistent = False
                break
                
        return consistent
    
    def _estimate_frequency(self, dates):
        """Estimate frequency of recurring transactions"""
        if len(dates) < 2:
            return "unknown"
            
        # Sort dates
        dates = sorted(dates)
        
        # Calculate average interval
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_interval = sum(intervals) / len(intervals)
        
        # Determine frequency
        if avg_interval < 15:
            return "bi-weekly"
        elif 15 <= avg_interval < 35:
            return "monthly"
        elif 85 <= avg_interval < 95:
            return "quarterly"
        elif 350 <= avg_interval < 380:
            return "annual"
        else:
            return f"every {int(round(avg_interval))} days"
    
    def extract_user_features(self, user, transactions, investment_profile=None):
        """
        Extract comprehensive feature set for the user
        
        Args:
            user: User object
            transactions: List of transaction objects
            investment_profile: Investment profile object
            
        Returns:
            Feature dictionary for model input and analysis
        """
        # Base user features
        features = {
            'user_id': user.id,
            'profile': {}
        }
        
        # Process transactions
        time_series, trans_stats = self.prepare_user_transactions(transactions)
        if trans_stats:
            features['transaction_stats'] = trans_stats
        
        # User profile features
        if user:
            profile_features = {
                'age': None,
                'risk_tolerance': user.risk_tolerance,
                'monthly_income': user.monthly_income,
                'financial_goal': user.financial_goal
            }
            
            if user.date_of_birth:
                today = datetime.utcnow()
                age = (today - user.date_of_birth).days / 365.25
                profile_features['age'] = int(age)
                
            features['profile'] = profile_features
        
        # Investment profile features
        if investment_profile:
            features['investment'] = {
                'risk_tolerance': investment_profile.risk_tolerance,
                'investment_horizon': investment_profile.investment_horizon,
                'goal': investment_profile.investment_goal,
                'target_amount': investment_profile.target_amount,
                'monthly_contribution': investment_profile.monthly_contribution
            }
        
        # Spending patterns
        spending_patterns = self.identify_spending_patterns(transactions)
        if spending_patterns:
            features['patterns'] = spending_patterns
        
        return features