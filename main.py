import time
import yaml
import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

from core.mt5_connector import MT5Connector
from core.execution import Executor
from core.risk import calculate_position_size, check_daily_drawdown
from core.data_feed import DataFeed
from strategy.mean_reversion import MeanReversionStrategy
from services.trade_manager import TradeManager
from services.order_validator import OrderValidator
from utils.logger import setup_logger

# Load Config
with open("config/settings.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

SYMBOL = CONFIG['trading']['symbol']
TIMEFRAME = mt5.TIMEFRAME_M5
MAGIC = CONFIG['project']['magic_number']

logger = setup_logger("Main")

def main():
    logger.info("Bot Starting...")
    
    # 1. Connect
    connector = MT5Connector()
    if not connector.connect():
        logger.error("Failed to connect to MT5")
        return

    # 2. Initialize Modules
    strategy = MeanReversionStrategy(CONFIG)
    executor = Executor(magic=MAGIC)
    trade_manager = TradeManager(magic=MAGIC)
    validator = OrderValidator(CONFIG)
    data_feed = DataFeed(SYMBOL)
    
    # Track Daily Balance for Drawdown
    account = mt5.account_info()
    initial_balance_day = account.balance
    current_day = datetime.now().day

    logger.info(f"Connected. Balance: {account.balance} {account.currency}")

    # Main Loop
    while True:
        try:
            # Daily Reset Logic
            if datetime.now().day != current_day:
                initial_balance_day = mt5.account_info().balance
                current_day = datetime.now().day
                logger.info("New Day: Resetting Daily Drawdown Baseline")

            # Verify Drawdown
            current_account = mt5.account_info()
            if check_daily_drawdown(initial_balance_day, current_account.equity, CONFIG['trading']['max_daily_drawdown_pct']):
                logger.error("Max Daily Drawdown Reached. halting.")
                time.sleep(60)
                continue

            # Get Data
            df = data_feed.get_candles(n=200) # Need enough history for indicators
            if df is None:
                time.sleep(5)
                continue

            # Calculate Indicators
            df = strategy.calculate_indicators(df)

            # Manage Existing Trades
            trade_manager.manage_positions(df)

            # Analyze for New Signals
            signal_data = strategy.analyze_market(df)
            
            if signal_data:
                logger.info(f"Signal Detected: {signal_data['bias']} | Z: {signal_data['z_score']:.2f}")

                # Check Entry Zone (Current Price vs Zone)
                tick = mt5.symbol_info_tick(SYMBOL)
                current_price = tick.ask if signal_data['bias'] == "BUY" else tick.bid
                current_z = (current_price - signal_data['vwap']) / (signal_data['volatility'] * current_price) # Approx Z update
                
                # Note: Strategy Z-calculation was (Close - VWAP) / StdDev. 
                # Replicating logic slightly for real-time check
                
                # Check Risk & Filters
                if validator.validate(current_account, 0): # 0 passed as generic exposure check
                    
                    # Calculate Dynamic SL/TP
                    # Hybrid Stop = VWAP +/- (alpha * volatility)
                    # For simplicity, using Volatility from signal * Factor
                    vol_price_scale = signal_data['volatility'] * current_price # Convert % vol to Price
                    
                    sl_dist = vol_price_scale * 2 # Alpha = 2
                    
                    if signal_data['bias'] == "BUY":
                        sl = current_price - sl_dist
                        tp = current_price + (sl_dist * CONFIG['trading']['risk_reward_ratio'])
                    else:
                        sl = current_price + sl_dist
                        tp = current_price - (sl_dist * CONFIG['trading']['risk_reward_ratio'])

                    # Calc Lots
                    lot_size = calculate_position_size(
                        current_account.balance, 
                        CONFIG['trading']['risk_per_trade'], 
                        sl_dist, 
                        SYMBOL
                    )

                    # Execute
                    if lot_size > 0:
                        executor.place_trade(SYMBOL, signal_data['bias'], lot_size, sl, tp)

            # Sleep to next candle or tick
            time.sleep(10) 

        except KeyboardInterrupt:
            logger.info("Stopping Bot...")
            break
        except Exception as e:
            logger.exception(f"Unexpected Error: {e}")
            time.sleep(5)

    connector.disconnect()

if __name__ == "__main__":
    main()
