#!/usr/bin/env python3
"""
Stock Research Engine - Ultra Robust Version
Focuses on Price and RSI calculation to ensure 100% availability.
"""

import json
import sys
import pandas as pd
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
            "consensus": {"recommendation": "N/A", "number_of_analysts": "N/A", "target_price": "N/A", "upside_potential": "N/A"},
            "fundamentals": {"gross_margin": "N/A", "net_margin": "N/A", "roe": "N/A", "book_value": "N/A"},
            "technicals": {"rsi": "N/A", "ma_5": "N/A", "ma_20": "N/A", "ma_60": "N/A"},
            "checklists": {}
        }

    def _calculate_rsi(self, series, period=14):
        try:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return round(rsi.iloc[-1], 2)
        except:
            return "N/A"

    def run_research(self):
        print(f"🔍 Researching {self.ticker}...")
        try:
            t = yf.Ticker(self.ticker)
            # Fetch history first as it's more reliable than .info
            hist = t.history(period="1y")
            
            if hist.empty:
                raise ValueError("No data found")

            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100

            # Calculate RSI
            rsi = self._calculate_rsi(hist['Close'])
            
            # Try to get some info but don't crash if it fails
            try:
                info = t.info
                pb = info.get('priceToBook', "N/A")
                if isinstance(pb, (int, float)): pb = round(pb, 2)
                
                self.data["price"].update({
                    "current_price": round(current_price, 3),
                    "change": round(change, 3),
                    "change_percent": round(change_pct, 2),
                    "pb_ratio": pb
                })
                
                self.data["fundamentals"].update({
                    "gross_margin": round(info.get('grossMargins', 0) * 100, 1) if info.get('grossMargins') else "N/A",
                    "net_margin": round(info.get('profitMargins', 0) * 100, 1) if info.get('profitMargins') else "N/A",
                    "roe": round(info.get('returnOnEquity', 0) * 100, 1) if info.get('returnOnEquity') else "N/A",
                    "book_value": round(info.get('bookValue', 0), 2) if info.get('bookValue') else "N/A"
                })
                
                self.data["consensus"].update({
                    "recommendation": info.get('recommendationKey', 'N/A').upper(),
                    "number_of_analysts": info.get('numberOfAnalysts', "N/A"),
                    "target_price": info.get('targetMeanPrice', "N/A")
                })
            except:
                self.data["price"].update({"current_price": round(current_price, 3), "change": round(change, 3), "change_percent": round(change_pct, 2)})

            # Update Technicals
            self.data["technicals"].update({
                "rsi": rsi,
                "ma_5": round(hist['Close'].tail(5).mean(), 2),
                "ma_20": round(hist['Close'].tail(20).mean(), 2),
                "ma_60": round(hist['Close'].tail(60).mean(), 2)
            })

            # Checklists
            pb_val = self.data["price"]["pb_ratio"]
            self.data["checklists"] = {
                "rsi_monitor": {
                    "name": "RSI (14) Monitor",
                    "value": rsi,
                    "triggered": isinstance(rsi, (int, float)) and (rsi <= 35 or rsi >= 65),
                    "status": "OVERSOLD" if isinstance(rsi, (int, float)) and rsi <= 35 else "OVERBOUGHT" if isinstance(rsi, (int, float)) and rsi >= 65 else "NORMAL"
                },
                "pb_monitor": {
                    "name": "PB Ratio Monitor",
                    "value": pb_val,
                    "triggered": isinstance(pb_val, (int, float)) and pb_val <= 1.5 and pb_val > 0,
                    "status": "UNDERVALUED" if (isinstance(pb_val, (int, float)) and pb_val <= 1.5 and pb_val > 0) else "NORMAL"
                }
            }
            
            print(f"✅ Success: {self.ticker} @ {current_price}")
            return self.data
        except Exception as e:
            print(f"❌ Error: {e}")
            raise e

    def save_to_json(self):
        filepath = f"research_data_{self.ticker}.json"
        def serialize(obj):
            if hasattr(obj, 'item'): return obj.item()
            return str(obj)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2, default=serialize)

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    try:
        engine = StockResearchEngine(ticker)
        engine.run_research()
        engine.save_to_json()
    except:
        sys.exit(1)
