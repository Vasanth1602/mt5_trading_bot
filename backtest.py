import pandas as pd
import numpy as np
import yaml
import MetaTrader5 as mt5
import matplotlib.pyplot as plt

from core.mt5_connector import MT5Connector
from core.data_feed import DataFeed
from strategy.mean_reversion import MeanReversionStrategy
from core.risk import calculate_position_size

# Load Config
with open("config/settings.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

SYMBOL = CONFIG['trading']['symbol']
BARS = 10000 

def run_backtest():
    print(f"🚀 Starting Optimized Backtest (RSI+AC) for {SYMBOL} ({BARS} bars)...")

    # 1. Connect
    connector = MT5Connector()
    if not connector.connect():
        return

    # 2. Fetch Data
    # Map Timeframe
    tf_map = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1}
    tf = tf_map.get(CONFIG['trading']['timeframe'], mt5.TIMEFRAME_M15)
    
    feed = DataFeed(SYMBOL, timeframe=tf, bars=BARS)
    df = feed.get_candles(n=BARS)
    
    if df is None or df.empty:
        print("❌ No data fetched")
        return

    print(f"✅ Data fetched: {len(df)} candles")
    
    # 3. Apply Indicators
    strategy = MeanReversionStrategy(CONFIG)
    df = strategy.calculate_indicators(df)
    
    # 4. Simulation Loop
    balance = 10000.0
    history = []
    positions = []
    
    # STATE TRACKING FOR BACKTEST
    pending_signal = None 
    wait_counter = 0
    Z_TRIGGER = CONFIG['strategy']['z_score_trigger']
    ENTRY_TARGET = CONFIG['strategy']['entry_zone_target']
    HURST_LIMIT = CONFIG['strategy']['hurst_threshold']
    RSI_OB = CONFIG['strategy']['rsi_overbought']
    RSI_OS = CONFIG['strategy']['rsi_oversold']

    print(f"⚙️ Config: H<{HURST_LIMIT}, Z>{Z_TRIGGER}, RSI, R:R={CONFIG['trading']['risk_reward_ratio']}")

    for i in range(100, len(df)):
        current_candle = df.iloc[i]
        prev_candle = df.iloc[i-1] 
        
        # --- PnL Calc ---
        active_positions = []
        for pos in positions:
            pnl = 0
            closed = False
            
            if pos['type'] == 'BUY':
                if current_candle['low'] <= pos['sl']:
                    pnl = (pos['sl'] - pos['price']) * pos['lots'] * 100000
                    closed = True; reason = "SL"
                elif current_candle['high'] >= pos['tp']:
                    pnl = (pos['tp'] - pos['price']) * pos['lots'] * 100000
                    closed = True; reason = "TP"
            else: # SELL
                if current_candle['high'] >= pos['sl']:
                    pnl = (pos['price'] - pos['sl']) * pos['lots'] * 100000
                    closed = True; reason = "SL"
                elif current_candle['low'] <= pos['tp']:
                    pnl = (pos['price'] - pos['tp']) * pos['lots'] * 100000
                    closed = True; reason = "TP"
            
            if closed:
                balance += pnl
                history.append({'time': current_candle['time'], 'pnl': pnl, 'reason': reason})
            else:
                active_positions.append(pos)
        positions = active_positions

        # --- Strategy Logic ---
        
        if prev_candle['hurst'] > HURST_LIMIT:
            pending_signal = None; wait_counter = 0; continue 

        z = prev_candle['z_score']
        rsi = prev_candle['rsi']
        
        if pending_signal:
            wait_counter += 1
            if wait_counter > 20: 
                pending_signal = None
                wait_counter = 0
        
        # 3. Trigger (RSI + Z)
        if abs(z) >= Z_TRIGGER:
            if z > 0 and rsi > RSI_OB: # Overbought
                pending_signal = "SELL_WAIT"; wait_counter = 0
            elif z < 0 and rsi < RSI_OS: # Oversold
                pending_signal = "BUY_WAIT"; wait_counter = 0
            
        # 4. Entry Execution
        signal = None
        if pending_signal == "SELL_WAIT":
            if z <= ENTRY_TARGET: 
                signal = "SELL"; pending_signal = None
        elif pending_signal == "BUY_WAIT":
            if z >= -ENTRY_TARGET: 
                signal = "BUY"; pending_signal = None
                
        # Execute
        if signal:
            price = current_candle['close']
            vol_price = prev_candle['volatility'] * price
            sl_dist = vol_price * 2 
            
            # Risk Reward from Config
            rr = CONFIG['trading']['risk_reward_ratio']
            if signal == "BUY":
                sl = price - sl_dist
                tp = price + (sl_dist * rr)
            else:
                sl = price + sl_dist
                tp = price - (sl_dist * rr)
            
            lots = calculate_position_size(balance, 0.01, sl_dist, SYMBOL)
            
            if lots > 0:
                positions.append({
                    'type': signal, 'price': price, 'sl': sl, 'tp': tp, 'lots': lots
                })

    # Stats
    wins = len([x for x in history if x['pnl'] > 0])
    total = len(history)
    win_rate = (wins/total*100) if total > 0 else 0
    total_pnl = sum([x['pnl'] for x in history])
    
    print("\n--- Optimized Results (RSI) ---")
    print(f"Final Balance: ${balance:.2f}")
    print(f"Net Profit   : ${total_pnl:.2f}")
    print(f"Total Trades : {total}")
    print(f"Win Rate     : {win_rate:.1f}%")

    connector.disconnect()

if __name__ == "__main__":
    run_backtest()
