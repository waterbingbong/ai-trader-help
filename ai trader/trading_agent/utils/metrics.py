# Trading Metrics and Risk Management Utilities
# This module provides functions for calculating trading performance metrics and risk management

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union


class PerformanceMetrics:
    """Calculate performance metrics for trading strategies."""
    
    @staticmethod
    def calculate_returns(portfolio_values: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray]:
        """Calculate total and periodic returns from portfolio values.
        
        Args:
            portfolio_values: Array of portfolio values over time
            
        Returns:
            Tuple of (total_return, period_returns, log_returns)
        """
        if len(portfolio_values) < 2:
            return 0.0, np.array([]), np.array([])
        
        # Calculate total return
        total_return = (portfolio_values[-1] / portfolio_values[0]) - 1
        
        # Calculate period returns
        period_returns = np.diff(portfolio_values) / portfolio_values[:-1]
        
        # Calculate log returns
        log_returns = np.log(portfolio_values[1:] / portfolio_values[:-1])
        
        return total_return, period_returns, log_returns
    
    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """Calculate the Sharpe ratio.
        
        Args:
            returns: Array of period returns
            risk_free_rate: Risk-free rate (annualized)
            periods_per_year: Number of periods in a year (252 for daily trading days)
            
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        # Convert risk-free rate to per-period rate
        rf_per_period = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
        
        # Calculate excess returns
        excess_returns = returns - rf_per_period
        
        # Calculate Sharpe ratio
        sharpe = np.mean(excess_returns) / np.std(excess_returns, ddof=1) if np.std(excess_returns, ddof=1) > 0 else 0
        
        # Annualize
        sharpe_annualized = sharpe * np.sqrt(periods_per_year)
        
        return sharpe_annualized
    
    @staticmethod
    def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """Calculate the Sortino ratio.
        
        Args:
            returns: Array of period returns
            risk_free_rate: Risk-free rate (annualized)
            periods_per_year: Number of periods in a year (252 for daily trading days)
            
        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return 0.0
        
        # Convert risk-free rate to per-period rate
        rf_per_period = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
        
        # Calculate excess returns
        excess_returns = returns - rf_per_period
        
        # Calculate downside deviation (only negative returns)
        negative_returns = excess_returns[excess_returns < 0]
        downside_deviation = np.std(negative_returns, ddof=1) if len(negative_returns) > 1 else 0
        
        # Calculate Sortino ratio
        sortino = np.mean(excess_returns) / downside_deviation if downside_deviation > 0 else 0
        
        # Annualize
        sortino_annualized = sortino * np.sqrt(periods_per_year)
        
        return sortino_annualized
    
    @staticmethod
    def calculate_max_drawdown(portfolio_values: np.ndarray) -> Tuple[float, int, int]:
        """Calculate maximum drawdown and its duration.
        
        Args:
            portfolio_values: Array of portfolio values over time
            
        Returns:
            Tuple of (max_drawdown, drawdown_start, drawdown_end)
        """
        if len(portfolio_values) < 2:
            return 0.0, 0, 0
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(portfolio_values)
        
        # Calculate drawdown
        drawdown = (portfolio_values / running_max) - 1
        
        # Find maximum drawdown and its indices
        max_drawdown = np.min(drawdown)
        max_drawdown_end = np.argmin(drawdown)
        
        # Find the start of the drawdown period
        max_drawdown_start = np.argmax(portfolio_values[:max_drawdown_end])
        
        return max_drawdown, max_drawdown_start, max_drawdown_end
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict]) -> float:
        """Calculate win rate from a list of trades.
        
        Args:
            trades: List of trade dictionaries with 'type' and 'profit' keys
            
        Returns:
            Win rate as a fraction
        """
        if not trades:
            return 0.0
        
        # Count profitable trades
        profitable_trades = sum(1 for trade in trades if trade.get('profit', 0) > 0)
        
        # Calculate win rate
        win_rate = profitable_trades / len(trades)
        
        return win_rate
    
    @staticmethod
    def calculate_profit_factor(trades: List[Dict]) -> float:
        """Calculate profit factor from a list of trades.
        
        Args:
            trades: List of trade dictionaries with 'profit' key
            
        Returns:
            Profit factor
        """
        if not trades:
            return 0.0
        
        # Sum profits and losses
        gross_profit = sum(trade.get('profit', 0) for trade in trades if trade.get('profit', 0) > 0)
        gross_loss = abs(sum(trade.get('profit', 0) for trade in trades if trade.get('profit', 0) < 0))
        
        # Calculate profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return profit_factor
    
    @staticmethod
    def calculate_average_trade(trades: List[Dict]) -> Tuple[float, float, float]:
        """Calculate average trade metrics.
        
        Args:
            trades: List of trade dictionaries with 'profit' key
            
        Returns:
            Tuple of (avg_profit, avg_win, avg_loss)
        """
        if not trades:
            return 0.0, 0.0, 0.0
        
        # Calculate average profit/loss
        profits = [trade.get('profit', 0) for trade in trades]
        avg_profit = np.mean(profits)
        
        # Calculate average win
        wins = [p for p in profits if p > 0]
        avg_win = np.mean(wins) if wins else 0.0
        
        # Calculate average loss
        losses = [p for p in profits if p < 0]
        avg_loss = np.mean(losses) if losses else 0.0
        
        return avg_profit, avg_win, avg_loss


class RiskManagement:
    """Risk management utilities for trading."""
    
    def __init__(self, 
                 max_position_size: float = 0.1,
                 max_portfolio_risk: float = 0.02,
                 stop_loss_pct: float = 0.02,
                 take_profit_pct: float = 0.04):
        """Initialize risk management parameters.
        
        Args:
            max_position_size: Maximum position size as a fraction of portfolio
            max_portfolio_risk: Maximum portfolio risk per trade
            stop_loss_pct: Default stop loss percentage
            take_profit_pct: Default take profit percentage
        """
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
    
    def calculate_position_size(self, portfolio_value: float, price: float, volatility: float = None) -> float:
        """Calculate the appropriate position size based on risk parameters.
        
        Args:
            portfolio_value: Current portfolio value
            price: Current price of the asset
            volatility: Asset volatility (optional)
            
        Returns:
            Number of shares to trade
        """
        # Basic position sizing based on max_position_size
        max_position_value = portfolio_value * self.max_position_size
        
        # If volatility is provided, adjust position size based on risk
        if volatility is not None and volatility > 0:
            # Risk-adjusted position size
            risk_amount = portfolio_value * self.max_portfolio_risk
            risk_per_share = price * volatility  # Simplified risk model
            risk_adjusted_shares = risk_amount / risk_per_share
            risk_adjusted_value = risk_adjusted_shares * price
            
            # Take the smaller of the two position sizes
            position_value = min(max_position_value, risk_adjusted_value)
        else:
            position_value = max_position_value
        
        # Calculate number of shares
        shares = position_value / price
        
        return shares
    
    def calculate_stop_loss(self, entry_price: float, is_long: bool = True) -> float:
        """Calculate stop loss price.
        
        Args:
            entry_price: Entry price of the trade
            is_long: Whether the position is long (True) or short (False)
            
        Returns:
            Stop loss price
        """
        if is_long:
            return entry_price * (1 - self.stop_loss_pct)
        else:
            return entry_price * (1 + self.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: float, is_long: bool = True) -> float:
        """Calculate take profit price.
        
        Args:
            entry_price: Entry price of the trade
            is_long: Whether the position is long (True) or short (False)
            
        Returns:
            Take profit price
        """
        if is_long:
            return entry_price * (1 + self.take_profit_pct)
        else:
            return entry_price * (1 - self.take_profit_pct)
    
    def calculate_risk_reward_ratio(self, entry_price: float, stop_loss: float, take_profit: float) -> float:
        """Calculate risk-reward ratio for a trade.
        
        Args:
            entry_price: Entry price of the trade
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Risk-reward ratio
        """
        # Calculate risk and reward
        risk = abs(entry_price - stop_loss)
        reward = abs(entry_price - take_profit)
        
        # Calculate ratio
        ratio = reward / risk if risk > 0 else float('inf')
        
        return ratio
    
    def should_take_trade(self, entry_price: float, stop_loss: float, take_profit: float, min_risk_reward: float = 2.0) -> bool:
        """Determine if a trade should be taken based on risk-reward ratio.
        
        Args:
            entry_price: Entry price of the trade
            stop_loss: Stop loss price
            take_profit: Take profit price
            min_risk_reward: Minimum acceptable risk-reward ratio
            
        Returns:
            True if the trade should be taken, False otherwise
        """
        risk_reward = self.calculate_risk_reward_ratio(entry_price, stop_loss, take_profit)
        return risk_reward >= min_risk_reward


class PortfolioAnalytics:
    """Analytics for portfolio performance."""
    
    @staticmethod
    def calculate_portfolio_stats(portfolio_values: np.ndarray, benchmark_values: Optional[np.ndarray] = None, risk_free_rate: float = 0.0) -> Dict:
        """Calculate comprehensive portfolio statistics.
        
        Args:
            portfolio_values: Array of portfolio values over time
            benchmark_values: Array of benchmark values over time (optional)
            risk_free_rate: Risk-free rate (annualized)
            
        Returns:
            Dictionary of portfolio statistics
        """
        if len(portfolio_values) < 2:
            return {}
        
        # Calculate returns
        total_return, period_returns, log_returns = PerformanceMetrics.calculate_returns(portfolio_values)
        
        # Calculate annualized return (assuming 252 trading days per year)
        periods = len(portfolio_values) - 1
        periods_per_year = 252  # Trading days in a year
        years = periods / periods_per_year
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Calculate volatility
        volatility = np.std(period_returns, ddof=1) if len(period_returns) > 1 else 0
        annualized_volatility = volatility * np.sqrt(periods_per_year)
        
        # Calculate Sharpe and Sortino ratios
        sharpe_ratio = PerformanceMetrics.calculate_sharpe_ratio(period_returns, risk_free_rate, periods_per_year)
        sortino_ratio = PerformanceMetrics.calculate_sortino_ratio(period_returns, risk_free_rate, periods_per_year)
        
        # Calculate maximum drawdown
        max_drawdown, dd_start, dd_end = PerformanceMetrics.calculate_max_drawdown(portfolio_values)
        
        # Calculate Calmar ratio (annualized return / max drawdown)
        calmar_ratio = abs(annualized_return / max_drawdown) if max_drawdown != 0 else float('inf')
        
        # Calculate benchmark comparison if provided
        benchmark_stats = {}
        if benchmark_values is not None and len(benchmark_values) == len(portfolio_values):
            # Calculate benchmark returns
            bench_total_return, bench_period_returns, _ = PerformanceMetrics.calculate_returns(benchmark_values)
            
            # Calculate beta
            covariance = np.cov(period_returns, bench_period_returns)[0, 1] if len(period_returns) > 1 else 0
            benchmark_variance = np.var(bench_period_returns, ddof=1) if len(bench_period_returns) > 1 else 0
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            
            # Calculate alpha (Jensen's alpha)
            benchmark_annualized_return = (1 + bench_total_return) ** (1 / years) - 1 if years > 0 else 0
            expected_return = risk_free_rate + beta * (benchmark_annualized_return - risk_free_rate)
            alpha = annualized_return - expected_return
            
            # Calculate information ratio
            tracking_error = np.std(period_returns - bench_period_returns, ddof=1) if len(period_returns) > 1 else 0
            information_ratio = (annualized_return - benchmark_annualized_return) / (tracking_error * np.sqrt(periods_per_year)) if tracking_error > 0 else 0
            
            benchmark_stats = {
                'beta': beta,
                'alpha': alpha,
                'information_ratio': information_ratio,
                'tracking_error': tracking_error * np.sqrt(periods_per_year),
                'benchmark_return': bench_total_return,
                'benchmark_annualized_return': benchmark_annualized_return
            }
        
        # Combine all statistics
        stats = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': annualized_volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'drawdown_start': dd_start,
            'drawdown_end': dd_end,
            'drawdown_length': dd_end - dd_start if dd_end > dd_start else 0
        }
        
        # Add benchmark stats if available
        if benchmark_stats:
            stats.update(benchmark_stats)
        
        return stats