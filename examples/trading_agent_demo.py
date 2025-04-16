# Trading Agent Demo
# This script demonstrates the core functionality of the AI Trading Assistant

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import project modules
from trading_agent.environments.trading_env import TradingEnvironment
from trading_agent.models.agent import TradingAgent
from trading_agent.training.trainer import TradingAgentTrainer
from trading_agent.utils.metrics import PerformanceMetrics, RiskManagement, PortfolioAnalytics
from data_processing.connectors.market_data import get_data_connector
from data_processing.processors.feature_engineering import FeatureEngineer, DataNormalizer


def run_demo():
    """Run a demonstration of the AI Trading Assistant."""
    print("\n===== AI Trading Assistant Demo =====\n")
    
    # Set up parameters
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')  # 2 years of data
    
    print(f"Fetching data for {', '.join(symbols)} from {start_date} to {end_date}...\n")
    
    # Create data directory if it doesn't exist
    os.makedirs('./data', exist_ok=True)
    os.makedirs('./models', exist_ok=True)
    os.makedirs('./logs', exist_ok=True)
    
    # 1. Data Collection and Processing
    print("1. Data Collection and Processing")
    print("-" * 30)
    
    # Get data connector
    data_connector = get_data_connector(source='yahoo')
    
    # Fetch and process data for each symbol
    processed_data = {}
    for symbol in symbols:
        print(f"Processing {symbol}...")
        
        # Fetch historical data
        raw_data = data_connector.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval='1d'
        )
        
        # Process features
        feature_engineer = FeatureEngineer(include_indicators=True)
        data = feature_engineer.process(raw_data)
        
        # Normalize data
        normalizer = DataNormalizer(method='minmax')
        normalized_data = normalizer.fit_transform(data)
        
        # Store processed data
        processed_data[symbol] = normalized_data
        
        print(f"  - Processed {len(data)} data points with {data.shape[1]} features")
        
        # Save processed data
        data.to_csv(f"./data/{symbol}_processed.csv", index=False)
    
    print("\nData processing complete!\n")
    
    # 2. Trading Environment Setup
    print("2. Trading Environment Setup")
    print("-" * 30)
    
    # Select a symbol for demonstration
    demo_symbol = symbols[0]
    demo_data = processed_data[demo_symbol]
    
    # Split data into train and test sets
    split_idx = int(len(demo_data) * 0.8)
    train_data = demo_data.iloc[:split_idx].copy()
    test_data = demo_data.iloc[split_idx:].copy()
    
    print(f"Setting up trading environment for {demo_symbol}")
    print(f"  - Training data: {len(train_data)} samples")
    print(f"  - Testing data: {len(test_data)} samples")
    
    # Create trading environment
    env_params = {
        'initial_balance': 10000.0,
        'transaction_fee_percent': 0.001,
        'window_size': 20
    }
    
    train_env = TradingEnvironment(data=train_data, **env_params)
    test_env = TradingEnvironment(data=test_data, **env_params)
    
    print(f"  - Environment created with initial balance: ${env_params['initial_balance']}")
    print(f"  - Transaction fee: {env_params['transaction_fee_percent']*100}%")
    print(f"  - Observation window size: {env_params['window_size']} days")
    
    # 3. Agent Training
    print("\n3. Agent Training")
    print("-" * 30)
    
    # Set up the agent
    algorithm = 'ppo'  # Options: 'ppo', 'a2c', 'dqn'
    model_params = {
        'learning_rate': 0.0003,
        'n_steps': 2048,
        'batch_size': 64,
        'n_epochs': 10,
        'gamma': 0.99,
        'gae_lambda': 0.95,
        'clip_range': 0.2,
        'verbose': 1
    }
    
    print(f"Setting up {algorithm.upper()} trading agent")
    agent = TradingAgent(
        env=train_env,
        algorithm=algorithm,
        model_params=model_params,
        tensorboard_log='./logs/tensorboard/'
    )
    
    # Train the agent (reduced timesteps for demo)
    total_timesteps = 50000  # Reduced for demo purposes
    print(f"Training agent for {total_timesteps} timesteps...")
    print("Note: In a real scenario, training would use 500,000+ timesteps")
    print("Training... (this may take a few minutes)")
    
    agent.train(
        total_timesteps=total_timesteps,
        eval_freq=10000,
        save_freq=10000,
        log_dir='./logs/',
        save_dir='./models/'
    )
    
    print("Agent training complete!")
    
    # 4. Backtesting
    print("\n4. Backtesting")
    print("-" * 30)
    
    print(f"Backtesting trained agent on {demo_symbol} test data")
    
    # Set up trainer for backtesting
    trainer = TradingAgentTrainer(
        symbols=[demo_symbol],
        start_date=start_date,
        end_date=end_date,
        data_source='yahoo'
    )
    
    # Set the agent to use the test environment
    agent.env = test_env
    trainer.agent = agent
    trainer.test_env = test_env
    
    # Run backtest
    backtest_results = trainer.backtest()
    
    # Plot backtest results
    print("\nGenerating backtest visualization...")
    trainer.plot_backtest_results(backtest_results, save_path='./models/backtest_results.png')
    
    # 5. Performance Analysis
    print("\n5. Performance Analysis")
    print("-" * 30)
    
    # Calculate portfolio statistics
    portfolio_values = backtest_results['portfolio_value'].values
    
    # Get benchmark data (using the symbol's price as benchmark)
    benchmark_values = test_data['close'].values * (portfolio_values[0] / test_data['close'].values[0])
    
    # Calculate performance metrics
    stats = PortfolioAnalytics.calculate_portfolio_stats(
        portfolio_values=portfolio_values,
        benchmark_values=benchmark_values,
        risk_free_rate=0.02  # Assuming 2% risk-free rate
    )
    
    # Print performance summary
    print("\nPerformance Summary:")
    print(f"Total Return: {stats['total_return']:.2%}")
    print(f"Annualized Return: {stats['annualized_return']:.2%}")
    print(f"Volatility: {stats['volatility']:.2%}")
    print(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {stats['sortino_ratio']:.2f}")
    print(f"Maximum Drawdown: {stats['max_drawdown']:.2%}")
    print(f"Calmar Ratio: {stats['calmar_ratio']:.2f}")
    
    if 'beta' in stats:
        print(f"\nBenchmark Comparison:")
        print(f"Beta: {stats['beta']:.2f}")
        print(f"Alpha: {stats['alpha']:.2%}")
        print(f"Information Ratio: {stats['information_ratio']:.2f}")
        print(f"Benchmark Return: {stats['benchmark_return']:.2%}")
    
    # 6. Risk Management
    print("\n6. Risk Management")
    print("-" * 30)
    
    # Set up risk management
    risk_manager = RiskManagement(
        max_position_size=0.2,
        max_portfolio_risk=0.02,
        stop_loss_pct=0.03,
        take_profit_pct=0.06
    )
    
    # Calculate position size for a new trade
    current_portfolio_value = portfolio_values[-1]
    current_price = test_data['close'].values[-1]
    current_volatility = test_data['volatility_20d'].values[-1]
    
    position_size = risk_manager.calculate_position_size(
        portfolio_value=current_portfolio_value,
        price=current_price,
        volatility=current_volatility
    )
    
    # Calculate stop loss and take profit levels
    stop_loss = risk_manager.calculate_stop_loss(current_price)
    take_profit = risk_manager.calculate_take_profit(current_price)
    risk_reward = risk_manager.calculate_risk_reward_ratio(current_price, stop_loss, take_profit)
    
    print("Risk Management Example:")
    print(f"Current Portfolio Value: ${current_portfolio_value:.2f}")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Recommended Position Size: {position_size:.2f} shares (${position_size * current_price:.2f})")
    print(f"Stop Loss: ${stop_loss:.2f} ({risk_manager.stop_loss_pct*100:.1f}% below entry)")
    print(f"Take Profit: ${take_profit:.2f} ({risk_manager.take_profit_pct*100:.1f}% above entry)")
    print(f"Risk-Reward Ratio: {risk_reward:.2f}")
    
    print("\n===== Demo Complete =====\n")
    print("The AI Trading Assistant has successfully demonstrated:")
    print("1. Market data collection and processing")
    print("2. Trading environment setup")
    print("3. Reinforcement learning agent training")
    print("4. Strategy backtesting")
    print("5. Performance analysis")
    print("6. Risk management")
    print("\nBacktest results visualization saved to ./models/backtest_results.png")


if __name__ == "__main__":
    run_demo()