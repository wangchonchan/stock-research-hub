#!/usr/bin/env python3
"""
Stock Research Engine
100% Real-time data from Yahoo Finance API
Optimized for HKT and simplified checklists.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import yfinance as yf

class StockResearchEngine:
    def __init__(self, ticker: str = "AAPL"):
        self.ticker = ticker.upper()
        # Define HKT timezone (UTC+8)
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
    
    def fetch_stock_price(self) -> Dict[str, Any]:
        """获取实时股票价格"""
        try:
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            
            if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info):
                raise ValueError(f"No real-time data found for {self.ticker}")
            
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            price_data = {
                "current_price": round(current_price, 3),
                "change": round(info.get('regularMarketChange', 0), 3),
                "change_percent": round(info.get('regularMarketChangePercent', 0), 2),
                "high_52w": round(info.get('fiftyTwoWeekHigh', 0), 2),
                "low_52w": round(info.get('fiftyTwoWeekLow', 0), 2),
                "market_cap": self._format_market_cap(info.get('marketCap', 0)),
                "pe_ratio": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "N/A",
                "pb_ratio": round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else 0,
                "volume": self._format_volume(info.get('volume', 0)),
                "avg_volume": self._format_volume(info.get('averageVolume', 0)),
                "dividend_yield": round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else 0
            }
            return price_data
        except Exception as e:
            print(f"❌ Error fetching stock price for {self.ticker}: {e}")
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
        """获取基本面数据"""
        try:
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            
            fundamentals = {
                "revenue": info.get('totalRevenue', 0),
                "revenue_per_share": round(info.get('revenuePerShare', 0), 2),
                "gross_margin": round(info.get('grossMargins', 0) * 100, 1) if info.get('grossMargins') else 0,
                "operating_margin": round(info.get('operatingMargins', 0) * 100, 1) if info.get('operatingMargins') else 0,
                "net_margin": round(info.get('profitMargins', 0) * 100, 1) if info.get('profitMargins') else 0,
                "roe": round(info.get('returnOnEquity', 0) * 100, 1) if info.get('returnOnEquity') else 0,
                "debt_to_equity": round(info.get('debtToEquity', 0), 2) if info.get('debtToEquity') else 0,
                "current_ratio": round(info.get('currentRatio', 0), 2) if info.get('currentRatio') else 0,
                "book_value": round(info.get('bookValue', 0), 2),
                "earnings_per_share": round(info.get('trailingEps', 0), 2) if info.get('trailingEps') else 0,
                "forward_eps": round(info.get('forwardEps', 0), 2) if info.get('forwardEps') else 0
            }
            return fundamentals
        except Exception as e:
            print(f"❌ Error fetching fundamentals for {self.ticker}: {e}")
            return {}
    
    def fetch_technical_indicators(self) -> Dict[str, Any]:
        """获取技术指标"""
        try:
            ticker = yf.Ticker(self.ticker)
            hist = ticker.history(period="1y")
            
            if hist.empty:
                raise ValueError(f"No historical data found for {self.ticker}")
            
            ma_5 = hist['Close'].tail(5).mean()
            ma_20 = hist['Close'].tail(20).mean()
            ma_60 = hist['Close'].tail(60).mean()
            
            std_20 = hist['Close'].tail(20).std()
            
            technicals = {
                "ma_5": round(ma_5, 2),
                "ma_20": round(ma_20, 2),
                "ma_60": round(ma_60, 2),
                "bollinger_upper": round(ma_20 + (std_20 * 2), 2),
                "bollinger_middle": round(ma_20, 2),
                "bollinger_lower": round(ma_20 - (std_20 * 2), 2),
                "rsi": self._calculate_rsi(hist['Close']),
                "macd": self._calculate_macd(hist['Close'])
            }
            return technicals
        except Exception as e:
            print(f"❌ Error fetching technicals for {self.ticker}: {e}")
            return {}
    
    def _calculate_rsi(self, prices, period=14) -> float:
        if len(prices) < period: return 50
        deltas = prices.diff()
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    def _calculate_macd(self, prices) -> float:
        if len(prices) < 26: return 0
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        return round(macd.iloc[-1], 4)
    
    def fetch_analyst_consensus(self) -> Dict[str, Any]:
        """获取分析师共识"""
        try:
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            
            # Use recommendationMean for a more reliable indicator
            rec_mean = info.get('recommendationMean', 'N/A')
            num_analysts = info.get('numberOfAnalysts', 0)
            
            target_price = info.get('targetMeanPrice', 0)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            upside = ((target_price - current_price) / current_price * 100) if current_price > 0 and target_price else 0
            
            consensus = {
                "target_price": round(target_price, 2) if target_price else "N/A",
                "upside_potential": round(upside, 1) if upside else "N/A",
                "number_of_analysts": num_analysts,
                "recommendation": info.get('recommendationKey', 'N/A').upper(),
                "recommendation_mean": rec_mean
            }
            return consensus
        except Exception as e:
            print(f"❌ Error fetching consensus for {self.ticker}: {e}")
            return {}
    
    def run_research(self) -> Dict[str, Any]:
        print(f"🔍 Fetching REAL data for {self.ticker} from Yahoo Finance...")
        
        price_data = self.fetch_stock_price()
        fundamentals = self.fetch_fundamentals()
        technicals = self.fetch_technical_indicators()
        consensus = self.fetch_analyst_consensus()
        
        # Calculate Simplified Checklists
        rsi = technicals.get("rsi", 50)
        pb = price_data.get("pb_ratio", 0)
        
        checklists = {
            "rsi_monitor": {
                "name": "RSI (14) Monitor",
                "value": rsi,
                "triggered": rsi <= 35 or rsi >= 65,
                "status": "OVERSOLD" if rsi <= 35 else "OVERBOUGHT" if rsi >= 65 else "NORMAL"
            },
            "pb_monitor": {
                "name": "PB Ratio Monitor",
                "value": pb,
                "triggered": pb <= 1.5 and pb > 0,
                "status": "UNDERVALUED" if (pb <= 1.5 and pb > 0) else "NORMAL"
            }
        }
        
        self.data["price"] = price_data
        self.data["fundamentals"] = fundamentals
        self.data["technicals"] = technicals
        self.data["consensus"] = consensus
        self.data["checklists"] = checklists
        
        print(f"✅ Success! Current Price: ${price_data.get('current_price')}")
        return self.data
    
    def save_to_json(self, filepath: str = None):
        if filepath is None:
            filepath = f"research_data_{self.ticker}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        return True

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    try:
        engine = StockResearchEngine(ticker)
        research_data = engine.run_research()
        engine.save_to_json()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
