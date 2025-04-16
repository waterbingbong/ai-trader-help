# Performance Dashboard Component
# This module implements the dashboard for visualizing trading performance

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional, Union
import json

# Import project modules
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from trading_agent.utils.metrics import PerformanceMetrics, PortfolioAnalytics


class PerformanceDashboard:
    """Dashboard for visualizing trading performance."""
    
    def __init__(self, portfolio_data: pd.DataFrame, benchmark_data: Optional[pd.DataFrame] = None):
        """Initialize the performance dashboard.
        
        Args:
            portfolio_data: DataFrame with portfolio performance data
            benchmark_data: DataFrame with benchmark performance data (optional)
        """
        self.portfolio_data = portfolio_data
        self.benchmark_data = benchmark_data
        
        # Validate portfolio data
        required_columns = ['date', 'portfolio_value']
        for col in required_columns:
            if col not in self.portfolio_data.columns:
                raise ValueError(f"Required column '{col}' not found in portfolio data")
        
        # Calculate returns if not already present
        if 'daily_return' not in self.portfolio_data.columns:
            self.portfolio_data['daily_return'] = self.portfolio_data['portfolio_value'].pct_change()
        
        # Calculate cumulative returns
        self.portfolio_data['cumulative_return'] = (1 + self.portfolio_data['daily_return']).cumprod() - 1
        
        # Process benchmark data if provided
        if self.benchmark_data is not None:
            # Validate benchmark data
            if 'date' not in self.benchmark_data.columns:
                raise ValueError("Required column 'date' not found in benchmark data")
            
            # Align benchmark data with portfolio data
            self.benchmark_data = pd.merge(
                self.portfolio_data[['date']],
                self.benchmark_data,
                on='date',
                how='left'
            )
            
            # Calculate benchmark returns
            if 'value' in self.benchmark_data.columns:
                self.benchmark_data['daily_return'] = self.benchmark_data['value'].pct_change()
                self.benchmark_data['cumulative_return'] = (1 + self.benchmark_data['daily_return']).cumprod() - 1
    
    def create_performance_summary(self) -> Dict:
        """Create a summary of performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        # Extract portfolio values
        portfolio_values = self.portfolio_data['portfolio_value'].values
        
        # Extract benchmark values if available
        benchmark_values = None
        if self.benchmark_data is not None and 'value' in self.benchmark_data.columns:
            benchmark_values = self.benchmark_data['value'].values
        
        # Calculate portfolio statistics
        stats = PortfolioAnalytics.calculate_portfolio_stats(
            portfolio_values=portfolio_values,
            benchmark_values=benchmark_values,
            risk_free_rate=0.02  # Assuming 2% risk-free rate
        )
        
        return stats
    
    def plot_portfolio_value(self) -> go.Figure:
        """Plot portfolio value over time.
        
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        # Add portfolio value trace
        fig.add_trace(go.Scatter(
            x=self.portfolio_data['date'],
            y=self.portfolio_data['portfolio_value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Add benchmark value if available
        if self.benchmark_data is not None and 'value' in self.benchmark_data.columns:
            fig.add_trace(go.Scatter(
                x=self.benchmark_data['date'],
                y=self.benchmark_data['value'],
                mode='lines',
                name='Benchmark',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
        
        # Update layout
        fig.update_layout(
            title='Portfolio Value Over Time',
            xaxis_title='Date',
            yaxis_title='Value ($)',
            template='plotly_white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def plot_cumulative_returns(self) -> go.Figure:
        """Plot cumulative returns over time.
        
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        # Add portfolio cumulative returns trace
        fig.add_trace(go.Scatter(
            x=self.portfolio_data['date'],
            y=self.portfolio_data['cumulative_return'] * 100,
            mode='lines',
            name='Portfolio',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Add benchmark cumulative returns if available
        if self.benchmark_data is not None and 'cumulative_return' in self.benchmark_data.columns:
            fig.add_trace(go.Scatter(
                x=self.benchmark_data['date'],
                y=self.benchmark_data['cumulative_return'] * 100,
                mode='lines',
                name='Benchmark',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
        
        # Update layout
        fig.update_layout(
            title='Cumulative Returns',
            xaxis_title='Date',
            yaxis_title='Cumulative Return (%)',
            template='plotly_white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def plot_drawdown(self) -> go.Figure:
        """Plot drawdown over time.
        
        Returns:
            Plotly figure object
        """
        # Calculate running maximum
        self.portfolio_data['running_max'] = self.portfolio_data['portfolio_value'].cummax()
        
        # Calculate drawdown
        self.portfolio_data['drawdown'] = (self.portfolio_data['portfolio_value'] / self.portfolio_data['running_max']) - 1
        
        fig = go.Figure()
        
        # Add drawdown trace
        fig.add_trace(go.Scatter(
            x=self.portfolio_data['date'],
            y=self.portfolio_data['drawdown'] * 100,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='#d62728', width=2)
        ))
        
        # Update layout
        fig.update_layout(
            title='Portfolio Drawdown',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40),
            yaxis=dict(tickformat='.1f')
        )
        
        return fig
    
    def plot_monthly_returns(self) -> go.Figure:
        """Plot monthly returns heatmap.
        
        Returns:
            Plotly figure object
        """
        # Extract date components
        self.portfolio_data['year'] = pd.DatetimeIndex(self.portfolio_data['date']).year
        self.portfolio_data['month'] = pd.DatetimeIndex(self.portfolio_data['date']).month
        
        # Calculate monthly returns
        monthly_returns = self.portfolio_data.groupby(['year', 'month'])['daily_return'].apply(
            lambda x: (1 + x).prod() - 1
        ).reset_index()
        
        # Create pivot table
        pivot_table = monthly_returns.pivot(index='year', columns='month', values='daily_return')
        
        # Replace month numbers with names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        pivot_table.columns = [month_names[i-1] for i in pivot_table.columns]
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values * 100,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='RdBu',
            zmid=0,
            text=np.round(pivot_table.values * 100, 1),
            texttemplate='%{text:.1f}%',
            colorbar=dict(title='Return (%)')
        ))
        
        # Update layout
        fig.update_layout(
            title='Monthly Returns (%)',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(title='Month'),
            yaxis=dict(title='Year', autorange='reversed')
        )
        
        return fig
    
    def plot_rolling_volatility(self, window: int = 21) -> go.Figure:
        """Plot rolling volatility.
        
        Args:
            window: Rolling window size in days
            
        Returns:
            Plotly figure object
        """
        # Calculate rolling volatility (annualized)
        self.portfolio_data[f'volatility_{window}d'] = self.portfolio_data['daily_return'].rolling(window=window).std() * np.sqrt(252)
        
        fig = go.Figure()
        
        # Add volatility trace
        fig.add_trace(go.Scatter(
            x=self.portfolio_data['date'],
            y=self.portfolio_data[f'volatility_{window}d'] * 100,
            mode='lines',
            name=f'{window}-Day Volatility',
            line=dict(color='#9467bd', width=2)
        ))
        
        # Update layout
        fig.update_layout(
            title=f'{window}-Day Rolling Volatility (Annualized)',
            xaxis_title='Date',
            yaxis_title='Volatility (%)',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def plot_rolling_sharpe(self, window: int = 63, risk_free_rate: float = 0.02) -> go.Figure:
        """Plot rolling Sharpe ratio.
        
        Args:
            window: Rolling window size in days
            risk_free_rate: Annualized risk-free rate
            
        Returns:
            Plotly figure object
        """
        # Calculate daily risk-free rate
        daily_rf = (1 + risk_free_rate) ** (1/252) - 1
        
        # Calculate excess returns
        self.portfolio_data['excess_return'] = self.portfolio_data['daily_return'] - daily_rf
        
        # Calculate rolling mean and std of excess returns
        rolling_mean = self.portfolio_data['excess_return'].rolling(window=window).mean() * 252
        rolling_std = self.portfolio_data['excess_return'].rolling(window=window).std() * np.sqrt(252)
        
        # Calculate rolling Sharpe ratio
        self.portfolio_data[f'sharpe_{window}d'] = rolling_mean / rolling_std
        
        fig = go.Figure()
        
        # Add Sharpe ratio trace
        fig.add_trace(go.Scatter(
            x=self.portfolio_data['date'],
            y=self.portfolio_data[f'sharpe_{window}d'],
            mode='lines',
            name=f'{window}-Day Sharpe Ratio',
            line=dict(color='#2ca02c', width=2)
        ))
        
        # Add zero line
        fig.add_hline(y=0, line=dict(color='gray', width=1, dash='dash'))
        
        # Update layout
        fig.update_layout(
            title=f'{window}-Day Rolling Sharpe Ratio',
            xaxis_title='Date',
            yaxis_title='Sharpe Ratio',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def create_dashboard(self, output_file: Optional[str] = None) -> Dict:
        """Create a complete dashboard with all visualizations.
        
        Args:
            output_file: Path to save the dashboard HTML (optional)
            
        Returns:
            Dictionary with performance metrics and figures
        """
        # Calculate performance metrics
        metrics = self.create_performance_summary()
        
        # Create figures
        portfolio_value_fig = self.plot_portfolio_value()
        cumulative_returns_fig = self.plot_cumulative_returns()
        drawdown_fig = self.plot_drawdown()
        monthly_returns_fig = self.plot_monthly_returns()
        volatility_fig = self.plot_rolling_volatility()
        sharpe_fig = self.plot_rolling_sharpe()
        
        # Combine figures into a dashboard
        if output_file:
            # Create a combined figure for HTML output
            dashboard = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'Portfolio Value', 'Cumulative Returns',
                    'Drawdown', 'Monthly Returns',
                    'Rolling Volatility', 'Rolling Sharpe Ratio'
                ),
                specs=[
                    [{'type': 'xy'}, {'type': 'xy'}],
                    [{'type': 'xy'}, {'type': 'heatmap'}],
                    [{'type': 'xy'}, {'type': 'xy'}]
                ],
                vertical_spacing=0.1,
                horizontal_spacing=0.05
            )
            
            # Add traces from individual figures
            for trace in portfolio_value_fig.data:
                dashboard.add_trace(trace, row=1, col=1)
            
            for trace in cumulative_returns_fig.data:
                dashboard.add_trace(trace, row=1, col=2)
            
            for trace in drawdown_fig.data:
                dashboard.add_trace(trace, row=2, col=1)
            
            for trace in monthly_returns_fig.data:
                dashboard.add_trace(trace, row=2, col=2)
            
            for trace in volatility_fig.data:
                dashboard.add_trace(trace, row=3, col=1)
            
            for trace in sharpe_fig.data:
                dashboard.add_trace(trace, row=3, col=2)
            
            # Update layout
            dashboard.update_layout(
                title='Trading Performance Dashboard',
                template='plotly_white',
                height=1200,
                width=1200,
                showlegend=False
            )
            
            # Write to HTML file
            dashboard.write_html(output_file)
            print(f"Dashboard saved to {output_file}")
        
        # Return metrics and figures
        return {
            'metrics': metrics,
            'figures': {
                'portfolio_value': portfolio_value_fig,
                'cumulative_returns': cumulative_returns_fig,
                'drawdown': drawdown_fig,
                'monthly_returns': monthly_returns_fig,
                'volatility': volatility_fig,
                'sharpe': sharpe_fig
            }
        }


class TradeAnalyzer:
    """Analyze and visualize trade data."""
    
    def __init__(self, trades: List[Dict]):
        """Initialize the trade analyzer.
        
        Args:
            trades: List of trade dictionaries
        """
        self.trades = trades
        
        # Convert trades to DataFrame
        self.trades_df = pd.DataFrame(trades)
        
        # Calculate trade metrics
        self._calculate_trade_metrics()
    
    def _calculate_trade_metrics(self) -> None:
        """Calculate metrics for each trade."""
        if self.trades_df.empty:
            return
        
        # Ensure required columns exist
        required_columns = ['type', 'price', 'shares']
        for col in required_columns:
            if col not in self.trades_df.columns:
                raise ValueError(f"Required column '{col}' not found in trades data")
        
        # Add timestamp if not present
        if 'timestamp' not in self.trades_df.columns and 'step' in self.trades_df.columns:
            self.trades_df['timestamp'] = pd.to_datetime('today') - pd.to_timedelta(self.trades_df['step'], unit='d')
        
        # Calculate trade profits
        buy_trades = self.trades_df[self.trades_df['type'] == 'buy'].copy()
        sell_trades = self.trades_df[self.trades_df['type'] == 'sell'].copy()
        
        if not buy_trades.empty and not sell_trades.empty:
            # Match buys and sells to calculate profits
            buy_index = 0
            remaining_shares = 0
            
            for i, sell in sell_trades.iterrows():
                sell_shares = sell['shares']
                sell_price = sell['price']
                profit = 0
                cost_basis = 0
                
                # Match with buy trades
                while sell_shares > 0 and buy_index < len(buy_trades):
                    buy = buy_trades.iloc[buy_index]
                    
                    if remaining_shares == 0:
                        remaining_shares = buy['shares']
                    
                    # Calculate shares to match
                    matched_shares = min(remaining_shares, sell_shares)
                    
                    # Calculate profit for this match
                    buy_price = buy['price']
                    match_profit = matched_shares * (sell_price - buy_price)
                    profit += match_profit
                    cost_basis += matched_shares * buy_price
                    
                    # Update remaining shares
                    remaining_shares -= matched_shares
                    sell_shares -= matched_shares
                    
                    # Move to next buy if this one is fully used
                    if remaining_shares == 0:
                        buy_index += 1
                
                # Store profit in sell trade
                self.trades_df.loc[i, 'profit'] = profit
                self.trades_df.loc[i, 'profit_pct'] = profit / cost_basis if cost_basis > 0 else 0
        
        # Calculate cumulative profit
        if 'profit' in self.trades_df.columns:
            self.trades_df['cumulative_profit'] = self.trades_df['profit'].cumsum()
    
    def get_trade_summary(self) -> Dict:
        """Get a summary of trade performance.
        
        Returns:
            Dictionary with trade summary statistics
        """
        if self.trades_df.empty:
            return {}
        
        # Count trades by type
        buy_count = len(self.trades_df[self.trades_df['type'] == 'buy'])
        sell_count = len(self.trades_df[self.trades_df['type'] == 'sell'])
        
        # Calculate profit metrics if available
        profit_metrics = {}
        if 'profit' in self.trades_df.columns:
            sell_trades = self.trades_df[self.trades_df['type'] == 'sell']
            
            if not sell_trades.empty:
                # Calculate total profit
                total_profit = sell_trades['profit'].sum()
                
                # Calculate win rate
                winning_trades = sell_trades[sell_trades['profit'] > 0]
                win_rate = len(winning_trades) / len(sell_trades) if len(sell_trades) > 0 else 0
                
                # Calculate average profit/loss
                avg_profit = sell_trades['profit'].mean()
                avg_win = winning_trades['profit'].mean() if not winning_trades.empty else 0
                
                losing_trades = sell_trades[sell_trades['profit'] <= 0]
                avg_loss = losing_trades['profit'].mean() if not losing_trades.empty else 0
                
                # Calculate profit factor
                gross_profit = winning_trades['profit'].sum() if not winning_trades.empty else 0
                gross_loss = abs(losing_trades['profit'].sum()) if not losing_trades.empty else 0
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                
                profit_metrics = {
                    'total_profit': total_profit,
                    'win_rate': win_rate,
                    'avg_profit': avg_profit,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'profit_factor': profit_factor,
                    'winning_trades': len(winning_trades),
                    'losing_trades': len(losing_trades)
                }
        
        # Combine all metrics
        summary = {
            'total_trades': len(self.trades_df),
            'buy_trades': buy_count,
            'sell_trades': sell_count,
            **profit_metrics
        }
        
        return summary
    
    def plot_trade_history(self) -> go.Figure:
        """Plot trade history with buy/sell markers.
        
        Returns:
            Plotly figure object
        """
        if self.trades_df.empty:
            return go.Figure()
        
        fig = go.Figure()
        
        # Add price trace if we have a continuous price series
        if 'step' in self.trades_df.columns and 'price' in self.trades_df.columns:
            # Sort by step
            sorted_df = self.trades_df.sort_values('step')
            
            # Create a continuous price series
            steps = sorted_df['step'].unique()
            prices = []
            for step in steps:
                step_price = sorted_df[sorted_df['step'] == step]['price'].iloc[0]
                prices.append(step_price)
            
            # Plot price line
            fig.add_trace(go.Scatter(
                x=steps,
                y=prices,
                mode='lines',
                name='Price',
                line=dict(color='gray', width=1)
            ))
        
        # Add buy markers
        buy_trades = self.trades_df[self.trades_df['type'] == 'buy']
        if not buy_trades.empty:
            x_values = buy_trades['step'] if 'step' in buy_trades.columns else buy_trades['timestamp']
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=buy_trades['price'],
                mode='markers',
                name='Buy',
                marker=dict(color='green', size=10, symbol='triangle-up')
            ))
        
        # Add sell markers
        sell_trades = self.trades_df[self.trades_df['type'] == 'sell']
        if not sell_trades.empty:
            x_values = sell_trades['step'] if 'step' in sell_trades.columns else sell_trades['timestamp']
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=sell_trades['price'],
                mode='markers',
                name='Sell',
                marker=dict(color='red', size=10, symbol='triangle-down')
            ))
        
        # Update layout
        x_title = 'Step' if 'step' in self.trades_df.columns else 'Date'
        fig.update_layout(
            title='Trade History',
            xaxis_title=x_title,
            yaxis_title='Price',
            template='plotly_white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def plot_profit_curve(self) -> go.Figure:
        """Plot cumulative profit curve.
        
        Returns:
            Plotly figure object
        """
        if self.trades_df.empty or 'cumulative_profit' not in self.trades_df.columns:
            return go.Figure()
        
        # Filter to sell trades (which have profit)
        sell_trades = self.trades_df[self.trades_df['type'] == 'sell'].copy()
        
        if sell_trades.empty:
            return go.Figure()
        
        fig = go.Figure()
        
        # Add cumulative profit trace
        x_values = sell_trades['step'] if 'step' in sell_trades.columns else sell_trades['timestamp']
        
        fig.add_trace(go.Scatter(
            x=x_values,
            y=sell_trades['cumulative_profit'],
            mode='lines',
            name='Cumulative Profit',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Add zero line
        fig.add_hline(y=0, line=dict(color='gray', width=1, dash='dash'))
        
        # Update layout
        x_title = 'Step' if 'step' in sell_trades.columns else 'Date'
        fig.update_layout(
            title='Cumulative Profit',
            xaxis_title=x_title,
            yaxis_title='Profit ($)',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def plot_profit_distribution(self) -> go.Figure:
        """Plot distribution of trade profits.
        
        Returns:
            Plotly figure object
        """
        if self.trades_df.empty or 'profit' not in self.trades_df.columns:
            return go.Figure()
        
        # Filter to sell trades (which have profit)
        sell_trades = self.trades_df[self.trades_df['type'] == 'sell']
        
        if sell_trades.empty:
            return go.Figure()
        
        fig = go.Figure()
        
        # Add histogram of profits
        fig.add_trace(go.Histogram(
            x=sell_trades['profit'],
            nbinsx=20,
            marker_color='#1f77b4',
            opacity=0.7,
            name='Profit Distribution'
        ))
        
        # Add vertical line at zero
        fig.add_vline(x=0, line=dict(color='red', width=2, dash='dash'))
        
        # Update layout
        fig.update_layout(
            title='Trade Profit Distribution',
            xaxis_title='Profit ($)',
            yaxis_title='Number of Trades',
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def create_trade_dashboard(self, output_file: Optional[str] = None) -> Dict:
        """Create a complete trade analysis dashboard.
        
        Args:
            output_file: Path to save the dashboard HTML (optional)
            
        Returns:
            Dictionary with trade summary and figures
        """
        # Get trade summary
        summary = self.get_trade_summary()
        
        # Create figures
        trade_history_fig = self.plot_trade_history()
        profit_curve_fig = self.plot_profit_curve()
        profit_dist_fig = self.plot_profit_distribution()
        
        # Combine figures into a dashboard
        if output_file:
            # Create a combined figure for HTML output
            dashboard = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Trade History', 'Cumulative Profit',
                    'Trade Profit Distribution', 'Trade Summary'
                ),
                specs=[
                    [{'type': 'xy'}, {'type': 'xy'}],
                    [{'type': 'xy'}, {'type': 'table'}]
                ],
                vertical_spacing=0.1,
                horizontal_spacing=0.05
            )
            
            # Add traces from individual figures
            for trace in trade_history_fig.data:
                dashboard.add_trace(trace, row=1, col=1)
            
            for trace in profit_curve_fig.data:
                dashboard.add_trace(trace, row=1, col=2)
            
            for trace in profit_dist_fig.data:
                dashboard.add_trace(trace, row=2, col=1)
            
            # Add summary table
            if summary:
                # Convert summary to table format
                table_data = []
                for key, value in summary.items():
                    if isinstance(value, float):
                        if key in ['win_rate']:
                            formatted_value = f"{value:.1%}"
                        else:
                            formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = str(value)
                    
                    table_data.append([key.replace('_', '