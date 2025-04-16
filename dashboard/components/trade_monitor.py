# Trade Monitoring Dashboard Component
# This module implements real-time trade monitoring and alerts

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional, Union
import datetime
import json

# Import project modules
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from trading_agent.utils.metrics import RiskManagement


class TradeMonitor:
    """Real-time trade monitoring dashboard."""
    
    def __init__(self, portfolio_data: Optional[pd.DataFrame] = None):
        """Initialize the trade monitor.
        
        Args:
            portfolio_data: DataFrame with portfolio data (optional)
        """
        self.portfolio_data = portfolio_data or pd.DataFrame()
        self.active_trades = []
        self.trade_history = []
        self.alerts = []
        self.risk_manager = RiskManagement()
    
    def update_portfolio_data(self, new_data: pd.DataFrame) -> None:
        """Update portfolio data.
        
        Args:
            new_data: New portfolio data to append
        """
        if self.portfolio_data.empty:
            self.portfolio_data = new_data
        else:
            self.portfolio_data = pd.concat([self.portfolio_data, new_data])
    
    def add_trade(self, trade: Dict) -> None:
        """Add a new trade to the monitor.
        
        Args:
            trade: Trade dictionary with details
        """
        # Ensure trade has a timestamp
        if 'timestamp' not in trade:
            trade['timestamp'] = datetime.datetime.now()
        
        # Add trade to active trades or history based on status
        if trade.get('status') == 'closed':
            self.trade_history.append(trade)
        else:
            trade['status'] = 'open'  # Default to open if not specified
            self.active_trades.append(trade)
    
    def close_trade(self, trade_id: str, close_price: float, close_time: Optional[datetime.datetime] = None) -> None:
        """Close an active trade.
        
        Args:
            trade_id: ID of the trade to close
            close_price: Closing price
            close_time: Closing timestamp (default: current time)
        """
        # Find the trade in active trades
        for i, trade in enumerate(self.active_trades):
            if trade.get('id') == trade_id:
                # Update trade with closing details
                trade['close_price'] = close_price
                trade['close_time'] = close_time or datetime.datetime.now()
                trade['status'] = 'closed'
                
                # Calculate profit/loss
                if trade.get('type') == 'buy':
                    trade['profit'] = (close_price - trade.get('price', 0)) * trade.get('shares', 0)
                    trade['profit_pct'] = (close_price / trade.get('price', 1) - 1) * 100
                elif trade.get('type') == 'sell':
                    trade['profit'] = (trade.get('price', 0) - close_price) * trade.get('shares', 0)
                    trade['profit_pct'] = (trade.get('price', 1) / close_price - 1) * 100
                
                # Move to history
                self.trade_history.append(trade)
                self.active_trades.pop(i)
                break
    
    def add_alert(self, alert: Dict) -> None:
        """Add a new alert to the monitor.
        
        Args:
            alert: Alert dictionary with details
        """
        # Ensure alert has a timestamp
        if 'timestamp' not in alert:
            alert['timestamp'] = datetime.datetime.now()
        
        # Add alert to the list
        self.alerts.append(alert)
    
    def get_portfolio_summary(self) -> Dict:
        """Get a summary of the current portfolio.
        
        Returns:
            Dictionary with portfolio summary
        """
        if self.portfolio_data.empty:
            return {}
        
        # Get latest portfolio value
        latest_data = self.portfolio_data.iloc[-1]
        portfolio_value = latest_data.get('portfolio_value', 0)
        
        # Calculate daily change
        if len(self.portfolio_data) > 1:
            prev_value = self.portfolio_data.iloc[-2].get('portfolio_value', portfolio_value)
            daily_change = portfolio_value - prev_value
            daily_change_pct = (daily_change / prev_value) * 100 if prev_value > 0 else 0
        else:
            daily_change = 0
            daily_change_pct = 0
        
        # Calculate total value of active trades
        active_value = sum(trade.get('shares', 0) * trade.get('price', 0) for trade in self.active_trades)
        
        # Calculate cash (assuming portfolio_value includes active trades)
        cash = portfolio_value - active_value
        
        # Calculate allocation percentages
        if portfolio_value > 0:
            cash_allocation = (cash / portfolio_value) * 100
            invested_allocation = (active_value / portfolio_value) * 100
        else:
            cash_allocation = 0
            invested_allocation = 0
        
        return {
            'portfolio_value': portfolio_value,
            'daily_change': daily_change,
            'daily_change_pct': daily_change_pct,
            'cash': cash,
            'invested': active_value,
            'cash_allocation': cash_allocation,
            'invested_allocation': invested_allocation,
            'active_trades': len(self.active_trades),
            'total_trades': len(self.active_trades) + len(self.trade_history)
        }
    
    def get_active_trades_summary(self) -> Dict:
        """Get a summary of active trades.
        
        Returns:
            Dictionary with active trades summary
        """
        if not self.active_trades:
            return {}
        
        # Calculate total value and unrealized P&L
        total_value = 0
        unrealized_pnl = 0
        unrealized_pnl_pct = 0
        
        # Get latest prices (assuming they're in the portfolio data)
        latest_prices = {}
        if not self.portfolio_data.empty and 'symbol' in self.portfolio_data.columns and 'close' in self.portfolio_data.columns:
            for symbol in self.portfolio_data['symbol'].unique():
                symbol_data = self.portfolio_data[self.portfolio_data['symbol'] == symbol]
                if not symbol_data.empty:
                    latest_prices[symbol] = symbol_data.iloc[-1]['close']
        
        # Calculate metrics for each trade
        for trade in self.active_trades:
            symbol = trade.get('symbol')
            shares = trade.get('shares', 0)
            entry_price = trade.get('price', 0)
            current_price = latest_prices.get(symbol, entry_price)
            
            # Calculate trade value and P&L
            trade_value = shares * current_price
            total_value += trade_value
            
            if trade.get('type') == 'buy':
                trade_pnl = (current_price - entry_price) * shares
                trade_pnl_pct = (current_price / entry_price - 1) * 100 if entry_price > 0 else 0
            elif trade.get('type') == 'sell':
                trade_pnl = (entry_price - current_price) * shares
                trade_pnl_pct = (entry_price / current_price - 1) * 100 if current_price > 0 else 0
            else:
                trade_pnl = 0
                trade_pnl_pct = 0
            
            unrealized_pnl += trade_pnl
        
        # Calculate average P&L percentage
        if total_value > 0:
            unrealized_pnl_pct = (unrealized_pnl / total_value) * 100
        
        return {
            'active_trades': len(self.active_trades),
            'total_value': total_value,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_pct': unrealized_pnl_pct
        }
    
    def plot_portfolio_value(self) -> go.Figure:
        """Plot portfolio value over time.
        
        Returns:
            Plotly figure object
        """
        if self.portfolio_data.empty or 'portfolio_value' not in self.portfolio_data.columns:
            return go.Figure()
        
        fig = go.Figure()
        
        # Add portfolio value trace
        x_values = self.portfolio_data['date'] if 'date' in self.portfolio_data.columns else self.portfolio_data.index
        
        fig.add_trace(go.Scatter(
            x=x_values,
            y=self.portfolio_data['portfolio_value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Add trade markers
        for trade in self.trade_history + self.active_trades:
            if 'timestamp' in trade and trade['timestamp'] in x_values:
                marker_color = 'green' if trade.get('type') == 'buy' else 'red'
                marker_symbol = 'triangle-up' if trade.get('type') == 'buy' else 'triangle-down'
                
                fig.add_trace(go.Scatter(
                    x=[trade['timestamp']],
                    y=[self.portfolio_data.loc[self.portfolio_data.index == trade['timestamp'], 'portfolio_value'].values[0]],
                    mode='markers',
                    marker=dict(color=marker_color, size=10, symbol=marker_symbol),
                    name=f"{trade.get('type', '').capitalize()} {trade.get('symbol', '')}",
                    showlegend=False
                ))
        
        # Update layout
        fig.update_layout(
            title='Portfolio Value',
            xaxis_title='Date',
            yaxis_title='Value ($)',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def plot_active_trades(self) -> go.Figure:
        """Plot active trades with current P&L.
        
        Returns:
            Plotly figure object
        """
        if not self.active_trades:
            return go.Figure()
        
        # Get latest prices (assuming they're in the portfolio data)
        latest_prices = {}
        if not self.portfolio_data.empty and 'symbol' in self.portfolio_data.columns and 'close' in self.portfolio_data.columns:
            for symbol in self.portfolio_data['symbol'].unique():
                symbol_data = self.portfolio_data[self.portfolio_data['symbol'] == symbol]
                if not symbol_data.empty:
                    latest_prices[symbol] = symbol_data.iloc[-1]['close']
        
        # Prepare data for plotting
        symbols = []
        entry_prices = []
        current_prices = []
        pnl_pcts = []
        trade_types = []
        
        for trade in self.active_trades:
            symbol = trade.get('symbol', '')
            entry_price = trade.get('price', 0)
            current_price = latest_prices.get(symbol, entry_price)
            
            symbols.append(symbol)
            entry_prices.append(entry_price)
            current_prices.append(current_price)
            
            if trade.get('type') == 'buy':
                pnl_pct = (current_price / entry_price - 1) * 100 if entry_price > 0 else 0
            elif trade.get('type') == 'sell':
                pnl_pct = (entry_price / current_price - 1) * 100 if current_price > 0 else 0
            else:
                pnl_pct = 0
            
            pnl_pcts.append(pnl_pct)
            trade_types.append(trade.get('type', ''))
        
        # Create figure
        fig = go.Figure()
        
        # Add horizontal bar chart of P&L percentages
        colors = ['green' if pnl >= 0 else 'red' for pnl in pnl_pcts]
        
        fig.add_trace(go.Bar(
            y=symbols,
            x=pnl_pcts,
            orientation='h',
            marker_color=colors,
            text=[f"{pnl:.1f}%" for pnl in pnl_pcts],
            textposition='auto',
            name='P&L %'
        ))
        
        # Add zero line
        fig.add_vline(x=0, line=dict(color='gray', width=1, dash='dash'))
        
        # Update layout
        fig.update_layout(
            title='Active Trades P&L',
            xaxis_title='Profit/Loss (%)',
            yaxis_title='Symbol',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def plot_trade_history(self) -> go.Figure:
        """Plot trade history with P&L.
        
        Returns:
            Plotly figure object
        """
        if not self.trade_history:
            return go.Figure()
        
        # Prepare data for plotting
        timestamps = []
        symbols = []
        profits = []
        trade_types = []
        
        for trade in self.trade_history:
            if 'timestamp' in trade and 'profit' in trade:
                timestamps.append(trade['timestamp'])
                symbols.append(trade.get('symbol', ''))
                profits.append(trade['profit'])
                trade_types.append(trade.get('type', ''))
        
        if not timestamps:  # No trades with complete data
            return go.Figure()
        
        # Create figure
        fig = go.Figure()
        
        # Add scatter plot of trade profits
        colors = ['green' if profit >= 0 else 'red' for profit in profits]
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=profits,
            mode='markers',
            marker=dict(
                color=colors,
                size=10,
                symbol='circle'
            ),
            text=[f"{symbol}: ${profit:.2f}" for symbol, profit in zip(symbols, profits)],
            name='Trade P&L'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line=dict(color='gray', width=1, dash='dash'))
        
        # Update layout
        fig.update_layout(
            title='Trade History P&L',
            xaxis_title='Date',
            yaxis_title='Profit/Loss ($)',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def plot_alerts(self) -> go.Figure:
        """Plot alerts timeline.
        
        Returns:
            Plotly figure object
        """
        if not self.alerts:
            return go.Figure()
        
        # Prepare data for plotting
        timestamps = []
        alert_types = []
        messages = []
        symbols = []
        
        for alert in self.alerts:
            if 'timestamp' in alert and 'message' in alert:
                timestamps.append(alert['timestamp'])
                alert_types.append(alert.get('type', 'info'))
                messages.append(alert['message'])
                symbols.append(alert.get('symbol', ''))
        
        if not timestamps:  # No alerts with complete data
            return go.Figure()
        
        # Create figure
        fig = go.Figure()
        
        # Map alert types to colors
        color_map = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'success': 'green'
        }
        
        colors = [color_map.get(alert_type, 'gray') for alert_type in alert_types]
        
        # Add scatter plot of alerts
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=[1] * len(timestamps),  # All points at y=1
            mode='markers',
            marker=dict(
                color=colors,
                size=10,
                symbol='diamond'
            ),
            text=[f"{symbol}: {message}" for symbol, message in zip(symbols, messages)],
            name='Alerts'
        ))
        
        # Update layout
        fig.update_layout(
            title='Alerts Timeline',
            xaxis_title='Date',
            yaxis_title='',
            yaxis=dict(visible=False),
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def create_risk_metrics(self) -> Dict:
        """Calculate risk metrics for the portfolio.
        
        Returns:
            Dictionary with risk metrics
        """
        if self.portfolio_data.empty or not self.active_trades:
            return {}
        
        # Get portfolio value
        portfolio_value = self.portfolio_data['portfolio_value'].iloc[-1] if 'portfolio_value' in self.portfolio_data.columns else 0
        
        # Calculate exposure by symbol
        exposure = {}
        total_exposure = 0
        
        for trade in self.active_trades:
            symbol = trade.get('symbol', 'Unknown')
            shares = trade.get('shares', 0)
            price = trade.get('price', 0)
            value = shares * price
            
            if symbol in exposure:
                exposure[symbol] += value
            else:
                exposure[symbol] = value
            
            total_exposure += value
        
        # Calculate exposure percentages
        exposure_pct = {symbol: (value / portfolio_value) * 100 for symbol, value in exposure.items()} if portfolio_value > 0 else {}
        
        # Calculate portfolio concentration
        if exposure_pct:
            max_concentration = max(exposure_pct.values())
            concentration_symbol = max(exposure_pct.items(), key=lambda x: x[1])[0]
        else:
            max_concentration = 0
            concentration_symbol = ''
        
        # Calculate portfolio beta (simplified)
        portfolio_beta = 1.0  # Placeholder for actual beta calculation
        
        # Calculate value at risk (VaR) - simplified
        if not self.portfolio_data.empty and 'daily_return' in self.portfolio_data.columns:
            # 95% VaR based on historical returns
            var_95 = np.percentile(self.portfolio_data['daily_return'], 5) * portfolio_value
        else:
            var_95 = 0
        
        return {
            'total_exposure': total_exposure,
            'exposure_pct': total_exposure / portfolio_value * 100 if portfolio_value > 0 else 0,
            'max_concentration': max_concentration,
            'concentration_symbol': concentration_symbol,
            'portfolio_beta': portfolio_beta,
            'value_at_risk_95': var_95,
            'exposure_by_symbol': exposure,
            'exposure_pct_by_symbol': exposure_pct
        }
    
    def create_dashboard(self, output_file: Optional[str] = None) -> Dict:
        """Create a complete trade monitoring dashboard.
        
        Args:
            output_file: Path to save the dashboard HTML (optional)
            
        Returns:
            Dictionary with dashboard components
        """
        # Get summaries
        portfolio_summary = self.get_portfolio_summary()
        active_trades_summary = self.get_active_trades_summary()
        risk_metrics = self.create_risk_metrics()
        
        # Create figures
        portfolio_value_fig = self.plot_portfolio_value()
        active_trades_fig = self.plot_active_trades()
        trade_history_fig = self.plot_trade_history()
        alerts_fig = self.plot_alerts()
        
        # Combine figures into a dashboard
        if output_file:
            # Create a combined figure for HTML output
            dashboard = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'Portfolio Value', 'Active Trades P&L',
                    'Trade History P&L', 'Alerts Timeline',
                    'Portfolio Summary', 'Risk Metrics'
                ),
                specs=[
                    [{'type': 'xy'}, {'type': 'xy'}],
                    [{'type': 'xy'}, {'type': 'xy'}],
                    [{'type': 'table'}, {'type': 'table'}]
                ],
                vertical_spacing=0.1,
                horizontal_spacing=0.05
            )
            
            # Add traces from individual figures
            for trace in portfolio_value_fig.data:
                dashboard.add_trace(trace, row=1, col=1)
            
            for trace in active_trades_fig.data:
                dashboard.add_trace(trace, row=1, col=2)
            
            for trace in trade_history_fig.data:
                dashboard.add_trace(trace, row=2, col=1)
            
            for trace in alerts_fig.data:
                dashboard.add_trace(trace, row=2, col=2)
            
            # Update layout
            dashboard.update_layout(
                title='Trade Monitoring Dashboard',
                template='plotly_white',
                height=1000,
                width=1200,
                showlegend=False
            )
            
            # Write to HTML file
            dashboard.write_html(output_file)
            print(f"Dashboard saved to {output_file}")
        
        # Return dashboard components
        return {
            'portfolio_summary': portfolio_summary,
            'active_trades_summary': active_trades_summary,
            'risk_metrics': risk_metrics,
            'figures': {
                'portfolio_value': portfolio_value_fig,
                'active_trades': active_trades_fig,
                'trade_history': trade_history_fig,
                'alerts': alerts_fig
            }
        }


class AlertSystem:
    """System for generating trading alerts."""
    
    def __init__(self, trade_monitor: TradeMonitor):
        """Initialize the alert system.
        
        Args:
            trade_monitor: TradeMonitor instance to add alerts to
        """
        self.trade_monitor = trade_monitor
        self.risk_manager = RiskManagement()
    
    def check_price_alerts(self, symbol: str, current_price: float, price_targets: Dict[str, float]) -> None:
        """Check for price-based alerts.
        
        Args:
            symbol: Symbol to check
            current_price: Current price
            price_targets: Dictionary of price targets (e.g., {'stop_loss': 100.0, 'take_profit': 110.0})
        """
        for target_name, target_price in price_targets.items():
            if target_name == 'stop_loss' and current_price <= target_price:
                self.trade_monitor.add_alert({
                    'type': 'warning',
                    'symbol': symbol,
                    'message': f"Stop loss triggered at ${target_price:.2f}",
                    'timestamp': datetime.datetime.now()
                })
            elif target_name == 'take_profit' and current_price >= target_price:
                self.trade_monitor.add_alert({
                    'type': 'success',
                    'symbol': symbol,
                    'message': f"Take profit target reached at ${target_price:.2f}",
                    'timestamp': datetime.datetime.now()
                })
    
    def check_technical_alerts(self, symbol: str, technical_data: Dict) -> None:
        """Check for technical indicator-based alerts.
        
        Args:
            symbol: Symbol to check
            technical_data: Dictionary of technical indicators
        """
        # Check for moving average crossovers
        if 'sma_5' in technical_data and 'sma_20' in technical_data:
            sma_5 = technical_data['sma_5']
            sma_20 = technical_data['sma_20']
            prev_sma_5 = technical_data.get('prev_sma_5', sma_5)
            prev_sma_20 = technical_data.get('prev_sma_20', sma_20)
            
            # Golden cross (short-term MA crosses above long-term MA)
            if prev_sma_5 <= prev_sma_20 and sma_5 > sma_20:
                self.trade_monitor.add_alert({
                    'type': 'info',
                    'symbol': symbol,
                    'message': f"Golden cross: 5-day SMA crossed above 20-day SMA",
                    'timestamp': datetime.datetime.now()
                })
            
            # Death cross (short-term MA crosses below long-term MA)
            elif prev_sma_5 >= prev_sma_20 and sma_5 < sma_20:
                self.trade_monitor.add_alert({
                    'type': 'warning',
                    'symbol': symbol,
                    'message': f"Death cross: 5-day SMA crossed below 20-day SMA",
                    'timestamp': datetime.datetime.now()
                })
        
        # Check for RSI overbought/oversold conditions
        if 'rsi_14' in technical_data:
            rsi = technical_data['rsi_14']
            
            if rsi >= 70:
                self.trade_monitor.add_alert({
                    'type': 'warning',
                    'symbol': symbol,
                    'message': f"RSI overbought: {rsi:.1f}",
                    'timestamp': datetime.datetime.now()
                })
            elif rsi <= 30:
                self.trade_monitor.add_alert({
                    'type': 'info',
                    'symbol': symbol,
                    'message': f"RSI oversold: {rsi:.1f}",
                    'timestamp': datetime.datetime.now()
                })
    
    def check_risk_alerts(self) -> None:
        """Check for risk management alerts."""
        # Get risk metrics
        risk_metrics = self.trade_monitor.create_risk_metrics()
        
        if not risk_metrics:
            return
        
        # Check for excessive concentration
        max_concentration = risk_metrics.get('max_concentration', 0)
        concentration_symbol = risk_metrics.get('concentration_symbol', '')
        
        if max_concentration > 25:  # Alert if any position is >25% of portfolio
            self.trade_monitor.add_alert({
                'type': 'warning',
                'symbol': concentration_symbol,
                'message': f"High concentration: {concentration_symbol} is {max_concentration:.1f}% of portfolio",
                'timestamp': datetime.datetime.now()
            })
        
        # Check for excessive overall exposure
        exposure_pct = risk_metrics.get('exposure_pct', 0)
        
        if exposure_pct > 80:  # Alert if exposure is >80% of portfolio
            self.trade_monitor.add_alert({
                'type': 'warning',
                'symbol': 'PORTFOLIO',
                'message': f"High exposure: {exposure_pct:.1f}% of portfolio is invested",
                'timestamp': datetime.datetime.now()
            })
    
    def check_trade_performance_alerts(self) -> None:
        """Check for trade performance alerts."""
        # Check active trades for significant losses
        for trade in self.trade_monitor.active_trades:
            symbol = trade.get('symbol', '')
            entry_price = trade.get('price', 0)
            current_price = 0
            
            # Get current price from portfolio data
            if not self.trade_monitor.portfolio_data.empty and 'symbol' in self.trade_monitor.portfolio_data.columns and 'close' in self.trade_monitor.portfolio_data.columns:
                symbol_data = self.trade_monitor.portfolio_data[self.trade_monitor.portfolio_data['symbol'] == symbol]
                if not symbol_data.empty:
                    current_price = symbol_data.iloc[-1]['close']
            
            if current_price > 0 and entry_price > 0:
                # Calculate P&L percentage
                if trade.get('type') == 'buy':
                    pnl_pct = (current_price / entry_price - 1) * 100
                elif trade.get('type') == 'sell':
                    pnl_pct = (entry_price / current_price - 1) * 100
                else:
                    pnl_pct = 0
                
                # Alert on significant losses
                if pnl_pct < -10:  # Alert if loss is >10%
                    self.trade_monitor.add_alert({
                        'type': 'error',
                        'symbol': symbol,
                        'message': f"Significant loss: {symbol} is down {abs(pnl_pct