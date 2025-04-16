# Feature Engineering Module
# This module transforms raw market data into features for the trading agent

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import talib as ta

class FeatureEngineer:
    """Feature engineering for market data.
    
    This class transforms raw market data into features that can be used
    by the trading agent, including technical indicators and other derived features.
    """
    
    def __init__(self, include_indicators: bool = True):
        """Initialize the feature engineer.
        
        Args:
            include_indicators: Whether to include technical indicators
        """
        self.include_indicators = include_indicators
    
    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process raw market data into features.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added features
        """
        # Make a copy to avoid modifying the original data
        df = data.copy()
        
        # Ensure we have the required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column {col} not found in data")
        
        # Add basic price features
        df = self._add_price_features(df)
        
        # Add technical indicators if requested
        if self.include_indicators:
            df = self._add_technical_indicators(df)
        
        # Fill any NaN values that might have been introduced
        df.fillna(method='ffill', inplace=True)
        df.fillna(method='bfill', inplace=True)
        
        # Drop any remaining NaN rows
        df.dropna(inplace=True)
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic price-derived features.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added price features
        """
        # Calculate returns
        df['daily_return'] = df['close'].pct_change()
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
        
        # Calculate price ranges
        df['high_low_range'] = df['high'] - df['low']
        df['close_open_range'] = df['close'] - df['open']
        
        # Normalized price
        df['normalized_price'] = df['close'] / df['close'].iloc[0] if len(df) > 0 else 1.0
        
        # Volatility (rolling standard deviation of returns)
        df['volatility_5d'] = df['daily_return'].rolling(window=5).std()
        df['volatility_20d'] = df['daily_return'].rolling(window=20).std()
        
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators as features.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added technical indicators
        """
        # Moving averages
        df['sma_5'] = ta.SMA(df['close'], timeperiod=5)
        df['sma_20'] = ta.SMA(df['close'], timeperiod=20)
        df['sma_50'] = ta.SMA(df['close'], timeperiod=50)
        df['sma_200'] = ta.SMA(df['close'], timeperiod=200)
        
        # Exponential moving averages
        df['ema_5'] = ta.EMA(df['close'], timeperiod=5)
        df['ema_20'] = ta.EMA(df['close'], timeperiod=20)
        
        # MACD
        macd, macd_signal, macd_hist = ta.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        
        # RSI
        df['rsi_14'] = ta.RSI(df['close'], timeperiod=14)
        
        # Bollinger Bands
        upper, middle, lower = ta.BBANDS(
            df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        
        # Stochastic Oscillator
        slowk, slowd = ta.STOCH(
            df['high'], df['low'], df['close'],
            fastk_period=5, slowk_period=3, slowk_matype=0,
            slowd_period=3, slowd_matype=0
        )
        df['stoch_k'] = slowk
        df['stoch_d'] = slowd
        
        # Average True Range (ATR)
        df['atr'] = ta.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # On-Balance Volume (OBV)
        df['obv'] = ta.OBV(df['close'], df['volume'])
        
        # Commodity Channel Index (CCI)
        df['cci'] = ta.CCI(df['high'], df['low'], df['close'], timeperiod=14)
        
        # Relative price position
        df['price_sma_ratio_20'] = df['close'] / df['sma_20']
        df['price_sma_ratio_50'] = df['close'] / df['sma_50']
        
        # Moving average crossovers
        df['sma_5_20_cross'] = (df['sma_5'] > df['sma_20']).astype(int)
        df['sma_20_50_cross'] = (df['sma_20'] > df['sma_50']).astype(int)
        
        return df


class DataNormalizer:
    """Normalize data for machine learning models."""
    
    def __init__(self, method: str = 'minmax'):
        """Initialize the data normalizer.
        
        Args:
            method: Normalization method ('minmax', 'zscore', or 'robust')
        """
        self.method = method
        self.stats = {}
    
    def fit(self, data: pd.DataFrame) -> None:
        """Fit the normalizer to the data.
        
        Args:
            data: DataFrame to fit the normalizer to
        """
        self.stats = {}
        
        for column in data.columns:
            if self.method == 'minmax':
                self.stats[column] = {
                    'min': data[column].min(),
                    'max': data[column].max()
                }
            elif self.method == 'zscore':
                self.stats[column] = {
                    'mean': data[column].mean(),
                    'std': data[column].std()
                }
            elif self.method == 'robust':
                self.stats[column] = {
                    'median': data[column].median(),
                    'iqr': data[column].quantile(0.75) - data[column].quantile(0.25)
                }
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform the data using the fitted normalizer.
        
        Args:
            data: DataFrame to normalize
            
        Returns:
            Normalized DataFrame
        """
        if not self.stats:
            raise ValueError("Normalizer has not been fitted. Call fit() first.")
        
        df = data.copy()
        
        for column in df.columns:
            if column in self.stats:
                if self.method == 'minmax':
                    min_val = self.stats[column]['min']
                    max_val = self.stats[column]['max']
                    if max_val > min_val:  # Avoid division by zero
                        df[column] = (df[column] - min_val) / (max_val - min_val)
                elif self.method == 'zscore':
                    mean = self.stats[column]['mean']
                    std = self.stats[column]['std']
                    if std > 0:  # Avoid division by zero
                        df[column] = (df[column] - mean) / std
                elif self.method == 'robust':
                    median = self.stats[column]['median']
                    iqr = self.stats[column]['iqr']
                    if iqr > 0:  # Avoid division by zero
                        df[column] = (df[column] - median) / iqr
        
        return df
    
    def fit_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Fit the normalizer to the data and transform it.
        
        Args:
            data: DataFrame to fit and transform
            
        Returns:
            Normalized DataFrame
        """
        self.fit(data)
        return self.transform(data)
    
    def inverse_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Inverse transform normalized data back to original scale.
        
        Args:
            data: Normalized DataFrame
            
        Returns:
            DataFrame in original scale
        """
        if not self.stats:
            raise ValueError("Normalizer has not been fitted. Call fit() first.")
        
        df = data.copy()
        
        for column in df.columns:
            if column in self.stats:
                if self.method == 'minmax':
                    min_val = self.stats[column]['min']
                    max_val = self.stats[column]['max']
                    df[column] = df[column] * (max_val - min_val) + min_val
                elif self.method == 'zscore':
                    mean = self.stats[column]['mean']
                    std = self.stats[column]['std']
                    df[column] = df[column] * std + mean
                elif self.method == 'robust':
                    median = self.stats[column]['median']
                    iqr = self.stats[column]['iqr']
                    df[column] = df[column] * iqr + median
        
        return df