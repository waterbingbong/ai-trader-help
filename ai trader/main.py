# AI Trading Assistant - Main Entry Point
# This script demonstrates how to run the AI Trading Assistant

import os
import sys
import argparse
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set Gemini API key as environment variable (if provided)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDpu_h1aoBZbQDG829NYub_8hMAt144JXk")
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import project modules
from trading_agent.environments.trading_env import TradingEnvironment
from trading_agent.models.agent import TradingAgent
from trading_agent.training.trainer import TradingAgentTrainer, run_training_pipeline
from trading_agent.utils.metrics import PerformanceMetrics, RiskManagement, PortfolioAnalytics
from data_processing.connectors.market_data import get_data_connector
from data_processing.processors.feature_engineering import FeatureEngineer, DataNormalizer
from dashboard.components.performance_dashboard import PerformanceDashboard, TradeAnalyzer
from dashboard.components.trade_monitor import TradeMonitor, AlertSystem
from ai_integration.gemini_integration import GeminiIntegration
from ai_integration.knowledge_base import KnowledgeBase


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AI Trading Assistant")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train a trading agent")
    train_parser.add_argument("--symbols", nargs="+", default=["AAPL"], help="Symbols to train on")
    train_parser.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD)")
    train_parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD)")
    train_parser.add_argument("--algorithm", default="ppo", choices=["ppo", "a2c", "dqn"], help="RL algorithm")
    train_parser.add_argument("--timesteps", type=int, default=100000, help="Training timesteps")
    
    # Backtest command
    backtest_parser = subparsers.add_parser("backtest", help="Backtest a trained model")
    backtest_parser.add_argument("--model-path", required=True, help="Path to trained model")
    backtest_parser.add_argument("--symbol", default="AAPL", help="Symbol to backtest")
    backtest_parser.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD)")
    backtest_parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD)")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Run the dashboard")
    dashboard_parser.add_argument("--port", type=int, default=8050, help="Dashboard port")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run a demonstration")
    
    # AI command for Gemini integration
    ai_parser = subparsers.add_parser("ai", help="Use AI features with Gemini 2.5")
    ai_subparsers = ai_parser.add_subparsers(dest="ai_command", help="AI command to run")
    
    # AI analyze command
    analyze_parser = ai_subparsers.add_parser("analyze", help="Analyze data with Gemini 2.5")
    analyze_parser.add_argument("--symbol", required=True, help="Symbol to analyze")
    analyze_parser.add_argument("--days", type=int, default=30, help="Number of days of data to analyze")
    
    # AI knowledge base commands
    kb_parser = ai_subparsers.add_parser("kb", help="Manage knowledge base")
    kb_subparsers = kb_parser.add_subparsers(dest="kb_command", help="Knowledge base command")
    
    # Add to knowledge base
    kb_add_parser = kb_subparsers.add_parser("add", help="Add to knowledge base")
    kb_add_parser.add_argument("--type", choices=["text", "file", "image", "video"], default="text", help="Type of content to add")
    kb_add_parser.add_argument("--content", help="Content or file path to add")
    kb_add_parser.add_argument("--category", default=None, help="Category to add content to")
    
    # List knowledge base
    kb_list_parser = kb_subparsers.add_parser("list", help="List knowledge base items")
    kb_list_parser.add_argument("--category", default=None, help="Category to list")
    
    # Search knowledge base
    kb_search_parser = kb_subparsers.add_parser("search", help="Search knowledge base")
    kb_search_parser.add_argument("--query", required=True, help="Search query")
    
    # Delete from knowledge base
    kb_delete_parser = kb_subparsers.add_parser("delete", help="Delete from knowledge base")
    kb_delete_parser.add_argument("--id", help="ID of item to delete")
    kb_delete_parser.add_argument("--category", help="Category to clear")
    
    return parser.parse_args()


def run_training(args):
    """Run the training pipeline."""
    print("\n===== AI Trading Assistant - Training =====\n")
    
    # Set up date range
    if args.end_date is None:
        args.end_date = datetime.now().strftime("%Y-%m-%d")
    
    if args.start_date is None:
        # Default to 2 years of data
        args.start_date = (datetime.strptime(args.end_date, "%Y-%m-%d") - timedelta(days=365*2)).strftime("%Y-%m-%d")
    
    print(f"Training on symbols: {', '.join(args.symbols)}")
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Algorithm: {args.algorithm.upper()}")
    print(f"Training timesteps: {args.timesteps}")
    print("\nStarting training pipeline...\n")
    
    # Run the training pipeline
    trainer = run_training_pipeline(
        symbols=args.symbols,
        start_date=args.start_date,
        end_date=args.end_date,
        algorithm=args.algorithm,
        total_timesteps=args.timesteps
    )
    
    print("\n===== Training Complete =====\n")
    print("The AI Trading Assistant has successfully trained models for the specified symbols.")
    print("Backtest results and model files are saved in the ./models directory.")


def run_backtest(args):
    """Run backtesting on a trained model."""
    print("\n===== AI Trading Assistant - Backtesting =====\n")
    
    # Set up date range
    if args.end_date is None:
        args.end_date = datetime.now().strftime("%Y-%m-%d")
    
    if args.start_date is None:
        # Default to 1 year of data
        args.start_date = (datetime.strptime(args.end_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
    
    print(f"Backtesting model: {args.model_path}")
    print(f"Symbol: {args.symbol}")
    print(f"Date range: {args.start_date} to {args.end_date}")
    print("\nPreparing data...")
    
    # Get data
    data_connector = get_data_connector(source="yahoo")
    raw_data = data_connector.get_historical_data(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        interval="1d"
    )
    
    # Process features
    feature_engineer = FeatureEngineer(include_indicators=True)
    processed_data = feature_engineer.process(raw_data)
    
    # Normalize data
    normalizer = DataNormalizer(method="minmax")
    normalized_data = normalizer.fit_transform(processed_data)
    
    print(f"Processed {len(normalized_data)} data points with {normalized_data.shape[1]} features")
    
    # Create environment
    env = TradingEnvironment(
        data=normalized_data,
        initial_balance=10000.0,
        transaction_fee_percent=0.001,
        window_size=20
    )
    
    # Create agent and load model
    # Determine algorithm from model path
    if "ppo" in args.model_path.lower():
        algorithm = "ppo"
    elif "a2c" in args.model_path.lower():
        algorithm = "a2c"
    elif "dqn" in args.model_path.lower():
        algorithm = "dqn"
    else:
        algorithm = "ppo"  # Default
    
    print(f"Loading {algorithm.upper()} model from {args.model_path}")
    agent = TradingAgent(env=env, algorithm=algorithm)
    agent.load(args.model_path)
    
    # Create trainer for backtesting
    trainer = TradingAgentTrainer(
        symbols=[args.symbol],
        start_date=args.start_date,
        end_date=args.end_date,
        data_source="yahoo"
    )
    trainer.agent = agent
    trainer.test_env = env
    
    # Run backtest
    print("\nRunning backtest...")
    results_df = trainer.backtest()
    
    # Plot results
    plot_path = os.path.join(os.path.dirname(args.model_path), f"{args.symbol}_backtest_results.png")
    trainer.plot_backtest_results(results_df, save_path=plot_path)
    
    print("\n===== Backtesting Complete =====\n")
    print(f"Backtest results visualization saved to {plot_path}")


def run_dashboard(args):
    """Run the dashboard application."""
    print("\n===== AI Trading Assistant - Dashboard =====\n")
    print(f"Starting dashboard on port {args.port}...")
    
    # Import dashboard app
    from dashboard.app import app, server
    
    # Run the dashboard
    app.run_server(debug=True, port=args.port)


def run_demo():
    """Run a demonstration of the AI Trading Assistant."""
    print("\n===== AI Trading Assistant - Demo =====\n")
    print("Running trading agent demonstration...")
    
    # Import and run the demo
    from examples.trading_agent_demo import run_demo
    run_demo()


def run_ai_analyze(args):
    """Run AI analysis using Gemini 2.5."""
    print("\n===== AI Trading Assistant - Gemini 2.5 Analysis =====\n")
    print(f"Analyzing symbol: {args.symbol}")
    print(f"Data period: {args.days} days")
    
    # Get data for analysis
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    
    print(f"Fetching data from {start_date} to {end_date}...")
    data_connector = get_data_connector(source="yahoo")
    raw_data = data_connector.get_historical_data(
        symbol=args.symbol,
        start_date=start_date,
        end_date=end_date,
        interval="1d"
    )
    
    # Process features
    feature_engineer = FeatureEngineer(include_indicators=True)
    processed_data = feature_engineer.process(raw_data)
    
    # Initialize Gemini integration
    gemini = GeminiIntegration()
    
    # Prepare data for analysis
    data_dict = {
        "price_data": processed_data.tail(10).to_dict(),
        "indicators": {
            col: processed_data[col].tolist() for col in processed_data.columns 
            if col not in ['open', 'high', 'low', 'close', 'volume']
        }
    }
    
    print("\nSending data to Gemini 2.5 for analysis...")
    insights = gemini.get_trading_insights(
        symbol=args.symbol,
        data=data_dict,
        context=f"Analyze trading data for {args.symbol} from {start_date} to {end_date}"
    )
    
    if "error" in insights:
        print(f"\nError: {insights['error']}")
    else:
        print("\n===== Gemini 2.5 Trading Insights =====\n")
        print(insights["insights"])
        print("\n=======================================")


def run_knowledge_base(args):
    """Run knowledge base operations."""
    kb = KnowledgeBase()
    
    if args.kb_command == "add":
        print("\n===== Adding to Knowledge Base =====\n")
        
        if args.type == "text":
            if not args.content:
                args.content = input("Enter text to add to knowledge base: ")
            item_id = kb.add_text(args.content, category=args.category)
            if item_id:
                print(f"Added text to knowledge base with ID: {item_id}")
        else:  # file, image, video
            if not args.content:
                args.content = input(f"Enter path to {args.type} file: ")
            item_id = kb.add_file(args.content, category=args.category)
            if item_id:
                print(f"Added {args.type} to knowledge base with ID: {item_id}")
    
    elif args.kb_command == "list":
        print("\n===== Knowledge Base Contents =====\n")
        
        if args.category:
            items = kb.get_items_by_category(args.category)
            print(f"Category: {args.category} ({len(items)} items)")
        else:
            categories = kb.get_all_categories()
            for category in categories:
                items = kb.get_items_by_category(category)
                print(f"Category: {category} ({len(items)} items)")
                
                # Show first 5 items in each category
                for i, item in enumerate(items[:5]):
                    print(f"  {i+1}. ID: {item['id']}")
                    if isinstance(item['content'], str) and len(item['content']) > 50:
                        print(f"     Content: {item['content'][:50]}...")
                    else:
                        print(f"     Content: {item['content']}")
                    print(f"     Added: {item['added_at']}")
                
                if len(items) > 5:
                    print(f"  ... and {len(items) - 5} more items")
    
    elif args.kb_command == "search":
        print(f"\n===== Searching Knowledge Base for '{args.query}' =====\n")
        results = kb.search(args.query)
        print(f"Found {len(results)} matching items:")
        
        for i, item in enumerate(results):
            print(f"\n{i+1}. ID: {item['id']}")
            if isinstance(item['content'], str) and len(item['content']) > 100:
                print(f"Content: {item['content'][:100]}...")
            else:
                print(f"Content: {item['content']}")
            print(f"Added: {item['added_at']}")
            if item['metadata']:
                print(f"Metadata: {item['metadata']}")
    
    elif args.kb_command == "delete":
        print("\n===== Deleting from Knowledge Base =====\n")
        
        if args.id:
            success = kb.delete_item(args.id)
            if success:
                print(f"Successfully deleted item {args.id}")
            else:
                print(f"Failed to delete item {args.id}")
        elif args.category:
            success = kb.clear_category(args.category)
            if success:
                print(f"Successfully cleared category {args.category}")
            else:
                print(f"Failed to clear category {args.category}")
        else:
            print("Error: Must specify either --id or --category")
    
    else:
        print("Please specify a knowledge base command. Use --help for more information.")


def run_ai(args):
    """Run AI-related commands."""
    if args.ai_command == "analyze":
        run_ai_analyze(args)
    elif args.ai_command == "kb":
        run_knowledge_base(args)
    else:
        print("Please specify an AI command. Use --help for more information.")
        print("Available AI commands: analyze, kb")


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Run the appropriate command
    if args.command == "train":
        run_training(args)
    elif args.command == "backtest":
        run_backtest(args)
    elif args.command == "dashboard":
        run_dashboard(args)
    elif args.command == "demo":
        run_demo()
    elif args.command == "ai":
        run_ai(args)
    else:
        # If no command is specified, show help
        print("Please specify a command. Use --help for more information.")
        print("Available commands: train, backtest, dashboard, demo, ai")


if __name__ == "__main__":
    main()