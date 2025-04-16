# Trading Agent Model
# This module implements the reinforcement learning agent for trading

import os
import numpy as np
import torch
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from typing import Dict, List, Tuple, Optional, Union, Any

class TradingAgent:
    """Trading agent based on reinforcement learning.
    
    This class implements a trading agent that uses reinforcement learning
    algorithms from stable-baselines3 to make trading decisions.
    """
    
    def __init__(self, 
                 env,
                 algorithm: str = 'ppo',
                 policy: str = 'MlpPolicy',
                 model_params: Dict[str, Any] = None,
                 tensorboard_log: str = './tensorboard_logs/'):
        """Initialize the trading agent.
        
        Args:
            env: The trading environment
            algorithm: RL algorithm to use ('ppo', 'a2c', or 'dqn')
            policy: Policy network architecture
            model_params: Parameters for the RL algorithm
            tensorboard_log: Directory for tensorboard logs
        """
        self.env = env
        self.algorithm = algorithm.lower()
        self.policy = policy
        self.model_params = model_params or {}
        self.tensorboard_log = tensorboard_log
        
        # Create the model directory if it doesn't exist
        os.makedirs('./models', exist_ok=True)
        os.makedirs(tensorboard_log, exist_ok=True)
        
        # Initialize the model
        self.model = self._create_model()
    
    def _create_model(self):
        """Create the RL model based on the specified algorithm."""
        # Set up default parameters if not provided
        if 'verbose' not in self.model_params:
            self.model_params['verbose'] = 1
            
        if 'tensorboard_log' not in self.model_params:
            self.model_params['tensorboard_log'] = self.tensorboard_log
        
        # Create the appropriate model based on the algorithm
        if self.algorithm == 'ppo':
            model = PPO(self.policy, self.env, **self.model_params)
        elif self.algorithm == 'a2c':
            model = A2C(self.policy, self.env, **self.model_params)
        elif self.algorithm == 'dqn':
            model = DQN(self.policy, self.env, **self.model_params)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}. Choose from 'ppo', 'a2c', or 'dqn'.")
        
        return model
    
    def train(self, 
              total_timesteps: int = 100000, 
              eval_freq: int = 10000,
              save_freq: int = 10000,
              log_dir: str = './logs/',
              save_dir: str = './models/'):
        """Train the agent.
        
        Args:
            total_timesteps: Total number of timesteps to train for
            eval_freq: Frequency of evaluation during training
            save_freq: Frequency of saving model checkpoints
            log_dir: Directory to save logs
            save_dir: Directory to save model checkpoints
        
        Returns:
            Trained model
        """
        # Create directories if they don't exist
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(save_dir, exist_ok=True)
        
        # Set up callbacks
        checkpoint_callback = CheckpointCallback(
            save_freq=save_freq,
            save_path=save_dir,
            name_prefix=f"trading_{self.algorithm}"
        )
        
        # Train the model
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=checkpoint_callback
        )
        
        # Save the final model
        final_model_path = os.path.join(save_dir, f"trading_{self.algorithm}_final")
        self.model.save(final_model_path)
        
        return self.model
    
    def evaluate(self, n_eval_episodes: int = 10) -> Tuple[float, float]:
        """Evaluate the agent's performance.
        
        Args:
            n_eval_episodes: Number of episodes to evaluate
            
        Returns:
            Mean reward and standard deviation
        """
        mean_reward, std_reward = evaluate_policy(
            self.model,
            self.env,
            n_eval_episodes=n_eval_episodes
        )
        
        print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")
        return mean_reward, std_reward
    
    def predict(self, observation) -> Tuple[int, Dict]:
        """Make a prediction for a single observation.
        
        Args:
            observation: The environment observation
            
        Returns:
            Action and action probabilities
        """
        action, _states = self.model.predict(observation, deterministic=True)
        return action, _states
    
    def save(self, path: str) -> None:
        """Save the model to disk.
        
        Args:
            path: Path to save the model
        """
        self.model.save(path)
        print(f"Model saved to {path}")
    
    def load(self, path: str) -> None:
        """Load a model from disk.
        
        Args:
            path: Path to the saved model
        """
        if self.algorithm == 'ppo':
            self.model = PPO.load(path, env=self.env)
        elif self.algorithm == 'a2c':
            self.model = A2C.load(path, env=self.env)
        elif self.algorithm == 'dqn':
            self.model = DQN.load(path, env=self.env)
        
        print(f"Model loaded from {path}")


class TrainingCallback(BaseCallback):
    """Custom callback for tracking training progress."""
    
    def __init__(self, verbose=0):
        super(TrainingCallback, self).__init__(verbose)
        self.rewards = []
        self.portfolio_values = []
    
    def _on_step(self) -> bool:
        """Called after each step in the environment."""
        # Extract info from the environment
        info = self.locals.get('infos')[0]
        if info and 'portfolio_value' in info:
            self.portfolio_values.append(info['portfolio_value'])
        
        # Extract reward
        reward = self.locals.get('rewards')[0]
        self.rewards.append(reward)
        
        return True