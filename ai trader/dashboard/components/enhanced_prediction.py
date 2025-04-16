# Enhanced Prediction Component
# This module implements advanced prediction functionality with improved accuracy

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional, Union, Any
import datetime
import yfinance as yf
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier, VotingRegressor, VotingClassifier, StackingRegressor, StackingClassifier, AdaBoostRegressor, AdaBoostClassifier
from sklearn.svm import SVR, SVC
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, precision_score, recall_score, f1_score, r2_score, confusion_matrix
from xgboost import XGBRegressor, XGBClassifier
import lightgbm as lgb
import catboost as cb
from dash import html, dcc
from dash.dependencies import Input, Output, State
import sys
import os
import warnings
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
import json
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import project modules
from data_processing.connectors.market_data import get_data_connector
from data_processing.processors.feature_engineering import FeatureEngineer
from ai_integration.gemini_integration_manager import gemini_manager
from dashboard.components.prediction import PredictionEngine

# Suppress warnings
warnings.filterwarnings('ignore')

class EnhancedPredictionEngine(PredictionEngine):
    """Enhanced engine for making highly accurate price and time predictions using advanced ML models."""
    
    def __init__(self):
        """Initialize the enhanced prediction engine."""
        super().__init__()
        
        # Add more advanced models with optimized hyperparameters
        self.models['price'] = {
            'Linear': LinearRegression(),
            'Ridge': Ridge(alpha=0.1),
            'Lasso': Lasso(alpha=0.01),
            'ElasticNet': ElasticNet(alpha=0.01, l1_ratio=0.5),
            'RandomForest': RandomForestRegressor(n_estimators=200, max_depth=10, min_samples_split=5, random_state=42),
            'GradientBoosting': GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42),
            'XGBoost': XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42),
            'LightGBM': lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42),
            'CatBoost': cb.CatBoostRegressor(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42, verbose=0),
            'SVR': SVR(C=1.0, epsilon=0.1, kernel='rbf'),
            'KNN': KNeighborsRegressor(n_neighbors=7, weights='distance'),
        }
        
        self.models['direction'] = {
            'Logistic': LogisticRegression(C=1.0, class_weight='balanced', random_state=42),
            'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=10, class_weight='balanced', random_state=42),
            'GradientBoosting': GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42),
            'XGBoost': XGBClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, scale_pos_weight=2, random_state=42),
            'LightGBM': lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, class_weight='balanced', random_state=42),
            'CatBoost': cb.CatBoostClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42, verbose=0),
            'SVC': SVC(C=1.0, kernel='rbf', probability=True, class_weight='balanced', random_state=42),
            'KNN': KNeighborsClassifier(n_neighbors=7, weights='distance'),
        }
        
        # Initialize ensemble models (will be created during training)
        self.ensemble_models = {
            'price': None,
            'direction': None
        }
        
        # Feature engineer for advanced feature creation
        self.feature_engineer = FeatureEngineer(include_indicators=True)
        
        # Scalers for different approaches
        self.scaler_types = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': RobustScaler()
        }
        
        # Track model performance metrics
        self.model_performance = {}
        
        # Anomaly detection thresholds
        self.anomaly_threshold = 2.0  # Z-score threshold for outlier detection
    
    def prepare_enhanced_features(self, df: pd.DataFrame, for_direction: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare enhanced features for prediction models.
        
        Args:
            df: DataFrame with historical data
            for_direction: Whether to prepare features for direction prediction
            
        Returns:
            Tuple of (X, y) where X is features and y is target
        """
        # Create features using the base method first
        X, y = self.prepare_features(df, for_direction)
        
        # Add more advanced features
        df_feat = df.copy()
        
        # Add technical indicators using FeatureEngineer
        enhanced_df = self.feature_engineer.process(df_feat)
        
        # Select relevant columns from enhanced dataframe
        technical_columns = [
            'rsi_14', 'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower',
            'stoch_k', 'stoch_d', 'atr', 'cci',
            'sma_5_20_cross', 'sma_20_50_cross'
        ]
        
        # Add available technical indicators to features
        for col in technical_columns:
            if col in enhanced_df.columns:
                X[col] = enhanced_df[col]
        
        # Add market regime features
        X['bull_market'] = (df_feat['close'] > df_feat['close'].shift(20)).astype(int)
        X['bear_market'] = (df_feat['close'] < df_feat['close'].shift(20)).astype(int)
        
        # Add volatility regime
        vol = df_feat['close'].pct_change().rolling(20).std()
        X['high_volatility'] = (vol > vol.rolling(100).mean()).astype(int)
        
        # Add day of week and month features for seasonality
        if 'date' in df_feat.columns:
            X['day_of_week'] = pd.to_datetime(df_feat['date']).dt.dayofweek
            X['month'] = pd.to_datetime(df_feat['date']).dt.month
            X['day_of_month'] = pd.to_datetime(df_feat['date']).dt.day
            
            # One-hot encode day of week and month
            for day in range(5):  # Trading days (0-4)
                X[f'day_{day}'] = (X['day_of_week'] == day).astype(int)
            
            for month in range(1, 13):
                X[f'month_{month}'] = (X['month'] == month).astype(int)
        
        # Drop original day and month columns
        X = X.drop(['day_of_week', 'month'], errors='ignore')
        
        # Remove any NaN values
        X.fillna(method='ffill', inplace=True)
        X.fillna(method='bfill', inplace=True)
        X.fillna(0, inplace=True)
        
        return X, y
    
    def detect_anomalies(self, X: pd.DataFrame) -> pd.Series:
        """Detect anomalies in the feature data.
        
        Args:
            X: DataFrame with features
            
        Returns:
            Series with boolean mask of anomalies
        """
        # Calculate z-scores for each feature
        z_scores = pd.DataFrame()
        for column in X.columns:
            z_scores[column] = stats.zscore(X[column], nan_policy='omit')
        
        # Identify rows with extreme values
        anomalies = (z_scores.abs() > self.anomaly_threshold).any(axis=1)
        
        return anomalies
    
    def create_ensemble_model(self, model_type: str, base_models: Dict) -> Union[VotingRegressor, VotingClassifier]:
        """Create an ensemble model from base models.
        
        Args:
            model_type: Type of model ('price' or 'direction')
            base_models: Dictionary of trained base models
            
        Returns:
            Ensemble model
        """
        if model_type == 'price':
            # Create a voting regressor for price prediction
            estimators = [(name, model) for name, model in base_models.items()]
            return VotingRegressor(estimators=estimators)
        else:
            # Create a voting classifier for direction prediction
            estimators = [(name, model) for name, model in base_models.items()]
            return VotingClassifier(estimators=estimators, voting='soft')
    
    def create_stacking_model(self, model_type: str, base_models: Dict) -> Union[StackingRegressor, StackingClassifier]:
        """Create a stacking model from base models.
        
        Args:
            model_type: Type of model ('price' or 'direction')
            base_models: Dictionary of trained base models
            
        Returns:
            Stacking model
        """
        if model_type == 'price':
            # Create a stacking regressor for price prediction
            estimators = [(name, model) for name, model in base_models.items()]
            return StackingRegressor(
                estimators=estimators,
                final_estimator=Ridge(alpha=0.1)
            )
        else:
            # Create a stacking classifier for direction prediction
            estimators = [(name, model) for name, model in base_models.items()]
            return StackingClassifier(
                estimators=estimators,
                final_estimator=LogisticRegression(C=1.0, class_weight='balanced')
            )
    
    def train_models(self, ticker: str, data_range: str, interval: str, prediction_type: str) -> Dict:
        """Train prediction models with enhanced features and ensemble methods.
        
        Args:
            ticker: The ticker symbol
            data_range: The data range
            interval: The data interval
            prediction_type: Type of prediction ("price", "time", "price and time")
            
        Returns:
            Dictionary with training results
        """
        results = {}
        
        # Get data based on prediction type
        if prediction_type in ["price", "price and time"]:
            # Train price prediction models
            df = self.get_historical_data(ticker, data_range, interval)
            X, y = self.prepare_enhanced_features(df)
            
            # Detect and remove anomalies
            anomalies = self.detect_anomalies(X)
            X_clean = X[~anomalies]
            y_clean = y[~anomalies]
            
            # Split data with time series consideration
            tscv = TimeSeriesSplit(n_splits=5)
            split = list(tscv.split(X_clean))[-1]  # Get the last split
            train_idx, test_idx = split
            
            X_train, X_test = X_clean.iloc[train_idx], X_clean.iloc[test_idx]
            y_train, y_test = y_clean.iloc[train_idx], y_clean.iloc[test_idx]
            
            # Scale features
            scaler = self.scaler_types['robust']  # Use robust scaler for better handling of outliers
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train models for high and low prediction
            trained_models = {}
            model_metrics = {}
            
            for target_idx, target_name in enumerate(['next_day_high', 'next_day_low']):
                target_train = y_train.iloc[:, target_idx]
                target_test = y_test.iloc[:, target_idx]
                
                target_models = {}
                target_metrics = {}
                
                # Train individual models
                for model_name, model in self.models['price'].items():
                    # Train model
                    model.fit(X_train_scaled, target_train)
                    
                    # Make predictions
                    y_pred = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    mse = mean_squared_error(target_test, y_pred)
                    mae = mean_absolute_error(target_test, y_pred)
                    r2 = r2_score(target_test, y_pred)
                    
                    # Store model and metrics
                    target_models[model_name] = model
                    target_metrics[model_name] = {
                        'mse': mse,
                        'mae': mae,
                        'rmse': np.sqrt(mse),
                        'r2': r2
                    }
                
                # Create and train ensemble models
                # 1. Voting Ensemble
                voting_ensemble = self.create_ensemble_model('price', target_models)
                voting_ensemble.fit(X_train_scaled, target_train)
                voting_pred = voting_ensemble.predict(X_test_scaled)
                
                voting_mse = mean_squared_error(target_test, voting_pred)
                voting_mae = mean_absolute_error(target_test, voting_pred)
                voting_r2 = r2_score(target_test, voting_pred)
                
                target_models['VotingEnsemble'] = voting_ensemble
                target_metrics['VotingEnsemble'] = {
                    'mse': voting_mse,
                    'mae': voting_mae,
                    'rmse': np.sqrt(voting_mse),
                    'r2': voting_r2
                }
                
                # 2. Stacking Ensemble
                stacking_ensemble = self.create_stacking_model('price', target_models)
                stacking_ensemble.fit(X_train_scaled, target_train)
                stacking_pred = stacking_ensemble.predict(X_test_scaled)
                
                stacking_mse = mean_squared_error(target_test, stacking_pred)
                stacking_mae = mean_absolute_error(target_test, stacking_pred)
                stacking_r2 = r2_score(target_test, stacking_pred)
                
                target_models['StackingEnsemble'] = stacking_ensemble
                target_metrics['StackingEnsemble'] = {
                    'mse': stacking_mse,
                    'mae': stacking_mae,
                    'rmse': np.sqrt(stacking_mse),
                    'r2': stacking_r2
                }
                
                trained_models[target_name] = target_models
                model_metrics[target_name] = target_metrics
            
            # Store trained models and scaler
            model_key = f"{ticker}_{data_range}_{interval}_price"
            self.trained_models[model_key] = trained_models
            self.scalers[model_key] = scaler
            
            # Store feature columns for future prediction
            self.model_performance[model_key] = {
                'metrics': model_metrics,
                'features': X.columns.tolist(),
                'scaler': scaler,
                'anomalies_removed': sum(anomalies)
            }
            
            results['price'] = {
                'metrics': model_metrics,
                'features': X.columns.tolist(),
                'scaler': scaler,
                'anomalies_removed': sum(anomalies)
            }
        
        # Train direction prediction models if requested
        if prediction_type in ["bias"] or "bias" in prediction_type:
            # Train direction prediction models
            df = self.get_historical_data(ticker, data_range, interval)
            X, y = self.prepare_enhanced_features(df, for_direction=True)
            
            # Detect and remove anomalies
            anomalies = self.detect_anomalies(X)
            X_clean = X[~anomalies]
            y_clean = y[~anomalies]
            
            # Split data with time series consideration
            tscv = TimeSeriesSplit(n_splits=5)
            split = list(tscv.split(X_clean))[-1]  # Get the last split
            train_idx, test_idx = split
            
            X_train, X_test = X_clean.iloc[train_idx], X_clean.iloc[test_idx]
            y_train, y_test = y_clean.iloc[train_idx], y_clean.iloc[test_idx]
            
            # Scale features
            scaler_dir = self.scaler_types['robust']
            X_train_scaled = scaler_dir.fit_transform(X_train)
            X_test_scaled = scaler_dir.transform(X_test)
            
            # Train models for direction prediction
            trained_dir_models = {}
            dir_model_metrics = {}
            
            for model_name, model in self.models['direction'].items():
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Make predictions
                y_pred = model.predict(X_test_scaled)
                y_proba = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, 'predict_proba') else None
                
                # Calculate metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, zero_division=0)
                recall = recall_score(y_test, y_pred, zero_division=0)
                f1 = f1_score(y_test, y_pred, zero_division=0)
                
                # Store model and metrics
                trained_dir_models[model_name] = model
                dir_model_metrics[model_name] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1
                }
            
            # Create and train ensemble models
            # 1. Voting Ensemble
            voting_ensemble = self.create_ensemble_model('direction', trained_dir_models)
            voting_ensemble.fit(X_train_scaled, y_train)
            voting_pred = voting_ensemble.predict(X_test_scaled)
            
            voting_accuracy = accuracy_score(y_test, voting_pred)
            voting_precision = precision_score(y_test, voting_pred, zero_division=0)
            voting_recall = recall_score(y_test, voting_pred, zero_division=0)
            voting_f1 = f1_score(y_test, voting_pred, zero_division=0)
            
            trained_dir_models['VotingEnsemble'] = voting_ensemble
            dir_model_metrics['VotingEnsemble'] = {
                'accuracy': voting_accuracy,
                'precision': voting_precision,
                'recall': voting_recall,
                'f1': voting_f1
            }
            
            # 2. Stacking Ensemble
            stacking_ensemble = self.create_stacking_model('direction', trained_dir_models)
            stacking_ensemble.fit(X_train_scaled, y_train)
            stacking_pred = stacking_ensemble.predict(X_test_scaled)
            
            stacking_accuracy = accuracy_score(y_test, stacking_pred)
            stacking_precision = precision_score(y_test, stacking_pred, zero_division=0)
            stacking_recall = recall_score(y_test, stacking_pred, zero_division=0)
            stacking_f1 = f1_score(y_test, stacking_pred, zero_division=0)
            
            trained_dir_models['StackingEnsemble'] = stacking_ensemble
            dir_model_metrics['StackingEnsemble'] = {
                'accuracy': stacking_accuracy,
                'precision': stacking_precision,
                'recall': stacking_recall,
                'f1': stacking_f1
            }
            
            # Store trained models and scaler
            model_key = f"{ticker}_{data_range}_{interval}_direction"
            self.trained_models[model_key] = trained_dir_models
            self.scalers[model_key] = scaler_dir
            
            # Store performance metrics
            self.model_performance[model_key] = {
                'metrics': dir_model_metrics,
                'features': X.columns.tolist(),
                'scaler': scaler_dir,
                'anomalies_removed': sum(anomalies)
            }
            
            results['direction'] = {
                'metrics': dir_model_metrics,
                'features': X.columns.tolist(),
                'scaler': scaler_dir,
                'anomalies_removed': sum(anomalies)
            }
        
        return results
    
    def predict(self, ticker: str, data_range: str, interval: str, prediction_date: str, prediction_type: str) -> Dict:
        """Make predictions with enhanced accuracy using ensemble models and AI insights.
        
        Args:
            ticker: The ticker symbol
            data_range: The data range
            interval: The data interval
            prediction_date: The date to predict for
            prediction_type: Type of prediction ("price", "time", "price and time", "bias")
            
        Returns:
            Dictionary with predictions
        """
        predictions = {}
        
        # Get the latest data for feature creation
        df = self.get_historical_data(ticker, data_range, interval)
        
        # Try to get Gemini insights if available
        gemini_insights = self._get_gemini_insights(ticker, df)
        
        if prediction_type in ["price", "price and time"]:
            # Prepare features
            X, _ = self.prepare_enhanced_features(df)
            X_latest = X.iloc[-1:].copy()
            
            # Get trained models and scaler
            model_key = f"{ticker}_{data_range}_{interval}_price"
            if model_key not in self.trained_models:
                return {"error": "Models not trained. Please train models first."}
            
            trained_models = self.trained_models[model_key]
            scaler = self.scalers[model_key]
            
            # Scale features
            X_latest_scaled = scaler.transform(X_latest)
            
            # Make predictions for high and low
            price_predictions = {}
            confidence_scores = {}
            
            for target_name, target_models in trained_models.items():
                target_predictions = {}
                target_confidence = {}
                
                for model_name, model in target_models.items():
                    # Skip non-ensemble models for final prediction
                    if model_name not in ['VotingEnsemble', 'StackingEnsemble']:
                        continue
                        
                    pred = model.predict(X_latest_scaled)[0]
                    target_predictions[model_name] = pred
                    
                    # Calculate confidence based on model performance
                    if model_key in self.model_performance and 'metrics' in self.model_performance[model_key]:
                        metrics = self.model_performance[model_key]['metrics'][target_name]
                        if model_name in metrics:
                            # Higher R2 means higher confidence
                            r2 = metrics[model_name].get('r2', 0)
                            # Scale R2 to a confidence percentage (0-100%)
                            confidence = max(0, min(100, (r2 * 100)))
                            target_confidence[model_name] = confidence
                
                # Calculate weighted ensemble prediction
                if 'VotingEnsemble' in target_predictions and 'StackingEnsemble' in target_predictions:
                    # Use stacking ensemble as primary, with voting as backup
                    ensemble_pred = target_predictions['StackingEnsemble'] * 0.7 + target_predictions['VotingEnsemble'] * 0.3
                    
                    # Average confidence scores
                    ensemble_confidence = 0
                    if 'VotingEnsemble' in target_confidence and 'StackingEnsemble' in target_confidence:
                        ensemble_confidence = (target_confidence['StackingEnsemble'] * 0.7 + 
                                              target_confidence['VotingEnsemble'] * 0.3)
                elif 'StackingEnsemble' in target_predictions:
                    ensemble_pred = target_predictions['StackingEnsemble']
                    ensemble_confidence = target_confidence.get('StackingEnsemble', 70)  # Default confidence
                elif 'VotingEnsemble' in target_predictions:
                    ensemble_pred = target_predictions['VotingEnsemble']
                    ensemble_confidence = target_confidence.get('VotingEnsemble', 70)  # Default confidence
                else:
                    # Fallback to individual models if no ensemble is available
                    ensemble_pred = np.mean(list(target_predictions.values()))
                    ensemble_confidence = 50  # Lower default confidence
                
                # Apply Gemini insights if available
                if gemini_insights and 'price_adjustment' in gemini_insights:
                    adjustment = gemini_insights['price_adjustment']
                    # Apply a small adjustment based on AI insights (max ±2%)
                    ensemble_pred *= (1 + (adjustment * 0.02))
                
                target_predictions['ensemble'] = ensemble_pred
                target_confidence['ensemble'] = ensemble_confidence
                
                price_predictions[target_name] = target_predictions
                confidence_scores[target_name] = target_confidence
            
            predictions['price'] = price_predictions
            predictions['confidence'] = confidence_scores
        
        if prediction_type in ["bias"] or "bias" in prediction_type:
            # Prepare features for direction prediction
            X, _ = self.prepare_enhanced_features(df, for_direction=True)
            X_latest = X.iloc[-1:].copy()
            
            # Get trained models and scaler
            model_key = f"{ticker}_{data_range}_{interval}_direction"
            if model_key not in self.trained_models:
                predictions['direction'] = {"error": "Direction models not trained. Please train models first."}
            else:
                trained_dir_models = self.trained_models[model_key]
                scaler_dir = self.scalers[model_key]
                
                # Scale features
                X_latest_scaled = scaler_dir.transform(X_latest)
                
                # Make predictions for direction
                direction_predictions = {}
                direction_probabilities = {}
                
                for model_name, model in trained_dir_models.items():
                    # Skip non-ensemble models for final prediction
                    if model_name not in ['VotingEnsemble', 'StackingEnsemble']:
                        continue
                        
                    # Predict class (0 = bearish, 1 = bullish)
                    pred_class = model.predict(X_latest_scaled)[0]
                    direction_predictions[model_name] = "bullish" if pred_class == 1 else "bearish"
                    
                    # Get probability if available
                    if hasattr(model, "predict_proba"):
                        pred_proba = model.predict_proba(X_latest_scaled)[0]
                        direction_probabilities[model_name] = pred_proba[1] if pred_class == 1 else pred_proba[0]
                    else:
                        direction_probabilities[model_name] = 0.7  # Default probability
                
                # Determine ensemble prediction with weighted voting
                if 'VotingEnsemble' in direction_predictions and 'StackingEnsemble' in direction_predictions:
                    # If both ensembles agree, use that direction
                    if direction_predictions['VotingEnsemble'] == direction_predictions['StackingEnsemble']:
                        ensemble_direction = direction_predictions['VotingEnsemble']
                        # Average the probabilities but boost confidence when models agree
                        ensemble_probability = (direction_probabilities['VotingEnsemble'] * 0.3 + 
                                               direction_probabilities['StackingEnsemble'] * 0.7) * 1.1
                        # Cap at 1.0
                        ensemble_probability = min(1.0, ensemble_probability)
                    else:
                        # If they disagree, use the one with higher confidence
                        if direction_probabilities['VotingEnsemble'] > direction_probabilities['StackingEnsemble']:
                            ensemble_direction = direction_predictions['VotingEnsemble']
                            ensemble_probability = direction_probabilities['VotingEnsemble']
                        else:
                            ensemble_direction = direction_predictions['StackingEnsemble']
                            ensemble_probability = direction_probabilities['StackingEnsemble']
                elif 'StackingEnsemble' in direction_predictions:
                    ensemble_direction = direction_predictions['StackingEnsemble']
                    ensemble_probability = direction_probabilities['StackingEnsemble']
                elif 'VotingEnsemble' in direction_predictions:
                    ensemble_direction = direction_predictions['VotingEnsemble']
                    ensemble_probability = direction_probabilities['VotingEnsemble']
                else:
                    # Fallback to majority vote of individual models
                    bullish_count = sum(1 for pred in direction_predictions.values() if pred == "bullish")
                    bearish_count = len(direction_predictions) - bullish_count
                    ensemble_direction = "bullish" if bullish_count > bearish_count else "bearish"
                    ensemble_probability = max(bullish_count, bearish_count) / (bullish_count + bearish_count) if (bullish_count + bearish_count) > 0 else 0.5
                
                # Apply Gemini insights if available
                if gemini_insights and 'direction_bias' in gemini_insights:
                    # If AI has high confidence and contradicts model, adjust probability
                    ai_direction = gemini_insights['direction_bias']
                    ai_confidence = gemini_insights.get('direction_confidence', 0.5)
                    
                    if ai_direction != ensemble_direction and ai_confidence > 0.7:
                        # Reduce model confidence when AI strongly disagrees
                        ensemble_probability *= 0.9
                    elif ai_direction == ensemble_direction:
                        # Boost confidence when AI agrees
                        ensemble_probability = min(1.0, ensemble_probability * 1.1)
                
                # Store final predictions
                direction_predictions['ensemble'] = ensemble_direction
                direction_probabilities['ensemble'] = ensemble_probability
                
                predictions['direction'] = {
                    'predictions': direction_predictions,
                    'probabilities': direction_probabilities,
                    'ensemble': ensemble_direction,
                    'ensemble_probability': ensemble_probability
                }
        
        return predictions
    
    def _get_gemini_insights(self, ticker: str, df: pd.DataFrame) -> Optional[Dict]:
        """Get market insights from Gemini AI.
        
        Args:
            ticker: The ticker symbol
            df: DataFrame with historical data
            
        Returns:
            Dictionary with AI insights or None if not available
        """
        try:
            # Try to get a user ID for Gemini integration
            user_id = "default_user"  # Fallback user ID
            
            # Get Gemini integration for the user
            integration = gemini_manager.get_integration(user_id)
            
            if not integration or not hasattr(integration, 'analyze_text'):
                return None
            
            # Prepare market data summary for AI analysis
            recent_data = df.tail(20).copy()
            
            # Calculate some basic metrics
            price_change = (recent_data['close'].iloc[-1] / recent_data['close'].iloc[0] - 1) * 100
            avg_volume = recent_data['volume'].mean() if 'volume' in recent_data.columns else 'N/A'
            volatility = recent_data['close'].pct_change().std() * 100
            
            # Create a market summary
            market_summary = f"""
            Market Analysis Request for {ticker}:
            - Current Price: ${recent_data['close'].iloc[-1]:.2f}
            - Price Change (last 20 periods): {price_change:.2f}%
            - Volatility: {volatility:.2f}%
            - Average Volume: {avg_volume}
            
            Based on technical indicators and market conditions, what is your assessment of:
            1. The likely price direction (bullish/bearish) in the short term?
            2. Any potential price targets or support/resistance levels?
            3. Key risk factors to monitor?
            
            Please provide a numerical score from -5 to +5 for price direction bias, where:
            - Negative values indicate bearish bias (with -5 being extremely bearish)
            - Positive values indicate bullish bias (with +5 being extremely bullish)
            - 0 indicates neutral outlook
            
            Format your response with a clear 'Direction Score: X' on a separate line.
            """
            
            # Get AI analysis
            analysis = integration.analyze_text(market_summary)
            
            if not analysis or 'text' not in analysis:
                return None
            
            # Extract insights from the analysis
            insights = {}
            
            # Extract direction score
            direction_score_match = re.search(r'Direction Score:\s*([+-]?\d+)', analysis['text'])
            if direction_score_match:
                direction_score = float(direction_score_match.group(1))
                # Normalize to -1 to +1 range
                normalized_score = direction_score / 5.0
                
                insights['direction_bias'] = 'bullish' if normalized_score > 0 else 'bearish'
                insights['direction_confidence'] = min(1.0, abs(normalized_score) * 0.8 + 0.2)  # Scale to 0.2-1.0 range
                insights['price_adjustment'] = normalized_score * 0.5  # Scale for price adjustment
            
            return insights
        
        except Exception as e:
            print(f"Error getting Gemini insights: {e}")
            return None
    
    def run_backtest(self, ticker: str, data_range: str, interval: str, models: List[str]) -> Dict:
        """Run an enhanced backtest for selected models with cross-validation.
        
        Args:
            ticker: The ticker symbol
            data_range: The data range
            interval: The data interval
            models: List of model names to include in backtest
            
        Returns:
            Dictionary with backtest results
        """
        # Get historical data
        df = self.get_historical_data(ticker, data_range, interval)
        
        # Prepare enhanced features
        X, y = self.prepare_enhanced_features(df)
        
        # Remove anomalies
        anomalies = self.detect_anomalies(X)
        X_clean = X[~anomalies]
        y_clean = y[~anomalies]
        
        # Use time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Initialize results containers
        backtest_results = {}
        metrics = {}
        cv_scores = {}
        
        for target_idx, target_name in enumerate(['next_day_high', 'next_day_low']):
            target_y = y_clean.iloc[:, target_idx]
            target_results = {}
            
            for model_name in models:
                if model_name in self.models['price']:
                    model = self.models['price'][model_name]
                    
                    # Initialize arrays for predictions and actuals
                    all_predictions = []
                    all_actuals = []
                    fold_metrics = []
                    
                    # Perform cross-validation
                    for train_idx, test_idx in tscv.split(X_clean):
                        X_train, X_test = X_clean.iloc[train_idx], X_clean.iloc[test_idx]
                        y_train, y_test = target_y.iloc[train_idx], target_y.iloc[test_idx]
                        
                        # Scale features
                        scaler = self.scaler_types['robust']
                        X_train_scaled = scaler.fit_transform(X_train)
                        X_test_scaled = scaler.transform(X_test)
                        
                        # Train model
                        model.fit(X_train_scaled, y_train)
                        
                        # Make predictions
                        y_pred = model.predict(X_test_scaled)
                        
                        # Store predictions and actuals
                        all_predictions.extend(y_pred)
                        all_actuals.extend(y_test.values)
                        
                        # Calculate fold metrics
                        mse = mean_squared_error(y_test, y_pred)
                        mae = mean_absolute_error(y_test, y_pred)
                        r2 = r2_score(y_test, y_pred)
                        
                        fold_metrics.append({
                            'mse': mse,
                            'mae': mae,
                            'rmse': np.sqrt(mse),
                            'r2': r2
                        })
                    
                    # Convert to numpy arrays
                    all_predictions = np.array(all_predictions)
                    all_actuals = np.array(all_actuals)
                    
                    # Calculate overall metrics
                    mse = mean_squared_error(all_actuals, all_predictions)
                    mae = mean_absolute_error(all_actuals, all_predictions)
                    rmse = np.sqrt(mse)
                    r2 = r2_score(all_actuals, all_predictions)
                    
                    # Calculate average error as percentage
                    avg_error_pct = np.mean(np.abs((all_actuals - all_predictions) / all_actuals)) * 100
                    
                    # Store results
                    if model_name not in metrics:
                        metrics[model_name] = {}
                    
                    metrics[model_name][f"{target_name.split('_')[-1]}_rmse"] = rmse
                    metrics[model_name][f"{target_name.split('_')[-1]}_mae"] = mae
                    metrics[model_name][f"{target_name.split('_')[-1]}_r2"] = r2
                    
                    # Average the error percentages across high and low
                    if 'avg_error_pct' not in metrics[model_name]:
                        metrics[model_name]['avg_error_pct'] = avg_error_pct
                    else:
                        metrics[model_name]['avg_error_pct'] = (metrics[model_name]['avg_error_pct'] + avg_error_pct) / 2
                    
                    # Store cross-validation scores
                    if model_name not in cv_scores:
                        cv_scores[model_name] = {}
                    
                    cv_scores[model_name][target_name] = {
                        'fold_metrics': fold_metrics,
                        'avg_rmse': np.mean([m['rmse'] for m in fold_metrics]),
                        'avg_r2': np.mean([m['r2'] for m in fold_metrics])
                    }
                    
                    # Store predictions for visualization
                    target_results[model_name] = {
                        'actual': all_actuals,
                        'predicted': all_predictions,
                        'error': np.abs(all_actuals - all_predictions),
                        'error_pct': np.abs((all_actuals - all_predictions) / all_actuals) * 100
                    }
            
            backtest_results[target_name] = target_results
        
        # Create error visualization
        error_chart = self._create_enhanced_error_chart(backtest_results, models)
        
        return {
            'metrics': metrics,
            'cv_scores': cv_scores,
            'predictions': backtest_results,
            'error_chart': error_chart,
            'anomalies_removed': sum(anomalies)
        }
    
    def _create_enhanced_error_chart(self, backtest_results: Dict, models: List[str]) -> go.Figure:
        """Create an enhanced chart visualizing backtest errors with confidence intervals.
        
        Args:
            backtest_results: Dictionary with backtest results
            models: List of model names included in backtest
            
        Returns:
            Plotly figure object
        """
        fig = make_subplots(rows=2, cols=1, subplot_titles=('High Price Prediction Error %', 'Low Price Prediction Error %'))
        
        colors = px.colors.qualitative.Plotly
        
        # Add traces for high price errors
        for i, model_name in enumerate(models):
            if model_name in backtest_results['next_day_high']:
                error_pct = backtest_results['next_day_high'][model_name]['error_pct']
                
                # Calculate moving average and standard deviation for confidence intervals
                window = min(20, len(error_pct) // 4)
                error_ma = pd.Series(error_pct).rolling(window=window).mean()
                error_std = pd.Series(error_pct).rolling(window=window).std()
                
                # Add main error line
                fig.add_trace(
                    go.Scatter(
                        y=error_ma,
                        mode='lines',
                        name=f"{model_name} (High)",
                        line=dict(color=colors[i % len(colors)]),
                        legendgroup=model_name
                    ),
                    row=1, col=1
                )
                
                # Add confidence interval
                fig.add_trace(
                    go.Scatter(
                        y=error_ma + error_std,
                        mode='lines',
                        line=dict(width=0),
                        showlegend=False,
                        legendgroup=model_name
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        y=error_ma - error_std,
                        mode='lines',
                        line=dict(width=0),
                        fill='tonexty',
                        fillcolor=f'rgba({int(colors[i % len(colors)][1:3], 16)}, {int(colors[i % len(colors)][3:5], 16)}, {int(colors[i % len(colors)][5:7], 16)}, 0.2)',
                        showlegend=False,
                        legendgroup=model_name
                    ),
                    row=1, col=1
                )
        
        # Add traces for low price errors
        for i, model_name in enumerate(models):
            if model_name in backtest_results['next_day_low']:
                error_pct = backtest_results['next_day_low'][model_name]['error_pct']
                
                # Calculate moving average and standard deviation for confidence intervals
                window = min(20, len(error_pct) // 4)
                error_ma = pd.Series(error_pct).rolling(window=window).mean()
                error_std = pd.Series(error_pct).rolling(window=window).std()
                
                # Add main error line
                fig.add_trace(
                    go.Scatter(
                        y=error_ma,
                        mode='lines',
                        name=f"{model_name} (Low)",
                        line=dict(color=colors[i % len(colors)], dash='dash'),
                        legendgroup=model_name,
                        showlegend=False
                    ),
                    row=2, col=1
                )
                
                # Add confidence interval
                fig.add_trace(
                    go.Scatter(
                        y=error_ma + error_std,
                        mode='lines',
                        line=dict(width=0),
                        showlegend=False,
                        legendgroup=model_name
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        y=error_ma - error_std,
                        mode='lines',
                        line=dict(width=0),
                        fill='tonexty',
                        fillcolor=f'rgba({int(colors[i % len(colors)][1:3], 16)}, {int(colors[i % len(colors)][3:5], 16)}, {int(colors[i % len(colors)][5:7], 16)}, 0.2)',
                        showlegend=False,
                        legendgroup=model_name
                    ),
                    row=2, col=1
                )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text=f"Prediction Error Percentage by Model with Confidence Intervals",
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            template='plotly_white'
        )
        
        # Update y-axes
        fig.update_yaxes(title_text='Error %', row=1, col=1)
        fig.update_yaxes(title_text='Error %', row=2, col=1)
        
        # Update x-axes
        fig.update_xaxes(title_text='Test Sample', row=2, col=1)
        
        return fig