import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import joblib
import os

class EmissionPredictor:
    """Machine Learning model for predicting future emissions"""
    
    def __init__(self, model_path='models/emission_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_trained = False
        self._ensure_model_dir()
    
    def _ensure_model_dir(self):
        """Create models directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
    
    def _prepare_features(self, emissions_data):
        """Prepare features from raw emission data"""
        df = pd.DataFrame(emissions_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Create time-based features
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        
        # Activity type encoding
        activity_dummies = pd.get_dummies(df['type'], prefix='activity')
        category_dummies = pd.get_dummies(df['category'], prefix='category')
        
        # Combine all features
        features = pd.concat([
            df[['days_since_start', 'day_of_week', 'day_of_month', 'month', 'value']],
            activity_dummies,
            category_dummies
        ], axis=1)
        
        target = df['emissions']
        
        return features, target, df, features.columns.tolist()
    
    def train_model(self, emissions_data):
        """Train ML model on emission data"""
        if len(emissions_data) < 5:
            print("Not enough data to train model. Need at least 5 records.")
            return False
        
        try:
            X, y, df, feature_names = self._prepare_features(emissions_data)
            self.feature_names = feature_names
            
            # Use Gradient Boosting for better performance
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
                subsample=0.8
            )
            
            self.model.fit(X, y)
            self.is_trained = True
            
            # Save model
            joblib.dump(self.model, self.model_path)
            self.scaler.fit(X)
            
            print(f"Model trained successfully with {len(emissions_data)} records")
            return True
        except Exception as e:
            print(f"Error training model: {str(e)}")
            return False
    
    def load_model(self):
        """Load pre-trained model from disk"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print(f"Model loaded from {self.model_path}")
                return True
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                return False
        return False
    
    def predict_future(self, emissions_data, days_ahead=30):
        """Predict emissions for future days"""
        if not self.is_trained and len(emissions_data) >= 5:
            self.train_model(emissions_data)
        
        if not self.is_trained or self.model is None:
            return {
                'success': False,
                'error': 'Model not trained. Need historical data.',
                'predictions': []
            }
        
        try:
            df = pd.DataFrame(emissions_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Get last known date
            last_date = df['date'].max()
            last_day_index = (last_date - df['date'].min()).days
            
            # Calculate average features
            avg_value = df['value'].mean()
            avg_activity_type = df['type'].mode()[0] if len(df['type'].mode()) > 0 else df['type'].iloc[0]
            avg_category = df['category'].mode()[0] if len(df['category'].mode()) > 0 else df['category'].iloc[0]
            
            predictions = []
            
            for i in range(1, days_ahead + 1):
                future_date = last_date + timedelta(days=i)
                
                # Create feature vector
                feature_dict = {name: 0 for name in self.feature_names}
                
                feature_dict['days_since_start'] = last_day_index + i
                feature_dict['day_of_week'] = future_date.dayofweek
                feature_dict['day_of_month'] = future_date.day
                feature_dict['month'] = future_date.month
                feature_dict['value'] = avg_value
                feature_dict[f'activity_{avg_activity_type}'] = 1
                feature_dict[f'category_{avg_category}'] = 1
                
                X_future = np.array([feature_dict.get(name, 0) for name in self.feature_names]).reshape(1, -1)
                pred = self.model.predict(X_future)[0]
                pred = max(0, pred)  # Ensure non-negative
                
                predictions.append({
                    'date': future_date.isoformat(),
                    'predicted_emissions_kg': round(pred, 2)
                })
            
            avg_predicted = np.mean([p['predicted_emissions_kg'] for p in predictions])
            trend = 'increasing' if predictions[-1]['predicted_emissions_kg'] > predictions[0]['predicted_emissions_kg'] else 'decreasing'
            
            return {
                'success': True,
                'days_ahead': days_ahead,
                'average_predicted_kg': round(avg_predicted, 2),
                'trend': trend,
                'predictions': predictions
            }
        except Exception as e:
            print(f"Error making predictions: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'predictions': []
            }
    
    def get_feature_importance(self):
        """Get feature importance from model"""
        if self.model is None or not self.is_trained:
            return {}
        
        try:
            importances = self.model.feature_importances_
            feature_importance = dict(zip(self.feature_names, importances))
            sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            return sorted_importance
        except Exception as e:
            print(f"Error getting feature importance: {str(e)}")
            return {}
    
    def predict_single(self, emission_record):
        """Predict emissions for a single record"""
        if not self.is_trained or self.model is None:
            return None
        
        try:
            feature_dict = {name: 0 for name in self.feature_names}
            
            # Set available features
            for key, value in emission_record.items():
                if key in feature_dict:
                    feature_dict[key] = value
            
            X = np.array([feature_dict.get(name, 0) for name in self.feature_names]).reshape(1, -1)
            prediction = self.model.predict(X)[0]
            return max(0, prediction)
        except Exception as e:
            print(f"Error predicting single record: {str(e)}")
            return None
    
    def get_model_info(self):
        """Get information about the trained model"""
        if not self.is_trained or self.model is None:
            return {
                'status': 'not_trained',
                'message': 'Model has not been trained yet'
            }
        
        return {
            'status': 'trained',
            'model_type': 'GradientBoostingRegressor',
            'n_estimators': self.model.n_estimators,
            'learning_rate': self.model.learning_rate,
            'max_depth': self.model.max_depth,
            'n_features': len(self.feature_names) if self.feature_names else 0,
            'feature_names': self.feature_names if self.feature_names else [],
            'model_path': self.model_path
        }


# Example usage (for testing)
if __name__ == "__main__":
    # Create sample data for testing
    sample_data = [
        {
            'date': '2024-11-01T10:00:00',
            'type': 'car',
            'value': 50,
            'emissions': 10.5,
            'category': 'transport'
        },
        {
            'date': '2024-11-02T10:00:00',
            'type': 'car',
            'value': 50,
            'emissions': 10.5,
            'category': 'transport'
        },
        {
            'date': '2024-11-03T10:00:00',
            'type': 'electricity',
            'value': 20,
            'emissions': 18.4,
            'category': 'energy'
        },
        {
            'date': '2024-11-04T10:00:00',
            'type': 'meat',
            'value': 2,
            'emissions': 54.0,
            'category': 'food'
        },
        {
            'date': '2024-11-05T10:00:00',
            'type': 'flight',
            'value': 500,
            'emissions': 127.5,
            'category': 'transport'
        }
    ]
    
    # Initialize predictor
    predictor = EmissionPredictor()
    
    # Train model
    print("Training model...")
    predictor.train_model(sample_data)
    
    # Get model info
    print("\nModel Info:")
    print(predictor.get_model_info())
    
    # Make predictions
    print("\nMaking predictions for 10 days...")
    predictions = predictor.predict_future(sample_data, days_ahead=10)
    print(f"Average predicted emissions: {predictions['average_predicted_kg']} kg CO₂")
    print(f"Trend: {predictions['trend']}")
    
    # Get feature importance
    print("\nTop 5 Important Features:")
    importance = predictor.get_feature_importance()
    for i, (feature, imp) in enumerate(list(importance.items())[:5]):
        print(f"{i+1}. {feature}: {imp:.4f}")