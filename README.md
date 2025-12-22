# 🤖 Advanced Mean Reversion MT5 Bot

A professional-grade automated trading system for **MetaTrader 5**, designed for Mean Reversion strategies using statistical arbitrage concepts (Hurst Exponent, Z-Score, Rolling VWAP).

> **Status**: Production Ready ✅
> **Live/Backtest Parity**: 100% Verified (Identical Logic)

---

## 🚀 Key Features

### 🧠 Intelligent Strategy
*   **Hurst Exponent Filter**: Trades *only* when the market is in a "Mean Reverting" regime (Hurst < 0.45). Avoids fighting strong trends.
*   **Z-Score Triggers**: Enters trades at statistical extremes (Standard Deviations > 2.5) from the Rolling VWAP.
*   **RSI Confirmation**: Adds momentum confirmation to prevent catching falling knives.
*   **Volatility Filters**: Skips trading during erratic volatility spikes (`Vol Slope` check).

### 🛡️ Robust Risk Management
*   **Dynamic Position Sizing**: Lot size is calculated automatically based on Volatility (ATR-like) and Account Risk %.
*   **Hard Drawdown Stops**:
    *   **Daily Stop**: Stops trading if daily loss exceeds `2%`.
    *   **Total Equity Stop**: Halts the bot if total drawdown hits `10%`.
*   **Risk:Reward**: Strict 1:2 R:R ratio enforced on every trade.

### ⚙️ Precision Timing
*   **Broker-Time Filters**: Session logic (Asian/London) runs on **Server Time**, making it immune to local computer timezone issues.
*   **Heartbeat Monitor**: Logs "Waiting for candle..." updates to ensure the bot is alive during quiet periods.

---

## 📂 Project Structure

```text
├── config/
│   └── settings.yaml       # 🔧 All strategy, risk, and session parameters
├── core/
│   ├── mt5_connector.py    # MT5 Connection handling
│   ├── data_feed.py        # Live & Historical Data fetching
│   ├── execution.py        # Trade placement logic
│   └── risk.py             # Position sizing & Drawdown checks
├── strategy/
│   └── mean_reversion.py   # 🧠 The Brain (Signal Logic)
├── services/
│   ├── trade_manager.py    # Monitors open trades & logs exits
│   └── order_validator.py  # Final safety checks before execution
├── utils/
│   ├── helpers.py          # Timezone and Session logic
│   ├── indicators.py       # Math (Hurst, Z-Score, VWAP)
│   └── logger.py           # Logging configuration
├── main.py                 # 🚀 LIVE Trading Entry Point
└── backtest.py             # 🧪 Historical Simulation Entry Point
```

---

## 🛠️ Installation

1.  **Prerequisites**:
    *   **Python 3.8+** (Verified on 3.10/3.11).
    *   **MetaTrader 5 Terminal** (Installed, Logged in, and "Algo Trading" Enabled).
    *   **Windows OS** (Required for MT5 Python API).

2.  **Install Dependencies**:
    The project includes a `requirements.txt` for easy setup.
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies: `MetaTrader5`, `pandas`, `numpy`, `pyyaml`, `matplotlib`*

---

## ⚡ How to Run

### 1. Configure
Edit `config/settings.yaml` to set your risk and hours.
*   **Important**: Set `asian_start`/`end` based on your **Broker's Market Watch Time**, not your local time.

### 2. Live Trading
Run the bot to start trading on your active MT5 account.
```bash
python main.py
```
*   *Logs are saved to `logs/bot.log`*
*   *Strategy Snapshots are printed every candle.*

### 3. Backtesting
Run the simulation to verify performance on historical data (50,000 bars).
```bash
python backtest.py
```
*   *Prints detailed trade logs (Entry, Exit, PnL).*
*   *Interactive Drawdown Reset if equity drops too low.*

---

## 📊 Strategy Logic (Snapshot)

1.  **Check Regime**: Is `Hurst Exponent` < 0.45? (Market is ranging).
2.  **Check Extremes**: Is Price `Z-Score` > 2.5 deviations from VWAP?
3.  **Check Timing**: Is active Session (Asian/London) OPEN?
4.  **Signal**: If all Yes -> **Wait for Retracement** to Zone (1.8) -> **EXECUTE**.

---

## ⚠️ Disclaimer
*   Trading Forex/CFDs involves substantial risk of loss.
*   Backtest results do not guarantee future performance.
*   Always test on a **Demo Account** first.
