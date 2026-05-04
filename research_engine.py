#!/usr/bin/env python3
"""
Stock Research Engine v3.0 - Enhanced with Historical Trends, Sentiment, and Smart Checklists
"""

import json
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import yfinance as yf
import urllib.request
import xml.etree.ElementTree as ET
import re

class StockResearchEngine:
    def __init__(self, ticker: str = "AAPL"):
        self.ticker = ticker.upper()
        self.hkt = timezone(timedelta(hours=8))
        self.data = {
            "ticker": self.ticker,
            "company_name": "N/A",
            "description": "N/A",
            "timestamp": datetime.now(self.hkt).isoformat(),
            "updated_at": datetime.now(self.hkt).strftime("%Y-%m-%d %H:%M:%S"),
            "price": {"current_price": 0, "change": 0, "change_percent": 0, "pb_ratio": "N/A", "pe_ratio": "N/A"},
            "consensus": {"recommendation": "N/A", "target_price": "N/A", "upside_potential": "N/A"},
            "fundamentals": {
                "quarter": "N/A",
                "revenue": "N/A",
                "revenue_yoy": "N/A",
                "gross_margin": "N/A",
                "net_margin": "N/A",
                "cash_reserves": "N/A",
                "historical_trends": [] # [{period: "Q1", revenue: 100, net_income: 20}]
            },
            "technicals": {
                "rsi": "N/A",
                "ma_5": "N/A",
                "ma_60": "N/A",
                "osc_20": "N/A",
                "bias_24": "N/A",
                "cci_14": "N/A"
            },
            "news": [],
            "checklists": [], # List of objects for better ordering
            "capital_flow": {
                "market_bucket": "N/A",
                "market_cap": "N/A",
                "volume": "N/A",
                "avg_volume_10d": "N/A",
                "volume_ratio": "N/A",
                "estimated_flow_intensity": "N/A",
                "net_flow_proxy_usd": "N/A"
            }
        }

    def _summarize_description(self, text: str, max_words: int = 30) -> str:
        if not text or text == "N/A":
            return "N/A"
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "..."

    def _get_sentiment(self, title: str) -> str:
        positive_words = ['buy', 'growth', 'up', 'surge', 'beat', 'positive', 'bullish', 'gain', 'profit', 'strong']
        negative_words = ['sell', 'drop', 'down', 'fall', 'miss', 'negative', 'bearish', 'loss', 'weak', 'risk']
        
        title_lower = title.lower()
        score = 0
        for word in positive_words:
            if word in title_lower: score += 1
        for word in negative_words:
            if word in title_lower: score -= 1
            
        if score > 0: return "Positive"
        if score < 0: return "Negative"
        return "Neutral"

    def _fetch_google_news(self):
        try:
            url = f"https://news.google.com/rss/search?q={self.ticker}+stock&hl=en-US&gl=US&ceid=US:en"
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                seen_titles = set()
                count = 0
                for item in root.findall('.//item'):
                    if count >= 4: break
                    title = item.find('title').text if item.find('title') is not None else "N/A"
                    link = item.find('link').text if item.find('link') is not None else "N/A"
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else "N/A"
                    source = item.find('source').text if item.find('source') is not None else "N/A"
                    
                    if " - " in title:
                        title = title.rsplit(" - ", 1)[0]
                    
                    if title != "N/A" and title not in seen_titles:
                        self.data["news"].append({
                            "title": title,
                            "publisher": source,
                            "link": link,
                            "provider_publish_time": pub_date,
                            "sentiment": self._get_sentiment(title)
                        })
                        seen_titles.add(title)
                        count += 1
        except Exception:
            pass

    def _calculate_indicators(self, df):
        try:
            if len(df) < 60: return {}
            close = df['Close']
            ma5 = close.rolling(window=5).mean().iloc[-1]
            ma60 = close.rolling(window=60).mean().iloc[-1]
            ma20 = close.rolling(window=20).mean()
            osc20 = (close - ma20).iloc[-1]
            ma24 = close.rolling(window=24).mean()
            bias24 = ((close - ma24) / ma24 * 100).iloc[-1]
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            ma_tp = tp.rolling(window=14).mean()
            md_tp = tp.rolling(window=14).apply(lambda x: np.abs(x - x.mean()).mean())
            cci14 = ((tp - ma_tp) / (0.015 * md_tp)).iloc[-1]
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
        except:
            return {}

    def run_research(self):
        try:
            t = yf.Ticker(self.ticker)
            hist = pd.DataFrame()
            try:
                hist = t.history(period="1y")
                if hist.empty:
                    hist = t.history(period="1mo")
            except Exception:
                hist = pd.DataFrame()
            
            current_price = 0
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
                self.data["price"].update({
                    "current_price": round(current_price, 3),
                    "change": round(current_price - prev_close, 3),
                    "change_percent": round(((current_price - prev_close) / prev_close) * 100, 2)
                })
                self.data["technicals"].update(self._calculate_indicators(hist))

            try:
                info = t.info
                if info:
                    self.data["company_name"] = info.get('longName', self.ticker)
                    raw_desc = info.get('longBusinessSummary', "N/A")
                    self.data["description"] = self._summarize_description(raw_desc, 30)
                    
                    self.data["price"]["pb_ratio"] = round(float(info.get('priceToBook', 0)), 2) if info.get('priceToBook') else "N/A"
                    self.data["price"]["pe_ratio"] = round(float(info.get('trailingPE', 0)), 2) if info.get('trailingPE') else "N/A"
                    
                    target = info.get('targetMeanPrice')
                    self.data["consensus"].update({
                        "recommendation": str(info.get('recommendationKey', 'N/A')).upper(),
                        "target_price": round(float(target), 2) if target else "N/A",
                        "upside_potential": round(((float(target) - current_price) / current_price) * 100, 1) if target and current_price > 0 else "N/A"
                    })

                    market_cap = info.get("marketCap")
                    volume = info.get("volume")
                    avg_vol = info.get("averageVolume10days") or info.get("averageVolume")
                    bucket = "N/A"
                    if isinstance(market_cap, (int, float)):
                        if market_cap >= 200_000_000_000:
                            bucket = "特大盘"
                        elif market_cap >= 10_000_000_000:
                            bucket = "大盘"
                        elif market_cap >= 2_000_000_000:
                            bucket = "中盘"
                        else:
                            bucket = "小盘"

                    ratio = (float(volume) / float(avg_vol)) if volume and avg_vol else None
                    intensity = "N/A"
                    if ratio is not None:
                        if ratio >= 1.5:
                            intensity = "强流入/强成交"
                        elif ratio >= 1.0:
                            intensity = "中性偏强"
                        else:
                            intensity = "偏弱"

                    net_flow_proxy = (float(volume) * current_price) if volume and current_price else "N/A"
                    self.data["capital_flow"] = {
                        "market_bucket": bucket,
                        "market_cap": float(market_cap) if market_cap else "N/A",
                        "volume": float(volume) if volume else "N/A",
                        "avg_volume_10d": float(avg_vol) if avg_vol else "N/A",
                        "volume_ratio": round(ratio, 2) if ratio is not None else "N/A",
                        "estimated_flow_intensity": intensity,
                        "net_flow_proxy_usd": round(net_flow_proxy, 2) if isinstance(net_flow_proxy, (int, float)) else "N/A"
                    }
            except: pass

            self._fetch_google_news()

            try:
                q_fin = t.quarterly_financials
                if not q_fin.empty:
                    # Historical Trends (Last 4 quarters)
                    trends = []
                    cols = q_fin.columns[:4][::-1] # Get last 4, oldest first
                    for col in cols:
                        q_date = col
                        period = f"Q{(q_date.month-1)//3 + 1} '{str(q_date.year)[2:]}"
                        rev = q_fin.loc['Total Revenue', col] if 'Total Revenue' in q_fin.index else 0
                        ni = q_fin.loc['Net Income', col] if 'Net Income' in q_fin.index else 0
                        trends.append({
                            "period": period,
                            "revenue": float(rev) if not pd.isna(rev) else 0,
                            "net_income": float(ni) if not pd.isna(ni) else 0
                        })
                    self.data["fundamentals"]["historical_trends"] = trends

                    latest_q_date = q_fin.columns[0]
                    self.data["fundamentals"]["quarter"] = f"Q{(latest_q_date.month-1)//3 + 1} {latest_q_date.year}"
                    rev = q_fin.loc['Total Revenue'].iloc[0] if 'Total Revenue' in q_fin.index else "N/A"
                    self.data["fundamentals"]["revenue"] = rev
                    if len(q_fin.columns) > 4 and 'Total Revenue' in q_fin.index:
                        prev_rev = q_fin.loc['Total Revenue'].iloc[4]
                        if prev_rev and prev_rev != 0:
                            self.data["fundamentals"]["revenue_yoy"] = round(float(((rev - prev_rev) / prev_rev) * 100), 1)
                    if 'Gross Profit' in q_fin.index and rev != "N/A" and rev != 0:
                        self.data["fundamentals"]["gross_margin"] = round(float((q_fin.loc['Gross Profit'].iloc[0] / rev) * 100), 1)
                    if 'Net Income' in q_fin.index and rev != "N/A" and rev != 0:
                        self.data["fundamentals"]["net_margin"] = round(float((q_fin.loc['Net Income'].iloc[0] / rev) * 100), 1)
                
                q_bs = t.quarterly_balance_sheet
                if not q_bs.empty:
                    cash = q_bs.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in q_bs.index else \
                           q_bs.loc['Cash Cash Equivalents And Short Term Investments'].iloc[0] if 'Cash Cash Equivalents And Short Term Investments' in q_bs.index else "N/A"
                    self.data["fundamentals"]["cash_reserves"] = cash
            except: pass

            # Smart Checklists
            rsi = self.data["technicals"]["rsi"]
            pb = self.data["price"]["pb_ratio"]
            pe = self.data["price"]["pe_ratio"]
            rev_yoy = self.data["fundamentals"]["revenue_yoy"]
            
            checklists = []
            
            # 1. RSI Monitor
            checklists.append({
                "name": "Technical RSI Monitor",
                "value": f"RSI: {rsi}",
                "status": "OVERSOLD" if isinstance(rsi, (int, float)) and rsi <= 35 else "OVERBOUGHT" if isinstance(rsi, (int, float)) and rsi >= 65 else "NORMAL",
                "triggered": isinstance(rsi, (int, float)) and (rsi <= 35 or rsi >= 65),
                "description": "RSI below 35 suggests oversold (potential buy), above 65 suggests overbought (potential risk)."
            })
            
            # 2. Valuation Monitor
            checklists.append({
                "name": "Valuation (PB) Monitor",
                "value": f"PB: {pb}",
                "status": "UNDERVALUED" if (isinstance(pb, (int, float)) and 0 < pb <= 1.5) else "NORMAL",
                "triggered": isinstance(pb, (int, float)) and 0 < pb <= 1.5,
                "description": "PB ratio below 1.5 often indicates the stock is trading near or below its book value."
            })
            
            # 3. Growth Monitor
            checklists.append({
                "name": "Revenue Growth Monitor",
                "value": f"YoY: {rev_yoy}%" if isinstance(rev_yoy, (int, float)) else "N/A",
                "status": "HIGH GROWTH" if (isinstance(rev_yoy, (int, float)) and rev_yoy > 20) else "STAGNANT" if (isinstance(rev_yoy, (int, float)) and rev_yoy < 0) else "NORMAL",
                "triggered": isinstance(rev_yoy, (int, float)) and (rev_yoy > 20 or rev_yoy < 0),
                "description": "Revenue growth > 20% is a strong positive signal; negative growth is a warning."
            })

            self.data["checklists"] = checklists
            return self.data
        except Exception as e:
            print(f"Error in research: {e}", file=sys.stderr)
            return self.data

    def output_json(self):
        def serialize(obj):
            if hasattr(obj, 'item'): return obj.item()
            if isinstance(obj, (datetime, pd.Timestamp)): return obj.isoformat()
            return str(obj)
        print(json.dumps(self.data, ensure_ascii=False, default=serialize))

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    engine = StockResearchEngine(ticker)
    engine.run_research()
    engine.output_json()
