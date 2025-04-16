# Trading Agent Trainer
# This module implements the training pipeline for the trading agent

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime

# Import local modules
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from trading_agent.environments.trading_env import TradingEnvironment
from trading_agent.models.agent import TradingAgent, TrainingCallback
from data_processing.connectors.market_data import get_data_connector
from data_processing.processors.feature_engineering import FeatureEngineer, DataNormalizer

class TradingAgentTrainer:
    """Training pipeline for the trading agent.
    
    This class orchestrates the training process for the trading agent,
    including data preparation, environment setup, and model training.
    """
    
    def __init__(self, 
                 symbols: List[str],
                 start_date: str,
                 end_date: str,
                 data_source: str = 'yahoo',
                 interval: str = '1d',
                 test_ratio: float = 0.2,
                 include_indicators: bool = True,
                 normalize_data: bool = True,
                 initial_balance: float = 10000.0,
                 transaction_fee_percent: float = 0.001,
                 window_size: int = 20,
                 algorithm: str = 'ppo',
                 model_params: Dict[str, Any] = None):
        """Initialize the trainer.
        
        Args:
            symbols: List of ticker symbols to train on
            start_date: Start date for historical data (YYYY-MM-DD)
            end_date: End date for historical data (YYYY-MM-DD)
            data_source: Source for market data ('yahoo' or 'alpha_vantage')
            interval: Data interval ('1d', '1h', etc.)
            test_ratio: Ratio of data to use for testing
            include_indicators: Whether to include technical indicators
            normalize_data: Whether to normalize the data
            initial_balance: Initial account balance for the environment
            transaction_fee_percent: Transaction fee percentage
            window_size: Number of past observations to include in state
            algorithm: RL algorithm to use ('ppo', 'a2c', or 'dqn')
            model_params: Parameters for the RL algorithm
        """
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.data_source = data_source
        self.interval = interval
        self.test_ratio = test_ratio
        self.include_indicators = include_indicators
        self.normalize_data = normalize_data
        self.initial_balance = initial_balance
        self.transaction_fee_percent = transaction_fee_percent
        self.window_size = window_size
        self.algorithm = algorithm
        self.model_params = model_params or {}
        
        # Initialize components
        self.data_connector = get_data_connector(source=data_source)
        self.feature_engineer = FeatureEngineer(include_indicators=include_indicators)
        self.normalizer = DataNormalizer(method='minmax') if normalize_data else None
        
        # Placeholders for data and environments
        self.data = {}
        self.train_data = {}
        self.test_data = {}
        self.train_env = None
        self.test_env = None
        self.agent = None
    
    def prepare_data(self) -> None:
        """Prepare data for training and testing."""
        for symbol in self.symbols:
            print(f"Fetching data for {symbol}...")
            # Get historical data
            raw_data = self.data_connector.get_historical_data(
                symbol=symbol,
                start_date=self.start_date,
                end_date=self.end_date,
                interval=self.interval
            )
            
            # Process features
            processed_data = self.feature_engineer.process(raw_data)
            
            # Normalize if requested
            if self.normalize_data and self.normalizer:
                processed_data = self.normalizer.fit_transform(processed_data)
            
            # Split into train and test sets
            split_idx = int(len(processed_data) * (1 - self.test_ratio))
            train_data = processed_data.iloc[:split_idx].copy()
            test_data = processed_data.iloc[split_idx:].copy()
            
            # Store data
            self.data[symbol] = processed_data
            self.train_data[symbol] = train_data
            self.test_data[symbol] = test_data
            
            print(f"Prepared {len(train_data)} training samples and {len(test_data)} testing samples for {symbol}")
    
    def setup_environments(self, symbol: str) -> None:
        """Set up training and testing environments for a symbol.
        
        Args:
            symbol: Ticker symbol to set up environments for
        """
        if symbol not in self.train_data or symbol not in self.test_data:
            raise ValueError(f"Data for {symbol} not prepared. Call prepare_data() first.")
        
        # Create training environment
        self.train_env = TradingEnvironment(
            data=self.train_data[symbol],
            initial_balance=self.initial_balance,
            transaction_fee_percent=self.transaction_fee_percent,
            window_size=self.window_size
        )
        
        # Create testing environment
        self.test_env = TradingEnvironment(
            data=self.test_data[symbol],
            initial_balance=self.initial_balance,
            transaction_fee_percent=self.transaction_fee_percent,
            window_size=self.window_size
        )
        
        print(f"Environments set up for {symbol}")
    
    def train_agent(self, 
                    symbol: str, 
                    total_timesteps: int = 100000,
                    eval_freq: int = 10000,
                    save_freq: int = 10000,
                    log_dir: str = './logs/',
                    save_dir: str = './models/') -> None:
        """Train the agent on a symbol.
        
        Args:
            symbol: Ticker symbol to train on
            total_timesteps: Total number of timesteps to train for
            eval_freq: Frequency of evaluation during training
            save_freq: Frequency of saving model checkpoints
            log_dir: Directory to save logs
            save_dir: Directory to save model checkpoints
        """
        # Set up environments if not already done
        if self.train_env is None or self.test_env is None:
            self.setup_environments(symbol)
        
        # Create the agent
        self.agent = TradingAgent(
            env=self.train_env,
            algorithm=self.algorithm,
            model_params=self.model_params,
            tensorboard_log=os.path.join(log_dir, f"{symbol}_{self.algorithm}")
        )
        
        # Train the agent
        print(f"Training agent on {symbol} for {total_timesteps} timesteps...")
        self.agent.train(
            total_timesteps=total_timesteps,
            eval_freq=eval_freq,
            save_freq=save_freq,
            log_dir=log_dir,
            save_dir=os.path.join(save_dir, symbol)
        )
        
        # Evaluate on test data
        self.evaluate_agent()
    
    def evaluate_agent(self) -> Tuple[float, float]:
        """Evaluate the trained agent on test data.
        
        Returns:
            Mean reward and standard deviation
        """
        if self.agent is None or self.test_env is None:
            raise ValueError("Agent or test environment not initialized")
        
        # Load the agent into the test environment
        self.agent.env = self.test_env
        
        # Evaluate
        mean_reward, std_reward = self.agent.evaluate(n_eval_episodes=10)
        
        print(f"Test evaluation: Mean reward = {mean_reward:.2f} ± {std_reward:.2f}")
        return mean_reward, std_reward
    
    def backtest(self, model_path: Optional[str] = None) -> pd.DataFrame:
        """Backtest a trained model on test data.
        
        Args:
            model_path: Path to a saved model (if None, uses the current agent)
            
        Returns:
            DataFrame with backtest results
        """
        if self.agent is None or self.test_env is None:
            raise ValueError("Agent or test environment not initialized")
        
        # Load model if specified
        if model_path:
            self.agent.load(model_path)
        
        # Set the agent to use the test environment
        self.agent.env = self.test_env
        
        # Reset the environment
        obs = self.test_env.reset()
        
        # Run the backtest
        done = False
        results = []
        
        while not done:
            # Get action from agent
            action, _states = self.agent.predict(obs)
            
            # Take step in environment
            obs, reward, done, info = self.test_env.step(action)
            
            # Record results
            result = {
                'step': self.test_env.current_step,
                'price': info['current_price'],
                'action': action,
                'reward': reward,
                'balance': info['balance'],
                'holdings': info['holdings'],
                'portfolio_value': info['portfolio_value']
            }
            
            if 'trade' in info:
                result['trade'] = info['trade']
            
            results.append(result)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Calculate performance metrics
        initial_value = self.initial_balance
        final_value = results_df['portfolio_value'].iloc[-1]
        total_return = (final_value / initial_value) - 1
        
        # Calculate daily returns
        results_df['daily_return'] = results_df['portfolio_value'].pct_change()
        
        # Calculate annualized return (assuming 252 trading days per year)
        days = len(results_df)
        annualized_return = (1 + total_return) ** (252 / days) - 1
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0)
        sharpe_ratio = np.sqrt(252) * results_df['daily_return'].mean() / results_df['daily_return'].std()
        
        # Calculate maximum drawdown
        results_df['cummax'] = results_df['portfolio_value'].cummax()
        results_df['drawdown'] = (results_df['portfolio_value'] / results_df['cummax']) - 1
        max_drawdown = results_df['drawdown'].min()
        
        # Print performance summary
        print(f"Backtest Results:")
        print(f"Initial Value: ${initial_value:.2f}")
        print(f"Final Value: ${final_value:.2f}")
        print(f"Total Return: {total_return:.2%}")
        print(f"Annualized Return: {annualized_return:.2%}")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"Maximum Drawdown: {max_drawdown:.2%}")
        
        return results_df
    
    def plot_backtest_results(self, results_df: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """Plot backtest results.
        
        Args:
            results_df: DataFrame with backtest results
            save_path: Path to save the plot (if None, displays the plot)
        """
        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1]})
        
        # Plot portfolio value
        ax1.plot(results_df['step'], results_df['portfolio_value'], label='Portfolio Value')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.set_title('Backtest Results')
        ax1.legend()
        ax1.grid(True)
        
        # Plot price with buy/sell markers
        ax2.plot(results_df['step'], results_df['price'], label='Price', color='gray')
        
        # Add buy markers
        buy_points = results_df[results_df['trade'] == 'buy']
        if not buy_points.empty:
            ax2.scatter(buy_points['step'], buy_points['price'], color='green', marker='^', s=100, label='Buy')
        
        # Add sell markers
        sell_points = results_df[results_df['trade'] == 'sell']
        if not sell_points.empty:
            ax2.scatter(sell_points['step'], sell_points['price'], color='red', marker='v', s=100, label='Sell')
        
        ax2.set_ylabel('Price ($)')
        ax2.legend()
        ax2.grid(True)
        
        # Plot drawdown
        ax3.fill_between(results_df['step'], 0, results_df['drawdown'] * 100, color='red', alpha=0.3, label='Drawdown')
        ax3.set_ylabel('Drawdown (%)')
        ax3.set_xlabel('Time Step')
        ax3.legend()
        ax3.grid(True)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
            print(f"Plot saved to {save_path}")
        else:
            plt.show()


def run_training_pipeline(symbols: List[str],
                         start_date: str,
                         end_date: str,
                         data_source: str = 'yahoo',
                         algorithm: str = 'ppo',
                         total_timesteps: int = 100000) -> TradingAgentTrainer:
    """Run the complete training pipeline.
    
    Args:
        symbols: List of ticker symbols to train on
        start_date: Start date for historical data (YYYY-MM-DD)
        end_date: End date for historical data (YYYY-MM-DD)
        data_source: Source for market data ('yahoo' or 'alpha_vantage')
        algorithm: RL algorithm to use ('ppo', 'a2c', or 'dqn')
        total_timesteps: Total number of timesteps to train for
        
    Returns:
        Trained TradingAgentTrainer instance
    """
    # Create timestamp for this training run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create directories for logs and models
    log_dir = f"./logs/{timestamp}"
    model_dir = f"./models/{timestamp}"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    # Initialize trainer
    trainer = TradingAgentTrainer(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        data_source=data_source,
        algorithm=algorithm
    )
    
    # Prepare data
    trainer.prepare_data()
    
    # Train on each symbol
    for symbol in symbols:
        print(f"\nTraining on {symbol}...")
        trainer.setup_environments(symbol)
        trainer.train_agent(
            symbol=symbol,
            total_timesteps=total_timesteps,
            log_dir=log_dir,
            save_dir=model_dir
        )
        
        # Run backtest
        results_df = trainer.backtest()
        
        # Plot results
        plot_path = os.path.join(model_dir, f"{symbol}_backtest_results.png")
        trainer.plot_backtest_results(results_df, save_path=plot_path)
    
    return trainer