import numpy as np
import pandas as pd
from utils.indicators import *
from utils.helpers import check_trading_session, check_news_impact
from utils.logger import setup_logger

logger = setup_logger("Strategy")

class MeanReversionStrategy:
    def __init__(self, config):
        self.config = config
        self.z_trigger = config['strategy']['z_score_trigger']
        self.entry_start = config['strategy']['entry_zone_start']
        self.entry_end = config['strategy']['entry_zone_end']

    def calculate_indicators(self, df):
        """
        Calculates all required indicators and adds them to the DataFrame.
        """
        df = df.copy()
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        df['volatility'] = compute_volatility(df['returns'])
        df['vwap'] = compute_vwap(df)
        df['z_score'] = (df['close'] - df['vwap']) / (df['close'].rolling(20).std()) # Simplified Z relative to VWAP
        df['vol_slope'] = compute_volatility_slope(df['volatility'])
        df['auto_corr'] = compute_autocorrelation(df['returns'])
        return df

    def analyze_market(self, df):
        """
        Executes the STEP 1 - STEP 4 logic.
        Returns a dict with signal details or None.
        Expects df to have indicators already calculated.
        """
        # --- Pre-Checks ---
        if len(df) < 100:
            return None
            
        # STEP 1: Time & Event Filter
        if not check_trading_session(self.config):
            logger.info("Outside Trading Session")
            return None
            
        if not check_news_impact():
            logger.info("High Impact News Detected")
            return None

        # Grab latest closed candle
        last = df.iloc[-2]

        # STEP 1 (Cont): Volatility Regime
        # "Volatility slope must not be strongly positive"
        if last.vol_slope > 0.0001: # Threshold needs tuning
            logger.info("Volatility Expanding (Slope > 0) - REJECT")
            return None

        # STEP 3: Confirmations
        signal_bias = None
        
        # Z-Score Trigger
        if last.z_score >= self.z_trigger:
            signal_bias = "SELL"
        elif last.z_score <= -self.z_trigger:
            signal_bias = "BUY"
            
        if not signal_bias:
            return None

        # Autocorrelation Filter (Memory)
        # "AC < -0.1 -> Mean Reversion Confirmed"
        if last.auto_corr > self.config['filters']['autocorrelation_threshold']:
            logger.info(f"Autocorrelation {last.auto_corr} > Threshold - Trend Mode - REJECT")
            return None

        # STEP 4: Entry Zone Logic
        # We need to check if current Price (Ask/Bid) is in the "Retracement Zone"
        # Since we are analyzing historical candles, this part actually happens in Real-Time loop usually.
        # But for Signal generation, we say "Ready to Enter".
        # The Main Loop will check the specific Price level.
        
        # Construct Signal Object
        entry_signal = {
            "bias": signal_bias,
            "z_score": last.z_score,
            "vwap": last.vwap,
            "volatility": last.volatility, # This is returns std, need price scale 
            "close": last.close
        }
        
        return entry_signal
        
    def check_entry_zone(self, market_price, z_score_current, signal_data):
        """
        Checks if current live price is within Z-Score 1.6-1.8 retracement zone.
        This is tricky because Z-Score changes with price.
        Approximation: Use the Z-score from the closed candle.
        User required: "Z retraces from >= 2.0 -> 1.6-1.8"
        
        If Entry Signal was generated (Z > 2), we wait for Z to drop to 1.8.
        """
        # This stateful logic is best handled by the main loop or a state machine.
        # For this implementation, we return Valid if Z is currently in zone provided filter passed.
        
        # Simplified: If signal was "SELL" (Z > 2 previously), allows entry if Z is now 1.6-1.8?
        # Or does it mean we simply limit order there?
        
        # Let's interpret: Current Z needs to be in entry zone.
        z = abs(z_score_current)
        if self.entry_start <= z <= self.entry_end:
            return True
        return False
