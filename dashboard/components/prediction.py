# Prediction Component
# This module implements the prediction functionality for the AI Trading Assistant

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional, Union, Any
import datetime
import yfinance as yf
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.svm import SVR, SVC
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, precision_score, recall_score, f1_score
from xgboost import XGBRegressor, XGBClassifier
import lightgbm as lgb
import catboost as cb
from dash import html, dcc
from dash.dependencies import Input, Output, State
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import project modules
from data_processing.connectors.market_data import get_data_connector


class PredictionEngine:
    """Engine for making price and time predictions using machine learning models."""
    
    def __init__(self):
        """Initialize the prediction engine."""
        self.data_connector = get_data_connector(source="yahoo")
        self.models = {
            'price': {
                'Linear Regression': LinearRegression(),
                'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'XGBoost': XGBRegressor(n_estimators=100, random_state=42),
                'LightGBM': lgb.LGBMRegressor(n_estimators=100, random_state=42),
                'CatBoost': cb.CatBoostRegressor(n_estimators=100, random_state=42, verbose=0),
                'SVR': SVR(),
                'KNN': KNeighborsRegressor(n_neighbors=5),
                'Decision Tree': DecisionTreeRegressor(random_state=42)
            },
            'direction': {
                'Logistic Regression': LogisticRegression(random_state=42),
                'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
                'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'XGBoost': XGBClassifier(n_estimators=100, random_state=42),
                'LightGBM': lgb.LGBMClassifier(n_estimators=100, random_state=42),
                'CatBoost': cb.CatBoostClassifier(n_estimators=100, random_state=42, verbose=0),
                'SVC': SVC(probability=True, random_state=42),
                'KNN': KNeighborsClassifier(n_neighbors=5),
                'Decision Tree': DecisionTreeClassifier(random_state=42)
            }
        }
        self.trained_models = {}
        self.scalers = {}
        self.available_tickers = [
            "NQ=F", "ES=F", "YM=F", "RTY=F", "GC=F", 
            "CL=F", "NG=F", "EURUSD=X", "GBPUSD=X", "DX-Y.NYB"
        ]
        self.data_ranges = ["1 year", "2 years", "3 years", "5 years", "10 years"]
        self.intervals = ["daily", "weekly"]
    
    def get_historical_data(self, ticker: str, data_range: str, interval: str = "daily") -> pd.DataFrame:
        """Get historical data for a ticker.
        
        Args:
            ticker: The ticker symbol
            data_range: The data range (e.g., "1 year", "2 years")
            interval: The data interval ("daily" or "weekly")
            
        Returns:
            DataFrame with historical data
        """
        # Convert data range to days
        range_map = {
            "1 year": 365,
            "2 years": 365 * 2,
            "3 years": 365 * 3,
            "5 years": 365 * 5,
            "10 years": 365 * 10
        }
        days = range_map.get(data_range, 365)
        
        # Calculate start and end dates
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Map interval to yfinance interval
        interval_map = {
            "daily": "1d",
            "weekly": "1wk"
        }
        yf_interval = interval_map.get(interval, "1d")
        
        # Get data
        df = self.data_connector.get_historical_data(
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            interval=yf_interval
        )
        
        return df
    
    def get_intraday_data(self, ticker: str, data_range: str) -> pd.DataFrame:
        """Get intraday data for time-based predictions.
        
        Args:
            ticker: The ticker symbol
            data_range: The data range (e.g., "1 year", "2 years")
            
        Returns:
            DataFrame with intraday data
        """
        # For intraday data, we'll use yfinance directly as our connector might not support it fully
        # Convert data range to days
        range_map = {
            "1 year": 365,
            "2 years": 365 * 2
        }
        days = range_map.get(data_range, 365)
        
        # Calculate start and end dates
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Get data - we'll use 1h interval for intraday analysis
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(start=start_date, end=end_date, interval="1h")
        
        # Reset index and rename columns
        df.reset_index(inplace=True)
        df.columns = [col.lower() for col in df.columns]
        if 'datetime' in df.columns:
            df.rename(columns={'datetime': 'date'}, inplace=True)
        
        # Add hour column for time prediction
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        
        return df
    
    def prepare_features(self, df: pd.DataFrame, for_direction: bool = False) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features for prediction models.
        
        Args:
            df: DataFrame with historical data
            for_direction: Whether to prepare features for direction prediction
            
        Returns:
            Tuple of (X, y) where X is features and y is target
        """
        # Create features
        df_feat = df.copy()
        
        # Add technical indicators
        # Moving averages
        df_feat['ma5'] = df_feat['close'].rolling(window=5).mean()
        df_feat['ma10'] = df_feat['close'].rolling(window=10).mean()
        df_feat['ma20'] = df_feat['close'].rolling(window=20).mean()
        df_feat['ma50'] = df_feat['close'].rolling(window=50).mean()
        
        # Price momentum
        df_feat['return_1d'] = df_feat['close'].pct_change(periods=1)
        df_feat['return_5d'] = df_feat['close'].pct_change(periods=5)
        df_feat['return_10d'] = df_feat['close'].pct_change(periods=10)
        
        # Volatility
        df_feat['volatility_5d'] = df_feat['return_1d'].rolling(window=5).std()
        df_feat['volatility_10d'] = df_feat['return_1d'].rolling(window=10).std()
        
        # Price relative to moving averages
        df_feat['price_to_ma5'] = df_feat['close'] / df_feat['ma5']
        df_feat['price_to_ma10'] = df_feat['close'] / df_feat['ma10']
        df_feat['price_to_ma20'] = df_feat['close'] / df_feat['ma20']
        
        # Volume features
        if 'volume' in df_feat.columns:
            df_feat['volume_ma5'] = df_feat['volume'].rolling(window=5).mean()
            df_feat['volume_ma10'] = df_feat['volume'].rolling(window=10).mean()
            df_feat['volume_change'] = df_feat['volume'].pct_change()
            df_feat['volume_to_ma5'] = df_feat['volume'] / df_feat['volume_ma5']
        
        # High-Low range
        df_feat['hl_range'] = (df_feat['high'] - df_feat['low']) / df_feat['close']
        df_feat['hl_range_ma5'] = df_feat['hl_range'].rolling(window=5).mean()
        
        # Drop NaN values
        df_feat.dropna(inplace=True)
        
        # Define features to use
        feature_columns = [
            'ma5', 'ma10', 'ma20', 'ma50',
            'return_1d', 'return_5d', 'return_10d',
            'volatility_5d', 'volatility_10d',
            'price_to_ma5', 'price_to_ma10', 'price_to_ma20',
            'hl_range', 'hl_range_ma5'
        ]
        
        # Add volume features if available
        if 'volume' in df_feat.columns:
            feature_columns.extend(['volume_ma5', 'volume_ma10', 'volume_change', 'volume_to_ma5'])
        
        # Create target variables
        if for_direction:
            # For direction prediction (bullish/bearish)
            df_feat['next_day_return'] = df_feat['close'].shift(-1) / df_feat['close'] - 1
            df_feat['direction'] = (df_feat['next_day_return'] > 0).astype(int)
            y = df_feat['direction']
        else:
            # For price prediction (high/low)
            df_feat['next_day_high'] = df_feat['high'].shift(-1)
            df_feat['next_day_low'] = df_feat['low'].shift(-1)
            y = df_feat[['next_day_high', 'next_day_low']]
        
        # Select features
        X = df_feat[feature_columns]
        
        return X, y
    
    def prepare_time_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare features for time prediction models.
        
        Args:
            df: DataFrame with intraday data
            
        Returns:
            Tuple of (X, y) where X is features and y is target times
        """
        # Group by date to find daily high and low times
        df['date_only'] = df['date'].dt.date
        
        # Find the time of day when high and low occur for each day
        high_times = df.loc[df.groupby('date_only')['high'].idxmax()]
        low_times = df.loc[df.groupby('date_only')['low'].idxmax()]
        
        # Create a dataframe with the high and low times for each day
        time_df = pd.DataFrame({
            'date': high_times['date_only'],
            'high_hour': high_times['hour'],
            'low_hour': low_times['hour']
        })
        
        # Create features for each day based on previous days
        time_features = pd.DataFrame()
        for i in range(1, 6):  # Use previous 5 days as features
            time_features[f'high_hour_lag{i}'] = time_df['high_hour'].shift(i)
            time_features[f'low_hour_lag{i}'] = time_df['low_hour'].shift(i)
        
        # Add day of week
        time_features['day_of_week'] = pd.to_datetime(time_df['date']).dt.dayofweek
        
        # Drop NaN values
        time_features.dropna(inplace=True)
        
        # Target variables are the high and low hours
        y = time_df.loc[time_features.index, ['high_hour', 'low_hour']]
        
        return time_features, y
    
    def train_models(self, ticker: str, data_range: str, interval: str, prediction_type: str) -> Dict:
        """Train prediction models.
        
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
            X, y = self.prepare_features(df)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
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
                
                for model_name, model in self.models['price'].items():
                    # Train model
                    model.fit(X_train_scaled, target_train)
                    
                    # Make predictions
                    y_pred = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    mse = mean_squared_error(target_test, y_pred)
                    mae = mean_absolute_error(target_test, y_pred)
                    
                    # Store model and metrics
                    target_models[model_name] = model
                    target_metrics[model_name] = {
                        'mse': mse,
                        'mae': mae,
                        'rmse': np.sqrt(mse)
                    }
                
                trained_models[target_name] = target_models
                model_metrics[target_name] = target_metrics
            
            # Store trained models and scaler
            model_key = f"{ticker}_{data_range}_{interval}_price"
            self.trained_models[model_key] = trained_models
            self.scalers[model_key] = scaler
            
            results['price'] = {
                'metrics': model_metrics,
                'features': X.columns.tolist(),
                'scaler': scaler
            }
        
        if prediction_type in ["time", "price and time"] and data_range in ["1 year", "2 years"] and interval == "daily":
            # Train time prediction models
            df_intraday = self.get_intraday_data(ticker, data_range)
            X_time, y_time = self.prepare_time_features(df_intraday)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X_time, y_time, test_size=0.2, random_state=42)
            
            # Scale features
            scaler_time = StandardScaler()
            X_train_scaled = scaler_time.fit_transform(X_train)
            X_test_scaled = scaler_time.transform(X_test)
            
            # Train models for high and low time prediction
            trained_time_models = {}
            time_model_metrics = {}
            
            for target_idx, target_name in enumerate(['high_hour', 'low_hour']):
                target_train = y_train.iloc[:, target_idx]
                target_test = y_test.iloc[:, target_idx]
                
                target_models = {}
                target_metrics = {}
                
                for model_name, model in self.models['price'].items():  # Reuse regression models
                    # Train model
                    model.fit(X_train_scaled, target_train)
                    
                    # Make predictions
                    y_pred = model.predict(X_test_scaled)
                    
                    # Calculate metrics
                    mse = mean_squared_error(target_test, y_pred)
                    mae = mean_absolute_error(target_test, y_pred)
                    
                    # Store model and metrics
                    target_models[model_name] = model
                    target_metrics[model_name] = {
                        'mse': mse,
                        'mae': mae,
                        'rmse': np.sqrt(mse)
                    }
                
                trained_time_models[target_name] = target_models
                time_model_metrics[target_name] = target_metrics
            
            # Store trained models and scaler
            model_key = f"{ticker}_{data_range}_{interval}_time"
            self.trained_models[model_key] = trained_time_models
            self.scalers[model_key] = scaler_time
            
            results['time'] = {
                'metrics': time_model_metrics,
                'features': X_time.columns.tolist(),
                'scaler': scaler_time
            }
        
        if prediction_type in ["bias"] and data_range in ["1 year", "2 years"] and interval == "daily":
            # Train direction prediction models
            df = self.get_historical_data(ticker, data_range, interval)
            X, y = self.prepare_features(df, for_direction=True)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler_dir = StandardScaler()
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
            
            # Store trained models and scaler
            model_key = f"{ticker}_{data_range}_{interval}_direction"
            self.trained_models[model_key] = trained_dir_models
            self.scalers[model_key] = scaler_dir
            
            results['direction'] = {
                'metrics': dir_model_metrics,
                'features': X.columns.tolist(),
                'scaler': scaler_dir
            }
        
        return results
    
    def predict(self, ticker: str, data_range: str, interval: str, prediction_date: str, prediction_type: str) -> Dict:
        """Make predictions for a future date.
        
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
        
        if prediction_type in ["price", "price and time"]:
            # Prepare features
            X, _ = self.prepare_features(df)
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
            
            for target_name, target_models in trained_models.items():
                target_predictions = {}
                
                for model_name, model in target_models.items():
                    pred = model.predict(X_latest_scaled)[0]
                    target_predictions[model_name] = pred
                
                # Calculate ensemble prediction (average of all models)
                ensemble_pred = np.mean(list(target_predictions.values()))
                target_predictions['ensemble'] = ensemble_pred
                
                price_predictions[target_name] = target_predictions
            
            predictions['price'] = price_predictions
        
        if prediction_type in ["time", "price and time"] and data_range in ["1 year", "2 years"] and interval == "daily":
            # Get intraday data for time prediction
            df_intraday = self.get_intraday_data(ticker, data_range)
            X_time, _ = self.prepare_time_features(df_intraday)
            X_time_latest = X_time.iloc[-1:].copy()
            
            # Get trained models and scaler
            model_key = f"{ticker}_{data_range}_{interval}_time"
            if model_key not in self.trained_models:
                predictions['time'] = {"error": "Time models not trained. Please train models first."}
            else:
                trained_time_models = self.trained_models[model_key]
                scaler_time = self.scalers[model_key]
                
                # Scale features
                X_time_latest_scaled = scaler_time.transform(X_time_latest)
                
                # Make predictions for high and low times
                time_predictions = {}
                
                for target_name, target_models in trained_time_models.items():
                    target_predictions = {}
                    
                    for model_name, model in target_models.items():
                        pred = model.predict(X_time_latest_scaled)[0]
                        # Round to nearest hour and ensure it's within 0-23 range
                        pred = max(0, min(23, round(pred)))
                        target_predictions[model_name] = pred
                    
                    # Calculate ensemble prediction (most common prediction)
                    ensemble_pred = round(np.mean(list(target_predictions.values())))
                    ensemble_pred = max(0, min(23, ensemble_pred))
                    target_predictions['ensemble'] = ensemble_pred
                    
                    time_predictions[target_name] = target_predictions
                
                predictions['time'] = time_predictions
        
        if prediction_type in ["bias"] and data_range in ["1 year", "2 years"] and interval == "daily":
            # Prepare features for direction prediction
            X, _ = self.prepare_features(df, for_direction=True)
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
                    # Predict class (0 = bearish, 1 = bullish)
                    pred_class = model.predict(X_latest_scaled)[0]
                    direction_predictions[model_name] = "bullish" if pred_class == 1 else "bearish"
                    
                    # Get probability if available
                    if hasattr(model, "predict_proba"):
                        pred_proba = model.predict_proba(X_latest_scaled)[0]
                        direction_probabilities[model_name] = pred_proba[1] if pred_class == 1 else pred_proba[0]
                    else:
                        direction_probabilities[model_name] = 0.5
                
                # Calculate ensemble prediction (majority vote)
                bullish_count = sum(1 for pred in direction_predictions.values() if pred == "bullish")
                bearish_count = len(direction_predictions) - bullish_count
                ensemble_direction = "bullish" if bullish_count > bearish_count else "bearish"
                
                # Calculate average probability
                ensemble_probability = np.mean(list(direction_probabilities.values()))
                
                predictions['direction'] = {
                    'predictions': direction_predictions,
                    'probabilities': direction_probabilities,
                    'ensemble': ensemble_direction,
                    'ensemble_probability': ensemble_probability
                }
        
        return predictions
    
    def run_backtest(self, ticker: str, data_range: str, interval: str, models: List[str]) -> Dict:
        """Run a backtest for selected models.
        
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
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Define test period (last 20% of data)
        test_size = int(len(X) * 0.2)
        train_X = X.iloc[:-test_size]
        train_y = y.iloc[:-test_size]
        test_X = X.iloc[-test_size:]
        test_y = y.iloc[-test_size:]
        
        # Scale features
        scaler = StandardScaler()
        train_X_scaled = scaler.fit_transform(train_X)
        test_X_scaled = scaler.transform(test_X)
        
        # Train models and make predictions
        backtest_results = {}
        metrics = {}
        
        for target_idx, target_name in enumerate(['next_day_high', 'next_day_low']):
            target_train = train_y.iloc[:, target_idx]
            target_test = test_y.iloc[:, target_idx]
            
            target_results = {}
            
            for model_name in models:
                if model_name in self.models['price']:
                    model = self.models['price'][model_name]
                    
                    # Train model
                    model.fit(train_X_scaled, target_train)
                    
                    # Make predictions
                    y_pred = model.predict(test_X_scaled)
                    
                    # Calculate metrics
                    mse = mean_squared_error(target_test, y_pred)
                    mae = mean_absolute_error(target_test, y_pred)
                    rmse = np.sqrt(mse)
                    
                    # Calculate average error as percentage
                    avg_error_pct = np.mean(np.abs((target_test - y_pred) / target_test)) * 100
                    
                    # Store results
                    if model_name not in metrics:
                        metrics[model_name] = {}
                    
                    metrics[model_name][f"{target_name.split('_')[-1]}_rmse"] = rmse
                    metrics[model_name][f"{target_name.split('_')[-1]}_mae"] = mae
                    metrics[model_name][f"{target_name.split('_')[-1]}_mse"] = mse
                    
                    # Average the error percentages across high and low
                    if 'avg_error_pct' not in metrics[model_name]:
                        metrics[model_name]['avg_error_pct'] = avg_error_pct
                    else:
                        metrics[model_name]['avg_error_pct'] = (metrics[model_name]['avg_error_pct'] + avg_error_pct) / 2
                    
                    # Store predictions for visualization
                    target_results[model_name] = {
                        'actual': target_test.values,
                        'predicted': y_pred,
                        'error': np.abs(target_test.values - y_pred),
                        'error_pct': np.abs((target_test.values - y_pred) / target_test.values) * 100
                    }
            
            backtest_results[target_name] = target_results
        
        # Create error visualization
        error_chart = self._create_error_chart(backtest_results, models)
        
        return {
            'metrics': metrics,
            'predictions': backtest_results,
            'error_chart': error_chart
        }
    
    def _create_error_chart(self, backtest_results: Dict, models: List[str]) -> go.Figure:
        """Create a chart visualizing backtest errors.
        
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
                fig.add_trace(
                    go.Scatter(
                        y=error_pct,
                        mode='lines',
                        name=f"{model_name} (High)",
                        line=dict(color=colors[i % len(colors)]),
                        legendgroup=model_name
                    ),
                    row=1, col=1
                )
        
        # Add traces for low price errors
        for i, model_name in enumerate(models):
            if model_name in backtest_results['next_day_low']:
                error_pct = backtest_results['next_day_low'][model_name]['error_pct']
                fig.add_trace(
                    go.Scatter(
                        y=error_pct,
                        mode='lines',
                        name=f"{model_name} (Low)",
                        line=dict(color=colors[i % len(colors)], dash='dash'),
                        legendgroup=model_name,
                        showlegend=False
                    ),
                    row=2, col=1
                )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text=f"Prediction Error Percentage by Model",
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            template='plotly_white'
        )
        
        # Update y-axes
        fig.update_yaxes(title_text='Error %', row=1, col=1)
        fig.update_yaxes(title_text='Error %', row=2, col=1)
        
        # Update x-axes
        fig.update_xaxes(title_text='Test Sample', row=2, col=1)
        
        return fig