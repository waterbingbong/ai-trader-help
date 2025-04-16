# Vercel Adapter for TA-Lib Compatibility
# This module provides alternative implementations for TA-Lib functions using pandas-ta or custom implementations

import pandas as pd
import numpy as np

# Check if ta-lib is available, otherwise use alternatives
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    import ta
    TALIB_AVAILABLE = False
    print("TA-Lib not available, using alternative implementations")

# Technical indicator functions
def SMA(data, timeperiod=30):
    """Simple Moving Average"""
    if TALIB_AVAILABLE:
        return talib.SMA(data, timeperiod=timeperiod)
    else:
        return ta.trend.sma_indicator(pd.Series(data), window=timeperiod)

def EMA(data, timeperiod=30):
    """Exponential Moving Average"""
    if TALIB_AVAILABLE:
        return talib.EMA(data, timeperiod=timeperiod)
    else:
        return ta.trend.ema_indicator(pd.Series(data), window=timeperiod)

def RSI(data, timeperiod=14):
    """Relative Strength Index"""
    if TALIB_AVAILABLE:
        return talib.RSI(data, timeperiod=timeperiod)
    else:
        return ta.momentum.rsi(pd.Series(data), window=timeperiod)

def MACD(data, fastperiod=12, slowperiod=26, signalperiod=9):
    """Moving Average Convergence/Divergence"""
    if TALIB_AVAILABLE:
        macd, signal, hist = talib.MACD(data, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return macd, signal, hist
    else:
        series = pd.Series(data)
        macd = ta.trend.macd(series, window_slow=slowperiod, window_fast=fastperiod)
        signal = ta.trend.macd_signal(series, window_slow=slowperiod, window_fast=fastperiod, window_sign=signalperiod)
        hist = ta.trend.macd_diff(series, window_slow=slowperiod, window_fast=fastperiod, window_sign=signalperiod)
        return macd, signal, hist

def BBANDS(data, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0):
    """Bollinger Bands"""
    if TALIB_AVAILABLE:
        upper, middle, lower = talib.BBANDS(data, timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=matype)
        return upper, middle, lower
    else:
        series = pd.Series(data)
        indicator_bb = ta.volatility.BollingerBands(series, window=timeperiod, window_dev=nbdevup)
        upper = indicator_bb.bollinger_hband()
        middle = indicator_bb.bollinger_mavg()
        lower = indicator_bb.bollinger_lband()
        return upper, middle, lower

# Add more indicator functions as needed