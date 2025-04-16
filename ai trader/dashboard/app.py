# Dashboard Application
# This module implements a simple web dashboard for the AI Trading Assistant

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import project modules
from dashboard.components.performance_dashboard import PerformanceDashboard, TradeAnalyzer
from dashboard.components.trade_monitor import TradeMonitor, AlertSystem
from dashboard.components.api_integration_hub import APIIntegrationHub, get_api_integration_hub
from trading_agent.utils.metrics import PerformanceMetrics, RiskManagement, PortfolioAnalytics
from data_processing.connectors.market_data import get_data_connector
from ai_integration.gemini_integration_manager import gemini_manager

# Initialize the Dash app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[
        # Responsive viewport meta tag
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0, maximum-scale=5.0"},
        # PWA related meta tags
        {"name": "theme-color", "content": "#2c3e50"},
        {"name": "apple-mobile-web-app-capable", "content": "yes"},
        {"name": "apple-mobile-web-app-status-bar-style", "content": "black-translucent"},
        {"name": "apple-mobile-web-app-title", "content": "AI Trader"},
        # Web app manifest
        {"name": "manifest", "content": "/assets/manifest.json"},
        # SEO and accessibility
        {"name": "description", "content": "AI Trading Assistant Dashboard with real-time monitoring and alerts"},
        {"property": "og:title", "content": "AI Trading Assistant"},
        {"property": "og:description", "content": "Intelligent trading dashboard with real-time data and alerts"},
        {"http-equiv": "X-UA-Compatible", "content": "IE=edge"}
    ],
    external_stylesheets=[
        "/assets/styles.css",
        "/assets/responsive.css",
        "/assets/modern-ui.css",
        "/assets/prediction.css",
        "/assets/chat-styles.css",
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ]
)
server = app.server

# Register service worker for PWA support
app.clientside_callback(
    """
    function(n) {
        if (!n) return;
        
        // Initialize notification handler
        if (window.notificationHandler) {
            window.notificationHandler.init().then(supported => {
                if (supported) {
                    console.log('Notification system initialized');
                }
            });
        }
        
        // Register service worker for PWA
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/assets/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registered with scope:', registration.scope);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('portfolio-data-store', 'data-pwa-initialized'),
    [Input('interval-component', 'n_intervals')]
)

# Initialize API Integration Hub with improved UI
api_hub = get_api_integration_hub(app)

# Connect Risk Management to AI System
@app.callback(
    Output('risk-ai-connection-status', 'children'),
    [Input('trading-pair-select', 'value')]
)
def update_ai_risk_connection(trading_pair):
    if not trading_pair:
        return html.Div("No trading pair selected", className="warning-message")
    
    # Use default user ID for non-auth version
    user_id = 'default'
    
    # Update trading context in Gemini manager
    success = gemini_manager.update_trading_context(user_id, trading_pair)
    
    if success:
        return html.Div(f"AI system connected to risk management for {trading_pair}", className="success-message")
    else:
        return html.Div("Failed to connect AI to risk management", className="error-message")

# Import prediction pages
from dashboard.pages.prediction_page import get_prediction_page_layout, register_prediction_callbacks
from dashboard.pages.advanced_prediction_page import get_advanced_prediction_page_layout, register_advanced_prediction_callbacks
from dashboard.pages.enhanced_prediction_page import get_enhanced_prediction_page_layout, register_enhanced_prediction_callbacks
from dashboard.pages.chat_page import get_chat_page_layout, register_chat_callbacks

# Register prediction callbacks
register_prediction_callbacks(app)
register_advanced_prediction_callbacks(app)
register_enhanced_prediction_callbacks(app)
register_chat_callbacks(app)

# Define the app layout with improved accessibility and mobile responsiveness
app.layout = html.Div([
    html.Span("AI Trading Assistant", className="visually-hidden", id="app-title"),
    # Add notification permission request
    html.Div([
        html.Button(
            "Enable Notifications", 
            id="enable-notifications-button",
            className="notification-button",
            **{'aria-label': 'Enable push notifications'}
        ),
        html.Div(id="notification-status", className="notification-status")
    ], className="notification-container", style={"display": "none"}, id="notification-permission-container"),
    
    # Main content with tabs
    dcc.Tabs(id="main-tabs", value="dashboard-tab", children=[
        dcc.Tab(label="Dashboard", value="dashboard-tab", className="tab", selected_className="tab--selected", children=[
            # Main dashboard content
            html.Div([
                html.Div([
                    html.H1("AI Trading Assistant Dashboard", className="dashboard-title", **{'aria-labelledby': 'app-title'}),
                    html.Div([
                        html.Button(
                            "Refresh Data", 
                            id="refresh-button", 
                            className="refresh-button mobile-friendly-control",
                            **{'aria-label': 'Refresh dashboard data'}
                        ),
                        dcc.Dropdown(
                            id="symbol-dropdown",
                            options=[
                                {"label": "AAPL", "value": "AAPL"},
                                {"label": "MSFT", "value": "MSFT"},
                                {"label": "GOOGL", "value": "GOOGL"},
                                {"label": "AMZN", "value": "AMZN"},
                                {"label": "TSLA", "value": "TSLA"}
                            ],
                            value="AAPL",
                            className="symbol-dropdown mobile-friendly-control",
                            searchable=True,
                            clearable=False,
                            **{'aria-label': 'Select stock symbol'}
                        ),
                        html.Div(id="last-update-time", className="update-time")
                    ], className="controls-container")
                ], className="header-container"),
    
    html.Div([
        html.Div([
            html.H3("Portfolio Summary", className="panel-title"),
            html.Div(id="portfolio-summary-panel", className="summary-panel")
        ], className="summary-container"),
        
        html.Div([
            html.H3("Active Trades", className="panel-title"),
            html.Div(id="active-trades-panel", className="summary-panel")
        ], className="summary-container"),
        
        html.Div([
            html.H3("Risk Metrics", className="panel-title"),
            html.Div(id="risk-metrics-panel", className="summary-panel")
        ], className="summary-container")
    ], className="summary-row"),
    
    html.Div([
        html.Div([
            html.H3("Portfolio Value", className="chart-title"),
            dcc.Graph(id="portfolio-value-chart")
        ], className="chart-container"),
        
        html.Div([
            html.H3("Cumulative Returns", className="chart-title"),
            dcc.Graph(id="cumulative-returns-chart")
        ], className="chart-container")
    ], className="chart-row"),
    
    html.Div([
        html.Div([
            html.H3("Drawdown", className="chart-title"),
            dcc.Graph(id="drawdown-chart")
        ], className="chart-container"),
        
        html.Div([
            html.H3("Monthly Returns", className="chart-title"),
            dcc.Graph(id="monthly-returns-chart")
        ], className="chart-container")
    ], className="chart-row"),
    
    html.Div([
        html.Div([
            html.H3("Trade History", className="chart-title"),
            dcc.Graph(id="trade-history-chart")
        ], className="chart-container"),
        
        html.Div([
            html.H3("Alerts", className="chart-title"),
            html.Div(id="alerts-panel", className="alerts-panel")
        ], className="chart-container")
    ], className="chart-row"),
    
    # Hidden div for storing data
    html.Div(id="portfolio-data-store", **{'data-pwa-initialized': None}, style={"display": "none"}),
    html.Div(id="trades-data-store", style={"display": "none"}),
    html.Div(id="alerts-data-store", style={"display": "none"}),
    
    # Interval for auto-refresh
    dcc.Interval(
        id="interval-component",
        interval=60*1000,  # in milliseconds (1 minute)
        n_intervals=0
    ),
    
    # Notification components
    html.Div(id="notification-container"),
    html.Div(id="pwa-install-container", className="pwa-install-container")
], className="dashboard-container")

        ]),
        
        # API Integration Hub Tab
        # API Integration Hub Tab
        dcc.Tab(label="API Integration Hub", value="api-hub-tab", className="tab", selected_className="tab--selected", children=[
            api_hub.get_layout()
        ]),
        
        # Risk Management Tab with AI Connection
        dcc.Tab(label="Risk Management", value="risk-tab", className="tab", selected_className="tab--selected", children=[
            html.Div([
                html.H2("Risk Management", className="section-title"),
                html.P(
                    "Configure risk parameters and connect to AI system for context-aware trading.",
                    className="section-description"
                ),
                
                # Trading Pair Selection for AI Context
                html.Div([
                    html.Label("Selected Trading Pair", htmlFor="trading-pair-select", className="form-label"),
                    dcc.Dropdown(
                        id="trading-pair-select",
                        options=[
                            {"label": "BTC/USD", "value": "BTC-USD"},
                            {"label": "ETH/USD", "value": "ETH-USD"},
                            {"label": "SOL/USD", "value": "SOL-USD"},
                            {"label": "XRP/USD", "value": "XRP-USD"},
                            {"label": "ADA/USD", "value": "ADA-USD"},
                        ],
                        placeholder="Select a trading pair",
                        className="trading-pair-dropdown"
                    ),
                    html.Div(id="risk-ai-connection-status", className="context-status"),
                ], className="trading-context-form"),
                
                # Risk Parameters
                html.Div([
                    html.H3("Risk Parameters", className="subsection-title"),
                    html.Div([
                        html.Label("Max Position Size (%)", htmlFor="max-position-size", className="form-label"),
                        dcc.Slider(
                            id="max-position-size",
                            min=1,
                            max=100,
                            step=1,
                            value=10,
                            marks={i: str(i) for i in range(0, 101, 10)},
                            className="risk-slider"
                        ),
                    ], className="risk-parameter"),
                    
                    html.Div([
                        html.Label("Stop Loss (%)", htmlFor="stop-loss-pct", className="form-label"),
                        dcc.Slider(
                            id="stop-loss-pct",
                            min=0.5,
                            max=10,
                            step=0.5,
                            value=2,
                            marks={i: str(i) for i in range(0, 11, 1)},
                            className="risk-slider"
                        ),
                    ], className="risk-parameter"),
                ], className="risk-parameters-container"),
            ], className="risk-management-container")
        ]),
        
        # Prediction Tabs
        dcc.Tab(label="Price Prediction", value="prediction-tab", className="tab", selected_className="tab--selected", children=[
            get_prediction_page_layout()
        ]),
        
        # Advanced Prediction Tab
        dcc.Tab(label="Advanced Prediction", value="advanced-prediction-tab", className="tab", selected_className="tab--selected", children=[
            get_advanced_prediction_page_layout()
        ]),
        
        # Enhanced Prediction Tab
        dcc.Tab(label="Enhanced Prediction", value="enhanced-prediction-tab", className="tab", selected_className="tab--selected", children=[
            get_enhanced_prediction_page_layout()
        ]),
        
        # Chat Tab
        dcc.Tab(label="Chat", value="chat-tab", className="tab", selected_className="tab--selected", children=[
            get_chat_page_layout()
        ])
    ])
], className="dashboard-container")

# Callback for notification permission
@app.callback(
    [
        Output("notification-status", "children"),
        Output("notification-permission-container", "style")
    ],
    [Input("enable-notifications-button", "n_clicks")],
    [State("notification-permission-container", "style")]
)
def handle_notification_permission(n_clicks, current_style):
    if not n_clicks:
        return "", {"display": "none"}
    
    # In a real implementation, this would check the actual permission
    # For now, we'll just acknowledge the click
    return html.Span("Notifications enabled", className="success-text"), {"display": "block"}

# Add client-side callback for PWA installation
app.clientside_callback(
    """
    function(n) {
        if (!n) return;
        
        let deferredPrompt;
        const installContainer = document.getElementById('pwa-install-container');
        
        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevent Chrome 67+ from automatically showing the prompt
            e.preventDefault();
            // Stash the event so it can be triggered later
            deferredPrompt = e;
            
            // Update UI to notify the user they can add to home screen
            installContainer.innerHTML = '<button class="pwa-install-button">Install App</button>';
            installContainer.style.display = 'block';
            
            document.querySelector('.pwa-install-button').addEventListener('click', (e) => {
                // Hide our user interface that shows our install button
                installContainer.style.display = 'none';
                // Show the install prompt
                deferredPrompt.prompt();
                // Wait for the user to respond to the prompt
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted the install prompt');
                    } else {
                        console.log('User dismissed the install prompt');
                    }
                    deferredPrompt = null;
                });
            });
        });
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('notification-container', 'children'),
    [Input('interval-component', 'n_intervals')]
)

# Helper functions for generating sample data
def generate_sample_trades(market_data, symbol):
    """Generate sample trades for demonstration purposes.
    
    Args:
        market_data: DataFrame with market data
        symbol: The ticker symbol
        
    Returns:
        List of trade dictionaries
    """
    trades = []
    
    # Get a subset of dates for trades
    dates = market_data.index.tolist()
    if len(dates) > 10:
        trade_dates = [dates[i] for i in range(0, len(dates), len(dates) // 10)][:10]
    else:
        trade_dates = dates
    
    # Generate buy and sell trades
    for i, date in enumerate(trade_dates):
        # Get price for this date
        price = market_data.loc[date, 'close']
        
        # Alternate between buy and sell
        trade_type = 'buy' if i % 2 == 0 else 'sell'
        
        # Generate random shares
        shares = np.random.randint(10, 100)
        
        # Create trade
        trade = {
            'id': f'trade-{i}',
            'symbol': symbol,
            'type': trade_type,
            'price': price,
            'shares': shares,
            'timestamp': date,
            'status': 'open' if i >= len(trade_dates) - 3 else 'closed'
        }
        
        # Add closing details for closed trades
        if trade['status'] == 'closed':
            close_date_idx = min(i + 2, len(dates) - 1)
            close_date = dates[close_date_idx]
            close_price = market_data.loc[close_date, 'close']
            
            trade['close_price'] = close_price
            trade['close_time'] = close_date
            
            # Calculate profit/loss
            if trade_type == 'buy':
                trade['profit'] = (close_price - price) * shares
                trade['profit_pct'] = (close_price / price - 1) * 100
            else:
                trade['profit'] = (price - close_price) * shares
                trade['profit_pct'] = (price / close_price - 1) * 100
        
        trades.append(trade)
    
    return trades

def generate_sample_alerts(market_data, symbol):
    """Generate sample alerts for demonstration purposes.
    
    Args:
        market_data: DataFrame with market data
        symbol: The ticker symbol
        
    Returns:
        List of alert dictionaries
    """
    alerts = []
    
    # Get a subset of dates for alerts
    dates = market_data.index.tolist()
    if len(dates) > 5:
        alert_dates = [dates[i] for i in range(0, len(dates), len(dates) // 5)][:5]
    else:
        alert_dates = dates
    
    # Alert types
    alert_types = [
        'price_target_reached',
        'stop_loss_triggered',
        'volatility_spike',
        'volume_surge',
        'technical_signal'
    ]
    
    # Alert messages
    alert_messages = {
        'price_target_reached': f'{symbol} reached price target of ${{price:.2f}}',
        'stop_loss_triggered': f'Stop loss triggered for {symbol} at ${{price:.2f}}',
        'volatility_spike': f'Volatility spike detected in {symbol}',
        'volume_surge': f'Unusual volume detected in {symbol}',
        'technical_signal': f'Technical signal: {{signal}} for {symbol}'
    }
    
    # Technical signals
    signals = ['Golden Cross', 'Death Cross', 'RSI Overbought', 'RSI Oversold', 'MACD Crossover']
    
    # Generate alerts
    for i, date in enumerate(alert_dates):
        # Get price for this date
        price = market_data.loc[date, 'close']
        
        # Select alert type
        alert_type = alert_types[i % len(alert_types)]
        
        # Create message
        if alert_type == 'technical_signal':
            signal = signals[i % len(signals)]
            message = alert_messages[alert_type].format(signal=signal)
        else:
            message = alert_messages[alert_type].format(price=price)
        
        # Create alert
        alert = {
            'id': f'alert-{i}',
            'type': alert_type,
            'symbol': symbol,
            'message': message,
            'timestamp': date,
            'price': price,
            'priority': 'high' if alert_type in ['stop_loss_triggered', 'volatility_spike'] else 'medium'
        }
        
        alerts.append(alert)
    
    return alerts

# Define callback to load and process data with performance optimization
@app.callback(
    [
        Output("portfolio-data-store", "children"),
        Output("trades-data-store", "children"),
        Output("alerts-data-store", "children")
    ],
    [
        Input("refresh-button", "n_clicks"),
        Input("interval-component", "n_intervals"),
        Input("symbol-dropdown", "value")
    ],
    # Add loading states for better UX
    [State("portfolio-data-store", "children")]
)
def load_data(n_clicks, n_intervals, symbol, current_data):
    # Get date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")  # 1 year of data
    
    # Get market data
    try:
        data_connector = get_data_connector(source="yahoo")
        market_data = data_connector.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval="1d"
        )
        
        # Add portfolio value column (simulated)
        market_data["portfolio_value"] = 10000 * (1 + market_data["close"].pct_change().cumsum())
        market_data["portfolio_value"].fillna(10000, inplace=True)
        
        # Add symbol column
        market_data["symbol"] = symbol
        
        # Generate sample trades
        trades = generate_sample_trades(market_data, symbol)
        
        # Generate sample alerts
        alerts = generate_sample_alerts(market_data, symbol)
        
        # Convert to JSON for storage
        portfolio_data_json = market_data.to_json(date_format="iso", orient="split")
        trades_json = pd.DataFrame(trades).to_json(date_format="iso", orient="split")
        alerts_json = pd.DataFrame(alerts).to_json(date_format="iso", orient="split")
        
        return portfolio_data_json, trades_json, alerts_json
    
    except Exception as e:
        print(f"Error loading data: {e}")
        # Return empty data
        empty_df = pd.DataFrame()
        empty_json = empty_df.to_json(date_format="iso", orient="split")
        return empty_json, empty_json, empty_json

# Define callback to update portfolio summary panel
@app.callback(
    Output("portfolio-summary-panel", "children"),
    [Input("portfolio-data-store", "children")]
)
def update_portfolio_summary(portfolio_data_json):
    if not portfolio_data_json:
        return html.Div("No data available")
    
    try:
        # Parse portfolio data
        portfolio_data = pd.read_json(portfolio_data_json, orient="split")
        
        # Create trade monitor
        trade_monitor = TradeMonitor(portfolio_data)
        
        # Get portfolio summary
        summary = trade_monitor.get_portfolio_summary()
        
        # Create summary panel
        return html.Div([
            html.Div([
                html.Span("Portfolio Value:", className="summary-label"),
                html.Span(f"${summary.get('portfolio_value', 0):.2f}", className="summary-value")
            ]),
            html.Div([
                html.Span("Daily Change:", className="summary-label"),
                html.Span(
                    f"${summary.get('daily_change', 0):.2f} ({summary.get('daily_change_pct', 0):.2f}%)",
                    className="summary-value " + ("positive" if summary.get('daily_change', 0) >= 0 else "negative")
                )
            ]),
            html.Div([
                html.Span("Cash:", className="summary-label"),
                html.Span(f"${summary.get('cash', 0):.2f} ({summary.get('cash_allocation', 0):.1f}%)", className="summary-value")
            ]),
            html.Div([
                html.Span("Invested:", className="summary-label"),
                html.Span(f"${summary.get('invested', 0):.2f} ({summary.get('invested_allocation', 0):.1f}%)", className="summary-value")
            ])
        ])
    
    except Exception as e:
        print(f"Error updating portfolio summary: {e}")
        return html.Div("Error loading portfolio summary")

# Define callback to update active trades panel
@app.callback(
    Output("active-trades-panel", "children"),
    [Input("trades-data-store", "children")]
)
def update_active_trades(trades_json):
    if not trades_json:
        return html.Div("No trades available")
    
    try:
        # Parse trades data
        trades_df = pd.read_json(trades_json, orient="split")
        
        # Filter active trades
        active_trades = trades_df[trades_df["status"] == "open"].to_dict("records")
        
        if not active_trades:
            return html.Div("No active trades")
        
        # Create active trades panel
        return html.Div([
        html.Span("AI Trading Assistant", className="visually-hidden", id="app-title"),
            html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Symbol"),
                        html.Th("Type"),
                        html.Th("Price"),
                        html.Th("Shares"),
                        html.Th("Value")
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(trade.get("symbol", "")),
                        html.Td(trade.get("type", "").capitalize()),
                        html.Td(f"${trade.get('price', 0):.2f}"),
                        html.Td(f"{trade.get('shares', 0):.0f}"),
                        html.Td(f"${trade.get('price', 0) * trade.get('shares', 0):.2f}")
                    ]) for trade in active_trades
                ])
            ], className="trades-table")
        ])
    
    except Exception as e:
        print(f"Error updating active trades: {e}")
        return html.Div("Error loading active trades")

# Define callback to update risk metrics panel
@app.callback(
    Output("risk-metrics-panel", "children"),
    [Input("portfolio-data-store", "children"), Input("trades-data-store", "children")]
)
def update_risk_metrics(portfolio_data_json, trades_json):
    if not portfolio_data_json or not trades_json:
        return html.Div("No data available")
    
    try:
        # Parse data
        portfolio_data = pd.read_json(portfolio_data_json, orient="split")
        trades_df = pd.read_json(trades_json, orient="split")
        
        # Create trade monitor
        trade_monitor = TradeMonitor(portfolio_data)
        
        # Add active trades
        active_trades = trades_df[trades_df["status"] == "open"].to_dict("records")
        for trade in active_trades:
            trade_monitor.add_trade(trade)
        
        # Get risk metrics
        risk_metrics = trade_monitor.create_risk_metrics()
        
        # Create risk metrics panel
        return html.Div([
            html.Div([
                html.Span("Exposure:", className="summary-label"),
                html.Span(f"${risk_metrics.get('total_exposure', 0):.2f} ({risk_metrics.get('exposure_pct', 0):.1f}%)", className="summary-value")
            ]),
            html.Div([
                html.Span("Max Concentration:", className="summary-label"),
                html.Span(
                    f"{risk_metrics.get('concentration_symbol', '')}: {risk_metrics.get('max_concentration', 0):.1f}%",
                    className="summary-value"
                )
            ]),
            html.Div([
                html.Span("Portfolio Beta:", className="summary-label"),
                html.Span(f"{risk_metrics.get('portfolio_beta', 1.0):.2f}", className="summary-value")
            ]),
            html.Div([
                html.Span("Value at Risk (95%):", className="summary-label"),
                html.Span(f"${abs(risk_metrics.get('value_at_risk_95', 0)):.2f}", className="summary-value")
            ])
        ])
    
    except Exception as e:
        print(f"Error updating risk metrics: {e}")
        return html.Div("Error loading risk metrics")

# Define callback to update portfolio value chart
@app.callback(
    Output("portfolio-value-chart", "figure"),
    [Input("portfolio-data-store", "children")]
)
def update_portfolio_value_chart(portfolio_data_json):
    if not portfolio_data_json:
        return go.Figure()
    
    try:
        # Parse portfolio data
        portfolio_data = pd.read_json(portfolio_data_json, orient="split")
        
        # Create performance dashboard
        dashboard = PerformanceDashboard(portfolio_data)
        
        # Get portfolio value figure
        return dashboard.plot_portfolio_value()
    
    except Exception as e:
        print(f"Error updating portfolio value chart: {e}")
        return go.Figure()

# Define callback to update cumulative returns chart
@app.callback(
    Output("cumulative-returns-chart", "figure"),
    [Input("portfolio-data-store", "children")]
)
def update_cumulative_returns_chart(portfolio_data_json):
    if not portfolio_data_json:
        return go.Figure()
    
    try:
        # Parse portfolio data
        portfolio_data = pd.read_json(portfolio_data_json, orient="split")
        
        # Create performance dashboard
        dashboard = PerformanceDashboard(portfolio_data)
        
        # Get cumulative returns figure
        return dashboard.plot_cumulative_returns()
    
    except Exception as e:
        print(f"Error updating cumulative returns chart: {e}")
        return go.Figure()

# Define callback to update drawdown chart
@app.callback(
    Output("drawdown-chart", "figure"),
    [Input("portfolio-data-store", "children")]
)
def update_drawdown_chart(portfolio_data_json):
    if not portfolio_data_json:
        return go.Figure()
    
    try:
        # Parse portfolio data
        portfolio_data = pd.read_json(portfolio_data_json, orient="split")
        
        # Create performance dashboard
        dashboard = PerformanceDashboard(portfolio_data)
        
        # Get drawdown figure
        return dashboard.plot_drawdown()
    
    except Exception as e:
        print(f"Error updating drawdown chart: {e}")
        return go.Figure()

# Define callback to update monthly returns chart
@app.callback(
    Output("monthly-returns-chart", "figure"),
    [Input("portfolio-data-store", "children")]
)
def update_monthly_returns_chart(portfolio_data_json):
    if not portfolio_data_json:
        return go.Figure()
    
    try:
        # Parse portfolio data
        portfolio_data = pd.read_json(portfolio_data_json, orient="split")
        
        # Create performance dashboard
        dashboard = PerformanceDashboard(portfolio_data)
        
        # Get monthly returns figure
        return dashboard.plot_monthly_returns()
    
    except Exception as e:
        print(f"Error updating monthly returns chart: {e}")
        return go.Figure()

# Define callback to update trade history chart
@app.callback(
    Output("trade-history-chart", "figure"),
    [Input("trades-data-store", "children")]
)
def update_trade_history_chart(trades_json):
    if not trades_json:
        return go.Figure()
    
    try:
        # Parse trades data
        trades_df = pd.read_json(trades_json, orient="split")
        
        # Convert to list of dictionaries
        trades = trades_df.to_dict("records")
        
        # Create trade analyzer
        analyzer = TradeAnalyzer(trades)
        
        # Get trade history figure
        return analyzer.plot_trade_history()
    
    except Exception as e:
        print(f"Error updating trade history chart: {e}")
        return go.Figure()

# Define callback to update alerts panel
@app.callback(
    Output("alerts-panel", "children"),
    [Input("alerts-data-store", "children")]
)
def update_alerts_panel(alerts_json):
    if not alerts_json:
        return html.Div("No alerts available")
    
    try:
        # Parse alerts data
        alerts_df = pd.read_json(alerts_json, orient="split")
        
        if alerts_df.empty:
            return html.Div("No alerts")
        
        # Convert to list of dictionaries
        alerts = alerts_df.to_dict("records")
        
        # Sort alerts by timestamp (newest first)
        alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Create alerts panel
        return html.Div([
        html.Span("AI Trading Assistant", className="visually-hidden", id="app-title"),
            html.Div([
        html.Span("AI Trading Assistant", className="visually-hidden", id="app-title"),
                html.Span(alert.get("timestamp", "").split("T")[0], className="alert-time"),
                html.Span(alert.get("symbol", ""), className="alert-symbol"),
                html.Span(alert.get("message", ""), className="alert-message")
            ], className=f"alert-item {alert.get('type', 'info')}") for alert in alerts[:10]  # Show only the 10 most recent alerts
        ], className="alerts-list")
    
    except Exception as e:
        print(f"Error updating alerts panel: {e}")
        return html.Div("Error loading alerts")

# Helper function to generate sample trades
def generate_sample_trades(market_data, symbol):
    # Get price data
    prices = market_data["close"].values
    dates = market_data["date"].values
    
    # Generate random trades
    trades = []
    
    # Add some active trades
    trades.append({
        "id": "1",
        "symbol": symbol,
        "type": "buy",
        "price": prices[-20],
        "shares": 100,
        "timestamp": dates[-20],
        "status": "open"
    })
    
    trades.append({
        "id": "2",
        "symbol": symbol,
        "type": "buy",
        "price": prices[-10],
        "shares": 50,
        "timestamp": dates[-10],
        "status": "open"
    })
    
    # Add some historical trades
    for i in range(5):
        # Buy trade
        buy_idx = np.random.randint(30, len(prices) - 25)
        buy_price = prices[buy_idx]
        buy_date = dates[buy_idx]
        shares = np.random.randint(10, 100)
        
        # Sell trade (a few days later)
        sell_idx = buy_idx + np.random.randint(5, 20)
        sell_price = prices[sell_idx]
        sell_date = dates[sell_idx]
        
        # Calculate profit
        profit = (sell_price - buy_price) * shares
        profit_pct = (sell_price / buy_price - 1) * 100
        
        # Add buy trade
        trades.append({
            "id": f"hist_buy_{i}",
            "symbol": symbol,
            "type": "buy",
            "price": buy_price,
            "shares": shares,
            "timestamp": buy_date,
            "status": "closed"
        })
        
        # Add sell trade
        trades.append({
            "id": f"hist_sell_{i}",
            "symbol": symbol,
            "type": "sell",
            "price": sell_price,
            "shares": shares,
            "timestamp": sell_date,
            "profit": profit,
            "profit_pct": profit_pct,
            "status": "closed"
        })
    
    return trades

# Add accessibility features to the app
def add_accessibility_features():
    # Add keyboard navigation support
    app.clientside_callback(
        """
        function(n) {
            if (!n) return;
            
            // Add keyboard navigation for interactive elements
            document.addEventListener('keydown', function(e) {
                // Skip if user is in an input field
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                    return;
                }
                
                // Navigation shortcuts
                if (e.key === 'r' && e.altKey) {
                    // Alt+R to refresh data
                    document.getElementById('refresh-button').click();
                }
            });
            
            return window.dash_clientside.no_update;
        }
        """,
        Output('portfolio-data-store', 'data-a11y-initialized'),
        [Input('interval-component', 'n_intervals')]
    )

# Initialize accessibility features
add_accessibility_features()

# Helper function to generate sample alerts
def generate_sample_alerts(market_data, symbol):
    # Get price data
    prices = market_data["close"].values
    dates = market_data["date"].values
    
    # Generate random alerts
    alerts = []
    
    # Add some price alerts
    alerts.append({
        "type": "info",
        "symbol": symbol,
        "message": f"Price target reached: ${prices[-1]:.2f}",
        "timestamp": dates[-1]
    })
    
    # Add some technical alerts
    alerts.append({
        "type": "warning",
        "symbol": symbol,
        "message": "RSI overbought: 72.5",
        "timestamp": dates[-5]
    })
    
    alerts.append({
        "type": "info",
        "symbol": symbol,
        "message": "Golden cross: 5-day SMA crossed above 20-day SMA",
        "timestamp": dates[-15]
    })
    
    # Add some risk alerts
    alerts.append({
        "type": "warning",
        "symbol": "PORTFOLIO",
        "message": "High exposure: 82.5% of portfolio is invested",
        "timestamp": dates[-3]
    })
    
    # Add some trade alerts
    alerts.append({
        "type": "success",
        "symbol": symbol,
        "message": "Take profit target reached at $" + f"{prices[-7]:.2f}",
        "timestamp": dates[-7]
    })
    
    return alerts

# Add script to load notification handler
app.index_string = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        {%metas%}
        <title>AI Trading Assistant</title>
        {%favicon%}
        {%css%}
        <!-- Load notification handler -->
        <script src="/assets/notification-handler.js"></script>
    </head>
    <body>
        <div id="react-entry-point">
            {%app_entry%}
        </div>
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Original CSS styles (keeping for reference)
_original_index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>AI Trading Assistant</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            
            .dashboard-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                background-color: #2c3e50;
                padding: 15px 20px;
                border-radius: 5px;
                color: white;
            }
            
            .dashboard-title {
                margin: 0;
                font-size: 24px;
            }
            
            .controls-container {
                display: flex;
                align-items: center;
            }
            
            .refresh-button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
                margin-right: 15px;
            }
            
            .symbol-dropdown {
                width: 150px;
            }
            
            .summary-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }
            
            .summary-container {
                flex: 1;
                background-color: white;
                border-radius: 5px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-right: 15px;
            }
            
            .summary-container:last-child {
                margin-right: 0;
            }
            
            .panel-title {
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 18px;
                color: #2c3e50;
            }
            
            .summary-panel {
                font-size: 14px;
            }
            
            .summary-panel > div {
                margin-bottom: 8px;
                display: flex;
                justify-content: space-between;
            }
            
            .summary-label {
                color: #7f8c8d;
            }
            
            .summary-value {
                font-weight: bold;
            }
            
            .positive {
                color: #27ae60;
            }
            
            .negative {
                color: #e74c3c;
            }
            
            .chart-row {
                display: flex;
                margin-bottom: 20px;
            }
            
            .chart-container {
                flex: 1;
                background-color: white;
                border-radius: 5px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-right: 15px;
            }
            
            .chart-container:last-child {
                margin-right: 0;
            }
            
            .chart-title {
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 18px;
                color: #2c3e50;
            }
            
            .trades-table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .trades-table th, .trades-table td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            
            .trades-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            
            .alerts-panel {
                max-height: 300px;
                overflow-y: auto;
            }
            
            .alerts-list {
                font-size: 14px;
            }
            
            .alert-item {
                padding: 10px;
                margin-bottom: 5px;
                border-radius: 4px;
                display: flex;
                align-items: center;
            }
            
            .alert-item.info {
                background-color: #d6eaf8;
            }
            
            .alert-item.warning {
                background-color: #fdebd0;
            }
            
            .alert-item.error {
                background-color: #f9ebea;
            }
            
            .alert-item.success {
                background-color: #d5f5e3;
            }
            
            .alert-time {
                font-size: 12px;
                color: #7f8c8d;
                margin-right: 10px;
                width: 80px;
            }
            
            .alert-symbol {
                font-weight: bold;
                margin-right: 10px;
                width: 60px;
            }
            
            .alert-message {
                flex: 1;
            }
            
            @media (max-width: 1200px) {
                .summary-row, .chart-row {
                    flex-direction: column;
                }
                
                .summary-container, .chart-container {
                    margin-right: 0;
                    margin-bottom: 15px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Run the app
if __name__ == "__main__":