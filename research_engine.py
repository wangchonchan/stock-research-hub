#!/usr/bin/env python3
"""
Stock Research Engine
Primary: Yahoo Finance API
Fallback: Google Finance Web Scraping
Optimized for HKT and robust N/A handling.
"""

import json
import sys
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import yfinance as yf
from bs4 import BeautifulSoup

class StockResearchEngine:
    def __init__(self, ticker: str = "AAPL"):
        self.ticker = ticker.upper()
        self.hkt = timezone(timedelta(hours=8))
        self.data = {
            "ticker": self.ticker,
            "timestamp": datetime.now(self.hkt).isoformat(),
            "summary": {},
            "fundamentals": {},
            "technicals": {},
            "checklists": {},
            "updated_at": datetime.now(self.hkt).strftime("%Y-%m-%d %H:%M:%S")
        }

    def _get_google_finance_price(self) -> float:
        """Fallback: Scrape price from Google Finance"""
        try:
            url = f"https://www.google.com/finance/quote/{self.ticker}:NASDAQ"
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Google Finance price class often changes, but this is a common one
            price_div = soup.find("div", {"class": "YMlKec fxKbKc"})
            if price_div:
                return float(price_div.text.replace("$", "").replace(",", ""))
            
            # Try NYSE if NASDAQ fails
            url = f"https://www.google.com/finance/quote/{self.ticker}:NYSE"
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            price_div = soup.find("div", {"class": "YMlKec fxKbKc"})
            if price_div:
                return float(price_div.text.replace("$", "").replace(",", ""))
        except Exception as e:
            print(f"⚠️ Google Finance fallback failed: {e}")
        return 0.0

    def fetch_stock_price(self) -> Dict[str, Any]:
        """获取实时股票价格 - 带 Google Finance 备份"""
        price_data = {
            "current_price": 0,
            "change": 0,
            "change_percent": 0,
            "high_52w": "N/A",
            "low_52w": "N/A",
            "market_cap": "N/A",
            "pe_ratio": "N/A",
            "pb_ratio": 0,
            "volume": "N/A",
            "avg_volume": "N/A",
            "dividend_yield": 0
        }
        
        try:
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            
            current_price = info.get('currentPrice', info.get('regularMarketPrice'))
            
            # If Yahoo fails, try Google Finance
            if not current_price:
                print(f"⚠️ Yahoo Finance price failed for {self.ticker}, trying Google Finance...")
                current_price = self._get_google_finance_price()
            
            if not current_price:
                # Last resort: check 1d history
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]

            if not current_price:
                raise ValueError(f"Could not find any price data for {self.ticker}")

            price_data.update({
                "current_price": round(current_price, 3),
                "change": round(info.get('regularMarketChange', 0), 3) if info.get('regularMarketChange') else 0,
                "change_percent": round(info.get('regularMarketChangePercent', 0), 2) if info.get('regularMarketChangePercent') else 0,
                "high_52w": round(info.get('fiftyTwoWeekHigh', 0), 2) if info.get('fiftyTwoWeekHigh') else "N/A",
                "low_52w": round(info.get('fiftyTwoWeekLow', 0), 2) if info.get('fiftyTwoWeekLow') else "N/A",
                "market_cap": self._format_market_cap(info.get('marketCap', 0)),
                "pe_ratio": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "N/A",
                "pb_ratio": round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else 0,
                "volume": self._format_volume(info.get('volume', 0)),
                "avg_volume": self._format_volume(info.get('averageVolume', 0)),
                "dividend_yield": round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else 0
            })
            return price_data
        except Exception as e:
            print(f"❌ Critical error fetching price for {self.ticker}: {e}")
            if price_data["current_price"] > 0:
                return price_data
            raise e

    def _format_market_cap(self, value: float) -> str:
        if not value: return "N/A"
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        return f"${value:.0f}"

    def _format_volume(self, value: float) -> str:
        if not value: return "N/A"
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return f"{value:.0f}"

    def fetch_fundamentals(self) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            return {
                "revenue": info.get('totalRevenue', "N/A"),
                "revenue_per_share": round(info.get('revenuePerShare', 0), 2) if info.get('revenuePerShare') else "N/A",
                "gross_margin": round(info.get('grossMargins', 0) * 100, 1) if info.get('grossMargins') else "N/A",
                "operating_margin": round(info.get('operatingMargins', 0) * 100, 1) if info.get('operatingMargins') else "N/A",
                "net_margin": round(info.get('profitMargins', 0) * 100, 1) if info.get('profitMargins') else "N/A",
                "roe": round(info.get('returnOnEquity', 0) * 100, 1) if info.get('returnOnEquity') else "N/A",
                "debt_to_equity": round(info.get('debtToEquity', 0), 2) if info.get('debtToEquity') else "N/A",
                "current_ratio": round(info.get('currentRatio', 0), 2) if info.get('currentRatio') else "N/A",
                "book_value": round(info.get('bookValue', 0), 2) if info.get('bookValue') else "N/A",
                "earnings_per_share": round(info.get('trailingEps', 0), 2) if info.get('trailingEps') else "N/A",
                "forward_eps": round(info.get('forwardEps', 0), 2) if info.get('forwardEps') else "N/A"
            }
        except:
            return {k: "N/A" for k in ["revenue", "revenue_per_share", "gross_margin", "operating_margin", "net_margin", "roe", "debt_to_equity", "current_ratio", "book_value", "earnings_per_share", "forward_eps"]}

    def fetch_technical_indicators(self) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(self.ticker)
            hist = ticker.history(period="1y")
            if hist.empty: raise ValueError("No history")
            
            ma_5 = hist['Close'].tail(5).mean()
            ma_20 = hist['Close'].tail(20).mean()
            ma_60 = hist['Close'].tail(60).mean()
            std_20 = hist['Close'].tail(20).std()
            
            return {
                "ma_5": round(ma_5, 2),
                "ma_20": round(ma_20, 2),
                "ma_60": round(ma_60, 2),
                "bollinger_upper": round(ma_20 + (std_20 * 2), 2),
                "bollinger_middle": round(ma_20, 2),
                "bollinger_lower": round(ma_20 - (std_20 * 2), 2),
                "rsi": self._calculate_rsi(hist['Close']),
                "macd": self._calculate_macd(hist['Close'])
            }
        except:
            return {"rsi": "N/A", "ma_5": "N/A", "ma_20": "N/A", "ma_60": "N/A", "bollinger_upper": "N/A", "bollinger_middle": "N/A", "bollinger_lower": "N/A", "macd": "N/A"}

    def _calculate_rsi(self, prices, period=14) -> Any:
        try:
            if len(prices) < period: return "N/A"
            deltas = prices.diff()
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            rs = up / down if down != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            return round(rsi, 2)
        except: return "N/A"

    def _calculate_macd(self, prices) -> Any:
        try:
            if len(prices) < 26: return "N/A"
            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()
            macd = ema_12 - ema_26
            return round(macd.iloc[-1], 4)
        except: return "N/A"

    def fetch_analyst_consensus(self) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            target_price = info.get('targetMeanPrice', 0)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            upside = ((target_price - current_price) / current_price * 100) if current_price and current_price > 0 and target_price else 0
            
            return {
                "target_price": round(target_price, 2) if target_price else "N/A",
                "upside_potential": round(upside, 1) if upside else "N/A",
                "number_of_analysts": info.get('numberOfAnalysts', "N/A"),
                "recommendation": info.get('recommendationKey', 'N/A').upper()
            }
        except:
            return {"target_price": "N/A", "upside_potential": "N/A", "number_of_analysts": "N/A", "recommendation": "N/A"}

    def run_research(self) -> Dict[str, Any]:
        print(f"🔍 Researching {self.ticker}...")
        price_data = self.fetch_stock_price()
        fundamentals = self.fetch_fundamentals()
        technicals = self.fetch_technical_indicators()
        consensus = self.fetch_analyst_consensus()
        
        rsi = technicals.get("rsi")
        pb = price_data.get("pb_ratio", 0)
        
        checklists = {
            "rsi_monitor": {
                "name": "RSI (14) Monitor",
                "value": rsi,
                "triggered": isinstance(rsi, (int, float)) and (rsi <= 35 or rsi >= 65),
                "status": "OVERSOLD" if isinstance(rsi, (int, float)) and rsi <= 35 else "OVERBOUGHT" if isinstance(rsi, (int, float)) and rsi >= 65 else "NORMAL"
            },
            "pb_monitor": {
                "name": "PB Ratio Monitor",
                "value": pb if pb > 0 else "N/A",
                "triggered": isinstance(pb, (int, float)) and pb <= 1.5 and pb > 0,
                "status": "UNDERVALUED" if (isinstance(pb, (int, float)) and pb <= 1.5 and pb > 0) else "NORMAL"
            }
        }
        
        self.data.update({
            "price": price_data,
            "fundamentals": fundamentals,
            "technicals": technicals,
            "consensus": consensus,
            "checklists": checklists
        })
        return self.data

    def save_to_json(self, filepath: str = None):
        if filepath is None: filepath = f"research_data_{self.ticker}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        return True

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    try:
        engine = StockResearchEngine(ticker)
        engine.run_research()
        engine.save_to_json()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
