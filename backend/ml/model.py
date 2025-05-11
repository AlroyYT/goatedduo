import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model, Model
from tensorflow.keras.layers import Dense, Dropout, LSTM, Input, concatenate
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import os
import joblib
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class FinancialAdvisorModel:
    """Deep learning model for financial advice"""
    
    def __init__(self, model_path='models/finance_advisor_model.h5', 
                 scaler_path='models/finance_scaler.pkl'):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.scaler = None
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create a new one"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                logger.info("Loading existing model and scaler...")
                self.model = load_model(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Model and scaler loaded successfully")
            else:
                logger.info("Creating new model and scaler...")
                self._create_model()
                self.scaler = StandardScaler()
                logger.info("New model and scaler created")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            logger.info("Creating new model...")
            self._create_model()
            self.scaler = StandardScaler()
    
    def _create_model(self):
        """Create a hybrid deep learning model for financial advice
        
        Architecture:
        1. Transaction history through LSTM for time-series analysis
        2. User profile data through dense layers
        3. Concatenate outputs and pass through final dense layers
        """
        # Transaction history input (time series)
        transaction_input = Input(shape=(30, 5), name='transaction_input')  # 30 days of 5 features
        lstm_layer = LSTM(64, return_sequences=True)(transaction_input)
        lstm_layer = LSTM(32)(lstm_layer)
        lstm_output = Dense(16)(lstm_layer)
        
        # User profile input (static features)
        profile_input = Input(shape=(10,), name='profile_input')  # 10 user profile features
        profile_dense = Dense(32, activation='relu')(profile_input)
        profile_dense = Dense(16, activation='relu')(profile_dense)
        
        # Combine outputs
        combined = concatenate([lstm_output, profile_dense])
        
        # Output layers
        x = Dense(32, activation='relu')(combined)
        x = Dropout(0.3)(x)
        x = Dense(16, activation='relu')(x)
        
        # Multiple outputs for different advice types
        budget_advice = Dense(5, activation='softmax', name='budget_advice')(x)  # 5 budget categories
        investment_advice = Dense(4, activation='softmax', name='investment_advice')(x)  # 4 investment strategies
        savings_advice = Dense(3, activation='softmax', name='savings_advice')(x)  # 3 savings recommendations
        
        # Build the model
        self.model = Model(
            inputs=[transaction_input, profile_input],
            outputs=[budget_advice, investment_advice, savings_advice]
        )
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss={
                'budget_advice': 'categorical_crossentropy',
                'investment_advice': 'categorical_crossentropy',
                'savings_advice': 'categorical_crossentropy'
            },
            metrics=['accuracy']
        )
        
        logger.info("Model created successfully")
        self.model.summary()
    
    def prepare_transaction_data(self, transactions, days=30):
        """
        Prepare transaction data for LSTM input
        
        Args:
            transactions: List of transaction objects
            days: Number of days to include in sequence
            
        Returns:
            Prepared transaction data as numpy array
        """
        # Sort transactions by date
        sorted_transactions = sorted(transactions, key=lambda x: x.transaction_date)
        
        # Extract features (amount, category encoded, transaction_type encoded, etc.)
        features = []
        for t in sorted_transactions[-days:]:
            # Simplified features for example
            transaction_type_encoded = 1 if t.transaction_type == 'income' else -1
            category_encoded = hash(t.category) % 10 / 10.0  # Simple category encoding
            
            # Features: [amount, transaction_type, is_recurring, category, day_of_month]
            feature_vector = [
                t.amount,
                transaction_type_encoded,
                1.0 if t.is_recurring else 0.0,
                category_encoded,
                t.transaction_date.day / 31.0  # Normalize day of month
            ]
            features.append(feature_vector)
        
        # Pad if necessary
        if len(features) < days:
            padding = [[0, 0, 0, 0, 0]] * (days - len(features))
            features = padding + features
        
        # Return as numpy array with expected shape for LSTM (samples, timesteps, features)
        return np.array([features])
    
    def prepare_user_profile(self, user, investment_profile=None):
        """
        Prepare user profile data
        
        Args:
            user: User object
            investment_profile: Investment profile object
            
        Returns:
            Prepared user profile data as numpy array
        """
        # Convert risk tolerance to numeric
        risk_map = {'low': 0.0, 'moderate': 0.5, 'high': 1.0}
        risk_value = risk_map.get(user.risk_tolerance, 0.5)
        
        # Calculate age from date of birth
        age = 30.0  # Default
        if user.date_of_birth:
            from datetime import datetime
            today = datetime.utcnow()
            age = (today - user.date_of_birth).days / 365.25
            age = min(age / 100.0, 1.0)  # Normalize age
        
        # Investment horizon if available
        investment_horizon = 0.5
        if investment_profile and investment_profile.investment_horizon:
            investment_horizon = min(investment_profile.investment_horizon / 40.0, 1.0)
        
        # Features: [monthly_income, risk_tolerance, age, has_investment_profile, investment_horizon, ...]
        profile_features = [
            user.monthly_income / 10000.0,  # Normalize income
            risk_value,
            age,
            1.0 if investment_profile else 0.0,
            investment_horizon,
            # Add more features as needed to reach 10 total
            0.5,  # placeholder
            0.5,  # placeholder
            0.5,  # placeholder
            0.5,  # placeholder
            0.5,  # placeholder
        ]
        
        return np.array([profile_features])
    
    def train(self, transaction_data, profile_data, budget_labels, investment_labels, savings_labels, epochs=50):
        """
        Train the model with prepared data
        
        Args:
            transaction_data: LSTM input data shape (samples, timesteps, features)
            profile_data: User profile data shape (samples, features)
            budget_labels: Budget advice labels
            investment_labels: Investment advice labels
            savings_labels: Savings advice labels
            epochs: Number of training epochs
        """
        # Scale profile data
        profile_data_scaled = self.scaler.fit_transform(profile_data)
        
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
            ModelCheckpoint(filepath=self.model_path, save_best_only=True)
        ]
        
        # Train model
        history = self.model.fit(
            [transaction_data, profile_data_scaled],
            {
                'budget_advice': budget_labels,
                'investment_advice': investment_labels,
                'savings_advice': savings_labels
            },
            epochs=epochs,
            batch_size=32,
            validation_split=0.2,
            callbacks=callbacks
        )
        
        # Save scaler
        os.makedirs(os.path.dirname(self.scaler_path), exist_ok=True)
        joblib.dump(self.scaler, self.scaler_path)
        
        return history
    
    def predict(self, transaction_data, profile_data):
        """
        Generate predictions for a user
        
        Args:
            transaction_data: Prepared transaction data
            profile_data: Prepared user profile data
            
        Returns:
            Dictionary of predictions
        """
        # Scale profile data
        if self.scaler is None:
            self.scaler = StandardScaler()
            profile_data_scaled = profile_data
        else:
            profile_data_scaled = self.scaler.transform(profile_data)
        
        # Generate predictions
        budget_pred, investment_pred, savings_pred = self.model.predict(
            [transaction_data, profile_data_scaled]
        )
        
        return {
            'budget_advice': self._decode_budget_advice(budget_pred[0]),
            'investment_advice': self._decode_investment_advice(investment_pred[0]),
            'savings_advice': self._decode_savings_advice(savings_pred[0])
        }
    
    def _decode_budget_advice(self, predictions):
        """Decode budget advice predictions"""
        categories = [
            "Reduce discretionary spending",
            "Increase emergency savings",
            "Adjust essential spending",
            "Optimize debt payments",
            "Current budget is optimal"
        ]
        
        # Get top 2 recommendations
        top_indices = predictions.argsort()[-2:][::-1]
        return [categories[i] for i in top_indices]
    
    def _decode_investment_advice(self, predictions):
        """Decode investment advice predictions"""
        strategies = [
            "Conservative portfolio (bonds focus)",
            "Balanced portfolio",
            "Growth portfolio (stocks focus)",
            "Alternative investments"
        ]
        
        # Get top recommendation
        top_index = np.argmax(predictions)
        return strategies[top_index]
    
    def _decode_savings_advice(self, predictions):
        """Decode savings advice predictions"""
        advice = [
            "Increase retirement contributions",
            "Build emergency fund",
            "Save for short-term goals"
        ]
        
        # Get top recommendation
        top_index = np.argmax(predictions)
        return advice[top_index]


# Transfer Learning model for users with limited data
class TransferFinancialModel(FinancialAdvisorModel):
    """Transfer learning model for new users with limited data"""
    
    def __init__(self, base_model_path='models/base_finance_model.h5'):
        super().__init__(model_path='models/transfer_finance_model.h5')
        self.base_model_path = base_model_path
    
    import os
import logging
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam

logger = logging.getLogger(__name__)

def load_base_model(self):
    """Load pre-trained base model and transfer weights."""
    if os.path.exists(self.base_model_path):
        try:
            base_model = load_model(self.base_model_path)

            # Transfer weights from base model to current model
            for i, layer in enumerate(base_model.layers[:-3]):  # Skip last 3 output layers
                if i < len(self.model.layers):
                    self.model.layers[i].set_weights(layer.get_weights())

            # Freeze early layers
            for layer in self.model.layers[:5]:
                layer.trainable = False

            # Recompile model
            self.model.compile(
                optimizer=Adam(learning_rate=0.0005),
                loss={
                    'budget_advice': 'categorical_crossentropy',
                    'investment_advice': 'categorical_crossentropy',
                    'savings_advice': 'categorical_crossentropy'
                },
                metrics=['accuracy']
            )

            logger.info("Base model loaded and weights transferred successfully.")
        except Exception as e:
            logger.error(f"Error loading base model: {e}")
    else:
        logger.warning(f"Base model path does not exist: {self.base_model_path}")
