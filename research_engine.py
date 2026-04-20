#!/usr/bin/env python3
"""
Stock Research Engine - Direct Output Version
Fetches all data from Yahoo Finance and outputs JSON to stdout.
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
        # Initialize with N/A to ensure frontend always has a value
        self.data = {
            "ticker": self.ticker,
            "timestamp": datetime.now(self.hkt).isoformat(),
            "updated_at": datetime.now(self.hkt).strftime("%Y-%m-%d %H:%M:%S"),
            "price": {
                "current_price": 0, 
                "change": 0, 
                "change_percent": 0, 
                "pb_ratio": "N/A"
            },
            "consensus": {
                "recommendation": "N/A", 
                "number_of_analysts": "N/A", 
                "target_price": "N/A", 
                "upside_potential": "N/A"
            },
            "fundamentals": {
                "revenue": "N/A",
                "gross_margin": "N/A", 
                "net_margin": "N/A", 
                "roe": "N/A", 
                "book_value": "N/A"
            },
            "technicals": {
                "rsi": "N/A", 
                "ma_5": "N/A", 
                "ma_20": "N/A", 
                "ma_60": "N/A"
            },
            "checklists": {}
        }

    def _calculate_rsi(self, series, period=14):
        try:
            if len(series) < period + 1: return "N/A"
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            val = rsi.iloc[-1]
            return round(float(val), 2) if not pd.isna(val) else "N/A"
        except:
            return "N/A"

    def run_research(self):
        try:
            t = yf.Ticker(self.ticker)
            # 1. Fetch Price & History (Most reliable)
            hist = t.history(period="1y")
            if hist.empty:
                # Try one more time with different period
                hist = t.history(period="1mo")
            
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
                
                self.data["price"].update({
                    "current_price": round(current_price, 3),
                    "change": round(change, 3),
                    "change_percent": round(change_pct, 2)
                })
                
                # Calculate Technicals
                self.data["technicals"].update({
                    "rsi": self._calculate_rsi(hist['Close']),
                    "ma_5": round(float(hist['Close'].tail(5).mean()), 2),
                    "ma_20": round(float(hist['Close'].tail(20).mean()), 2),
                    "ma_60": round(float(hist['Close'].tail(60).mean()), 2)
                })

            # 2. Fetch Info (Less reliable, use try-except for each field)
            try:
                info = t.info
                if info:
                    # Price & Valuation
                    pb = info.get('priceToBook')
                    if pb is not None: self.data["price"]["pb_ratio"] = round(float(pb), 2)
                    
                    # Fundamentals
                    self.data["fundamentals"].update({
                        "revenue": info.get('totalRevenue', "N/A"),
                        "gross_margin": round(float(info.get('grossMargins', 0)) * 100, 1) if info.get('grossMargins') else "N/A",
                        "net_margin": round(float(info.get('profitMargins', 0)) * 100, 1) if info.get('profitMargins') else "N/A",
                        "roe": round(float(info.get('returnOnEquity', 0)) * 100, 1) if info.get('returnOnEquity') else "N/A",
                        "book_value": round(float(info.get('bookValue', 0)), 2) if info.get('bookValue') else "N/A"
                    })
                    
                    # Consensus
                    target = info.get('targetMeanPrice')
                    curr = self.data["price"]["current_price"]
                    upside = "N/A"
                    if target and curr > 0:
                        upside = round(((float(target) - curr) / curr) * 100, 1)

                    self.data["consensus"].update({
                        "recommendation": str(info.get('recommendationKey', 'N/A')).upper(),
                        "number_of_analysts": info.get('numberOfAnalysts', "N/A"),
                        "target_price": round(float(target), 2) if target else "N/A",
                        "upside_potential": upside
                    })
            except Exception as e:
                pass # Info failed, keep N/A

            # 3. Calculate Checklists
            rsi = self.data["technicals"]["rsi"]
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
            
            return self.data
        except Exception as e:
            # Return what we have even if partial failure
            return self.data

    def output_json(self):
        def serialize(obj):
            if hasattr(obj, 'item'): return obj.item()
            return str(obj)
        # Print ONLY the JSON to stdout
        print(json.dumps(self.data, ensure_ascii=False, default=serialize))

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    engine = StockResearchEngine(ticker)
    engine.run_research()
    engine.output_json()
