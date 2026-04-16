#!/usr/bin/env python3
"""
Stock Research Engine
自动进行深度调研，抓取实时数据并生成分析报告
集成 Yahoo Finance API 获取真实股票数据
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  Warning: yfinance not installed. Using mock data.")
    print("   To use real data, run: pip3 install yfinance")


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
        """获取实时股票价格 - 使用 Yahoo Finance API"""
        try:
            if not YFINANCE_AVAILABLE:
                return self._get_mock_price()
            
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            hist = ticker.history(period="1y")
            
            if hist.empty or info is None:
                print(f"⚠️  Warning: Could not fetch data for {self.ticker}, using mock data")
                return self._get_mock_price()
            
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            price_data = {
                "current_price": round(current_price, 3),
                "change": round(info.get('regularMarketChange', 0), 3),
                "change_percent": round(info.get('regularMarketChangePercent', 0), 2),
                "high_52w": round(info.get('fiftyTwoWeekHigh', 0), 2),
                "low_52w": round(info.get('fiftyTwoWeekLow', 0), 2),
                "market_cap": self._format_market_cap(info.get('marketCap', 0)),
                "pe_ratio": round(info.get('trailingPE', 0), 2),
                "volume": self._format_volume(info.get('volume', 0)),
                "avg_volume": self._format_volume(info.get('averageVolume', 0)),
                "dividend_yield": round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else 0
            }
            return price_data
        except Exception as e:
            print(f"⚠️  Error fetching stock price: {e}")
            return self._get_mock_price()
    
    def _get_mock_price(self) -> Dict[str, Any]:
        """获取模拟价格数据"""
        return {
            "current_price": 34.542,
            "change": -0.458,
            "change_percent": -1.31,
            "high_52w": 42.27,
            "low_52w": 15.20,
            "market_cap": "2.5B",
            "pe_ratio": 45.2,
            "volume": "5.2M",
            "avg_volume": "4.8M",
            "dividend_yield": 0
        }
    
    def _format_market_cap(self, value: float) -> str:
        """格式化市值"""
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        return f"${value:.0f}"
    
    def _format_volume(self, value: float) -> str:
        """格式化成交量"""
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return f"{value:.0f}"
    
    def fetch_fundamentals(self) -> Dict[str, Any]:
        """获取基本面数据 - 使用 Yahoo Finance API"""
        try:
            if not YFINANCE_AVAILABLE:
                return self._get_mock_fundamentals()
            
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            
            if info is None:
                return self._get_mock_fundamentals()
            
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
            print(f"⚠️  Error fetching fundamentals: {e}")
            return self._get_mock_fundamentals()
    
    def _get_mock_fundamentals(self) -> Dict[str, Any]:
        """获取模拟基本面数据"""
        return {
            "revenue": 507000000,
            "revenue_per_share": 15.2,
            "gross_margin": 93,
            "operating_margin": 12.5,
            "net_margin": 9.4,
            "roe": 18.5,
            "debt_to_equity": 0.25,
            "current_ratio": 2.1,
            "book_value": 12.5,
            "earnings_per_share": 0.75,
            "forward_eps": 0.92
        }
    
    def fetch_technical_indicators(self) -> Dict[str, Any]:
        """获取技术指标"""
        try:
            if not YFINANCE_AVAILABLE:
                return self._get_mock_technicals()
            
            ticker = yf.Ticker(self.ticker)
            hist = ticker.history(period="1y")
            
            if hist.empty:
                return self._get_mock_technicals()
            
            # 计算移动平均线
            ma_5 = hist['Close'].tail(5).mean()
            ma_20 = hist['Close'].tail(20).mean()
            ma_60 = hist['Close'].tail(60).mean()
            
            # 计算布林带
            ma_20_full = hist['Close'].tail(20).mean()
            std_20 = hist['Close'].tail(20).std()
            
            technicals = {
                "ma_5": round(ma_5, 2),
                "ma_20": round(ma_20, 2),
                "ma_60": round(ma_60, 2),
                "bollinger_upper": round(ma_20_full + (std_20 * 2), 2),
                "bollinger_middle": round(ma_20_full, 2),
                "bollinger_lower": round(ma_20_full - (std_20 * 2), 2),
                "rsi": self._calculate_rsi(hist['Close']),
                "macd": self._calculate_macd(hist['Close'])
            }
            return technicals
        except Exception as e:
            print(f"⚠️  Error fetching technical indicators: {e}")
            return self._get_mock_technicals()
    
    def _get_mock_technicals(self) -> Dict[str, Any]:
        """获取模拟技术指标"""
        return {
            "ma_5": 36.30,
            "ma_20": 32.79,
            "ma_60": 44.92,
            "bollinger_upper": 40.50,
            "bollinger_middle": 32.79,
            "bollinger_lower": 25.69,
            "rsi": 68,
            "macd": 0.85
        }
    
    def _calculate_rsi(self, prices, period=14) -> float:
        """计算 RSI 指标"""
        try:
            if len(prices) < period:
                return 50
            
            deltas = prices.diff()
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum() / period
            down = -seed[seed < 0].sum() / period
            
            rs = up / down if down != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            return round(rsi, 2)
        except:
            return 50
    
    def _calculate_macd(self, prices) -> float:
        """计算 MACD 指标"""
        try:
            if len(prices) < 26:
                return 0
            
            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()
            macd = ema_12 - ema_26
            return round(macd.iloc[-1], 4)
        except:
            return 0
    
    def fetch_analyst_consensus(self) -> Dict[str, Any]:
        """获取分析师共识"""
        try:
            if not YFINANCE_AVAILABLE:
                return self._get_mock_consensus()
            
            ticker = yf.Ticker(self.ticker)
            info = ticker.info
            
            if info is None:
                return self._get_mock_consensus()
            
            target_price = info.get('targetMeanPrice', 0)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            upside = ((target_price - current_price) / current_price * 100) if current_price > 0 else 0
            
            consensus = {
                "target_price": round(target_price, 2),
                "upside_potential": round(upside, 1),
                "number_of_analysts": info.get('numberOfAnalysts', 0),
                "recommendation": info.get('recommendationKey', 'none')
            }
            return consensus
        except Exception as e:
            print(f"⚠️  Error fetching analyst consensus: {e}")
            return self._get_mock_consensus()
    
    def _get_mock_consensus(self) -> Dict[str, Any]:
        """获取模拟分析师共识"""
        return {
            "target_price": 56.89,
            "upside_potential": 65,
            "number_of_analysts": 22,
            "recommendation": "buy"
        }
    
    def generate_strategy(self, current_price: float) -> Dict[str, Any]:
        """生成交易策略"""
        strategy = {
            "stage_1": {
                "triggered": current_price >= 34.42,
                "price_range": "34.42 - 35.6",
                "quantity": "基础舱",
                "target": "保本",
                "status": "已触发" if current_price >= 34.42 else "未触发"
            },
            "stage_2": {
                "triggered": current_price >= 37.6,
                "price_range": "37.6 - 38.0",
                "quantity": "部分仓位",
                "target": "首次获利",
                "status": "监控中"
            },
            "stage_3": {
                "triggered": current_price >= 39.5,
                "price_range": "39.5 - 40.0",
                "quantity": "剩余仓位",
                "target": "完成清仓",
                "status": "目标中"
            },
            "risk_control": {
                "stop_loss": 32.80,
                "time_trigger": 90  # 天数
            }
        }
        return strategy
    
    def run_research(self) -> Dict[str, Any]:
        """运行完整的调研流程"""
        print(f"🔍 开始调研 {self.ticker}...")
        
        # 获取各类数据
        price_data = self.fetch_stock_price()
        fundamentals = self.fetch_fundamentals()
        technicals = self.fetch_technical_indicators()
        consensus = self.fetch_analyst_consensus()
        
        current_price = price_data.get("current_price", 34.542)
        strategy = self.generate_strategy(current_price)
        
        # 组织数据
        self.data["price"] = price_data
        self.data["fundamentals"] = fundamentals
        self.data["technicals"] = technicals
        self.data["consensus"] = consensus
        self.data["strategy"] = strategy
        self.data["updated_at"] = datetime.now().isoformat()
        
        print(f"✅ 调研完成！当前股价: ${current_price}")
        return self.data
    
    def save_to_json(self, filepath: str = None):
        """保存数据到 JSON 文件"""
        if filepath is None:
            filepath = f"research_data_{self.ticker}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print(f"💾 数据已保存到 {filepath}")
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False


if __name__ == "__main__":
    # 获取命令行参数中的股票代码，默认为 FIGR
    ticker = sys.argv[1] if len(sys.argv) > 1 else "FIGR"
    
    engine = StockResearchEngine(ticker)
    research_data = engine.run_research()
    engine.save_to_json()
    
    # 打印摘要
    print("\n" + "="*50)
    print("📊 调研摘要")
    print("="*50)
    print(f"股票代码: {ticker}")
    print(f"当前股价: ${research_data['price']['current_price']}")
    print(f"目标价: ${research_data['consensus']['target_price']}")
    print(f"上升空间: +{research_data['consensus']['upside_potential']}%")
    print(f"第一阶段状态: {research_data['strategy']['stage_1']['status']}")
    print("="*50)
