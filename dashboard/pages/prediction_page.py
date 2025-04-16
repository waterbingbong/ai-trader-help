# Prediction Page for AI Trading Assistant
# This module implements the prediction page for the dashboard

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

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import project modules
from dashboard.components.prediction import PredictionEngine


def get_prediction_page_layout():
    """Get the layout for the prediction page."""
    prediction_engine = PredictionEngine()
    
    return html.Div([
        html.H1("Future Price Prediction", className="dashboard-title"),
        
        html.Div([
            # Ticker selection
            html.Div([
                html.Label("Select Ticker", className="form-label"),
                dcc.Dropdown(
                    id="prediction-ticker-dropdown",
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
                    id="prediction-range-dropdown",
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
                    id="prediction-interval-dropdown",
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
                    id="prediction-type-dropdown",
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
                    id="prediction-date-picker",
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
                    id="prediction-bias-checkbox",
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
                id="train-models-button",
                className="prediction-button"
            ),
            
            # Predict button
            html.Button(
                "Make Prediction", 
                id="make-prediction-button",
                className="prediction-button"
            ),
        ], className="prediction-controls-container"),
        
        # Progress bar
        html.Div([
            html.Div(id="prediction-progress-text", className="progress-text"),
            dcc.Loading(
                id="prediction-loading",
                type="circle",
                children=[
                    html.Div(id="prediction-progress-container", className="progress-container", children=[
                        html.Div(id="prediction-progress-bar", className="progress-bar")
                    ])
                ]
            )
        ], className="prediction-progress"),
        
        # Status indicators
        html.Div([
            html.Div(id="data-loaded-status", className="status-indicator"),
            html.Div(id="models-trained-status", className="status-indicator"),
        ], className="prediction-status-container"),
        
        # Results section
        html.Div([
            html.H2("Prediction Results", className="section-title"),
            
            # Price prediction results
            html.Div([
                html.H3("Price Predictions", className="subsection-title"),
                html.Div(id="price-prediction-results", className="prediction-results")
            ], id="price-results-container", style={"display": "none"}),
            
            # Time prediction results
            html.Div([
                html.H3("Time Predictions", className="subsection-title"),
                html.Div(id="time-prediction-results", className="prediction-results")
            ], id="time-results-container", style={"display": "none"}),
            
            # Bias prediction results
            html.Div([
                html.H3("Direction Bias", className="subsection-title"),
                html.Div(id="bias-prediction-results", className="prediction-results")
            ], id="bias-results-container", style={"display": "none"}),
            
        ], id="prediction-results-container", className="prediction-results-container"),
        
        # Backtesting section
        html.Div([
            html.H2("Backtesting", className="section-title"),
            html.P("Test model performance on historical data", className="section-description"),
            
            html.Div([
                # Model selection for backtesting
                html.Div([
                    html.Label("Select Models", className="form-label"),
                    dcc.Dropdown(
                        id="backtest-models-dropdown",
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
                    id="run-backtest-button",
                    className="backtest-button"
                ),
            ], className="backtest-controls-container"),
            
            # Backtest results
            html.Div(id="backtest-results-container", className="backtest-results-container")
            
        ], className="backtesting-container"),
        
        # Hidden div for storing prediction engine state
        dcc.Store(id="prediction-engine-store"),
    ], className="prediction-page-container")


def register_prediction_callbacks(app):
    """Register callbacks for the prediction page."""
    prediction_engine = PredictionEngine()
    
    # Callback to update interval options based on prediction type
    @app.callback(
        [Output("prediction-interval-dropdown", "options"),
         Output("prediction-interval-dropdown", "value"),
         Output("prediction-range-dropdown", "options"),
         Output("prediction-range-dropdown", "value")],
        [Input("prediction-type-dropdown", "value"),
         Input("prediction-bias-checkbox", "value")]
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
        [Output("prediction-progress-text", "children"),
         Output("prediction-progress-bar", "style"),
         Output("models-trained-status", "children"),
         Output("prediction-engine-store", "data")],
        [Input("train-models-button", "n_clicks")],
        [State("prediction-ticker-dropdown", "value"),
         State("prediction-range-dropdown", "value"),
         State("prediction-interval-dropdown", "value"),
         State("prediction-type-dropdown", "value"),
         State("prediction-bias-checkbox", "value"),
         State("prediction-engine-store", "data")]
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
            progress_pct = (i / len(models_to_train)) * 100
            progress_style = {"width": f"{progress_pct}%"}
            
            # Train model
            model_results = prediction_engine.train_models(ticker, data_range, interval, model_type)
            results[model_type] = model_results
        
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
        [Output("price-results-container", "style"),
         Output("price-prediction-results", "children"),
         Output("time-results-container", "style"),
         Output("time-prediction-results", "children"),
         Output("bias-results-container", "style"),
         Output("bias-prediction-results", "children")],
        [Input("make-prediction-button", "n_clicks")],
        [State("prediction-ticker-dropdown", "value"),
         State("prediction-range-dropdown", "value"),
         State("prediction-interval-dropdown", "value"),
         State("prediction-type-dropdown", "value"),
         State("prediction-bias-checkbox", "value"),
         State("prediction-date-picker", "date"),
         State("prediction-engine-store", "data")]
    )
    def make_prediction(n_clicks, ticker, data_range, interval, prediction_type, bias_options, prediction_date, stored_data):
        if not n_clicks or not stored_data or not stored_data.get("trained"):
            return {"display": "none"}, [], {"display": "none"}, [], {"display": "none"}, []
        
        # Make predictions
        predictions = prediction_engine.predict(
            ticker, data_range, interval, prediction_date, prediction_type
        )
        
        # Initialize results containers
        price_style = {"display": "none"}
        price_results = []
        time_style = {"display": "none"}
        time_results = []
        bias_style = {"display": "none"}
        bias_results = []
        
        # Process price predictions
        if prediction_type in ["price", "price and time"] and "price" in predictions:
            price_style = {"display": "block"}
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
        
        # Process time predictions
        if prediction_type in ["time", "price and time"] and "time" in predictions:
            time_style = {"display": "block"}
            time_data = predictions["time"]
            
            # Convert hour predictions to formatted time
            def format_hour(hour):
                return f"{hour:02d}:00 ET"
            
            # Create results table
            time_results = [
                html.Div([
                    html.H4(f"Predicted for {prediction_date}"),
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
                                html.Td(format_hour(time_data['high_hour']['ensemble'])),
                                html.Td(format_hour(time_data['low_hour']['ensemble']))
                            ]),
                            *[
                                html.Tr([
                                    html.Td(model_name),
                                    html.Td(format_hour(time_data['high_hour'][model_name])),
                                    html.Td(format_hour(time_data['low_hour'][model_name]))
                                ])
                                for model_name in time_data['high_hour'].keys()
                                if model_name != "ensemble"
                            ]
                        ])
                    ], className="prediction-table")
                ])
            ]
        
        # Process bias predictions
        if "bias" in bias_options and "direction" in predictions:
            bias_style = {"display": "block"}
            direction_data = predictions["direction"]
            
            # Create results table
            bias_results = [
                html.Div([
                    html.H4(f"Direction Bias for {prediction_date}"),
                    html.Div([
                        html.Span("Ensemble Prediction: "),
                        html.Span(
                            direction_data['ensemble'],
                            className=f"direction-{direction_data['ensemble'].lower()}"
                        ),
                        html.Span(f" ({direction_data['ensemble_probability']*100:.1f}% confidence)")
                    ], className="direction-ensemble"),
                    html.Table([
                        html.Thead(
                            html.Tr([
                                html.Th("Model"),
                                html.Th("Predicted Direction"),
                                html.Th("Confidence")
                            ])
                        ),
                        html.Tbody([
                            *[
                                html.Tr([
                                    html.Td(model_name),
                                    html.Td(
                                        direction_data['predictions'][model_name],
                                        className=f"direction-{direction_data['predictions'][model_name].lower()}"
                                    ),
                                    html.Td(f"{direction_data['probabilities'][model_name]*100:.1f}%")
                                ])
                                for model_name in direction_data['predictions'].keys()
                            ]
                        ])
                    ], className="prediction-table")
                ])
            ]
        
        return price_style, price_results, time_style, time_results, bias_style, bias_results
    
    # Callback to run backtest
    @app.callback(
        Output("backtest-results-container", "children"),
        [Input("run-backtest-button", "n_clicks")],
        [State("prediction-ticker-dropdown", "value"),
         State("prediction-range-dropdown", "value"),
         State("prediction-interval-dropdown", "value"),
         State("backtest-models-dropdown", "value")]
    )
    def run_backtest(n_clicks, ticker, data_range, interval, models):
        if not n_clicks or not models:
            return []
        
        # Run backtest
        backtest_results = prediction_engine.run_backtest(ticker, data_range, interval, models)
        
        # Create results visualization
        results_components = [
            html.H3(f"Backtest Results for {ticker}"),
            html.P("Testing on the last 20% of data", className="backtest-description")
        ]
        
        # Add accuracy metrics table
        if "metrics" in backtest_results:
            metrics_table = html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Model"),
                        html.Th("RMSE (High)"),
                        html.Th("RMSE (Low)"),
                        html.Th("MAE (High)"),
                        html.Th("MAE (Low)"),
                        html.Th("Avg Error %")
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(model),
                        html.Td(f"{backtest_results['metrics'][model]['high_rmse']:.2f}"),
                        html.Td(f"{backtest_results['metrics'][model]['low_rmse']:.2f}"),
                        html.Td(f"{backtest_results['metrics'][model]['high_mae']:.2f}"),
                        html.Td(f"{backtest_results['metrics'][model]['low_mae']:.2f}"),
                        html.Td(f"{backtest_results['metrics'][model]['avg_error_pct']:.2f}%")
                    ])
                    for model in backtest_results['metrics']
                ])
            ], className="backtest-table")
            
            results_components.append(metrics_table)
        
        # Add error visualization if available
        if "error_chart" in backtest_results:
            results_components.append(
                dcc.Graph(figure=backtest_results["error_chart"])
            )
        
        return results_components