#!/usr/bin/env python3
"""
Stock Research Engine
100% Real-time data from Yahoo Finance API
No mock data allowed.
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any
import yfinance as yf

class StockResearchEngine:
    def __init__(self, ticker: str = "FIGR"):
        self.ticker = ticker.upper()
        self.data = {
            "ticker": self.ticker,
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "fundamentals": {},
            "technicals": {},
            "sentiment": {},
            "strategy": {}
        }
    
    def fetch_stock_price(self) -> Dict[str, Any]:
        """获取实时股票价格 - 强制使用 Yahoo Finance API"""
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
            return f"${value / 1_000:.1f}M"
        return f"${value:.0f}"
    
    def _format_volume(self, value: float) -> str:
        if not value: return "N/A"
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return f"{value:.0f}"
    
    def fetch_fundamentals(self) -> Dict[str, Any]:
        """获取基本面数据 - 强制使用 Yahoo Finance API"""
        try:
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            
            if not info:
                raise ValueError(f"No fundamental data found for {self.ticker}")
            
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
            raise e
    
    def fetch_technical_indicators(self) -> Dict[str, Any]:
        """获取技术指标 - 强制使用 Yahoo Finance API"""
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
            raise e
    
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
        """获取分析师共识 - 强制使用 Yahoo Finance API"""
        try:
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            
            target_price = info.get('targetMeanPrice', 0)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            upside = ((target_price - current_price) / current_price * 100) if current_price > 0 and target_price else 0
            
            consensus = {
                "target_price": round(target_price, 2) if target_price else "N/A",
                "upside_potential": round(upside, 1) if upside else "N/A",
                "number_of_analysts": info.get('numberOfAnalysts', 0),
                "recommendation": info.get('recommendationKey', 'N/A')
            }
            return consensus
        except Exception as e:
            print(f"❌ Error fetching consensus for {self.ticker}: {e}")
            raise e
    
    def generate_strategy(self, current_price: float) -> Dict[str, Any]:
        """基于真实价格生成动态策略"""
        # 这里的策略逻辑可以根据真实价格动态调整，不再使用硬编码的 34.42
        p = current_price
        strategy = {
            "stage_1": {
                "triggered": True,
                "price_range": f"{round(p*0.98, 2)} - {round(p*1.02, 2)}",
                "quantity": "基础仓位",
                "target": "建立底仓",
                "status": "已执行"
            },
            "stage_2": {
                "triggered": False,
                "price_range": f"{round(p*1.05, 2)} - {round(p*1.08, 2)}",
                "quantity": "加仓",
                "target": "趋势确认",
                "status": "监控中"
            },
            "stage_3": {
                "triggered": False,
                "price_range": f"{round(p*1.15, 2)} - {round(p*1.20, 2)}",
                "quantity": "止盈",
                "target": "获利了结",
                "status": "目标中"
            },
            "risk_control": {
                "stop_loss": round(p*0.95, 2),
                "time_trigger": 30
            }
        }
        return strategy
    
    def run_research(self) -> Dict[str, Any]:
        print(f"🔍 Fetching REAL data for {self.ticker} from Yahoo Finance...")
        
        price_data = self.fetch_stock_price()
        fundamentals = self.fetch_fundamentals()
        technicals = self.fetch_technical_indicators()
        consensus = self.fetch_analyst_consensus()
        
        current_price = price_data.get("current_price")
        strategy = self.generate_strategy(current_price)
        
        self.data["price"] = price_data
        self.data["fundamentals"] = fundamentals
        self.data["technicals"] = technicals
        self.data["consensus"] = consensus
        self.data["strategy"] = strategy
        self.data["updated_at"] = datetime.now().isoformat()
        
        print(f"✅ Success! Current Price: ${current_price}")
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
