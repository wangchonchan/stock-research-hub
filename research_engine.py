#!/usr/bin/env python3
"""
Stock Research Engine v3.2 - Robust Data Fetching & Comprehensive Capital Flow Analysis
"""

import json
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import requests
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
            "price": {
                "current_price": 0,
                "change": 0,
                "change_percent": 0,
                "pb_ratio": "N/A",
                "pe_ratio": "N/A",
            },
            "consensus": {
                "recommendation": "N/A",
                "target_price": "N/A",
                "upside_potential": "N/A",
            },
            "fundamentals": {
                "quarter": "N/A",
                "revenue": "N/A",
                "revenue_yoy": "N/A",
                "gross_margin": "N/A",
                "net_margin": "N/A",
                "cash_reserves": "N/A",
                "historical_trends": [],
            },
            "technicals": {
                "rsi": "N/A",
                "ma_5": "N/A",
                "ma_60": "N/A",
                "osc_20": "N/A",
                "bias_24": "N/A",
                "cci_14": "N/A",
            },
            "capital_flow": {
                "market_bucket": "N/A",
                "market_cap": "N/A",
                "volume": "N/A",
                "avg_volume_10d": "N/A",
                "volume_ratio": "N/A",
                "estimated_flow_intensity": "N/A",
                "net_flow_proxy_usd": "N/A",
                "market_wide_flow": {
                    "mega_cap": "Neutral",
                    "large_cap": "Neutral",
                    "small_cap": "Neutral",
                },
                "market_flow_details": [],
                "sector_flow_details": [],
                "flow_destination_summary": {
                    "top_inflow": "N/A",
                    "top_outflow": "N/A",
                    "risk_appetite": "N/A",
                },
                "institutional_flow": {
                    "available": False,
                    "source": "Alpha Vantage INSTITUTIONAL_HOLDINGS",
                    "latest_report_date": "N/A",
                    "note": "需要配置 ALPHA_VANTAGE_API_KEY 才能显示真实 13F 机构持仓数据。",
                    "top_holders": [],
                    "top_increases": [],
                    "top_decreases": [],
                },
            },
            "news": [],
            "checklists": [],
            "diagnostics": [],
        }

    def _summarize_description(self, text: str, max_words: int = 30) -> str:
        if not text or text == "N/A":
            return "N/A"
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "..."

    def _get_sentiment(self, title: str) -> str:
        positive_words = [
            "buy",
            "growth",
            "up",
            "surge",
            "beat",
            "positive",
            "bullish",
            "gain",
            "profit",
            "strong",
        ]
        negative_words = [
            "sell",
            "drop",
            "down",
            "fall",
            "miss",
            "negative",
            "bearish",
            "loss",
            "weak",
            "risk",
        ]

        title_lower = title.lower()
        score = 0
        for word in positive_words:
            if word in title_lower:
                score += 1
        for word in negative_words:
            if word in title_lower:
                score -= 1

        if score > 0:
            return "Positive"
        if score < 0:
            return "Negative"
        return "中性"

    def _fetch_google_news(self):
        try:
            url = f"https://news.google.com/rss/search?q={self.ticker}+stock&hl=en-US&gl=US&ceid=US:en"
            headers = {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)

                seen_titles = set()
                count = 0
                for item in root.findall(".//item"):
                    if count >= 4:
                        break
                    title = (
                        item.find("title").text
                        if item.find("title") is not None
                        else "N/A"
                    )
                    link = (
                        item.find("link").text
                        if item.find("link") is not None
                        else "N/A"
                    )
                    pub_date = (
                        item.find("pubDate").text
                        if item.find("pubDate") is not None
                        else "N/A"
                    )
                    source = (
                        item.find("source").text
                        if item.find("source") is not None
                        else "N/A"
                    )

                    if " - " in title:
                        title = title.rsplit(" - ", 1)[0]

                    if title != "N/A" and title not in seen_titles:
                        self.data["news"].append(
                            {
                                "title": title,
                                "publisher": source,
                                "link": link,
                                "provider_publish_time": pub_date,
                                "sentiment": self._get_sentiment(title),
                            }
                        )
                        seen_titles.add(title)
                        count += 1
        except Exception:
            pass

    def _calculate_indicators(self, df):
        try:
            if len(df) < 60:
                return {}
            close = df["Close"]
            ma5 = close.rolling(window=5).mean().iloc[-1]
            ma60 = close.rolling(window=60).mean().iloc[-1]
            ma20 = close.rolling(window=20).mean()
            osc20 = (close - ma20).iloc[-1]
            ma24 = close.rolling(window=24).mean()
            bias24 = ((close - ma24) / ma24 * 100).iloc[-1]
            tp = (df["High"] + df["Low"] + df["Close"]) / 3
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
                "rsi": round(float(rsi_val), 2) if not pd.isna(rsi_val) else "N/A",
            }
        except:
            return {}

    def _to_float(self, value, default: float = 0) -> float:
        if value is None or value == "N/A":
            return default
        try:
            return float(str(value).replace(",", ""))
        except Exception:
            return default

    def _first_value(self, record: Dict[str, Any], keys: List[str], default="N/A"):
        for key in keys:
            if key in record and record[key] not in (None, ""):
                return record[key]
        return default

    def _normalize_institutional_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        holder = self._first_value(
            record,
            [
                "holder",
                "holderName",
                "institution",
                "institutionName",
                "entityProperName",
                "name",
            ],
        )
        report_date = self._first_value(
            record,
            [
                "date",
                "reportDate",
                "reportedDate",
                "filingDate",
                "periodOfReport",
                "period",
            ],
        )
        shares = self._to_float(
            self._first_value(record, ["shares", "share", "sshPrnamt", "sharesHeld"])
        )
        value = self._to_float(
            self._first_value(
                record, ["value", "marketValue", "value_usd", "market_value"]
            )
        )
        change = self._to_float(
            self._first_value(
                record,
                ["change", "changeInShares", "sharesChange", "change_shares"],
                None,
            ),
            None,
        )
        return {
            "holder": str(holder),
            "report_date": str(report_date),
            "shares": shares,
            "market_value_usd": value,
            "change_shares": change,
        }

    def _fetch_institutional_flow(self) -> Dict[str, Any]:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv(
            "ALPHAVANTAGE_API_KEY"
        )
        base = {
            "available": False,
            "source": "Alpha Vantage INSTITUTIONAL_HOLDINGS",
            "latest_report_date": "N/A",
            "note": "需要配置 ALPHA_VANTAGE_API_KEY 才能显示真实 13F 机构持仓数据。",
            "top_holders": [],
            "top_increases": [],
            "top_decreases": [],
        }
        if not api_key:
            return base

        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "INSTITUTIONAL_HOLDINGS",
                    "symbol": self.ticker,
                    "apikey": api_key,
                },
                timeout=8,
                headers={"User-Agent": "stock-research-hub/1.0"},
            )
            response.raise_for_status()
            payload = response.json()
            if (
                "Information" in payload
                or "Note" in payload
                or "Error Message" in payload
            ):
                base["note"] = (
                    payload.get("Information")
                    or payload.get("Note")
                    or payload.get("Error Message")
                )
                return base

            raw_records = None
            for key in (
                "data",
                "holdings",
                "institutionalHoldings",
                "institutional_holders",
            ):
                if isinstance(payload.get(key), list):
                    raw_records = payload[key]
                    break
            if raw_records is None and isinstance(payload, list):
                raw_records = payload
            if not raw_records:
                base["note"] = "API 未返回机构持仓记录。"
                return base

            records = [
                self._normalize_institutional_record(item)
                for item in raw_records
                if isinstance(item, dict)
            ]
            records = [item for item in records if item["holder"] != "N/A"]
            if not records:
                base["note"] = "API 返回格式中没有可识别的机构持仓字段。"
                return base

            latest_date = (
                max(
                    item["report_date"]
                    for item in records
                    if item["report_date"] != "N/A"
                )
                if any(item["report_date"] != "N/A" for item in records)
                else "N/A"
            )
            latest_records = (
                [item for item in records if item["report_date"] == latest_date]
                if latest_date != "N/A"
                else records
            )
            latest_records.sort(key=lambda item: item["market_value_usd"], reverse=True)

            increases = []
            decreases = []
            for item in records:
                if isinstance(item["change_shares"], (int, float)):
                    if item["change_shares"] > 0:
                        increases.append(item)
                    elif item["change_shares"] < 0:
                        decreases.append(item)
            increases.sort(key=lambda item: item["change_shares"], reverse=True)
            decreases.sort(key=lambda item: item["change_shares"])

            return {
                "available": True,
                "source": "Alpha Vantage INSTITUTIONAL_HOLDINGS",
                "latest_report_date": latest_date,
                "note": "真实 13F 机构持仓数据；通常按季度披露，存在报告延迟，不代表实时逐笔资金流。",
                "top_holders": latest_records[:8],
                "top_increases": increases[:5],
                "top_decreases": decreases[:5],
            }
        except Exception as e:
            self.data["diagnostics"].append(f"institutional_flow_unavailable: {e}")
            base["note"] = f"机构持仓 API 请求失败：{e}"
            return base

    def _flow_intensity(self, change_pct: float, volume_ratio: float) -> str:
        if change_pct > 0 and volume_ratio >= 1.2:
            return "强流入/强成交"
        if change_pct > 0:
            return "温和流入"
        if change_pct < 0 and volume_ratio >= 1.2:
            return "强流出/放量下跌"
        if change_pct < 0:
            return "温和流出"
        return "中性"

    def _flow_direction(self, change_pct: float) -> str:
        if change_pct > 0:
            return "流入"
        if change_pct < 0:
            return "流出"
        return "中性"

    def _build_flow_detail(
        self, symbol: str, label: str, category: str, hist
    ) -> Dict[str, Any]:
        if hist is None or hist.empty or len(hist) < 2:
            return {
                "symbol": symbol,
                "label": label,
                "category": category,
                "direction": "中性",
                "intensity": "N/A",
                "change_percent": "N/A",
                "volume_ratio": "N/A",
                "dollar_volume_proxy_usd": "N/A",
                "signed_flow_proxy_usd": "N/A",
            }

        close = hist["Close"].dropna()
        volume_series = hist["Volume"].dropna()
        if len(close) < 2 or volume_series.empty:
            return {
                "symbol": symbol,
                "label": label,
                "category": category,
                "direction": "中性",
                "intensity": "N/A",
                "change_percent": "N/A",
                "volume_ratio": "N/A",
                "dollar_volume_proxy_usd": "N/A",
                "signed_flow_proxy_usd": "N/A",
            }

        latest_close = float(close.iloc[-1])
        prev_close = float(close.iloc[-2])
        latest_volume = float(volume_series.iloc[-1])
        avg_volume = (
            float(volume_series.tail(10).mean())
            if len(volume_series) >= 10
            else float(volume_series.mean())
        )
        change_pct = (
            ((latest_close - prev_close) / prev_close) * 100 if prev_close else 0
        )
        volume_ratio = latest_volume / avg_volume if avg_volume else 0
        dollar_volume = latest_close * latest_volume
        direction = self._flow_direction(change_pct)
        signed_flow = (
            dollar_volume
            if direction == "流入"
            else -dollar_volume if direction == "流出" else 0
        )

        return {
            "symbol": symbol,
            "label": label,
            "category": category,
            "direction": direction,
            "intensity": self._flow_intensity(change_pct, volume_ratio),
            "change_percent": round(change_pct, 2),
            "volume_ratio": round(volume_ratio, 2),
            "dollar_volume_proxy_usd": round(dollar_volume, 2),
            "signed_flow_proxy_usd": round(signed_flow, 2),
        }

    def _download_flow_history(self, symbols: List[str]):
        try:
            return yf.download(
                symbols,
                period="15d",
                interval="1d",
                group_by="ticker",
                progress=False,
                threads=True,
                auto_adjust=False,
                timeout=5,
            )
        except Exception as e:
            self.data["diagnostics"].append(f"flow_history_unavailable: {e}")
            return None

    def _extract_symbol_history(self, downloaded, symbol: str):
        if downloaded is None or downloaded.empty:
            return pd.DataFrame()
        try:
            if isinstance(downloaded.columns, pd.MultiIndex):
                return downloaded[symbol].dropna(how="all")
            return downloaded.dropna(how="all")
        except Exception:
            return pd.DataFrame()

    def _get_market_flow_analysis(self):
        try:
            market_targets = [
                ("SPY", "S&P 500 / 大盘核心", "Broad Market"),
                ("QQQ", "Nasdaq 100 / 科技成长", "Growth"),
                ("IWM", "Russell 2000 / 小盘", "Small Cap"),
                ("DIA", "Dow 30 / 蓝筹", "Blue Chip"),
                ("RSP", "S&P 500 等权重", "Equal Weight"),
            ]
            sector_targets = [
                ("XLK", "科技 Technology", "Sector"),
                ("XLF", "金融 Financials", "Sector"),
                ("XLV", "医疗 Health Care", "Sector"),
                ("XLY", "可选消费 Consumer Discretionary", "Sector"),
                ("XLP", "必需消费 Consumer Staples", "Sector"),
                ("XLE", "能源 Energy", "Sector"),
                ("XLI", "工业 Industrials", "Sector"),
                ("XLC", "通信 Communication", "Sector"),
                ("XLU", "公用事业 Utilities", "Sector"),
                ("XLB", "材料 Materials", "Sector"),
                ("XLRE", "房地产 Real Estate", "Sector"),
            ]
            all_targets = market_targets + sector_targets
            downloaded = self._download_flow_history(
                [symbol for symbol, _, _ in all_targets]
            )

            details = []
            for symbol, label, category in all_targets:
                details.append(
                    self._build_flow_detail(
                        symbol,
                        label,
                        category,
                        self._extract_symbol_history(downloaded, symbol),
                    )
                )

            market_details = [item for item in details if item["category"] != "Sector"]
            sector_details = [item for item in details if item["category"] == "Sector"]
            sector_details.sort(
                key=lambda item: (
                    item["signed_flow_proxy_usd"]
                    if isinstance(item["signed_flow_proxy_usd"], (int, float))
                    else 0
                ),
                reverse=True,
            )

            def label_for(symbol: str, fallback: str) -> str:
                match = next(
                    (item for item in market_details if item["symbol"] == symbol), None
                )
                return match["intensity"] if match else fallback

            inflows = [
                item
                for item in sector_details
                if isinstance(item["signed_flow_proxy_usd"], (int, float))
                and item["signed_flow_proxy_usd"] > 0
            ]
            outflows = [
                item
                for item in sector_details
                if isinstance(item["signed_flow_proxy_usd"], (int, float))
                and item["signed_flow_proxy_usd"] < 0
            ]
            outflows.sort(key=lambda item: item["signed_flow_proxy_usd"])

            qqq = next(
                (item for item in market_details if item["symbol"] == "QQQ"), None
            )
            iwm = next(
                (item for item in market_details if item["symbol"] == "IWM"), None
            )
            risk_appetite = "N/A"
            if (
                qqq
                and iwm
                and isinstance(qqq["change_percent"], (int, float))
                and isinstance(iwm["change_percent"], (int, float))
            ):
                if qqq["change_percent"] > 0 and iwm["change_percent"] > 0:
                    risk_appetite = "风险偏好增强：成长与小盘同步走强"
                elif qqq["change_percent"] < 0 and iwm["change_percent"] < 0:
                    risk_appetite = "风险偏好下降：成长与小盘同步承压"
                elif qqq["change_percent"] > iwm["change_percent"]:
                    risk_appetite = "偏成长/科技，资金更集中在 Nasdaq"
                else:
                    risk_appetite = "偏小盘/扩散，资金更偏向 Russell 2000"

            return {
                "market_wide_flow": {
                    "mega_cap": label_for("SPY", "Neutral"),
                    "large_cap": label_for("SPY", "Neutral"),
                    "small_cap": label_for("IWM", "Neutral"),
                },
                "market_flow_details": market_details,
                "sector_flow_details": sector_details,
                "flow_destination_summary": {
                    "top_inflow": inflows[0]["label"] if inflows else "N/A",
                    "top_outflow": outflows[0]["label"] if outflows else "N/A",
                    "risk_appetite": risk_appetite,
                },
            }
        except Exception as e:
            self.data["diagnostics"].append(f"market_flow_unavailable: {e}")
            return {
                "market_wide_flow": {
                    "mega_cap": "Neutral",
                    "large_cap": "Neutral",
                    "small_cap": "Neutral",
                },
                "market_flow_details": [],
                "sector_flow_details": [],
                "flow_destination_summary": {
                    "top_inflow": "N/A",
                    "top_outflow": "N/A",
                    "risk_appetite": "N/A",
                },
            }

    def run_research(self):
        try:
            t = yf.Ticker(self.ticker)

            # 1. Price History & Technicals
            try:
                # Try multiple periods if 1y fails
                hist = t.history(period="1y")
                if hist.empty:
                    hist = t.history(period="1mo")
                if hist.empty:
                    hist = t.history(period="5d")

                if not hist.empty:
                    current_price = float(hist["Close"].iloc[-1])
                    prev_close = (
                        float(hist["Close"].iloc[-2])
                        if len(hist) > 1
                        else current_price
                    )
                    self.data["price"].update(
                        {
                            "current_price": round(current_price, 3),
                            "change": round(current_price - prev_close, 3),
                            "change_percent": round(
                                ((current_price - prev_close) / prev_close) * 100, 2
                            ),
                        }
                    )
                    self.data["technicals"].update(self._calculate_indicators(hist))
                else:
                    # Fallback to fast_info if history is empty
                    try:
                        current_price = t.fast_info["lastPrice"]
                        self.data["price"]["current_price"] = round(current_price, 3)
                    except:
                        current_price = 0
            except Exception as e:
                self.data["diagnostics"].append(f"price_history_unavailable: {e}")
                current_price = 0

            # 2. Company Info & Capital Flow
            try:
                info = t.info
                if info:
                    self.data["company_name"] = info.get("longName", self.ticker)
                    raw_desc = info.get("longBusinessSummary", "N/A")
                    self.data["description"] = self._summarize_description(raw_desc, 30)

                    self.data["price"]["pb_ratio"] = (
                        round(float(info.get("priceToBook", 0)), 2)
                        if info.get("priceToBook")
                        else "N/A"
                    )
                    self.data["price"]["pe_ratio"] = (
                        round(float(info.get("trailingPE", 0)), 2)
                        if info.get("trailingPE")
                        else "N/A"
                    )

                    target = info.get("targetMeanPrice")
                    if target and current_price > 0:
                        self.data["consensus"].update(
                            {
                                "recommendation": str(
                                    info.get("recommendationKey", "N/A")
                                ).upper(),
                                "target_price": round(float(target), 2),
                                "upside_potential": round(
                                    ((float(target) - current_price) / current_price)
                                    * 100,
                                    1,
                                ),
                            }
                        )

                    # Capital Flow Analysis
                    market_cap = info.get("marketCap")
                    volume = info.get("volume") or info.get("regularMarketVolume")
                    avg_vol = info.get("averageVolume10days") or info.get(
                        "averageVolume"
                    )

                    bucket = "N/A"
                    if isinstance(market_cap, (int, float)):
                        if market_cap >= 200_000_000_000:
                            bucket = "特大盘 (Mega Cap)"
                        elif market_cap >= 10_000_000_000:
                            bucket = "大盘 (Large Cap)"
                        elif market_cap >= 2_000_000_000:
                            bucket = "中盘 (Mid Cap)"
                        else:
                            bucket = "小盘 (Small Cap)"

                    ratio = (
                        (float(volume) / float(avg_vol)) if volume and avg_vol else None
                    )
                    intensity = "N/A"
                    if ratio is not None:
                        if ratio >= 1.5:
                            intensity = "强流入/强成交"
                        elif ratio >= 1.0:
                            intensity = "中性偏强"
                        else:
                            intensity = "偏弱"

                    net_flow_proxy = (
                        (float(volume) * current_price)
                        if volume and current_price
                        else "N/A"
                    )
                    self.data["capital_flow"] = {
                        "market_bucket": bucket,
                        "market_cap": float(market_cap) if market_cap else "N/A",
                        "volume": float(volume) if volume else "N/A",
                        "avg_volume_10d": float(avg_vol) if avg_vol else "N/A",
                        "volume_ratio": round(ratio, 2) if ratio is not None else "N/A",
                        "estimated_flow_intensity": intensity,
                        "net_flow_proxy_usd": (
                            round(net_flow_proxy, 2)
                            if isinstance(net_flow_proxy, (int, float))
                            else "N/A"
                        ),
                        **self._get_market_flow_analysis(),
                    }
                    self.data["capital_flow"][
                        "institutional_flow"
                    ] = self._fetch_institutional_flow()
            except Exception as e:
                self.data["diagnostics"].append(f"profile_unavailable: {e}")

            # 3. News
            self._fetch_google_news()

            # 4. Fundamentals
            try:
                q_fin = t.quarterly_financials
                if not q_fin.empty:
                    trends = []
                    cols = q_fin.columns[:4][::-1]
                    for col in cols:
                        q_date = col
                        period = f"Q{(q_date.month-1)//3 + 1} '{str(q_date.year)[2:]}"
                        rev = (
                            q_fin.loc["Total Revenue", col]
                            if "Total Revenue" in q_fin.index
                            else 0
                        )
                        ni = (
                            q_fin.loc["Net Income", col]
                            if "Net Income" in q_fin.index
                            else 0
                        )
                        trends.append(
                            {
                                "period": period,
                                "revenue": float(rev) if not pd.isna(rev) else 0,
                                "net_income": float(ni) if not pd.isna(ni) else 0,
                            }
                        )
                    self.data["fundamentals"]["historical_trends"] = trends

                    latest_q_date = q_fin.columns[0]
                    self.data["fundamentals"][
                        "quarter"
                    ] = f"Q{(latest_q_date.month-1)//3 + 1} {latest_q_date.year}"
                    rev = (
                        q_fin.loc["Total Revenue"].iloc[0]
                        if "Total Revenue" in q_fin.index
                        else "N/A"
                    )
                    self.data["fundamentals"]["revenue"] = rev

                    if len(q_fin.columns) > 4 and "Total Revenue" in q_fin.index:
                        prev_rev = q_fin.loc["Total Revenue"].iloc[4]
                        if prev_rev and prev_rev != 0:
                            self.data["fundamentals"]["revenue_yoy"] = round(
                                float(((rev - prev_rev) / prev_rev) * 100), 1
                            )

                    if "Gross Profit" in q_fin.index and rev != "N/A" and rev != 0:
                        self.data["fundamentals"]["gross_margin"] = round(
                            float((q_fin.loc["Gross Profit"].iloc[0] / rev) * 100), 1
                        )
                    if "Net Income" in q_fin.index and rev != "N/A" and rev != 0:
                        self.data["fundamentals"]["net_margin"] = round(
                            float((q_fin.loc["Net Income"].iloc[0] / rev) * 100), 1
                        )

                q_bs = t.quarterly_balance_sheet
                if not q_bs.empty:
                    cash = (
                        q_bs.loc["Cash And Cash Equivalents"].iloc[0]
                        if "Cash And Cash Equivalents" in q_bs.index
                        else (
                            q_bs.loc[
                                "Cash Cash Equivalents And Short Term Investments"
                            ].iloc[0]
                            if "Cash Cash Equivalents And Short Term Investments"
                            in q_bs.index
                            else "N/A"
                        )
                    )
                    self.data["fundamentals"]["cash_reserves"] = cash
            except Exception as e:
                self.data["diagnostics"].append(f"fundamentals_unavailable: {e}")

            # 5. Smart Checklists
            rsi = self.data["technicals"]["rsi"]
            pb = self.data["price"]["pb_ratio"]
            rev_yoy = self.data["fundamentals"]["revenue_yoy"]

            checklists = []
            checklists.append(
                {
                    "name": "技术 RSI 监控",
                    "value": f"RSI: {rsi}",
                    "status": (
                        "超卖"
                        if isinstance(rsi, (int, float)) and rsi <= 35
                        else (
                            "超买"
                            if isinstance(rsi, (int, float)) and rsi >= 65
                            else "正常"
                        )
                    ),
                    "triggered": isinstance(rsi, (int, float))
                    and (rsi <= 35 or rsi >= 65),
                    "description": "RSI 低于 35 通常代表超卖，高于 65 通常代表超买风险。",
                }
            )
            checklists.append(
                {
                    "name": "估值（PB）监控",
                    "value": f"PB: {pb}",
                    "status": (
                        "低估"
                        if (isinstance(pb, (int, float)) and 0 < pb <= 1.5)
                        else "正常"
                    ),
                    "triggered": isinstance(pb, (int, float)) and 0 < pb <= 1.5,
                    "description": "PB 低于 1.5 通常表示股价接近或低于账面价值。",
                }
            )
            checklists.append(
                {
                    "name": "营收增长监控",
                    "value": (
                        f"YoY: {rev_yoy}%"
                        if isinstance(rev_yoy, (int, float))
                        else "N/A"
                    ),
                    "status": (
                        "高增长"
                        if (isinstance(rev_yoy, (int, float)) and rev_yoy > 20)
                        else (
                            "增长停滞"
                            if (isinstance(rev_yoy, (int, float)) and rev_yoy < 0)
                            else "正常"
                        )
                    ),
                    "triggered": isinstance(rev_yoy, (int, float))
                    and (rev_yoy > 20 or rev_yoy < 0),
                    "description": "营收增长高于 20% 是较强的正面信号；负增长则需要警惕。",
                }
            )
            self.data["checklists"] = checklists

            return self.data
        except Exception as e:
            print(f"Error in research: {e}", file=sys.stderr)
            return self.data

    def output_json(self):
        def serialize(obj):
            if hasattr(obj, "item"):
                return obj.item()
            if isinstance(obj, (datetime, pd.Timestamp)):
                return obj.isoformat()
            return str(obj)

        print(json.dumps(self.data, ensure_ascii=False, default=serialize))


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    engine = StockResearchEngine(ticker)
    engine.run_research()
    engine.output_json()
