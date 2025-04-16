# Trading Environment Module
# This module implements a Gym-compatible trading environment for RL agents

import gym
import numpy as np
import pandas as pd
from gym import spaces
from typing import Dict, List, Tuple, Optional

class TradingEnvironment(gym.Env):
    """A trading environment for reinforcement learning agents.
    
    This environment simulates a trading scenario where an agent can buy, sell, or hold
    financial instruments based on market data observations.
    """
    
    metadata = {'render.modes': ['human']}
    
    def __init__(self, 
                 data: pd.DataFrame, 
                 initial_balance: float = 10000.0,
                 transaction_fee_percent: float = 0.001,
                 reward_scaling: float = 0.01,
                 window_size: int = 20):
        """Initialize the trading environment.
        
        Args:
            data: DataFrame containing OHLCV data for the asset
            initial_balance: Starting account balance
            transaction_fee_percent: Fee applied to transactions as a percentage
            reward_scaling: Scaling factor for rewards
            window_size: Number of past observations to include in state
        """
        super(TradingEnvironment, self).__init__()
        
        self.data = data
        self.initial_balance = initial_balance
        self.transaction_fee_percent = transaction_fee_percent
        self.reward_scaling = reward_scaling
        self.window_size = window_size
        
        # Define action and observation spaces
        # Actions: 0 = Hold, 1 = Buy, 2 = Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: price data + account info
        # Each price data point includes OHLCV + technical indicators
        # Account info includes current balance, holdings, and unrealized PnL
        features_per_timestep = data.shape[1]  # OHLCV + any technical indicators
        account_features = 3  # balance, holdings, unrealized PnL
        
        obs_shape = (window_size * features_per_timestep) + account_features
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_shape,), dtype=np.float32
        )
        
        # Initialize state variables
        self.reset()
    
    def reset(self):
        """Reset the environment to initial state."""
        self.current_step = self.window_size
        self.balance = self.initial_balance
        self.holdings = 0
        self.trades = []
        self.total_reward = 0
        self.done = False
        
        return self._get_observation()
    
    def step(self, action):
        """Take a step in the environment based on the action.
        
        Args:
            action: 0 = Hold, 1 = Buy, 2 = Sell
            
        Returns:
            observation, reward, done, info
        """
        if self.done:
            return self._get_observation(), 0, True, {}
        
        # Get current price
        current_price = self.data.iloc[self.current_step]['close']
        
        # Execute action
        reward = 0
        info = {}
        
        if action == 1:  # Buy
            if self.balance > 0:
                # Calculate max shares we can buy
                max_shares = self.balance / (current_price * (1 + self.transaction_fee_percent))
                shares_to_buy = max_shares  # Buy all we can
                
                # Update balance and holdings
                cost = shares_to_buy * current_price
                fee = cost * self.transaction_fee_percent
                self.balance -= (cost + fee)
                self.holdings += shares_to_buy
                
                # Record trade
                self.trades.append({
                    'step': self.current_step,
                    'type': 'buy',
                    'price': current_price,
                    'shares': shares_to_buy,
                    'cost': cost,
                    'fee': fee
                })
                
                info['trade'] = 'buy'
                
        elif action == 2:  # Sell
            if self.holdings > 0:
                # Sell all holdings
                shares_to_sell = self.holdings
                
                # Update balance and holdings
                revenue = shares_to_sell * current_price
                fee = revenue * self.transaction_fee_percent
                self.balance += (revenue - fee)
                self.holdings = 0
                
                # Record trade
                self.trades.append({
                    'step': self.current_step,
                    'type': 'sell',
                    'price': current_price,
                    'shares': shares_to_sell,
                    'revenue': revenue,
                    'fee': fee
                })
                
                info['trade'] = 'sell'
        
        # Calculate portfolio value and reward
        portfolio_value = self.balance + (self.holdings * current_price)
        prev_portfolio_value = self.balance + (self.holdings * self.data.iloc[self.current_step-1]['close'])
        
        # Reward is change in portfolio value
        reward = ((portfolio_value / prev_portfolio_value) - 1) * self.reward_scaling
        
        # Update state
        self.current_step += 1
        self.total_reward += reward
        
        # Check if episode is done
        if self.current_step >= len(self.data) - 1:
            self.done = True
            
            # Sell all holdings at the end
            if self.holdings > 0:
                final_price = self.data.iloc[self.current_step]['close']
                revenue = self.holdings * final_price
                fee = revenue * self.transaction_fee_percent
                self.balance += (revenue - fee)
                self.holdings = 0
        
        # Add additional info
        info['portfolio_value'] = portfolio_value
        info['balance'] = self.balance
        info['holdings'] = self.holdings
        info['current_price'] = current_price
        
        return self._get_observation(), reward, self.done, info
    
    def _get_observation(self):
        """Construct the observation from current state."""
        # Get window of price data
        obs_window = self.data.iloc[self.current_step - self.window_size:self.current_step]
        price_obs = obs_window.values.flatten()
        
        # Get account state
        current_price = self.data.iloc[self.current_step]['close']
        holdings_value = self.holdings * current_price
        unrealized_pnl = holdings_value - sum([t['cost'] for t in self.trades if t['type'] == 'buy']) \
                         + sum([t['revenue'] for t in self.trades if t['type'] == 'sell'])
        
        account_obs = np.array([self.balance, self.holdings, unrealized_pnl])
        
        # Combine observations
        obs = np.concatenate([price_obs, account_obs])
        
        return obs.astype(np.float32)
    
    def render(self, mode='human'):
        """Render the environment."""
        if mode != 'human':
            raise NotImplementedError(f"Render mode {mode} not supported")
        
        current_price = self.data.iloc[self.current_step]['close']
        portfolio_value = self.balance + (self.holdings * current_price)
        
        print(f"Step: {self.current_step}")
        print(f"Price: ${current_price:.2f}")
        print(f"Balance: ${self.balance:.2f}")
        print(f"Holdings: {self.holdings:.6f}")
        print(f"Portfolio Value: ${portfolio_value:.2f}")
        print(f"Total Reward: {self.total_reward:.4f}")
        print("---")
    
    def close(self):
        """Clean up resources."""
        pass