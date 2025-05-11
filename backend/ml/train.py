import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
import logging
import joblib
from datetime import datetime

from model import FinancialAdvisorModel, TransferFinancialModel
from preprocess import FinancialDataPreprocessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelTrainer:
    """Training pipeline for financial advisor models"""
    
    def __init__(self, data_path='data/training_data.csv', 
                 model_output_dir='models/', 
                 batch_size=32, 
                 epochs=50):
        self.data_path = data_path
        self.model_output_dir = model_output_dir
        self.batch_size = batch_size
        self.epochs = epochs
        self.preprocessor = FinancialDataPreprocessor()
        
        # Ensure output directory exists
        os.makedirs(self.model_output_dir, exist_ok=True)
    
    def load_training_data(self):
        """Load and prepare training data"""
        logger.info(f"Loading training data from {self.data_path}")
        
        if not os.path.exists(self.data_path):
            logger.error(f"Training data file not found: {self.data_path}")
            return None
        
        # Load CSV data
        try:
            df = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(df)} records from training data")
            return df
        except Exception as e:
            logger.error(f"Error loading training data: {str(e)}")
            return None
    
    def prepare_training_data(self, df):
        """Prepare and preprocess training data"""
        if df is None or df.empty:
            logger.error("No training data available")
            return None, None, None, None
            
        logger.info("Preparing training data")
        
        # Example data preparation - adjust based on your actual data structure
        try:
            # Assuming df contains sequence data for each user
            # Example: user_id, day_1_feature_1, day_1_feature_2, ..., day_30_feature_1, ...
            
            # Extract transaction sequences
            # This is a simplified example - actual implementation depends on data format
            sequence_columns = [col for col in df.columns if col.startswith('day_')]
            X_transaction = df[sequence_columns].values
            
            # Reshape for LSTM: (samples, timesteps, features)
            n_samples = X_transaction.shape[0]
            n_timesteps = 30  # Assuming 30 days of data
            n_features = X_transaction.shape[1] // n_timesteps
            
            X_transaction = X_transaction.reshape(n_samples, n_timesteps, n_features)
            
            # Extract user profile features
            profile_columns = [col for col in df.columns if col.startswith('profile_')]
            X_profile = df[profile_columns].values
            
            # Extract target labels
            budget_advice_columns = [col for col in df.columns if col.startswith('budget_')]
            investment_advice_columns = [col for col in df.columns if col.startswith('invest_')]
            savings_advice_columns = [col for col in df.columns if col.startswith('savings_')]
            
            y_budget = df[budget_advice_columns].values
            y_investment = df[investment_advice_columns].values
            y_savings = df[savings_advice_columns].values
            
            # Split into training and validation sets
            X_trans_train, X_trans_val, X_profile_train, X_profile_val, \
            y_budget_train, y_budget_val, y_invest_train, y_invest_val, \
            y_savings_train, y_savings_val = train_test_split(
                X_transaction, X_profile, 
                y_budget, y_investment, y_savings,
                test_size=0.2, random_state=42
            )
            
            # Scale profile features
            X_profile_train = self.preprocessor.scaler.fit_transform(X_profile_train)
            X_profile_val = self.preprocessor.scaler.transform(X_profile_val)
            
            # Save the scaler
            self.preprocessor.save_transformers()
            
            logger.info(f"Prepared training data with {X_trans_train.shape[0]} training samples "
                       f"and {X_trans_val.shape[0]} validation samples")
            
            train_data = {
                'transaction': X_trans_train,
                'profile': X_profile_train,
                'budget': y_budget_train,
                'investment': y_invest_train,
                'savings': y_savings_train
            }
            
            val_data = {
                'transaction': X_trans_val,
                'profile': X_profile_val,
                'budget': y_budget_val,
                'investment': y_invest_val,
                'savings': y_savings_val
            }
            
            return train_data, val_data
            
        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
            return None, None
    
    def train_model(self):
        """Train the financial advisor model"""
        # Load and prepare data
        raw_data = self.load_training_data()
        train_data, val_data = self.prepare_training_data(raw_data)
        
        if train_data is None or val_data is None:
            logger.error("Cannot train model: training data preparation failed")
            return False
        
        # Initialize model
        model_path = os.path.join(self.model_output_dir, 'finance_advisor_model.h5')
        financial_model = FinancialAdvisorModel(model_path=model_path)
        
        # Create callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.0001
            ),
            ModelCheckpoint(
                filepath=model_path,
                monitor='val_loss',
                save_best_only=True
            )
        ]
        
        try:
            # Fit model
            history = financial_model.model.fit(
                [train_data['transaction'], train_data['profile']],
                {
                    'budget_advice': train_data['budget'],
                    'investment_advice': train_data['investment'],
                    'savings_advice': train_data['savings']
                },
                validation_data=(
                    [val_data['transaction'], val_data['profile']],
                    {
                        'budget_advice': val_data['budget'],
                        'investment_advice': val_data['investment'],
                        'savings_advice': val_data['savings']
                    }
                ),
                epochs=self.epochs,
                batch_size=self.batch_size,
                callbacks=callbacks
            )
            
            # Save training history
            history_df = pd.DataFrame(history.history)
            history_path = os.path.join(self.model_output_dir, 'training_history.csv')
            history_df.to_csv(history_path, index=False)
            
            # Save model metadata
            metadata = {
                'training_date': datetime.utcnow().isoformat(),
                'train_samples': train_data['transaction'].shape[0],
                'val_samples': val_data['transaction'].shape[0],
                'epochs_trained': len(history.history['loss']),
                'final_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1]),
                'batch_size': self.batch_size
            }
            
            metadata_path = os.path.join(self.model_output_dir, 'model_metadata.joblib')
            joblib.dump(metadata, metadata_path)
            
            logger.info(f"Model training completed and saved to {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error during model training: {str(e)}")
            return False

    def transfer_learn(self, new_data):
        """
        Fine-tune pre-trained model with new user data
        
        Args:
            new_data: DataFrame with new user data
            
        Returns:
            True if successful, False otherwise
        """
        if new_data is None or new_data.empty:
            logger.error("No new data available for transfer learning")
            return False
        
        try:
            # Prepare new data
            # This would need to be adapted to your specific data structure
            X_transaction = new_data['transaction_data']
            X_profile = new_data['profile_data']
            y_budget = new_data['budget_targets']
            y_investment = new_data['investment_targets']
            y_savings = new_data['savings_targets']
            
            # Scale profile features
            X_profile = self.preprocessor.scaler.transform(X_profile)
            
            # Load transfer learning model
            base_model_path = os.path.join(self.model_output_dir, 'finance_advisor_model.h5')
            transfer_model_path = os.path.join(self.model_output_dir, 'transfer_finance_model.h5')
            
            transfer_model = TransferFinancialModel(base_model_path=base_model_path)
            transfer_model.load_base_model()
            
            # Fine-tune model with fewer epochs
            history = transfer_model.model.fit(
                [X_transaction, X_profile],
                {
                    'budget_advice': y_budget,
                    'investment_advice': y_investment,
                    'savings_advice': y_savings
                },
                epochs=15,  # Fewer epochs for fine-tuning
                batch_size=16,  # Smaller batch size
                callbacks=[
                    EarlyStopping(monitor='loss', patience=5, restore_best_weights=True),
                    ModelCheckpoint(filepath=transfer_model_path, save_best_only=True)
                ]
            )
            
            logger.info(f"Transfer learning completed and saved to {transfer_model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error during transfer learning: {str(e)}")
            return False
    
    def generate_synthetic_training_data(self, n_samples=1000):
        """
        Generate synthetic training data for initial model training
        when real user data is limited
        
        Args:
            n_samples: Number of synthetic samples to generate
            
        Returns:
            DataFrame with synthetic training data
        """
        logger.info(f"Generating {n_samples} synthetic training samples")
        
        try:
            # Generate user profile data
            np.random.seed(42)
            
            # Risk tolerance distribution
            risk_tolerances = ['low', 'moderate', 'high']
            risk_probs = [0.3, 0.5, 0.2]
            
            # Generate random profiles
            profiles = []
            for i in range(n_samples):
                age = np.random.randint(18, 75)
                income = np.random.lognormal(mean=10.5, sigma=0.8)  # Log-normal for income
                risk_tolerance = np.random.choice(risk_tolerances, p=risk_probs)
                investment_horizon = np.random.randint(1, 30)
                
                # Encode risk tolerance
                risk_value = {'low': 0, 'moderate': 1, 'high': 2}[risk_tolerance]
                
                profile = {
                    'profile_age': age,
                    'profile_income': income,
                    'profile_risk': risk_value,
                    'profile_horizon': investment_horizon
                }
                
                # Add more profile features as needed
                for j in range(6):  # Add 6 more features to get 10 total
                    profile[f'profile_feature_{j}'] = np.random.random()
                
                profiles.append(profile)
            
            # Generate transaction sequences
            transaction_sequences = []
            for i in range(n_samples):
                # Base income (monthly)
                base_income = np.random.lognormal(mean=8.5, sigma=0.4)
                
                # Generate 30 days of transaction data
                sequence = {}
                for day in range(30):
                    # Income appears approximately every 15 days
                    income = base_income if day % 15 == 0 else 0
                    
                    # Daily expenses follow a pattern
                    daily_expense_mean = base_income / 40  # Average daily expense
                    expense = np.random.lognormal(mean=np.log(daily_expense_mean), sigma=0.8)
                    
                    # Add some category information
                    cat_food = np.random.lognormal(mean=np.log(daily_expense_mean/3), sigma=0.5) if np.random.random() < 0.7 else 0
                    cat_transport = np.random.lognormal(mean=np.log(daily_expense_mean/5), sigma=0.6) if np.random.random() < 0.5 else 0
                    cat_entertainment = np.random.lognormal(mean=np.log(daily_expense_mean/4), sigma=0.7) if np.random.random() < 0.3 else 0
                    cat_utilities = np.random.lognormal(mean=np.log(daily_expense_mean/8), sigma=0.4) if day % 30 < 3 and np.random.random() < 0.8 else 0
                    
                    # Large expenses occasionally
                    cat_large = np.random.lognormal(mean=np.log(base_income/3), sigma=0.9) if np.random.random() < 0.02 else 0
                    
                    # Add all sequences for this day
                    sequence[f'day_{day}_income'] = income
                    sequence[f'day_{day}_expense'] = expense
                    sequence[f'day_{day}_food'] = cat_food
                    sequence[f'day_{day}_transport'] = cat_transport
                    sequence[f'day_{day}_entertainment'] = cat_entertainment
                    sequence[f'day_{day}_utilities'] = cat_utilities
                    sequence[f'day_{day}_large_expense'] = cat_large
                
                transaction_sequences.append(sequence)
            
            # Generate target advice outputs
            advice_outputs = []
            for i in range(n_samples):
                profile = profiles[i]
                
                # Extract key features for rule-based advice generation
                age = profile['profile_age']
                income = profile['profile_income']
                risk = profile['profile_risk']
                horizon = profile['profile_horizon']
                
                # Simple rule-based budget advice
                budget_emergency_fund = min(0.5, max(0.1, 0.3 - 0.005 * age))  # Emergency fund decreases with age
                budget_essentials = min(0.8, max(0.4, 0.9 - income / 100000))  # Essentials percentage drops with higher income
                budget_savings = min(0.4, max(0.05, 0.1 + income / 200000))  # Savings increases with income
                budget_discretionary = max(0.05, 1 - budget_essentials - budget_savings)
                
                # Simple rule-based investment advice
                invest_stocks = min(0.9, max(0.1, risk * 0.3 + 0.2))  # Higher risk = more stocks
                invest_bonds = min(0.8, max(0.1, 0.5 - risk * 0.2))  # Lower risk = more bonds
                invest_alternatives = min(0.3, max(0, risk * 0.1))  # Higher risk = some alternatives
                # Ensure allocations sum to 1
                total = invest_stocks + invest_bonds + invest_alternatives
                invest_stocks /= total
                invest_bonds /= total
                invest_alternatives /= total
                
                # Simple rule-based savings advice
                savings_retirement = min(0.8, max(0.2, 0.3 + (age / 100)))  # More retirement focus with age
                savings_short_term = min(0.7, max(0.1, 0.6 - (age / 100)))  # Less short-term focus with age
                savings_medium_term = min(0.5, max(0.1, 1 - savings_retirement - savings_short_term))
                
                # Add noise for realism
                budget_emergency_fund *= np.random.normal(1, 0.1)
                budget_essentials *= np.random.normal(1, 0.05)
                budget_savings *= np.random.normal(1, 0.1)
                budget_discretionary *= np.random.normal(1, 0.15)
                
                invest_stocks *= np.random.normal(1, 0.05)
                invest_bonds *= np.random.normal(1, 0.05)
                invest_alternatives *= np.random.normal(1, 0.05)
                
                savings_retirement *= np.random.normal(1, 0.05)
                savings_short_term *= np.random.normal(1, 0.05)
                savings_medium_term *= np.random.normal(1, 0.05)
                
                # Re-normalize
                budget_total = budget_emergency_fund + budget_essentials + budget_savings + budget_discretionary
                budget_emergency_fund /= budget_total
                budget_essentials /= budget_total
                budget_savings /= budget_total
                budget_discretionary /= budget_total
                
                invest_total = invest_stocks + invest_bonds + invest_alternatives
                invest_stocks /= invest_total
                invest_bonds /= invest_total
                invest_alternatives /= invest_total
                
                savings_total = savings_retirement + savings_short_term + savings_medium_term
                savings_retirement /= savings_total
                savings_short_term /= savings_total
                savings_medium_term /= savings_total
                
                # Create output dictionary
                output = {
                    'budget_emergency': budget_emergency_fund,
                    'budget_essentials': budget_essentials,
                    'budget_savings': budget_savings,
                    'budget_discretionary': budget_discretionary,
                    'invest_stocks': invest_stocks,
                    'invest_bonds': invest_bonds,
                    'invest_alternatives': invest_alternatives,
                    'savings_retirement': savings_retirement,
                    'savings_short_term': savings_short_term,
                    'savings_medium_term': savings_medium_term
                }
                
                advice_outputs.append(output)
            
            # Combine all data
            combined_data = []
            for i in range(n_samples):
                sample = {}
                sample.update(profiles[i])
                sample.update(transaction_sequences[i])
                sample.update(advice_outputs[i])
                combined_data.append(sample)
            
            # Create DataFrame
            df = pd.DataFrame(combined_data)
            
            # Save to CSV
            output_path = os.path.join('data', 'synthetic_training_data.csv')
            os.makedirs('data', exist_ok=True)
            df.to_csv(output_path, index=False)
            
            logger.info(f"Generated synthetic data saved to {output_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error generating synthetic data: {str(e)}")
            return None
    
    def evaluate_model(self, test_data=None):
        """
        Evaluate trained model on test data or validation split
        
        Args:
            test_data: Optional test data DataFrame. If None, will use validation split.
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating model performance")
        
        try:
            # If no test data provided, use validation split from training data
            if test_data is None:
                raw_data = self.load_training_data()
                _, val_data = self.prepare_training_data(raw_data)
                
                if val_data is None:
                    logger.error("No validation data available for evaluation")
                    return None
                
                X_test = [val_data['transaction'], val_data['profile']]
                y_test = {
                    'budget_advice': val_data['budget'],
                    'investment_advice': val_data['investment'],
                    'savings_advice': val_data['savings']
                }
            else:
                # Process test data
                # This would need to be adapted based on your data format
                X_transaction = test_data['transaction_data']
                X_profile = self.preprocessor.scaler.transform(test_data['profile_data'])
                
                y_budget = test_data['budget_targets']
                y_investment = test_data['investment_targets']
                y_savings = test_data['savings_targets']
                
                X_test = [X_transaction, X_profile]
                y_test = {
                    'budget_advice': y_budget,
                    'investment_advice': y_investment,
                    'savings_advice': y_savings
                }
            
            # Load model
            model_path = os.path.join(self.model_output_dir, 'finance_advisor_model.h5')
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return None
                
            financial_model = FinancialAdvisorModel(model_path=model_path)
            financial_model.load_model()
            
            # Evaluate model
            eval_results = financial_model.model.evaluate(
                X_test, y_test, 
                verbose=1,
                return_dict=True
            )
            
            # Save evaluation results
            eval_path = os.path.join(self.model_output_dir, 'evaluation_results.joblib')
            joblib.dump(eval_results, eval_path)
            
            logger.info(f"Model evaluation completed: {eval_results}")
            return eval_results
            
        except Exception as e:
            logger.error(f"Error during model evaluation: {str(e)}")
            return None
    
    def run_training_pipeline(self, use_synthetic=False):
        """
        Run complete training pipeline from data preparation to evaluation
        
        Args:
            use_synthetic: If True, generate synthetic data for training
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Get data
            if use_synthetic:
                logger.info("Using synthetic data for training")
                data = self.generate_synthetic_training_data(n_samples=2000)
                
                # Save synthetic data to training data path
                data.to_csv(self.data_path, index=False)
            else:
                logger.info("Using real data for training")
                data = self.load_training_data()
            
            if data is None or data.empty:
                logger.error("No data available for training")
                return False
            
            # Step 2: Train model
            training_success = self.train_model()
            if not training_success:
                logger.error("Model training failed")
                return False
            
            # Step 3: Evaluate model
            eval_results = self.evaluate_model()
            if eval_results is None:
                logger.warning("Model evaluation returned no results")
            
            logger.info("Training pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in training pipeline: {str(e)}")
            return False


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Financial Advisor Model Training')
    parser.add_argument('--data', type=str, default='data/training_data.csv', help='Path to training data')
    parser.add_argument('--output', type=str, default='models/', help='Output directory for model files')
    parser.add_argument('--batch', type=int, default=32, help='Batch size for training')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--synthetic', action='store_true', help='Use synthetic data for training')
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = ModelTrainer(
        data_path=args.data,
        model_output_dir=args.output,
        batch_size=args.batch,
        epochs=args.epochs
    )
    
    # Run training pipeline
    success = trainer.run_training_pipeline(use_synthetic=args.synthetic)
    
    if success:
        logger.info("Financial advisor model training completed successfully")
        exit(0)
    else:
        logger.error("Financial advisor model training failed")
        exit(1)