# Advanced Prediction Page for AI Trading Assistant
# This module implements an enhanced prediction page with advanced ML capabilities

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
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

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import project modules
from dashboard.components.prediction import PredictionEngine
from data_processing.connectors.market_data import get_data_connector


class AdvancedPredictionEngine(PredictionEngine):
    """Enhanced prediction engine with advanced ML models and features."""
    
    def __init__(self):
        """Initialize the advanced prediction engine."""
        super().__init__()
        
        # Add more advanced models
        self.models['price'].update({
            'LSTM': None,  # Will be initialized when needed
            'GRU': None,
            'N-BEATS': None,
            'Prophet': None,
            'Ensemble': None
        })
        
        self.models['direction'].update({
            'LSTM': None,
            'GRU': None,
            'Transformer': None,
            'Ensemble': None
        })
        
        # Available tickers for futures and forex
        self.available_tickers = [
            "NQ=F", "ES=F", "YM=F", "RTY=F", "GC=F", 
            "CL=F", "NG=F", "EURUSD=X", "GBPUSD=X", "DX-Y.NYB"
        ]
    
    def get_intraday_data(self, ticker: str, data_range: str) -> pd.DataFrame:
        """Get intraday data for time-based predictions with enhanced features.
        
        Args:
            ticker: The ticker symbol
            data_range: The data range (e.g., "1 year", "2 years")
            
        Returns:
            DataFrame with intraday data
        """
        # Convert data range to days
        range_map = {
            "1 year": 365,
            "2 years": 365 * 2
        }
        days = range_map.get(data_range, 365)
        
        # Calculate start and end dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
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
        df['minute'] = df['date'].dt.minute
        df['day_of_week'] = df['date'].dt.dayofweek
        
        # Add more advanced features
        df['session'] = df['hour'].apply(lambda x: 'morning' if 4 <= x < 12 else 
                                       'afternoon' if 12 <= x < 16 else 
                                       'evening' if 16 <= x < 20 else 'night')
        
        return df
    
    def prepare_bias_features(self, df: pd.DataFrame) -> tuple:
        """Prepare features for bias prediction (bullish/bearish).
        
        Args:
            df: DataFrame with historical data
            
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
        
        # Candlestick patterns
        df_feat['body_size'] = abs(df_feat['close'] - df_feat['open']) / df_feat['close']
        df_feat['upper_shadow'] = (df_feat['high'] - df_feat[['open', 'close']].max(axis=1)) / df_feat['close']
        df_feat['lower_shadow'] = (df_feat[['open', 'close']].min(axis=1) - df_feat['low']) / df_feat['close']
        
        # Drop NaN values
        df_feat.dropna(inplace=True)
        
        # Define features to use
        feature_columns = [
            'ma5', 'ma10', 'ma20', 'ma50',
            'return_1d', 'return_5d', 'return_10d',
            'volatility_5d', 'volatility_10d',
            'price_to_ma5', 'price_to_ma10', 'price_to_ma20',
            'hl_range', 'hl_range_ma5',
            'body_size', 'upper_shadow', 'lower_shadow'
        ]
        
        # Add volume features if available
        if 'volume' in df_feat.columns:
            feature_columns.extend(['volume_ma5', 'volume_ma10', 'volume_change', 'volume_to_ma5'])
        
        # Create target variable for direction prediction
        df_feat['next_day_return'] = df_feat['close'].shift(-1) / df_feat['close'] - 1
        df_feat['direction'] = (df_feat['next_day_return'] > 0).astype(int)
        
        # Select features and target
        X = df_feat[feature_columns]
        y = df_feat['direction']
        
        return X, y
    
    def train_bias_models(self, ticker: str, data_range: str) -> dict:
        """Train models for bias prediction (bullish/bearish).
        
        Args:
            ticker: The ticker symbol
            data_range: The data range
            
        Returns:
            Dictionary with training results
        """
        # Get data
        df = self.get_historical_data(ticker, data_range, "daily")
        X, y = self.prepare_bias_features(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train models
        trained_models = {}
        model_metrics = {}
        
        for model_name, model in self.models['direction'].items():
            if model is None:  # Skip models that require special initialization
                continue
                
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, 'predict_proba') else None
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            # Store model and metrics
            trained_models[model_name] = model
            model_metrics[model_name] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
        
        # Store trained models and scaler
        model_key = f"{ticker}_{data_range}_daily_bias"
        self.trained_models[model_key] = trained_models
        self.scalers[model_key] = scaler
        
        return {
            'metrics': model_metrics,
            'features': X.columns.tolist(),
            'scaler': scaler
        }
    
    def predict_bias(self, ticker: str, data_range: str, prediction_date: str) -> dict:
        """Predict market bias (bullish/bearish) for a future date.
        
        Args:
            ticker: The ticker symbol
            data_range: The data range
            prediction_date: The date to predict for
            
        Returns:
            Dictionary with bias predictions
        """
        # Get model key
        model_key = f"{ticker}_{data_range}_daily_bias"
        
        # Check if models are trained
        if model_key not in self.trained_models:
            self.train_bias_models(ticker, data_range)
        
        # Get latest data for prediction
        df = self.get_historical_data(ticker, "1 year", "daily")
        X, _ = self.prepare_bias_features(df)
        
        # Get the latest data point
        latest_features = X.iloc[-1:]
        
        # Scale features
        scaler = self.scalers[model_key]
        latest_features_scaled = scaler.transform(latest_features)
        
        # Make predictions with each model
        bias_predictions = {}
        probabilities = {}
        
        for model_name, model in self.trained_models[model_key].items():
            # Predict direction
            bias_pred = model.predict(latest_features_scaled)[0]
            
            # Get probability if available
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(latest_features_scaled)[0]
                probabilities[model_name] = proba[1] if bias_pred == 1 else proba[0]
            else:
                probabilities[model_name] = None
            
            # Store prediction
            bias_predictions[model_name] = "bullish" if bias_pred == 1 else "bearish"
        
        # Calculate ensemble prediction
        bullish_count = sum(1 for pred in bias_predictions.values() if pred == "bullish")
        bearish_count = sum(1 for pred in bias_predictions.values() if pred == "bearish")
        
        ensemble_bias = "bullish" if bullish_count > bearish_count else "bearish"
        ensemble_confidence = max(bullish_count, bearish_count) / (bullish_count + bearish_count) * 100
        
        # Add ensemble prediction
        bias_predictions["ensemble"] = ensemble_bias
        probabilities["ensemble"] = ensemble_confidence / 100
        
        return {
            'predictions': bias_predictions,
            'probabilities': probabilities
        }
    
    def run_backtest(self, ticker: str, data_range: str, interval: str, models: list, test_size: float = 0.2) -> dict:
        """Run backtest for selected models.
        
        Args:
            ticker: The ticker symbol
            data_range: The data range
            interval: The data interval
            models: List of model names to test
            test_size: Proportion of data to use for testing
            
        Returns:
            Dictionary with backtest results
        """
        # Get data
        df = self.get_historical_data(ticker, data_range, interval)
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Split data chronologically
        train_size = int((1 - test_size) * len(X))
        X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
        y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Run backtest for each model
        backtest_results = {}
        
        for target_idx, target_name in enumerate(['next_day_high', 'next_day_low']):
            target_train = y_train.iloc[:, target_idx]
            target_test = y_test.iloc[:, target_idx]
            
            model_results = {}
            
            for model_name in models:
                if model_name not in self.models['price'] or self.models['price'][model_name] is None:
                    continue
                
                # Get model
                model = self.models['price'][model_name]
                
                # Train model
                model.fit(X_train_scaled, target_train)
                
                # Make predictions
                y_pred = model.predict(X_test_scaled)
                
                # Calculate metrics
                mse = mean_squared_error(target_test, y_pred)
                mae = mean_absolute_error(target_test, y_pred)
                rmse = np.sqrt(mse)
                
                # Calculate average error as percentage
                avg_error_pct = np.mean(np.abs(y_pred - target_test) / target_test) * 100
                
                # Store results
                model_results[model_name] = {
                    'mse': mse,
                    'mae': mae,
                    'rmse': rmse,
                    'avg_error_pct': avg_error_pct,
                    'predictions': y_pred.tolist(),
                    'actual': target_test.tolist()
                }
            
            backtest_results[target_name] = model_results
        
        return backtest_results


def get_advanced_prediction_page_layout():
    """Get the layout for the advanced prediction page."""
    prediction_engine = AdvancedPredictionEngine()
    
    return html.Div([
        html.H1("Advanced Future Price Prediction", className="dashboard-title"),
        
        html.Div([
            # Ticker selection
            html.Div([
                html.Label("Select Ticker", className="form-label"),
                dcc.Dropdown(
                    id="advanced-prediction-ticker-dropdown",
                    options=[
                        {"label": ticker, "value": ticker} for ticker in [
                            "NQ=F", "ES=F", "YM=F", "RTY=F", "GC=F", 
                            "CL=F", "NG=F", "EURUSD=X", "GBPUSD=X", "DX-Y.NYB"
                        ]
                    ],
                    value="NQ=F",
                    clearable=False,
                    className="prediction-dropdown"
                )
            ], className="prediction-control"),
            
            # Data range selection
            html.Div([
                html.Label("Data Range", className="form-label"),
                dcc.Dropdown(
                    id="advanced-prediction-range-dropdown",
                    options=[
                        {"label": range_opt, "value": range_opt} for range_opt in [
                            "1 year", "2 years", "3 years", "5 years", "10 years"
                        ]
                    ],
                    value="1 year",
                    clearable=False,
                    className="prediction-dropdown"
                )
            ], className="prediction-control"),
            
            # Interval selection
            html.Div([
                html.Label("Interval", className="form-label"),
                dcc.Dropdown(
                    id="advanced-prediction-interval-dropdown",
                    options=[
                        {"label": "Daily", "value": "daily"},
                        {"label": "Weekly", "value": "weekly"}
                    ],
                    value="daily",
                    clearable=False,
                    className="prediction-dropdown"
                )
            ], className="prediction-control"),
            
            # Prediction type selection
            html.Div([
                html.Label("Prediction Type", className="form-label"),
                dcc.Dropdown(
                    id="advanced-prediction-type-dropdown",
                    options=[
                        {"label": "Price", "value": "price"},
                        {"label": "Time", "value": "time"},
                        {"label": "Price and Time", "value": "price and time"}
                    ],
                    value="price",
                    clearable=False,
                    className="prediction-dropdown"
                )
            ], className="prediction-control"),
            
            # Date picker for prediction date
            html.Div([
                html.Label("Prediction Date", className="form-label"),
                dcc.DatePickerSingle(
                    id="advanced-prediction-date-picker",
                    min_date_allowed=datetime.now().date() + timedelta(days=1),
                    max_date_allowed=datetime.now().date() + timedelta(days=30),
                    initial_visible_month=datetime.now().date() + timedelta(days=1),
                    date=datetime.now().date() + timedelta(days=1),
                    className="prediction-date-picker"
                )
            ], className="prediction-control"),
            
            # Bias option (checkbox)
            html.Div([
                html.Label("Include Bias Prediction", className="form-label"),
                dcc.Checklist(
                    id="advanced-prediction-bias-checkbox",
                    options=[
                        {"label": "Show Bullish/Bearish Bias", "value": "bias"}
                    ],
                    value=[],
                    className="prediction-checkbox"
                )
            ], className="prediction-control"),
            
            # Train model button
            html.Button(
                "Train Models", 
                id="advanced-train-models-button",
                className="prediction-button"
            ),
            
            # Predict button
            html.Button(
                "Make Prediction", 
                id="advanced-make-prediction-button",
                className="prediction-button"
            ),
        ], className="prediction-controls-container"),
        
        # Progress bar
        html.Div([
            html.Div(id="advanced-prediction-progress-text", className="progress-text"),
            dcc.Loading(
                id="advanced-prediction-loading",
                type="circle",
                children=[
                    html.Div(id="advanced-prediction-progress-container", className="progress-container", children=[
                        html.Div(id="advanced-prediction-progress-bar", className="progress-bar")
                    ])
                ]
            )
        ], className="prediction-progress"),
        
        # Status indicators
        html.Div([
            html.Div(id="advanced-data-loaded-status", className="status-indicator"),
            html.Div(id="advanced-models-trained-status", className="status-indicator"),
        ], className="prediction-status-container"),
        
        # Results section
        html.Div([
            html.H2("Prediction Results", className="section-title"),
            
            # Price prediction results
            html.Div([
                html.H3("Price Predictions", className="subsection-title"),
                html.Div(id="advanced-price-prediction-results", className="prediction-results")
            ], id="advanced-price-results-container", style={"display": "none"}),
            
            # Time prediction results
            html.Div([
                html.H3("Time Predictions", className="subsection-title"),
                html.Div(id="advanced-time-prediction-results", className="prediction-results")
            ], id="advanced-time-results-container", style={"display": "none"}),
            
            # Bias prediction results
            html.Div([
                html.H3("Direction Bias", className="subsection-title"),
                html.Div(id="advanced-bias-prediction-results", className="prediction-results")
            ], id="advanced-bias-results-container", style={"display": "none"}),
            
        ], id="advanced-prediction-results-container", className="prediction-results-container"),
        
        # Backtesting section
        html.Div([
            html.H2("Backtesting", className="section-title"),
            html.P("Test model performance on historical data", className="section-description"),
            
            html.Div([
                # Model selection for backtesting
                html.Div([
                    html.Label("Select Models", className="form-label"),
                    dcc.Dropdown(
                        id="advanced-backtest-models-dropdown",
                        options=[
                            {"label": "Linear Regression", "value": "Linear Regression"},
                            {"label": "Random Forest", "value": "Random Forest"},
                            {"label": "Gradient Boosting", "value": "Gradient Boosting"},
                            {"label": "XGBoost", "value": "XGBoost"},
                            {"label": "LightGBM", "value": "LightGBM"},
                            {"label": "CatBoost", "value": "CatBoost"},
                            {"label": "SVR", "value": "SVR"},
                            {"label": "KNN", "value": "KNN"},
                            {"label": "Decision Tree", "value": "Decision Tree"}
                        ],
                        value=["Linear Regression", "Random Forest", "XGBoost"],
                        multi=True,
                        className="backtest-dropdown"
                    )
                ], className="backtest-control"),
                
                # Run backtest button
                html.Button(
                    "Run Backtest", 
                    id="advanced-run-backtest-button",
                    className="backtest-button"
                ),
            ], className="backtest-controls-container"),
            
            # Backtest results
            html.Div(id="advanced-backtest-results-container", className="backtest-results-container")
            
        ], className="backtesting-container"),
        
        # Hidden div for storing prediction engine state
        dcc.Store(id="advanced-prediction-engine-store"),
    ], className="prediction-page-container")


def register_advanced_prediction_callbacks(app):
    """Register callbacks for the advanced prediction page."""
    prediction_engine = AdvancedPredictionEngine()
    
    # Callback to update interval options based on prediction type
    @app.callback(
        [Output("advanced-prediction-interval-dropdown", "options"),
         Output("advanced-prediction-interval-dropdown", "value"),
         Output("advanced-prediction-range-dropdown", "options"),
         Output("advanced-prediction-range-dropdown", "value")],
        [Input("advanced-prediction-type-dropdown", "value"),
         Input("advanced-prediction-bias-checkbox", "value")]
    )
    def update_interval_options(prediction_type, bias_options):
        # Default options
        interval_options = [
            {"label": "Daily", "value": "daily"},
            {"label": "Weekly", "value": "weekly"}
        ]
        interval_value = "daily"
        
        range_options = [
            {"label": range_opt, "value": range_opt} for range_opt in [
                "1 year", "2 years", "3 years", "5 years", "10 years"
            ]
        ]
        range_value = "1 year"
        
        # If time prediction or bias is selected, limit options
        if prediction_type in ["time", "price and time"] or "bias" in bias_options:
            interval_options = [{"label": "Daily", "value": "daily"}]
            interval_value = "daily"
            
            range_options = [
                {"label": range_opt, "value": range_opt} for range_opt in [
                    "1 year", "2 years"
                ]
            ]
            range_value = "1 year"
        
        return interval_options, interval_value, range_options, range_value
    
    # Callback to train models
    @app.callback(
        [Output("advanced-prediction-progress-text", "children"),
         Output("advanced-prediction-progress-bar", "style"),
         Output("advanced-models-trained-status", "children"),
         Output("advanced-prediction-engine-store", "data")],
        [Input("advanced-train-models-button", "n_clicks")],
        [State("advanced-prediction-ticker-dropdown", "value"),
         State("advanced-prediction-range-dropdown", "value"),
         State("advanced-prediction-interval-dropdown", "value"),
         State("advanced-prediction-type-dropdown", "value"),
         State("advanced-prediction-bias-checkbox", "value"),
         State("advanced-prediction-engine-store", "data")]
    )
    def train_models(n_clicks, ticker, data_range, interval, prediction_type, bias_options, stored_data):
        if not n_clicks:
            return "", {"width": "0%"}, "", None
        
        # Initialize progress
        progress_text = "Training models..."
        progress_style = {"width": "0%"}
        
        # Determine which models to train
        models_to_train = [prediction_type]
        if "bias" in bias_options:
            models_to_train.append("bias")
        
        # Train models
        results = {}
        for i, model_type in enumerate(models_to_train):
            # Update progress
            progress_pct = (i / len(models_to_train)) * 50  # First half of progress bar
            progress_style = {"width": f"{progress_pct}%"}
            
            # Train model based on type
            if model_type == "price" or model_type == "price and time":
                model_results = prediction_engine.train_models(ticker, data_range, interval, "price")
                results["price"] = model_results
            elif model_type == "time":
                model_results = prediction_engine.train_models(ticker, data_range, interval, "time")
                results["time"] = model_results
            elif model_type == "bias":
                model_results = prediction_engine.train_bias_models(ticker, data_range)
                results["bias"] = model_results
            
            # Update progress to show completion of this model type
            progress_pct = ((i + 1) / len(models_to_train)) * 100
            progress_style = {"width": f"{progress_pct}%"}
        
        # Update progress to complete
        progress_style = {"width": "100%"}
        
        # Create status indicator
        status = html.Div([
            html.I(className="fas fa-check-circle"),
            html.Span(f"Models trained for {ticker} ({interval})"),
        ], className="status-success")
        
        # Store trained models info
        store_data = {
            "ticker": ticker,
            "data_range": data_range,
            "interval": interval,
            "prediction_type": prediction_type,
            "bias": "bias" in bias_options,
            "trained": True
        }
        
        return progress_text, progress_style, status, store_data
    
    # Callback to make predictions
    @app.callback(
        [Output("advanced-price-results-container", "style"),
         Output("advanced-price-prediction-results", "children"),
         Output("advanced-time-results-container", "style"),
         Output("advanced-time-prediction-results", "children"),
         Output("advanced-bias-results-container", "style"),
         Output("advanced-bias-prediction-results", "children")],
        [Input("advanced-make-prediction-button", "n_clicks")],
        [State("advanced-prediction-ticker-dropdown", "value"),
         State("advanced-prediction-range-dropdown", "value"),
         State("advanced-prediction-interval-dropdown", "value"),
         State("advanced-prediction-type-dropdown", "value"),
         State("advanced-prediction-bias-checkbox", "value"),
         State("advanced-prediction-date-picker", "date"),
         State("advanced-prediction-engine-store", "data")]
    )
    def make_prediction(n_clicks, ticker, data_range, interval, prediction_type, bias_options, prediction_date, stored_data):
        if not n_clicks or not stored_data or not stored_data.get("trained"):
            return {"display": "none"}, [], {"display": "none"}, [], {"display": "none"}, []
        
        # Initialize results containers
        price_style = {"display": "none"}
        price_results = []
        time_style = {"display": "none"}
        time_results = []
        bias_style = {"display": "none"}
        bias_results = []
        
        # Make price predictions
        if prediction_type in ["price", "price and time"]:
            price_style = {"display": "block"}
            predictions = prediction_engine.predict(ticker, data_range, interval, prediction_date, "price")
            
            if "price" in predictions:
                price_data = predictions["price"]
                
                # Create results table
                price_results = [
                    html.Div([
                        html.H4(f"Predicted for {prediction_date}"),
                        html.Table([
                            html.Thead(
                                html.Tr([
                                    html.Th("Model"),
                                    html.Th("Predicted High"),
                                    html.Th("Predicted Low")
                                ])
                            ),
                            html.Tbody([
                                html.Tr([
                                    html.Td("Ensemble (Average)"),
                                    html.Td(f"${price_data['next_day_high']['ensemble']:.2f}"),
                                    html.Td(f"${price_data['next_day_low']['ensemble']:.2f}")
                                ]),
                                *[
                                    html.Tr([
                                        html.Td(model_name),
                                        html.Td(f"${price_data['next_day_high'][model_name]:.2f}"),
                                        html.Td(f"${price_data['next_day_low'][model_name]:.2f}")
                                    ])
                                    for model_name in price_data['next_day_high'].keys()
                                    if model_name != "ensemble"
                                ]
                            ])
                        ], className="prediction-table")
                    ])
                ]
        
        # Make time predictions
        if prediction_type in ["time", "price and time"]:
            time_style = {"display": "block"}
            predictions = prediction_engine.predict(ticker, data_range, interval, prediction_date, "time")
            
            if "time" in predictions:
                time_data = predictions["time"]
                
                # Create results table
                time_results = [
                    html.Div([
                        html.H4(f"Predicted Times for {prediction_date} (New York Time)"),
                        html.Table([
                            html.Thead(
                                html.Tr([
                                    html.Th("Model"),
                                    html.Th("High Time"),
                                    html.Th("Low Time")
                                ])
                            ),
                            html.Tbody([
                                html.Tr([
                                    html.Td("Ensemble (Average)"),
                                    html.Td(f"{int(time_data['high_hour']['ensemble']):02d}:00"),
                                    html.Td(f"{int(time_data['low_hour']['ensemble']):02d}:00")
                                ]),
                                *[
                                    html.Tr([
                                        html.Td(model_name),
                                        html.Td(f"{int(time_data['high_hour'][model_name]):02d}:00"),
                                        html.Td(f"{int(time_data['low_hour'][model_name]):02d}:00")
                                    ])
                                    for model_name in time_data['high_hour'].keys()
                                    if model_name != "ensemble"
                                ]
                            ])
                        ], className="prediction-table")
                    ])
                ]
        
        # Make bias predictions
        if "bias" in bias_options:
            bias_style = {"display": "block"}
            bias_predictions = prediction_engine.predict_bias(ticker, data_range, prediction_date)
            
            # Create results table
            bias_results = [
                html.Div([
                    html.H4(f"Direction Bias for {prediction_date}"),
                    html.Div([
                        html.Span(
                            f"Ensemble Prediction: ",
                            className="bias-label"
                        ),
                        html.Span(
                            f"{bias_predictions['predictions']['ensemble'].upper()} ",
                            className=f"direction-{bias_predictions['predictions']['ensemble']}"
                        ),
                        html.Span(
                            f"({bias_predictions['probabilities']['ensemble']*100:.1f}% confidence)",
                            className="bias-confidence"
                        )
                    ], className="direction-ensemble"),
                    html.Table([
                        html.Thead(
                            html.Tr([
                                html.Th("Model"),
                                html.Th("Prediction"),
                                html.Th("Confidence")
                            ])
                        ),
                        html.Tbody([
                            *[
                                html.Tr([
                                    html.Td(model_name),
                                    html.Td(
                                        bias_predictions['predictions'][model_name].upper(),
                                        className=f"direction-{bias_predictions['predictions'][model_name]}"
                                    ),
                                    html.Td(
                                        f"{bias_predictions['probabilities'][model_name]*100:.1f}%" if bias_predictions['probabilities'][model_name] is not None else "N/A"
                                    )
                                ])
                                for model_name in bias_predictions['predictions'].keys()
                                if model_name != "ensemble"
                            ]
                        ])
                    ], className="prediction-table")
                ])
            ]
        
        return price_style, price_results, time_style, time_results, bias_style, bias_results
    
    # Callback to run backtest
    @app.callback(
        Output("advanced-backtest-results-container", "children"),
        [Input("advanced-run-backtest-button", "n_clicks")],
        [State("advanced-prediction-ticker-dropdown", "value"),
         State("advanced-prediction-range-dropdown", "value"),
         State("advanced-prediction-interval-dropdown", "value"),
         State("advanced-backtest-models-dropdown", "value")]
    )
    def run_backtest(n_clicks, ticker, data_range, interval, models):
        if not n_clicks or not models:
            return []
        
        # Run backtest
        backtest_results = prediction_engine.run_backtest(ticker, data_range, interval, models)
        
        # Create results display
        results_components = []
        
        # Add summary section
        results_components.append(html.H3(f"Backtest Results for {ticker}"))
        results_components.append(html.P(f"Data Range: {data_range}, Interval: {interval}"))
        
        # Create tabs for high and low predictions
        for target_name, target_results in backtest_results.items():
            display_name = "Daily High" if target_name == "next_day_high" else "Daily Low"
            
            # Create table with model performance metrics
            metrics_table = html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Model"),
                        html.Th("RMSE"),
                        html.Th("MAE"),
                        html.Th("Avg Error %")
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(model_name),
                        html.Td(f"{metrics['rmse']:.2f}"),
                        html.Td(f"{metrics['mae']:.2f}"),
                        html.Td(f"{metrics['avg_error_pct']:.2f}%")
                    ])
                    for model_name, metrics in target_results.items()
                ])
            ], className="backtest-table")
            
            # Create visualization of predictions vs actual
            graphs = []
            for model_name, metrics in target_results.items():
                # Create figure
                fig = go.Figure()
                
                # Add actual values
                fig.add_trace(go.Scatter(
                    y=metrics['actual'],
                    mode='lines',
                    name='Actual',
                    line=dict(color='blue', width=2)
                ))
                
                # Add predicted values
                fig.add_trace(go.Scatter(
                    y=metrics['predictions'],
                    mode='lines',
                    name='Predicted',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                # Update layout
                fig.update_layout(
                    title=f"{model_name} - {display_name} Predictions",
                    xaxis_title="Test Data Points",
                    yaxis_title="Price",
                    template="plotly_white",
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                
                graphs.append(html.Div([
                    html.H4(f"{model_name} Performance"),
                    dcc.Graph(figure=fig)
                ], className="backtest-graph"))
            
            # Add section for this target
            results_components.append(html.Div([
                html.H4(f"{display_name} Prediction Performance"),
                metrics_table,
                html.Div(graphs, className="backtest-graphs-container")
            ], className="backtest-target-section"))
        
        return results_components": f"{progress_pct}%