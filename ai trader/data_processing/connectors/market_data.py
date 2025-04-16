# Market Data Connector
# This module provides interfaces to fetch market data from various sources

import pandas as pd
import numpy as np
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from typing import Dict, List, Tuple, Optional, Union
import os
from datetime import datetime, timedelta

class MarketDataConnector:
    """Base class for market data connectors."""
    
    def __init__(self):
        pass
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str) -> pd.DataFrame:
        """Get historical market data for a symbol.
        
        Args:
            symbol: The ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval (e.g., '1d', '1h')
            
        Returns:
            DataFrame with historical data
        """
        raise NotImplementedError("Subclasses must implement this method")


class YahooFinanceConnector(MarketDataConnector):
    """Connector for Yahoo Finance data."""
    
    def __init__(self):
        super().__init__()
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = '1d') -> pd.DataFrame:
        """Get historical market data from Yahoo Finance.
        
        Args:
            symbol: The ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval ('1d', '1h', '1m', etc.)
            
        Returns:
            DataFrame with historical data
        """
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        
        # Ensure the dataframe has the expected columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column {col} not found in Yahoo Finance data")
        
        # Rename columns to lowercase for consistency
        df.columns = [col.lower() for col in df.columns]
        
        # Reset index to make date a column
        df.reset_index(inplace=True)
        if 'date' not in df.columns and 'datetime' in df.columns:
            df.rename(columns={'datetime': 'date'}, inplace=True)
        
        return df
    
    def get_latest_data(self, symbol: str) -> pd.DataFrame:
        """Get the latest available data for a symbol.
        
        Args:
            symbol: The ticker symbol
            
        Returns:
            DataFrame with the latest data
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        df = self.get_historical_data(symbol, start_date, end_date, '1d')
        return df.tail(1)


class AlphaVantageConnector(MarketDataConnector):
    """Connector for Alpha Vantage data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Alpha Vantage connector.
        
        Args:
            api_key: Alpha Vantage API key (if None, will look for ALPHA_VANTAGE_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.environ.get('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required. Set it as an argument or as ALPHA_VANTAGE_API_KEY environment variable.")
        
        self.ts = TimeSeries(key=self.api_key, output_format='pandas')
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = 'daily') -> pd.DataFrame:
        """Get historical market data from Alpha Vantage.
        
        Args:
            symbol: The ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval ('daily', 'weekly', 'monthly', 'intraday')
            
        Returns:
            DataFrame with historical data
        """
        # Map interval to Alpha Vantage function
        if interval == 'daily':
            data, meta_data = self.ts.get_daily_adjusted(symbol=symbol, outputsize='full')
        elif interval == 'weekly':
            data, meta_data = self.ts.get_weekly_adjusted(symbol=symbol)
        elif interval == 'monthly':
            data, meta_data = self.ts.get_monthly_adjusted(symbol=symbol)
        elif 'intraday' in interval:
            # Extract interval from string like 'intraday_1min'
            intraday_interval = interval.split('_')[1] if '_' in interval else '5min'
            data, meta_data = self.ts.get_intraday(symbol=symbol, interval=intraday_interval, outputsize='full')
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        # Rename columns for consistency
        column_map = {
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. adjusted close': 'adjusted_close',
            '6. volume': 'volume',
            '7. dividend amount': 'dividend',
            '8. split coefficient': 'split_coefficient'
        }
        
        data.rename(columns=column_map, inplace=True)
        
        # Filter by date range
        data = data.loc[start_date:end_date]
        
        # Reset index to make date a column
        data.reset_index(inplace=True)
        data.rename(columns={'index': 'date'}, inplace=True)
        
        return data


def get_data_connector(source: str = 'yahoo', **kwargs) -> MarketDataConnector:
    """Factory function to get the appropriate data connector.
    
    Args:
        source: Data source ('yahoo' or 'alpha_vantage')
        **kwargs: Additional arguments for the connector
        
    Returns:
        MarketDataConnector instance
    """
    if source.lower() == 'yahoo':
        return YahooFinanceConnector()
    elif source.lower() == 'alpha_vantage':
        return AlphaVantageConnector(**kwargs)
    else:
        raise ValueError(f"Unsupported data source: {source}")