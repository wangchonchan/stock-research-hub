#!/usr/bin/env python3
"""
Stock Research Engine - Advanced Indicators & Quarterly Data
Includes OSC_20, BIAS_24, CCI_14 and real quarterly financial metrics.
"""

import json
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import yfinance as yf

class StockResearchEngine:
    def __init__(self, ticker: str = "AAPL"):
        self.ticker = ticker.upper()
        self.hkt = timezone(timedelta(hours=8))
        self.data = {
            "ticker": self.ticker,
            "timestamp": datetime.now(self.hkt).isoformat(),
            "updated_at": datetime.now(self.hkt).strftime("%Y-%m-%d %H:%M:%S"),
            "price": {"current_price": 0, "change": 0, "change_percent": 0, "pb_ratio": "N/A"},
            "consensus": {"recommendation": "N/A", "target_price": "N/A", "upside_potential": "N/A"},
            "fundamentals": {
                "quarter": "N/A",
                "revenue": "N/A",
                "revenue_yoy": "N/A",
                "gross_margin": "N/A",
                "net_margin": "N/A",
                "cash_reserves": "N/A"
            },
            "technicals": {
                "rsi": "N/A",
                "ma_5": "N/A",
                "ma_60": "N/A",
                "osc_20": "N/A",
                "bias_24": "N/A",
                "cci_14": "N/A"
            },
            "checklists": {}
        }

    def _calculate_indicators(self, df):
        try:
            close = df['Close']
            
            # MA 5 & 60
            ma5 = close.rolling(window=5).mean().iloc[-1]
            ma60 = close.rolling(window=60).mean().iloc[-1]
            
            # OSC_20 (Price Oscillator) - (Close - MA20)
            ma20 = close.rolling(window=20).mean()
            osc20 = (close - ma20).iloc[-1]
            
            # BIAS_24 - (Close - MA24) / MA24 * 100
            ma24 = close.rolling(window=24).mean()
            bias24 = ((close - ma24) / ma24 * 100).iloc[-1]
            
            # CCI_14
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            ma_tp = tp.rolling(window=14).mean()
            md_tp = tp.rolling(window=14).apply(lambda x: np.abs(x - x.mean()).mean())
            cci14 = ((tp - ma_tp) / (0.015 * md_tp)).iloc[-1]
            
            # RSI 14
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi14 = 100 - (100 / (1 + rs))
            rsi_val = rsi14.iloc[-1]

            return {
                "ma_5": round(float(ma5), 2),
                "ma_60": round(float(ma60), 2),
                "osc_20": round(float(osc20), 2),
                "bias_24": round(float(bias24), 2),
                "cci_14": round(float(cci14), 2),
                "rsi": round(float(rsi_val), 2) if not pd.isna(rsi_val) else "N/A"
            }
        except Exception as e:
            print(f"Error calculating indicators: {e}", file=sys.stderr)
            return {}

    def run_research(self):
        try:
            t = yf.Ticker(self.ticker)
            hist = t.history(period="1y")
            if hist.empty:
                hist = t.history(period="1mo")
            
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
                self.data["price"].update({
                    "current_price": round(current_price, 3),
                    "change": round(current_price - prev_close, 3),
                    "change_percent": round(((current_price - prev_close) / prev_close) * 100, 2)
                })
                self.data["technicals"].update(self._calculate_indicators(hist))

            # Fetch Quarterly Financials
            try:
                # Get quarterly financials
                q_fin = t.quarterly_financials
                if not q_fin.empty:
                    latest_q = q_fin.columns[0]
                    prev_y_q = q_fin.columns[4] if len(q_fin.columns) > 4 else None
                    
                    # Determine Quarter Name (e.g., 2023-12-31 -> Q4)
                    month = latest_q.month
                    q_name = f"Q{(month-1)//3 + 1}"
                    self.data["fundamentals"]["quarter"] = q_name
                    
                    rev = q_fin.loc['Total Revenue'].iloc[0] if 'Total Revenue' in q_fin.index else "N/A"
                    self.data["fundamentals"]["revenue"] = rev
                    
                    if prev_y_q is not None and 'Total Revenue' in q_fin.index:
                        prev_rev = q_fin.loc['Total Revenue'].iloc[4]
                        if prev_rev and prev_rev != 0:
                            growth = ((rev - prev_rev) / prev_rev) * 100
                            self.data["fundamentals"]["revenue_yoy"] = round(float(growth), 1)

                    # Margins
                    if 'Gross Profit' in q_fin.index and 'Total Revenue' in q_fin.index:
                        gm = (q_fin.loc['Gross Profit'].iloc[0] / rev) * 100
                        self.data["fundamentals"]["gross_margin"] = round(float(gm), 1)
                    
                    if 'Net Income' in q_fin.index and 'Total Revenue' in q_fin.index:
                        nm = (q_fin.loc['Net Income'].iloc[0] / rev) * 100
                        self.data["fundamentals"]["net_margin"] = round(float(nm), 1)

                # Cash Reserves from Balance Sheet
                q_bs = t.quarterly_balance_sheet
                if not q_bs.empty:
                    cash = q_bs.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in q_bs.index else \
                           q_bs.loc['Cash Cash Equivalents And Short Term Investments'].iloc[0] if 'Cash Cash Equivalents And Short Term Investments' in q_bs.index else "N/A"
                    self.data["fundamentals"]["cash_reserves"] = cash

                # Info for Consensus & PB
                info = t.info
                if info:
                    self.data["price"]["pb_ratio"] = round(float(info.get('priceToBook', 0)), 2) if info.get('priceToBook') else "N/A"
                    target = info.get('targetMeanPrice')
                    self.data["consensus"].update({
                        "recommendation": str(info.get('recommendationKey', 'N/A')).upper(),
                        "target_price": round(float(target), 2) if target else "N/A",
                        "upside_potential": round(((float(target) - current_price) / current_price) * 100, 1) if target and current_price > 0 else "N/A"
                    })
            except Exception as e:
                print(f"Error fetching financials: {e}", file=sys.stderr)

            # Checklists
            rsi = self.data["technicals"]["rsi"]
            pb = self.data["price"]["pb_ratio"]
            self.data["checklists"] = {
                "rsi_monitor": {
                    "name": "RSI (14) Monitor",
                    "value": rsi,
                    "triggered": isinstance(rsi, (int, float)) and (rsi <= 35 or rsi >= 65),
                    "status": "OVERSOLD" if isinstance(rsi, (int, float)) and rsi <= 35 else "OVERBOUGHT" if isinstance(rsi, (int, float)) and rsi >= 65 else "NORMAL"
                },
                "pb_monitor": {
                    "name": "PB Ratio Monitor",
                    "value": pb,
                    "triggered": isinstance(pb, (int, float)) and 0 < pb <= 1.5,
                    "status": "UNDERVALUED" if (isinstance(pb, (int, float)) and 0 < pb <= 1.5) else "NORMAL"
                }
            }
            return self.data
        except Exception as e:
            return self.data

    def output_json(self):
        def serialize(obj):
            if hasattr(obj, 'item'): return obj.item()
            return str(obj)
        print(json.dumps(self.data, ensure_ascii=False, default=serialize))

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    engine = StockResearchEngine(ticker)
    engine.run_research()
    engine.output_json()
