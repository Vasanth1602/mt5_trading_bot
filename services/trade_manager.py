import MetaTrader5 as mt5
from utils.logger import setup_logger

logger = setup_logger("TradeManager")

class TradeManager:
    def __init__(self, magic):
        self.magic = magic

    def manage_positions(self, df):
        """
        Monitors open positions for exit conditions.
        """
        positions = mt5.positions_get(magic=self.magic)
        if positions is None:
            return

        # Get latest market data
        last_candle = df.iloc[-1]
        current_vol = last_candle['volatility'] # Rolling val
        
        for pos in positions:
            symbol = pos.symbol
            # STEP 6: Partial Exit Logic
            # "Volatility Expansion: Current vol >= X * entry vol"
            # We don't store entry vol in MT5 comment easily, but we can check if current vol is extreme.
            
            # Simple Logic: If Volatility Spike, Reduce Risk.
            if current_vol > 0.0005: # Threshold example
                 logger.info(f"Volatility Spike on {symbol}. Managing position...")
                 # Implement partial close or tight SL here
                 pass

            # Trailing SL or Breakeven logic could go here
            pass

    def monitor_closed_trades(self):
        """
        Checks for recently closed trades and logs them.
        """
        from datetime import datetime, timedelta
        
        # Check last 5 minutes history
        from_date = datetime.now() - timedelta(minutes=5)
        deals = mt5.history_deals_get(from_date, datetime.now(), group="*")
        
        if deals:
            for deal in deals:
                # Filter for Exit Deals (Entry=0, Exit=1)
                # Deal Entry In=0, Out=1, In/Out=2
                if deal.entry == mt5.DEAL_ENTRY_OUT:
                    # Avoid duplicated logging (naive check: timestamp very recent)
                    # Ideally track by ticket, but simply logging found deals is OK for low freq.
                    
                    # Only log if it happened in last 15 seconds to avoid spam on every loop
                    deal_time = datetime.fromtimestamp(deal.time)
                    if (datetime.now() - deal_time).total_seconds() < 15:
                        res = "WIN" if deal.profit > 0 else "LOSS"
                        logger.info(
                            f"🏁 {res} | Ticket: {deal.position_id} | "
                            f"Price: {deal.price:.5f} | PnL: ${deal.profit:.2f} | "
                            f"Comment: {deal.comment}"
                        )
