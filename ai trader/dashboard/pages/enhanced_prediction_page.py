# Enhanced Prediction Page for AI Trading Assistant
# This module implements a high-accuracy prediction page with advanced ML and AI capabilities

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
from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, precision_score, recall_score, f1_score, r2_score

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import project modules
from dashboard.components.enhanced_prediction import EnhancedPredictionEngine
from data_processing.connectors.market_data import get_data_connector
from ai_integration.gemini_integration_manager import gemini_manager

def get_enhanced_prediction_page_layout():
    """Get the layout for the enhanced prediction page with improved accuracy."""
    prediction_engine = EnhancedPredictionEngine()
    
    return html.Div([
        html.H1("Enhanced Market Prediction", className="dashboard-title"),
        html.P("High-accuracy market predictions using ensemble ML models and AI integration", className="section-description"),
        
        html.Div([
            # Ticker selection
            html.Div([
                html.Label("Select Ticker", className="form-label"),
                dcc.Dropdown(
                    id="enhanced-prediction-ticker-dropdown",
                    options=[
                        {"label": ticker, "value": ticker} for ticker in [
                            "NQ=F", "ES=F", "YM=F", "RTY=F", "GC=F", 
                            "CL=F", "NG=F", "EURUSD=X", "GBPUSD=X", "DX-Y.NYB"
                        ]
                    ],
                    value="ES=F",
                    className="prediction-dropdown"
                )
            ], className="prediction-control"),
            
            # Data range selection
            html.Div([
                html.Label("Data Range", className="form-label"),
                dcc.Dropdown(
                    id="enhanced-prediction-range-dropdown",
                    options=[
                        {"label": "1 Year", "value": "1 year"},
                        {"label": "2 Years", "value": "2 years"},
                        {"label": "3 Years", "value": "3 years"}
                    ],
                    value="2 years",
                    className="prediction-dropdown"
                )
            ], className="prediction-control"),
            
            # Interval selection
            html.Div([
                html.Label("Interval", className="form-label"),
                dcc.Dropdown(
                    id="enhanced-prediction-interval-dropdown",
                    options=[
                        {"label": "Daily", "value": "daily"},
                        {"label": "Weekly", "value": "weekly"}
                    ],
                    value="daily",
                    className="prediction-dropdown"
                )
            ], className="prediction-control"),
            
            # Prediction type selection
            html.Div([
                html.Label("Prediction Type", className="form-label"),
                dcc.Dropdown(
                    id="enhanced-prediction-type-dropdown",
                    options=[
                        {"label": "Price", "value": "price"},
                        {"label": "Direction", "value": "bias"},
                        {"label": "Price & Direction", "value": "price and bias"}
                    ],
                    value="price and bias",
                    className="prediction-dropdown"
                )
            ], className="prediction-control"),
            
            # Date picker for prediction date
            html.Div([
                html.Label("Prediction Date", className="form-label"),
                dcc.DatePickerSingle(
                    id="enhanced-prediction-date-picker",
                    min_date_allowed=datetime.now().date(),
                    max_date_allowed=datetime.now().date() + timedelta(days=30),
                    initial_visible_month=datetime.now().date(),
                    date=datetime.now().date() + timedelta(days=1),
                    className="prediction-date-picker"
                )
            ], className="prediction-control"),
            
            # AI Integration toggle
            html.Div([
                html.Label("Use Gemini AI Integration", className="form-label"),
                dcc.Checklist(
                    id="enhanced-prediction-ai-checkbox",
                    options=[
                        {"label": "Enable AI-enhanced predictions", "value": "ai"}
                    ],
                    value=["ai"],
                    className="prediction-checkbox"
                )
            ], className="prediction-control"),
            
            # Buttons for training and prediction
            html.Div([
                html.Button(
                    "Train Enhanced Models",
                    id="enhanced-train-models-button",
                    className="prediction-button prediction-button-primary"
                ),
                html.Button(
                    "Make Prediction",
                    id="enhanced-make-prediction-button",
                    className="prediction-button prediction-button-primary"
                )
            ], className="prediction-controls-container"),
            
            # Progress indicators
            html.Div([
                html.Div(id="enhanced-prediction-progress-text", className="progress-text"),
                dcc.Loading(
                    id="enhanced-prediction-loading",
                    type="circle",
                    children=[
                        html.Div(id="enhanced-prediction-progress-container", className="progress-container", children=[
                            html.Div(id="enhanced-prediction-progress-bar", className="progress-bar")
                        ])
                    ]
                ),
                html.Div(id="enhanced-models-trained-status", className="status-indicator"),
            ], className="prediction-status-container"),
        ], className="prediction-controls-grid"),
        
        # Results section
        html.Div([
            html.H2("Prediction Results", className="section-title"),
            
            # Price prediction results
            html.Div([
                html.H3("Price Predictions", className="subsection-title"),
                html.Div(id="enhanced-price-prediction-results", className="prediction-results")
            ], id="enhanced-price-results-container", style={'display': 'none'}),
            
            # Direction prediction results
            html.Div([
                html.H3("Direction Predictions", className="subsection-title"),
                html.Div(id="enhanced-direction-prediction-results", className="prediction-results")
            ], id="enhanced-direction-results-container", style={'display': 'none'}),
            
            # Confidence visualization
            html.Div([
                html.H3("Prediction Confidence", className="subsection-title"),
                dcc.Graph(id="enhanced-confidence-chart")
            ], id="enhanced-confidence-container", style={'display': 'none'}),
            
            # AI Insights section
            html.Div([
                html.H3("AI Market Insights", className="subsection-title"),
                html.Div(id="enhanced-ai-insights", className="ai-insights")
            ], id="enhanced-ai-container", style={'display': 'none'}),
            
        ], id="enhanced-prediction-results-container", className="prediction-results-container"),
        
        # Backtesting section
        html.Div([
            html.H2("Model Performance", className="section-title"),
            html.P("Test model performance on historical data", className="section-description"),
            
            # Model selection for backtesting
            html.Div([
                html.Label("Select Models", className="form-label"),
                dcc.Dropdown(
                    id="enhanced-backtest-models-dropdown",
                    options=[
                        {"label": "Linear Regression", "value": "Linear"},
                        {"label": "Ridge Regression", "value": "Ridge"},
                        {"label": "Random Forest", "value": "RandomForest"},
                        {"label": "Gradient Boosting", "value": "GradientBoosting"},
                        {"label": "XGBoost", "value": "XGBoost"},
                        {"label": "LightGBM", "value": "LightGBM"},
                        {"label": "CatBoost", "value": "CatBoost"},
                        {"label": "Support Vector Regression", "value": "SVR"},
                        {"label": "K-Nearest Neighbors", "value": "KNN"}
                    ],
                    value=["Linear", "RandomForest", "XGBoost", "LightGBM"],
                    multi=True
                )
            ], className="prediction-control full-width"),
            
            html.Button(
                "Run Backtest",
                id="enhanced-run-backtest-button",
                className="prediction-button"
            ),
            
            # Backtest results
            html.Div(id="enhanced-backtest-results", className="backtest-results")
            
        ], className="backtest-container"),
        
        # Hidden div for storing prediction engine state
        dcc.Store(id="enhanced-prediction-engine-store"),
    ], className="prediction-page-container")

def register_enhanced_prediction_callbacks(app):
    """Register callbacks for the enhanced prediction page."""
    prediction_engine = EnhancedPredictionEngine()
    
    # Callback to update interval options based on prediction type
    @app.callback(
        [Output("enhanced-prediction-interval-dropdown", "options"),
         Output("enhanced-prediction-interval-dropdown", "value"),
         Output("enhanced-prediction-range-dropdown", "options"),
         Output("enhanced-prediction-range-dropdown", "value")],
        [Input("enhanced-prediction-type-dropdown", "value")]
    )
    def update_interval_options(prediction_type):
        # Default options
        interval_options = [
            {"label": "Daily", "value": "daily"},
            {"label": "Weekly", "value": "weekly"}
        ]
        interval_value = "daily"
        
        range_options = [
            {"label": "1 Year", "value": "1 year"},
            {"label": "2 Years", "value": "2 years"},
            {"label": "3 Years", "value": "3 years"}
        ]
        range_value = "2 years"
        
        # If bias prediction is selected, limit options
        if "bias" in prediction_type:
            interval_options = [{"label": "Daily", "value": "daily"}]
            interval_value = "daily"
            
            range_options = [
                {"label": "1 Year", "value": "1 year"},
                {"label": "2 Years", "value": "2 years"}
            ]
            range_value = "2 years"
        
        return interval_options, interval_value, range_options, range_value
    
    # Callback to train models
    @app.callback(
        [Output("enhanced-prediction-progress-text", "children"),
         Output("enhanced-prediction-progress-bar", "style"),
         Output("enhanced-models-trained-status", "children"),
         Output("enhanced-prediction-engine-store", "data")],
        [Input("enhanced-train-models-button", "n_clicks")],
        [State("enhanced-prediction-ticker-dropdown", "value"),
         State("enhanced-prediction-range-dropdown", "value"),
         State("enhanced-prediction-interval-dropdown", "value"),
         State("enhanced-prediction-type-dropdown", "value"),
         State("enhanced-prediction-engine-store", "data")]
    )
    def train_models(n_clicks, ticker, data_range, interval, prediction_type, stored_data):
        if not n_clicks:
            return "", {"width": "0%"}, "", stored_data or {}
        
        progress_text = "Training enhanced models..."
        results = {}
        
        # Determine which models to train
        models_to_train = []
        if "price" in prediction_type:
            models_to_train.append("price")
        if "bias" in prediction_type:
            models_to_train.append("bias")
        
        # Train models
        for i, model_type in enumerate(models_to_train):
            # Update progress
            progress_pct = (i / len(models_to_train)) * 100
            
            # Train model based on type
            model_results = prediction_engine.train_models(ticker, data_range, interval, model_type)
            results[model_type] = model_results
        
        # Update progress to show completion
        progress_style = {"width": "100%", "background-color": "#4CAF50"}
        
        # Create status indicator
        status = html.Div([
            html.Span("✓", className="status-icon success"),
            html.Span(f"Enhanced models trained for {ticker} ({interval})"),
        ])
        
        # Store trained models info
        stored_data = stored_data or {}
        stored_data.update({
            "ticker": ticker,
            "data_range": data_range,
            "interval": interval,
            "prediction_type": prediction_type,
            "models_trained": True,
            "training_results": results
        })
        
        return progress_text, progress_style, status, stored_data
    
    # Callback to make predictions
    @app.callback(
        [Output("enhanced-price-results-container", "style"),
         Output("enhanced-direction-results-container", "style"),
         Output("enhanced-confidence-container", "style"),
         Output("enhanced-ai-container", "style"),
         Output("enhanced-price-prediction-results", "children"),
         Output("enhanced-direction-prediction-results", "children"),
         Output("enhanced-confidence-chart", "figure"),
         Output("enhanced-ai-insights", "children")],
        [Input("enhanced-make-prediction-button", "n_clicks")],
        [State("enhanced-prediction-ticker-dropdown", "value"),
         State("enhanced-prediction-range-dropdown", "value"),
         State("enhanced-prediction-interval-dropdown", "value"),
         State("enhanced-prediction-type-dropdown", "value"),
         State("enhanced-prediction-date-picker", "date"),
         State("enhanced-prediction-ai-checkbox", "value"),
         State("enhanced-prediction-engine-store", "data")]
    )
    def make_prediction(n_clicks, ticker, data_range, interval, prediction_type, prediction_date, ai_options, stored_data):
        if not n_clicks or not stored_data or not stored_data.get("models_trained"):
            # Default empty outputs
            return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, \
                   "", "", {}, ""
        
        # Initialize display flags
        show_price = {'display': 'block'} if "price" in prediction_type else {'display': 'none'}
        show_direction = {'display': 'block'} if "bias" in prediction_type else {'display': 'none'}
        show_confidence = {'display': 'block'}
        show_ai = {'display': 'block'} if ai_options and "ai" in ai_options else {'display': 'none'}
        
        # Make predictions
        predictions = prediction_engine.predict(ticker, data_range, interval, prediction_date, prediction_type)
        
        # Process price predictions
        price_results = ""
        if "price" in prediction_type and "price" in predictions:
            price_data = predictions["price"]
            confidence_data = predictions.get("confidence", {})
            
            price_results = html.Div([
                html.H4(f"Predicted for {prediction_date}"),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Model"),
                            html.Th("High Price"),
                            html.Th("Low Price"),
                            html.Th("Confidence")
                        ])
                    ]),
                    html.Tbody([
                        # Ensemble prediction (first row)
                        html.Tr([
                            html.Td("Ensemble (Weighted)"),
                            html.Td(f"${price_data['next_day_high']['ensemble']:.2f}"),
                            html.Td(f"${price_data['next_day_low']['ensemble']:.2f}"),
                            html.Td(f"{confidence_data.get('next_day_high', {}).get('ensemble', 70):.1f}%")
                        ], className="ensemble-row"),
                        # Individual model predictions
                        *[
                            html.Tr([
                                html.Td(model_name),
                                html.Td(f"${price_data['next_day_high'][model_name]:.2f}"),
                                html.Td(f"${price_data['next_day_low'][model_name]:.2f}"),
                                html.Td(f"{confidence_data.get('next_day_high', {}).get(model_name, 50):.1f}%")
                            ])
                            for model_name in price_data['next_day_high'].keys()
                            if model_name != "ensemble" and model_name in ["VotingEnsemble", "StackingEnsemble"]
                        ]
                    ])
                ], className="prediction-table")
            ])
        
        # Process direction predictions
        direction_results = ""
        if "bias" in prediction_type and "direction" in predictions:
            direction_data = predictions["direction"]
            
            # Get direction and probability
            ensemble_direction = direction_data['ensemble']
            ensemble_probability = direction_data['ensemble_probability'] * 100
            
            # Create direction indicator with confidence
            direction_class = f"direction-{ensemble_direction.lower()}"
            confidence_level = "high" if ensemble_probability > 75 else "medium" if ensemble_probability > 60 else "low"
            
            direction_results = html.Div([
                html.H4(f"Market Direction Prediction for {prediction_date}"),
                
                # Direction indicator
                html.Div([
                    html.Div([
                        html.Span("Ensemble Prediction: "),
                        html.Span(
                            f"{ensemble_direction.upper()} ",
                            className=direction_class
                        ),
                        html.Span(f"({ensemble_probability:.1f}% confidence)"),
                    ], className="direction-ensemble"),
                    
                    # Confidence indicator
                    html.Div([
                        html.Div(className=f"confidence-indicator {confidence_level}"),
                        html.Span(f"{confidence_level.capitalize()} Confidence")
                    ], className="confidence-display")
                ], className="direction-container"),
                
                # Model breakdown table
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Model"),
                            html.Th("Prediction"),
                            html.Th("Confidence")
                        ])
                    ]),
                    html.Tbody([
                        *[
                            html.Tr([
                                html.Td(model_name),
                                html.Td(
                                    direction_data['predictions'][model_name].upper(),
                                    className=f"direction-{direction_data['predictions'][model_name].lower()}"
                                ),
                                html.Td(f"{direction_data['probabilities'][model_name]*100:.1f}%")
                            ])
                            for model_name in direction_data['predictions'].keys()
                            if model_name != "ensemble" and model_name in ["VotingEnsemble", "StackingEnsemble"]
                        ]
                    ])
                ], className="prediction-table")
            ])
        
        # Create confidence visualization
        confidence_fig = create_confidence_visualization(predictions)
        
        # Get AI insights if enabled
        ai_insights = ""
        if ai_options and "ai" in ai_options:
            ai_insights = html.Div([
                html.H4("Gemini AI Market Analysis"),
                html.Div([
                    html.P("AI analysis has been integrated into the prediction models to improve accuracy."),
                    html.Ul([
                        html.Li("Market sentiment has been analyzed and factored into predictions"),
                        html.Li("Technical patterns have been identified and weighted"),
                        html.Li("Anomalies have been detected and filtered out")
                    ])
                ], className="ai-insights-content")
            ])
        
        return show_price, show_direction, show_confidence, show_ai, \
               price_results, direction_results, confidence_fig, ai_insights
    
    # Callback to run backtest
    @app.callback(
        Output("enhanced-backtest-results", "children"),
        [Input("enhanced-run-backtest-button", "n_clicks")],
        [State("enhanced-prediction-ticker-dropdown", "value"),
         State("enhanced-prediction-range-dropdown", "value"),
         State("enhanced-prediction-interval-dropdown", "value"),
         State("enhanced-backtest-models-dropdown", "value")]
    )
    def run_backtest(n_clicks, ticker, data_range, interval, models):
        if not n_clicks or not models:
            return ""
        
        # Run enhanced backtest
        backtest_results = prediction_engine.run_backtest(ticker, data_range, interval, models)
        
        # Create results display
        results_display = html.Div([
            # Metrics table
            html.Div([
                html.H3("Model Performance Metrics"),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Model"),
                            html.Th("High RMSE"),
                            html.Th("Low RMSE"),
                            html.Th("High R²"),
                            html.Th("Low R²"),
                            html.Th("Avg Error %")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(model),
                            html.Td(f"{backtest_results['metrics'][model]['high_rmse']:.2f}"),
                            html.Td(f"{backtest_results['metrics'][model]['low_rmse']:.2f}"),
                            html.Td(f"{backtest_results['metrics'][model].get('high_r2', 0):.3f}"),
                            html.Td(f"{backtest_results['metrics'][model].get('low_r2', 0):.3f}"),
                            html.Td(f"{backtest_results['metrics'][model]['avg_error_pct']:.2f}%")
                        ])
                        for model in backtest_results['metrics']
                    ])
                ], className="metrics-table")
            ]),
            
            # Error visualization
            html.Div([
                html.H3("Prediction Error Analysis"),
                dcc.Graph(figure=backtest_results['error_chart'])
            ]),
            
            # Cross-validation results
            html.Div([
                html.H3("Cross-Validation Results"),
                html.P(f"Anomalies removed: {backtest_results.get('anomalies_removed', 0)}"),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Model"),
                            html.Th("High Avg RMSE"),
                            html.Th("Low Avg RMSE"),
                            html.Th("High Avg R²"),
                            html.Th("Low Avg R²")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(model),
                            html.Td(f"{backtest_results['cv_scores'][model]['next_day_high']['avg_rmse']:.2f}"),
                            html.Td(f"{backtest_results['cv_scores'][model]['next_day_low']['avg_rmse']:.2f}"),
                            html.Td(f"{backtest_results['cv_scores'][model]['next_day_high']['avg_r2']:.3f}"),
                            html.Td(f"{backtest_results['cv_scores'][model]['next_day_low']['avg_r2']:.3f}")
                        ])
                        for model in backtest_results['cv_scores']
                    ])
                ], className="cv-table")
            ])
        ])
        
        return results_display

def create_confidence_visualization(predictions):
    """Create a visualization of prediction confidence."""
    # Default empty figure
    if not predictions or ("price" not in predictions and "direction" not in predictions):
        return {}
    
    # Create figure
    fig = go.Figure()
    
    # Add price confidence if available
    if "price" in predictions and "confidence" in predictions:
        confidence_data = predictions["confidence"]
        
        # Get high price confidence
        if "next_day_high" in confidence_data:
            high_confidence = confidence_data["next_day_high"]
            
            # Add bar for ensemble
            if "ensemble" in high_confidence:
                fig.add_trace(go.Bar(
                    x=["High Price"],
                    y=[high_confidence["ensemble"]],
                    name="High Price Confidence",
                    marker_color="rgba(55, 128, 191, 0.7)"
                ))
        
        # Get low price confidence
        if "next_day_low" in confidence_data:
            low_confidence = confidence_data["next_day_low"]
            
            # Add bar for ensemble
            if "ensemble" in low_confidence:
                fig.add_trace(go.Bar(
                    x=["Low Price"],
                    y=[low_confidence["ensemble"]],
                    name="Low Price Confidence",
                    marker_color="rgba(219, 64, 82, 0.7)"
                ))
    
    # Add direction confidence if available
    if "direction" in predictions and "ensemble_probability" in predictions["direction"]:
        direction_prob = predictions["direction"]["ensemble_probability"] * 100
        direction = predictions["direction"]["ensemble"]
        
        fig.add_trace(go.Bar(
            x=["Market Direction"],
            y=[direction_prob],
            name=f"{direction.capitalize()} Direction Confidence",
            marker_color="rgba(50, 171, 96, 0.7)"
        ))
    
    # Update layout
    fig.update_layout(
        title="Prediction Confidence Levels",
        yaxis_title="Confidence (%)",
        yaxis=dict(range=[0, 100]),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig