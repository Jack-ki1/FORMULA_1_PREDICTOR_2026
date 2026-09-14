"""
ML models module - the model zoo with various prediction models.
Includes gradient boosting, random forest, logistic regression, and ensemble methods.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib
import os
from backend.app.config.settings import settings


class MLModel:
    """Base class for ML models."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train the model on given data.
        
        Args:
            X: Feature matrix
            y: Target variable
        
        Returns:
            Training metrics
        """
        raise NotImplementedError("Subclasses must implement train method")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data.
        
        Args:
            X: Feature matrix
        
        Returns:
            Predictions
        """
        raise NotImplementedError("Subclasses must implement predict method")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities.
        
        Args:
            X: Feature matrix
        
        Returns:
            Prediction probabilities
        """
        raise NotImplementedError("Subclasses must implement predict_proba method")
    
    def save(self, filepath: str):
        """Save model to disk."""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
        }
        joblib.dump(model_data, filepath)
    
    def load(self, filepath: str):
        """Load model from disk."""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']


class GradientBoostingModel(MLModel):
    """Gradient boosting model for tabular prediction."""
    
    def __init__(self):
        super().__init__("GradientBoosting")
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train gradient boosting model."""
        self.feature_names = X.columns.tolist()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Calculate cross-validation score
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
        
        return {
            'model_name': self.model_name,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_)),
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)


class RandomForestModel(MLModel):
    """Random forest model for ensemble diversity."""
    
    def __init__(self):
        super().__init__("RandomForest")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train random forest model."""
        self.feature_names = X.columns.tolist()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
        
        return {
            'model_name': self.model_name,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_)),
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)


class LogisticRegressionModel(MLModel):
    """Logistic regression for interpretable baseline."""
    
    def __init__(self):
        super().__init__("LogisticRegression")
        self.model = LogisticRegression(
            max_iter=1000,
            random_state=42,
        )
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Train logistic regression model."""
        self.feature_names = X.columns.tolist()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
        
        return {
            'model_name': self.model_name,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': dict(zip(self.feature_names, np.abs(self.model.coef_[0]))),
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)


class ModelZoo:
    """Collection of ML models for ensemble prediction."""
    
    def __init__(self):
        self.models = {
            'gradient_boosting': GradientBoostingModel(),
            'random_forest': RandomForestModel(),
            'logistic_regression': LogisticRegressionModel(),
        }
        self.active_models = ['gradient_boosting', 'random_forest']
    
    def get_model(self, model_name: str) -> MLModel:
        """Get a specific model from the zoo."""
        return self.models.get(model_name.lower())
    
    def train_all(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Dict[str, Any]]:
        """Train all active models."""
        results = {}
        for model_name in self.active_models:
            model = self.models[model_name]
            try:
                results[model_name] = model.train(X, y)
            except Exception as e:
                results[model_name] = {'error': str(e)}
        return results
    
    def predict_all(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Get predictions from all active models."""
        predictions = {}
        for model_name in self.active_models:
            model = self.models[model_name]
            if model.is_trained:
                try:
                    predictions[model_name] = model.predict_proba(X)
                except Exception as e:
                    predictions[model_name] = None
        return predictions
    
    def save_models(self, model_dir: str = None):
        """Save all active models to disk."""
        model_dir = model_dir or settings.MODEL_CACHE_PATH
        os.makedirs(model_dir, exist_ok=True)
        
        for model_name in self.active_models:
            model = self.models[model_name]
            if model.is_trained:
                filepath = os.path.join(model_dir, f"{model_name}.pkl")
                model.save(filepath)
    
    def load_models(self, model_dir: str = None):
        """Load all active models from disk."""
        model_dir = model_dir or settings.MODEL_CACHE_PATH
        
        for model_name in self.active_models:
            model = self.models[model_name]
            filepath = os.path.join(model_dir, f"{model_name}.pkl")
            if os.path.exists(filepath):
                model.load(filepath)
    
    def add_model(self, model_name: str, model: MLModel):
        """Add a custom model to the zoo."""
        self.models[model_name.lower()] = model
    
    def set_active_models(self, model_names: List[str]):
        """Set which models should be used for prediction."""
        for name in model_names:
            if name.lower() not in self.models:
                raise ValueError(f"Model {name} not in zoo")
        self.active_models = [name.lower() for name in model_names]


# Global model zoo instance
model_zoo = ModelZoo()
