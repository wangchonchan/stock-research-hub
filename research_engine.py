#!/usr/bin/env python3
"""
Stock Research Engine v3.2 - Robust Data Fetching & Comprehensive Capital Flow Analysis
"""

import csv
import json
import os
import sys
from io import StringIO
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import requests
import yfinance as yf
import urllib.request
import xml.etree.ElementTree as ET
import re


class StockResearchEngine:
    def __init__(self, ticker: str = "AAPL"):
        self.ticker = ticker.upper()
        self.hkt = timezone(timedelta(hours=8))
        self.http_session = requests.Session()
        self._yahoo_session_attempted = False
        self._yahoo_session_ready = False
        self._yahoo_crumb = None
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
                "source": "N/A",
                "updated_at": "N/A",
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
                "market_flow_source": "N/A",
                "market_flow_details": [],
                "sector_flow_details": [],
                "flow_destination_summary": {
                    "top_inflow": "N/A",
                    "top_outflow": "N/A",
                    "risk_appetite": "N/A",
                },
                "institutional_flow": {
                    "available": False,
                    "source": "Yahoo Finance / yfinance institutional_holders",
                    "latest_report_date": "N/A",
                    "note": "Yahoo Finance 返回机构持仓后会在这里显示；可配置 ALPHA_VANTAGE_API_KEY 作为备用数据源。",
                    "top_holders": [],
                    "top_increases": [],
                    "top_decreases": [],
                },
                "options_flow": {
                    "available": False,
                    "source": "Yahoo Finance options chain",
                    "as_of": "N/A",
                    "expirations_analyzed": [],
                    "bullish_premium_proxy_usd": "N/A",
                    "bearish_premium_proxy_usd": "N/A",
                    "put_call_premium_ratio": "N/A",
                    "unusual_contracts": [],
                    "note": "Yahoo Finance 返回期权链后会筛选异常成交合约。",
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

    def _append_diagnostic_once(self, message: str) -> None:
        if message not in self.data["diagnostics"]:
            self.data["diagnostics"].append(message)

    def _yahoo_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        merged = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Origin": "https://finance.yahoo.com",
            "Referer": f"https://finance.yahoo.com/quote/{self.ticker}",
        }
        if headers:
            merged.update(headers)
        return merged

    def _is_yahoo_url(self, url: str) -> bool:
        return "finance.yahoo.com" in url

    def _prime_yahoo_session(self) -> None:
        if self._yahoo_session_ready or self._yahoo_session_attempted:
            return
        self._yahoo_session_attempted = True
        try:
            response = self.http_session.get(
                f"https://finance.yahoo.com/quote/{self.ticker}",
                headers=self._yahoo_headers(
                    {
                        "Accept": (
                            "text/html,application/xhtml+xml,"
                            "application/xml;q=0.9,*/*;q=0.8"
                        )
                    }
                ),
                timeout=8,
            )
            if response.status_code < 500:
                self._yahoo_session_ready = True
        except Exception as e:
            self._append_diagnostic_once(f"yahoo_session_unavailable: {e}")

    def _get_yahoo_crumb(self) -> Optional[str]:
        if self._yahoo_crumb:
            return self._yahoo_crumb

        self._prime_yahoo_session()
        try:
            response = self.http_session.get(
                "https://query1.finance.yahoo.com/v1/test/getcrumb",
                headers=self._yahoo_headers({"Accept": "text/plain,*/*"}),
                timeout=8,
            )
            response.raise_for_status()
            crumb = response.text.strip()
            if crumb and "<" not in crumb and len(crumb) < 200:
                self._yahoo_crumb = crumb
                return crumb
        except Exception as e:
            self._append_diagnostic_once(f"yahoo_crumb_unavailable: {e}")
        return None

    def _request_yahoo_get(self, url: str, **kwargs) -> requests.Response:
        """GET Yahoo endpoints with a browser-like session and crumb retry."""
        headers = self._yahoo_headers(kwargs.pop("headers", {}) or {})
        timeout = kwargs.pop("timeout", 8)
        params = dict(kwargs.pop("params", {}) or {})
        include_crumb = kwargs.pop("include_crumb", False)

        self._prime_yahoo_session()
        if include_crumb:
            crumb = self._get_yahoo_crumb()
            if crumb:
                params.setdefault("crumb", crumb)

        response = self.http_session.get(
            url, headers=headers, timeout=timeout, params=params, **kwargs
        )

        if response.status_code in (401, 403):
            self._yahoo_crumb = None
            crumb = self._get_yahoo_crumb()
            if crumb:
                params["crumb"] = crumb
                response = self.http_session.get(
                    url, headers=headers, timeout=timeout, params=params, **kwargs
                )

        response.raise_for_status()
        return response

    def _request_get(self, url: str, **kwargs) -> requests.Response:
        """Run a bounded HTTP GET without letting provider calls hang the API."""
        if self._is_yahoo_url(url):
            return self._request_yahoo_get(url, **kwargs)

        headers = kwargs.pop("headers", {}) or {}
        headers.setdefault("User-Agent", "stock-research-hub/1.0 Mozilla/5.0")
        timeout = kwargs.pop("timeout", 8)
        response = self.http_session.get(url, headers=headers, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    def _get_alpha_vantage_key(self) -> Optional[str]:
        return os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv("ALPHAVANTAGE_API_KEY")

    def _fetch_alpha_vantage_global_quote(self) -> Optional[Dict[str, Any]]:
        api_key = self._get_alpha_vantage_key()
        if not api_key:
            return None

        try:
            payload = self._request_get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": self.ticker,
                    "apikey": api_key,
                },
            ).json()
            quote = payload.get("Global Quote") or {}
            price = self._to_float(quote.get("05. price"))
            if price <= 0:
                message = (
                    payload.get("Information")
                    or payload.get("Note")
                    or payload.get("Error Message")
                )
                if message:
                    self.data["diagnostics"].append(
                        f"alpha_vantage_quote_unavailable: {message}"
                    )
                return None
            return quote
        except Exception as e:
            self.data["diagnostics"].append(f"alpha_vantage_quote_unavailable: {e}")
            return None

    def _apply_alpha_vantage_global_quote(self) -> bool:
        quote = self._fetch_alpha_vantage_global_quote()
        if not quote:
            return False

        price = self._to_float(quote.get("05. price"))
        previous_close = self._to_float(quote.get("08. previous close"))
        change = self._to_float(quote.get("09. change"), price - previous_close)
        change_percent_raw = str(quote.get("10. change percent", "")).replace("%", "")
        change_percent = self._to_float(change_percent_raw)
        volume = self._to_float(quote.get("06. volume"))

        self.data["price"].update(
            {
                "current_price": round(price, 3),
                "change": round(change, 3),
                "change_percent": round(change_percent, 2),
            }
        )
        if volume > 0:
            self.data["capital_flow"]["volume"] = volume
            if price > 0:
                self.data["capital_flow"]["net_flow_proxy_usd"] = round(
                    volume * price, 2
                )
        self.data["diagnostics"].append("price_source: Alpha Vantage GLOBAL_QUOTE")
        return True

    def _apply_stooq_quote_fallback(self) -> bool:
        # Stooq uses .US suffix for U.S. equities and exposes a small CSV quote API.
        symbol = self.ticker.lower()
        if "." not in symbol:
            symbol = f"{symbol}.us"
        try:
            response = self._request_get(
                "https://stooq.com/q/l/",
                params={"s": symbol, "f": "sd2t2ohlcv", "h": "", "e": "csv"},
            )
            rows = list(csv.DictReader(StringIO(response.text)))
            if not rows:
                return False
            row = rows[0]
            close = self._to_float(row.get("Close"))
            if close <= 0:
                return False
            open_price = self._to_float(row.get("Open"), close)
            volume = self._to_float(row.get("Volume"))
            change = close - open_price
            self.data["price"].update(
                {
                    "current_price": round(close, 3),
                    "change": round(change, 3),
                    "change_percent": (
                        round((change / open_price) * 100, 2) if open_price else 0
                    ),
                }
            )
            if volume > 0:
                self.data["capital_flow"]["volume"] = volume
                self.data["capital_flow"]["net_flow_proxy_usd"] = round(
                    volume * close, 2
                )
            self.data["diagnostics"].append("price_source: Stooq delayed quote CSV")
            return True
        except Exception as e:
            self.data["diagnostics"].append(f"stooq_quote_unavailable: {e}")
            return False

    def _stooq_symbol(self, symbol: str) -> str:
        normalized = symbol.lower().replace("-", ".")
        if "." not in normalized:
            normalized = f"{normalized}.us"
        return normalized

    def _fetch_stooq_history(self, symbol: str, days: int = 25) -> pd.DataFrame:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days * 2)
        response = self._request_get(
            "https://stooq.com/q/d/l/",
            params={
                "s": self._stooq_symbol(symbol),
                "d1": start_date.strftime("%Y%m%d"),
                "d2": end_date.strftime("%Y%m%d"),
                "i": "d",
            },
        )
        rows = list(csv.DictReader(StringIO(response.text)))
        if not rows or "No data" in response.text:
            return pd.DataFrame()

        frame = pd.DataFrame(rows)
        required = {"Date", "Open", "High", "Low", "Close", "Volume"}
        if not required.issubset(frame.columns):
            return pd.DataFrame()

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame = frame.dropna(subset=["Date", "Close"]).set_index("Date")
        return frame.tail(days)

    def _normalize_history_frame(
        self, frame: pd.DataFrame, days: int = 260
    ) -> pd.DataFrame:
        if frame is None or frame.empty:
            return pd.DataFrame()

        normalized = frame.copy()
        if isinstance(normalized.columns, pd.MultiIndex):
            normalized.columns = [str(col[-1]) for col in normalized.columns]

        rename_map = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
        normalized = normalized.rename(
            columns={
                col: rename_map.get(str(col).lower(), col) for col in normalized.columns
            }
        )
        required = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in normalized.columns for col in required):
            return pd.DataFrame()

        for col in required:
            normalized[col] = pd.to_numeric(normalized[col], errors="coerce")
        normalized = normalized.dropna(subset=["Close"]).sort_index()
        return normalized.tail(days)

    def _fetch_yahoo_chart_history(self, symbol: str, days: int = 260) -> pd.DataFrame:
        try:
            payload = self._request_get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                params={
                    "range": "1y",
                    "interval": "1d",
                    "includePrePost": "false",
                    "events": "div,splits",
                },
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json,text/plain,*/*",
                    "Referer": "https://finance.yahoo.com/",
                },
            ).json()
            result = (payload.get("chart", {}).get("result") or [None])[0]
            if not result:
                error = payload.get("chart", {}).get("error")
                if error:
                    self.data["diagnostics"].append(f"yahoo_chart_unavailable: {error}")
                return pd.DataFrame()

            timestamps = result.get("timestamp") or []
            quote = ((result.get("indicators", {}).get("quote") or [None])[0]) or {}
            if not timestamps or not quote:
                return pd.DataFrame()

            frame = pd.DataFrame(
                {
                    "Date": pd.to_datetime(timestamps, unit="s", errors="coerce"),
                    "Open": quote.get("open", []),
                    "High": quote.get("high", []),
                    "Low": quote.get("low", []),
                    "Close": quote.get("close", []),
                    "Volume": quote.get("volume", []),
                }
            )
            frame = frame.dropna(subset=["Date"]).set_index("Date")
            return self._normalize_history_frame(frame, days)
        except Exception as e:
            self.data["diagnostics"].append(f"yahoo_chart_unavailable: {e}")
            return pd.DataFrame()

    def _fetch_alpha_vantage_daily_history(self, days: int = 260) -> pd.DataFrame:
        api_key = self._get_alpha_vantage_key()
        if not api_key:
            return pd.DataFrame()

        try:
            payload = self._request_get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "TIME_SERIES_DAILY_ADJUSTED",
                    "symbol": self.ticker,
                    "outputsize": "compact",
                    "apikey": api_key,
                },
            ).json()
            series = payload.get("Time Series (Daily)") or {}
            if not series:
                message = (
                    payload.get("Information")
                    or payload.get("Note")
                    or payload.get("Error Message")
                )
                if message:
                    self.data["diagnostics"].append(
                        f"alpha_vantage_daily_unavailable: {message}"
                    )
                return pd.DataFrame()

            records = []
            for date, row in series.items():
                records.append(
                    {
                        "Date": date,
                        "Open": row.get("1. open"),
                        "High": row.get("2. high"),
                        "Low": row.get("3. low"),
                        "Close": row.get("4. close"),
                        "Volume": row.get("6. volume"),
                    }
                )
            frame = pd.DataFrame(records)
            frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
            frame = frame.dropna(subset=["Date"]).set_index("Date")
            return self._normalize_history_frame(frame, days)
        except Exception as e:
            self.data["diagnostics"].append(f"alpha_vantage_daily_unavailable: {e}")
            return pd.DataFrame()

    def _fetch_price_history(self, ticker_obj) -> tuple[pd.DataFrame, str]:
        attempts = [
            (
                "Yahoo Finance yfinance history 1y",
                lambda: ticker_obj.history(period="1y"),
            ),
            (
                "Yahoo Finance yfinance history 1mo",
                lambda: ticker_obj.history(period="1mo"),
            ),
            (
                "Yahoo Finance yfinance history 5d",
                lambda: ticker_obj.history(period="5d"),
            ),
            (
                "Yahoo Finance chart API",
                lambda: self._fetch_yahoo_chart_history(self.ticker),
            ),
            (
                "Stooq delayed daily CSV",
                lambda: self._fetch_stooq_history(self.ticker, days=260),
            ),
            (
                "Alpha Vantage TIME_SERIES_DAILY_ADJUSTED",
                lambda: self._fetch_alpha_vantage_daily_history(days=260),
            ),
        ]

        for source, fetcher in attempts:
            try:
                hist = self._normalize_history_frame(fetcher())
                if not hist.empty:
                    return hist, source
            except Exception as e:
                self.data["diagnostics"].append(
                    f"price_history_attempt_failed: {source}: {e}"
                )

        return pd.DataFrame(), "N/A"

    def _apply_price_history(self, hist: pd.DataFrame, source: str) -> float:
        if hist is None or hist.empty:
            return 0

        current_price = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
        change = current_price - prev_close
        self.data["price"].update(
            {
                "current_price": round(current_price, 3),
                "change": round(change, 3),
                "change_percent": (
                    round((change / prev_close) * 100, 2) if prev_close else 0
                ),
            }
        )
        self.data["technicals"].update(self._calculate_indicators(hist))

        volume = self._to_float(hist["Volume"].iloc[-1]) if "Volume" in hist else 0
        avg_volume = (
            float(hist["Volume"].tail(10).mean())
            if "Volume" in hist and len(hist["Volume"].dropna()) > 0
            else 0
        )
        if volume > 0:
            self.data["capital_flow"]["volume"] = volume
            self.data["capital_flow"]["net_flow_proxy_usd"] = round(
                volume * current_price, 2
            )
        if avg_volume > 0:
            self.data["capital_flow"]["avg_volume_10d"] = avg_volume
            self.data["capital_flow"]["volume_ratio"] = round(volume / avg_volume, 2)
        self.data["diagnostics"].append(f"price_history_source: {source}")
        return current_price

    def _raw_value(self, value, default="N/A"):
        if isinstance(value, dict):
            return value.get("raw", value.get("fmt", default))
        return default if value in (None, "") else value

    def _consensus_from_rating(self, value) -> str:
        rating = str(self._raw_value(value, "")).strip()
        if not rating:
            return "N/A"
        if " - " in rating:
            rating = rating.split(" - ", 1)[1]
        return rating.upper() if rating else "N/A"

    def _consensus_from_trend(self, trend: Dict[str, Any]) -> str:
        rows = trend.get("trend") if isinstance(trend, dict) else None
        if not isinstance(rows, list) or not rows:
            return "N/A"

        current = next(
            (row for row in rows if isinstance(row, dict) and row.get("period") == "0m"),
            rows[0],
        )
        if not isinstance(current, dict):
            return "N/A"

        strong_buy = self._to_float(current.get("strongBuy"))
        buy = self._to_float(current.get("buy"))
        hold = self._to_float(current.get("hold"))
        sell = self._to_float(current.get("sell"))
        strong_sell = self._to_float(current.get("strongSell"))
        total = strong_buy + buy + hold + sell + strong_sell
        if total <= 0:
            return "N/A"

        score = ((strong_buy * 2) + buy - sell - (strong_sell * 2)) / total
        if score >= 1.1:
            return "STRONG BUY"
        if score >= 0.35:
            return "BUY"
        if score <= -1.1:
            return "STRONG SELL"
        if score <= -0.35:
            return "SELL"
        return "HOLD"

    def _update_consensus(
        self,
        *,
        target: float = 0,
        recommendation: str = "N/A",
        current_price: float = 0,
        source: str,
    ) -> bool:
        did_update = False
        if target > 0:
            self.data["consensus"]["target_price"] = round(target, 2)
            if current_price > 0:
                self.data["consensus"]["upside_potential"] = round(
                    ((target - current_price) / current_price) * 100, 1
                )
            did_update = True

        if recommendation != "N/A":
            self.data["consensus"]["recommendation"] = recommendation
            did_update = True

        if did_update:
            self.data["consensus"]["source"] = source
            self.data["consensus"]["updated_at"] = datetime.now(self.hkt).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            self.data["diagnostics"].append(f"consensus_source: {source}")
        return did_update

    def _has_missing_enrichment_fields(self) -> bool:
        has_profile = self.data["company_name"] not in ("N/A", self.ticker)
        return (
            not has_profile
            or self.data["capital_flow"].get("market_cap") == "N/A"
            or self.data["price"].get("pe_ratio") == "N/A"
            or self.data["price"].get("pb_ratio") == "N/A"
            or self.data["consensus"].get("target_price") == "N/A"
            or self.data["consensus"].get("recommendation") == "N/A"
        )

    def _apply_yahoo_quote_summary(self, current_price: float = 0) -> bool:
        try:
            modules = ",".join(
                [
                    "price",
                    "summaryProfile",
                    "defaultKeyStatistics",
                    "financialData",
                    "summaryDetail",
                    "recommendationTrend",
                ]
            )
            payload = self._request_get(
                f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{self.ticker}",
                params={"modules": modules, "formatted": "false"},
                include_crumb=True,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json,text/plain,*/*",
                    "Referer": "https://finance.yahoo.com/",
                },
            ).json()
            result = (payload.get("quoteSummary", {}).get("result") or [None])[0]
            if not result:
                error = payload.get("quoteSummary", {}).get("error")
                if error:
                    self.data["diagnostics"].append(
                        f"yahoo_quote_summary_unavailable: {error}"
                    )
                return False

            price = result.get("price") or {}
            profile = result.get("summaryProfile") or {}
            stats = result.get("defaultKeyStatistics") or {}
            financial = result.get("financialData") or {}
            detail = result.get("summaryDetail") or {}
            recommendation_trend = result.get("recommendationTrend") or {}

            self.data["company_name"] = self._raw_value(
                price.get("longName"), self.data["company_name"]
            )
            if self.data["company_name"] in ("N/A", self.ticker):
                self.data["company_name"] = self._raw_value(
                    price.get("shortName"), self.ticker
                )
            description = self._raw_value(
                profile.get("longBusinessSummary"), self.data["description"]
            )
            self.data["description"] = self._summarize_description(description, 30)

            quote_price = self._to_float(price.get("regularMarketPrice"))
            if quote_price > 0:
                current_price = quote_price
                self.data["price"]["current_price"] = round(quote_price, 3)
                change = self._to_float(price.get("regularMarketChange"))
                change_pct = self._to_float(price.get("regularMarketChangePercent"))
                self.data["price"]["change"] = round(change, 3)
                self.data["price"]["change_percent"] = round(change_pct, 2)

            pe_ratio = self._to_float(detail.get("trailingPE"))
            pb_ratio = self._to_float(stats.get("priceToBook"))
            if pe_ratio > 0:
                self.data["price"]["pe_ratio"] = round(pe_ratio, 2)
            if pb_ratio > 0:
                self.data["price"]["pb_ratio"] = round(pb_ratio, 2)

            target = self._to_float(financial.get("targetMeanPrice"))
            recommendation = self._consensus_from_trend(recommendation_trend)
            if recommendation == "N/A":
                recommendation = self._consensus_from_rating(
                    financial.get("recommendationKey")
                )
            self._update_consensus(
                target=target,
                recommendation=recommendation,
                current_price=current_price,
                source="Yahoo quoteSummary financialData/recommendationTrend",
            )

            market_cap = self._to_float(price.get("marketCap"))
            volume = self._to_float(price.get("regularMarketVolume"))
            avg_vol = self._to_float(
                price.get("averageDailyVolume10Day"),
                self._to_float(price.get("averageDailyVolume3Month")),
            )
            if market_cap > 0 or volume > 0 or avg_vol > 0:
                self._update_capital_flow_snapshot(
                    market_cap, volume, avg_vol, current_price
                )

            self.data["diagnostics"].append("profile_source: Yahoo quoteSummary direct")
            return True
        except Exception as e:
            self.data["diagnostics"].append(f"yahoo_quote_summary_unavailable: {e}")
            return False

    def _apply_yahoo_quote_lookup(self, current_price: float = 0) -> bool:
        """Fallback profile/quote fetch using Yahoo endpoints that do not need quoteSummary modules."""
        did_update = False

        try:
            payload = self._request_get(
                "https://query1.finance.yahoo.com/v7/finance/quote",
                params={"symbols": self.ticker, "formatted": "false"},
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json,text/plain,*/*",
                    "Referer": "https://finance.yahoo.com/",
                },
            ).json()
            quote = ((payload.get("quoteResponse") or {}).get("result") or [None])[0]
            if quote:
                name = quote.get("longName") or quote.get("shortName")
                if name:
                    self.data["company_name"] = name
                    did_update = True

                quote_price = self._to_float(quote.get("regularMarketPrice"))
                if quote_price > 0:
                    current_price = quote_price
                    self.data["price"]["current_price"] = round(quote_price, 3)
                    self.data["price"]["change"] = round(
                        self._to_float(quote.get("regularMarketChange")), 3
                    )
                    self.data["price"]["change_percent"] = round(
                        self._to_float(quote.get("regularMarketChangePercent")), 2
                    )
                    did_update = True

                pe_ratio = self._to_float(
                    quote.get("trailingPE"), self._to_float(quote.get("forwardPE"))
                )
                if pe_ratio <= 0 and current_price > 0:
                    eps = self._to_float(
                        quote.get("epsTrailingTwelveMonths"),
                        self._to_float(quote.get("epsForward")),
                    )
                    pe_ratio = current_price / eps if eps > 0 else 0

                pb_ratio = self._to_float(quote.get("priceToBook"))
                if pb_ratio <= 0 and current_price > 0:
                    book_value = self._to_float(quote.get("bookValue"))
                    pb_ratio = current_price / book_value if book_value > 0 else 0

                if pe_ratio > 0:
                    self.data["price"]["pe_ratio"] = round(pe_ratio, 2)
                    did_update = True
                if pb_ratio > 0:
                    self.data["price"]["pb_ratio"] = round(pb_ratio, 2)
                    did_update = True

                target = self._to_float(
                    quote.get("targetMeanPrice"),
                    self._to_float(quote.get("targetMedianPrice")),
                )
                recommendation = self._consensus_from_rating(
                    quote.get("averageAnalystRating") or quote.get("recommendationKey")
                )
                if self._update_consensus(
                    target=target,
                    recommendation=recommendation,
                    current_price=current_price,
                    source="Yahoo quote lookup",
                ):
                    did_update = True

                market_cap = self._to_float(quote.get("marketCap"))
                volume = self._to_float(quote.get("regularMarketVolume"))
                avg_vol = self._to_float(
                    quote.get("averageDailyVolume10Day"),
                    self._to_float(quote.get("averageDailyVolume3Month")),
                )
                if market_cap > 0 or volume > 0 or avg_vol > 0:
                    self._update_capital_flow_snapshot(
                        market_cap, volume, avg_vol, current_price
                    )
                    did_update = True
        except Exception as e:
            self.data["diagnostics"].append(f"yahoo_quote_lookup_unavailable: {e}")

        if self.data["company_name"] in ("N/A", self.ticker):
            try:
                payload = self._request_get(
                    "https://query1.finance.yahoo.com/v1/finance/search",
                    params={"q": self.ticker, "quotesCount": 1, "newsCount": 0},
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json,text/plain,*/*",
                        "Referer": "https://finance.yahoo.com/",
                    },
                ).json()
                quote = (payload.get("quotes") or [None])[0]
                if quote:
                    name = quote.get("longname") or quote.get("shortname")
                    if name:
                        self.data["company_name"] = name
                        did_update = True
            except Exception as e:
                self.data["diagnostics"].append(f"yahoo_search_unavailable: {e}")

        if did_update:
            self.data["diagnostics"].append(
                "profile_source: Yahoo quote/search fallback"
            )
        return did_update

    def _apply_yahoo_insights(self, current_price: float = 0) -> bool:
        """Fetch analyst recommendation/target from Yahoo's insights endpoint."""
        try:
            payload = self._request_get(
                "https://query2.finance.yahoo.com/ws/insights/v2/finance/insights",
                include_crumb=True,
                params={
                    "symbol": self.ticker,
                    "reportsCount": 3,
                    "region": "US",
                    "lang": "en-US",
                },
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json,text/plain,*/*",
                    "Referer": "https://finance.yahoo.com/",
                },
            ).json()

            result = (payload.get("finance") or {}).get("result")
            if isinstance(result, list):
                result = result[0] if result else None
            if not isinstance(result, dict):
                error = (payload.get("finance") or {}).get("error")
                if error:
                    self.data["diagnostics"].append(
                        f"yahoo_insights_unavailable: {error}"
                    )
                return False

            did_update = False
            recommendation = result.get("recommendation") or {}
            target = self._to_float(recommendation.get("targetPrice"))
            if target <= 0:
                report_targets = [
                    self._to_float(report.get("targetPrice"))
                    for report in (result.get("reports") or [])
                    if isinstance(report, dict)
                ]
                report_targets = [value for value in report_targets if value > 0]
                target = report_targets[0] if report_targets else 0

            rating = self._consensus_from_rating(recommendation.get("rating"))
            if rating == "N/A":
                report_ratings = [
                    self._consensus_from_rating(report.get("investmentRating"))
                    for report in (result.get("reports") or [])
                    if isinstance(report, dict)
                ]
                rating = next(
                    (
                        report_rating
                        for report_rating in report_ratings
                        if report_rating != "N/A"
                    ),
                    "N/A",
                )
            return self._update_consensus(
                target=target,
                recommendation=rating,
                current_price=current_price,
                source="Yahoo insights",
            )
        except Exception as e:
            self.data["diagnostics"].append(f"yahoo_insights_unavailable: {e}")
            return False

    def _market_bucket(self, market_cap: float) -> str:
        if market_cap >= 200_000_000_000:
            return "特大盘 (Mega Cap)"
        if market_cap >= 10_000_000_000:
            return "大盘 (Large Cap)"
        if market_cap >= 2_000_000_000:
            return "中盘 (Mid Cap)"
        if market_cap > 0:
            return "小盘 (Small Cap)"
        return "N/A"

    def _update_capital_flow_snapshot(
        self, market_cap: float, volume: float, avg_vol: float, current_price: float
    ) -> None:
        ratio = (float(volume) / float(avg_vol)) if volume and avg_vol else None
        intensity = "N/A"
        if ratio is not None:
            if ratio >= 1.5:
                intensity = "强流入/强成交"
            elif ratio >= 1.0:
                intensity = "中性偏强"
            else:
                intensity = "偏弱"

        net_flow_proxy = (
            (float(volume) * current_price) if volume and current_price else "N/A"
        )
        self.data["capital_flow"].update(
            {
                "market_bucket": self._market_bucket(market_cap),
                "market_cap": float(market_cap) if market_cap else "N/A",
                "volume": (
                    float(volume)
                    if volume
                    else self.data["capital_flow"].get("volume", "N/A")
                ),
                "avg_volume_10d": (
                    float(avg_vol)
                    if avg_vol
                    else self.data["capital_flow"].get("avg_volume_10d", "N/A")
                ),
                "volume_ratio": (
                    round(ratio, 2)
                    if ratio is not None
                    else self.data["capital_flow"].get("volume_ratio", "N/A")
                ),
                "estimated_flow_intensity": intensity,
                "net_flow_proxy_usd": (
                    round(net_flow_proxy, 2)
                    if isinstance(net_flow_proxy, (int, float))
                    else self.data["capital_flow"].get("net_flow_proxy_usd", "N/A")
                ),
            }
        )

    def _fetch_alpha_vantage_overview(self) -> Optional[Dict[str, Any]]:
        api_key = self._get_alpha_vantage_key()
        if not api_key:
            return None

        try:
            payload = self._request_get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "OVERVIEW",
                    "symbol": self.ticker,
                    "apikey": api_key,
                },
            ).json()
            if not payload or "Symbol" not in payload:
                message = (
                    (
                        payload.get("Information")
                        or payload.get("Note")
                        or payload.get("Error Message")
                    )
                    if isinstance(payload, dict)
                    else None
                )
                if message:
                    self.data["diagnostics"].append(
                        f"alpha_vantage_overview_unavailable: {message}"
                    )
                return None
            return payload
        except Exception as e:
            self.data["diagnostics"].append(f"alpha_vantage_overview_unavailable: {e}")
            return None

    def _apply_alpha_vantage_overview(self) -> bool:
        overview = self._fetch_alpha_vantage_overview()
        if not overview:
            return False

        self.data["company_name"] = overview.get("Name") or self.data["company_name"]
        description = overview.get("Description") or self.data["description"]
        self.data["description"] = self._summarize_description(description, 30)
        pe_ratio = self._to_float(overview.get("PERatio"))
        pb_ratio = self._to_float(overview.get("PriceToBookRatio"))
        if pe_ratio > 0:
            self.data["price"]["pe_ratio"] = round(pe_ratio, 2)
        if pb_ratio > 0:
            self.data["price"]["pb_ratio"] = round(pb_ratio, 2)

        target = self._to_float(overview.get("AnalystTargetPrice"))
        current_price = self._to_float(self.data["price"].get("current_price"))
        if target > 0:
            self.data["consensus"]["target_price"] = round(target, 2)
            if current_price > 0:
                self.data["consensus"]["upside_potential"] = round(
                    ((target - current_price) / current_price) * 100, 1
                )

        market_cap = self._to_float(overview.get("MarketCapitalization"))
        if market_cap > 0:
            self.data["capital_flow"]["market_cap"] = market_cap
            if market_cap >= 200_000_000_000:
                self.data["capital_flow"]["market_bucket"] = "特大盘 (Mega Cap)"
            elif market_cap >= 10_000_000_000:
                self.data["capital_flow"]["market_bucket"] = "大盘 (Large Cap)"
            elif market_cap >= 2_000_000_000:
                self.data["capital_flow"]["market_bucket"] = "中盘 (Mid Cap)"
            else:
                self.data["capital_flow"]["market_bucket"] = "小盘 (Small Cap)"
        self.data["diagnostics"].append("profile_source: Alpha Vantage OVERVIEW")
        return True

    def _normalize_institutional_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        holder = self._first_value(
            record,
            [
                "Holder",
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
                "Date Reported",
                "date",
                "reportDate",
                "reportedDate",
                "filingDate",
                "periodOfReport",
                "period",
            ],
        )
        shares = self._to_float(
            self._first_value(
                record, ["Shares", "shares", "share", "sshPrnamt", "sharesHeld"]
            )
        )
        value = self._to_float(
            self._first_value(
                record, ["Value", "value", "marketValue", "value_usd", "market_value"]
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

    def _empty_institutional_flow(
        self, note: str, source: str = "Yahoo Finance"
    ) -> Dict[str, Any]:
        return {
            "available": False,
            "source": source,
            "latest_report_date": "N/A",
            "note": note,
            "top_holders": [],
            "top_increases": [],
            "top_decreases": [],
        }

    def _records_from_holders_df(self, df) -> List[Dict[str, Any]]:
        if df is None or getattr(df, "empty", True):
            return []
        records = df.reset_index(drop=True).to_dict("records")
        normalized = []
        for record in records:
            clean = {}
            for key, value in record.items():
                if isinstance(value, (pd.Timestamp, datetime)):
                    clean[str(key)] = value.strftime("%Y-%m-%d")
                else:
                    clean[str(key)] = value
            item = self._normalize_institutional_record(clean)
            if item["holder"] != "N/A":
                normalized.append(item)
        return normalized

    def _build_institutional_payload(
        self,
        records: List[Dict[str, Any]],
        source: str,
        note: str,
    ) -> Dict[str, Any]:
        if not records:
            return self._empty_institutional_flow(
                "Yahoo Finance 未返回机构持仓记录。", source
            )

        latest_date = (
            max(item["report_date"] for item in records if item["report_date"] != "N/A")
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
            "source": source,
            "latest_report_date": latest_date,
            "note": note,
            "top_holders": latest_records[:8],
            "top_increases": increases[:5],
            "top_decreases": decreases[:5],
        }

    def _fetch_yahoo_institutional_flow(self) -> Dict[str, Any]:
        try:
            response = self._request_yahoo_get(
                f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{self.ticker}",
                params={
                    "modules": "institutionOwnership",
                    "formatted": "false",
                    "corsDomain": "finance.yahoo.com",
                },
                include_crumb=True,
            )
            payload = response.json()
            result = payload.get("quoteSummary", {}).get("result") or []
            ownership = result[0].get("institutionOwnership", {}) if result else {}
            raw_records = ownership.get("ownershipList") or []
            records = []
            for item in raw_records:
                if not isinstance(item, dict):
                    continue
                normalized = {
                    "Holder": self._first_value(item, ["organization"]),
                    "Date Reported": (
                        datetime.fromtimestamp(item["reportDate"]).strftime("%Y-%m-%d")
                        if item.get("reportDate")
                        else "N/A"
                    ),
                    "Shares": self._first_value(item, ["position"]),
                    "Value": self._first_value(item, ["value"]),
                }
                record = self._normalize_institutional_record(normalized)
                if record["holder"] != "N/A":
                    records.append(record)

            if not records:
                return self._empty_institutional_flow(
                    "Yahoo Finance 未返回机构持仓记录。"
                )
            return self._build_institutional_payload(
                records,
                "Yahoo Finance quoteSummary institutionOwnership",
                "真实 Yahoo Finance 机构持仓数据；通常来自 13F/机构披露，存在报告延迟，不代表实时逐笔资金流。",
            )
        except Exception as e:
            self.data["diagnostics"].append(
                f"yahoo_institutional_flow_unavailable: {e}"
            )
            return self._empty_institutional_flow(
                "Yahoo Finance 机构持仓当前不可用；已在 diagnostics 保留详细错误。可配置 ALPHA_VANTAGE_API_KEY 启用备用 13F 数据源。"
            )

    def _fetch_alpha_vantage_institutional_flow(self) -> Dict[str, Any]:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv(
            "ALPHAVANTAGE_API_KEY"
        )
        base = self._empty_institutional_flow(
            "Yahoo Finance 未返回数据；可配置 ALPHA_VANTAGE_API_KEY 作为备用真实 13F 数据源。",
            "Alpha Vantage INSTITUTIONAL_HOLDINGS",
        )
        if not api_key:
            return base

        try:
            response = self._request_get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "INSTITUTIONAL_HOLDINGS",
                    "symbol": self.ticker,
                    "apikey": api_key,
                },
                timeout=8,
                headers={"User-Agent": "stock-research-hub/1.0"},
            )
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

            return self._build_institutional_payload(
                records,
                "Alpha Vantage INSTITUTIONAL_HOLDINGS",
                "真实 13F 机构持仓数据；通常按季度披露，存在报告延迟，不代表实时逐笔资金流。",
            )
        except Exception as e:
            self.data["diagnostics"].append(
                f"alpha_vantage_institutional_flow_unavailable: {e}"
            )
            base["note"] = f"Alpha Vantage 机构持仓 API 请求失败：{e}"
            return base

    def _fetch_institutional_flow(self) -> Dict[str, Any]:
        yahoo_result = self._fetch_yahoo_institutional_flow()
        if yahoo_result.get("available"):
            return yahoo_result

        fallback = self._fetch_alpha_vantage_institutional_flow()
        if fallback.get("available"):
            return fallback

        return yahoo_result

    def _empty_options_flow(self, note: str) -> Dict[str, Any]:
        return {
            "available": False,
            "source": "Yahoo Finance options chain",
            "as_of": "N/A",
            "expirations_analyzed": [],
            "bullish_premium_proxy_usd": "N/A",
            "bearish_premium_proxy_usd": "N/A",
            "put_call_premium_ratio": "N/A",
            "unusual_contracts": [],
            "note": note,
        }

    def _fetch_yahoo_options_payload(self, expiration: int = None) -> Dict[str, Any]:
        params = {"formatted": "false"}
        if expiration is not None:
            params["date"] = expiration
        response = self._request_yahoo_get(
            f"https://query2.finance.yahoo.com/v7/finance/options/{self.ticker}",
            params=params,
            timeout=8,
            include_crumb=True,
        )
        return response.json()

    def _normalize_option_contract(
        self, contract: Dict[str, Any], option_type: str, expiration_label: str
    ) -> Dict[str, Any]:
        volume = self._to_float(contract.get("volume"))
        open_interest = self._to_float(contract.get("openInterest"))
        last_price = self._to_float(contract.get("lastPrice"))
        strike = self._to_float(contract.get("strike"))
        premium = volume * last_price * 100 if volume and last_price else 0
        volume_oi_ratio = (
            round(volume / open_interest, 2)
            if open_interest and open_interest > 0
            else "N/A"
        )
        last_trade_timestamp = contract.get("lastTradeDate")
        return {
            "contract_symbol": contract.get("contractSymbol", "N/A"),
            "type": option_type,
            "expiration": expiration_label,
            "strike": strike,
            "last_price": last_price,
            "volume": volume,
            "open_interest": open_interest,
            "volume_oi_ratio": volume_oi_ratio,
            "premium_usd": round(premium, 2),
            "implied_volatility": round(
                self._to_float(contract.get("impliedVolatility")) * 100, 2
            ),
            "last_trade_date": (
                datetime.fromtimestamp(last_trade_timestamp).strftime("%Y-%m-%d %H:%M")
                if last_trade_timestamp
                else "N/A"
            ),
        }

    def _is_unusual_option(self, item: Dict[str, Any]) -> bool:
        volume = item["volume"] if isinstance(item["volume"], (int, float)) else 0
        open_interest = (
            item["open_interest"]
            if isinstance(item["open_interest"], (int, float))
            else 0
        )
        ratio = (
            item["volume_oi_ratio"]
            if isinstance(item["volume_oi_ratio"], (int, float))
            else 0
        )
        premium = (
            item["premium_usd"] if isinstance(item["premium_usd"], (int, float)) else 0
        )
        return volume >= 500 and (
            premium >= 250_000 or ratio >= 2 or (open_interest == 0 and volume >= 1000)
        )

    def _fetch_options_flow(self) -> Dict[str, Any]:
        try:
            first_payload = self._fetch_yahoo_options_payload()
            result = first_payload.get("optionChain", {}).get("result") or []
            if not result:
                return self._empty_options_flow("Yahoo Finance 未返回期权链。")

            chain_root = result[0]
            expiration_dates = chain_root.get("expirationDates") or []
            expirations_to_check = expiration_dates[:3]
            if not expirations_to_check:
                return self._empty_options_flow("Yahoo Finance 未返回可用期权到期日。")

            unusual_contracts = []
            expirations_analyzed = []
            bullish_premium = 0
            bearish_premium = 0

            for expiration in expirations_to_check:
                payload = (
                    first_payload
                    if expiration == expirations_to_check[0]
                    else self._fetch_yahoo_options_payload(expiration)
                )
                option_result = payload.get("optionChain", {}).get("result") or []
                if not option_result:
                    continue
                option_sets = option_result[0].get("options") or []
                if not option_sets:
                    continue

                expiration_label = datetime.fromtimestamp(expiration).strftime(
                    "%Y-%m-%d"
                )
                expirations_analyzed.append(expiration_label)
                option_set = option_sets[0]
                for option_type, contracts in (
                    ("看涨", option_set.get("calls") or []),
                    ("看跌", option_set.get("puts") or []),
                ):
                    for contract in contracts:
                        if not isinstance(contract, dict):
                            continue
                        item = self._normalize_option_contract(
                            contract, option_type, expiration_label
                        )
                        if option_type == "看涨":
                            bullish_premium += (
                                item["premium_usd"]
                                if isinstance(item["premium_usd"], (int, float))
                                else 0
                            )
                        else:
                            bearish_premium += (
                                item["premium_usd"]
                                if isinstance(item["premium_usd"], (int, float))
                                else 0
                            )
                        if self._is_unusual_option(item):
                            unusual_contracts.append(item)

            unusual_contracts.sort(
                key=lambda item: (
                    item["premium_usd"]
                    if isinstance(item["premium_usd"], (int, float))
                    else 0
                ),
                reverse=True,
            )
            if not unusual_contracts:
                return {
                    "available": True,
                    "source": "Yahoo Finance options chain",
                    "as_of": datetime.now(self.hkt).strftime("%Y-%m-%d %H:%M:%S"),
                    "expirations_analyzed": expirations_analyzed,
                    "bullish_premium_proxy_usd": round(bullish_premium, 2),
                    "bearish_premium_proxy_usd": round(bearish_premium, 2),
                    "put_call_premium_ratio": (
                        round(bearish_premium / bullish_premium, 2)
                        if bullish_premium
                        else "N/A"
                    ),
                    "unusual_contracts": [],
                    "note": "未发现符合当前阈值的异常期权大单。",
                }

            return {
                "available": True,
                "source": "Yahoo Finance options chain",
                "as_of": datetime.now(self.hkt).strftime("%Y-%m-%d %H:%M:%S"),
                "expirations_analyzed": expirations_analyzed,
                "bullish_premium_proxy_usd": round(bullish_premium, 2),
                "bearish_premium_proxy_usd": round(bearish_premium, 2),
                "put_call_premium_ratio": (
                    round(bearish_premium / bullish_premium, 2)
                    if bullish_premium
                    else "N/A"
                ),
                "unusual_contracts": unusual_contracts[:8],
                "note": "基于 Yahoo Finance 期权链的成交量、未平仓量和权利金筛选；不包含买卖方向或机构身份。",
            }
        except Exception as e:
            self.data["diagnostics"].append(f"options_flow_unavailable: {e}")
            return self._empty_options_flow(
                "Yahoo Finance 期权链当前不可用；已在 diagnostics 保留详细错误，页面将继续展示其它可用数据。"
            )

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
        stooq_results = {}
        stooq_errors = []
        for symbol in symbols:
            try:
                hist = self._fetch_stooq_history(symbol, days=20)
                if not hist.empty:
                    stooq_results[symbol] = hist
            except Exception as e:
                stooq_errors.append(f"{symbol}: {e}")

        if stooq_results:
            missing = [symbol for symbol in symbols if symbol not in stooq_results]
            if missing:
                self.data["diagnostics"].append(
                    f"stooq_flow_partial: missing {', '.join(missing[:6])}"
                )
            return {"source": "免费延迟 ETF 日线（Stooq）", "data": stooq_results}

        if stooq_errors:
            self.data["diagnostics"].append(
                f"stooq_flow_unavailable: {'; '.join(stooq_errors[:3])}"
            )

        chart_results = {}
        chart_errors = []
        for symbol in symbols:
            try:
                hist = self._fetch_yahoo_chart_history(symbol, days=20)
                if not hist.empty:
                    chart_results[symbol] = hist
            except Exception as e:
                chart_errors.append(f"{symbol}: {e}")

        if chart_results:
            missing = [symbol for symbol in symbols if symbol not in chart_results]
            if missing:
                self.data["diagnostics"].append(
                    f"chart_flow_partial: missing {', '.join(missing[:6])}"
                )
            return {"source": "免费延迟 ETF 日线备用源", "data": chart_results}

        if chart_errors:
            self.data["diagnostics"].append(
                f"chart_flow_unavailable: {'; '.join(chart_errors[:3])}"
            )

        try:
            downloaded = yf.download(
                symbols,
                period="15d",
                interval="1d",
                group_by="ticker",
                progress=False,
                threads=True,
                auto_adjust=False,
                timeout=5,
            )
            if downloaded is not None and not downloaded.empty:
                return {
                    "source": "免费延迟 ETF 日线备用源",
                    "data": downloaded,
                }
            return {"source": "N/A", "data": None}
        except Exception as e:
            self.data["diagnostics"].append(f"flow_history_unavailable: {e}")
            return {"source": "N/A", "data": None}

    def _extract_symbol_history(self, downloaded, symbol: str):
        if not downloaded:
            return pd.DataFrame()
        source_data = downloaded.get("data")
        if isinstance(source_data, dict):
            return source_data.get(symbol, pd.DataFrame())
        if source_data is None or getattr(source_data, "empty", True):
            return pd.DataFrame()
        try:
            if isinstance(source_data.columns, pd.MultiIndex):
                return source_data[symbol].dropna(how="all")
            return source_data.dropna(how="all")
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
            flow_source = downloaded.get("source", "N/A") if downloaded else "N/A"

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
                "market_flow_source": flow_source,
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
                "market_flow_source": "N/A",
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
            current_price = 0
            try:
                hist, history_source = self._fetch_price_history(t)
                if not hist.empty:
                    current_price = self._apply_price_history(hist, history_source)
                else:
                    # Last resort for price only; technical indicators need daily OHLCV.
                    try:
                        current_price = self._to_float(t.fast_info["lastPrice"])
                        if current_price > 0:
                            self.data["price"]["current_price"] = round(
                                current_price, 3
                            )
                            self.data["diagnostics"].append(
                                "price_source: Yahoo fast_info lastPrice"
                            )
                    except Exception as e:
                        self.data["diagnostics"].append(
                            f"fast_info_price_unavailable: {e}"
                        )
            except Exception as e:
                self.data["diagnostics"].append(f"price_history_unavailable: {e}")

            if current_price <= 0:
                if (
                    self._apply_stooq_quote_fallback()
                    or self._apply_alpha_vantage_global_quote()
                ):
                    current_price = self._to_float(
                        self.data["price"].get("current_price")
                    )

            # 2. Company Info & Capital Flow
            try:
                info = t.info
                if info:
                    company_name = info.get("longName") or info.get("shortName")
                    if company_name:
                        self.data["company_name"] = company_name
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

                    target = self._to_float(info.get("targetMeanPrice"))
                    recommendation = self._consensus_from_rating(
                        info.get("recommendationKey")
                    )
                    self._update_consensus(
                        target=target,
                        recommendation=recommendation,
                        current_price=current_price,
                        source="Yahoo yfinance info fallback",
                    )

                    # Capital Flow Analysis
                    market_cap = self._to_float(info.get("marketCap"))
                    volume = self._to_float(
                        info.get("volume") or info.get("regularMarketVolume")
                    )
                    avg_vol = self._to_float(
                        info.get("averageVolume10days") or info.get("averageVolume")
                    )
                    self._update_capital_flow_snapshot(
                        market_cap, volume, avg_vol, current_price
                    )
                    self.data["diagnostics"].append(
                        "profile_source: Yahoo yfinance info"
                    )
            except Exception as e:
                self.data["diagnostics"].append(f"profile_unavailable: {e}")

            self._apply_yahoo_quote_summary(current_price)
            current_price = self._to_float(self.data["price"].get("current_price"))

            if self._has_missing_enrichment_fields():
                self._apply_yahoo_quote_lookup(current_price)
                current_price = self._to_float(self.data["price"].get("current_price"))

            consensus_source = self.data["consensus"].get("source")
            if (
                self.data["consensus"].get("target_price") == "N/A"
                or self.data["consensus"].get("recommendation") == "N/A"
                or consensus_source in ("N/A", "Yahoo yfinance info fallback")
            ):
                self._apply_yahoo_insights(current_price)

            has_profile = self.data["company_name"] not in ("N/A", self.ticker)
            if (
                not has_profile
                or self.data["capital_flow"].get("market_cap") == "N/A"
                or self.data["consensus"].get("target_price") == "N/A"
            ):
                self._apply_alpha_vantage_overview()

            if not self.data["capital_flow"].get("market_flow_details"):
                self.data["capital_flow"].update(self._get_market_flow_analysis())

            # 3. Real institutional holders (Yahoo Finance first, Alpha Vantage fallback)
            self.data["capital_flow"][
                "institutional_flow"
            ] = self._fetch_institutional_flow()

            # 4. Unusual options activity (Yahoo Finance options chain)
            self.data["capital_flow"]["options_flow"] = self._fetch_options_flow()

            # 5. News
            self._fetch_google_news()

            # 6. Fundamentals
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

            # 7. Smart Checklists
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

    def _json_safe(self, value):
        """Convert provider/pandas values into strict JSON-safe primitives."""
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(item) for item in value]
        if isinstance(value, (datetime, pd.Timestamp)):
            if pd.isna(value):
                return "N/A"
            return value.isoformat()
        if value is pd.NA or value is pd.NaT:
            return "N/A"
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, float):
            return value if np.isfinite(value) else "N/A"
        return value

    def output_json(self):
        def serialize(obj):
            if isinstance(obj, (datetime, pd.Timestamp)):
                return self._json_safe(obj)
            if isinstance(obj, np.generic):
                return self._json_safe(obj)
            return str(obj)

        safe_data = self._json_safe(self.data)
        print(
            json.dumps(
                safe_data, ensure_ascii=False, default=serialize, allow_nan=False
            )
        )


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    engine = StockResearchEngine(ticker)
    engine.run_research()
    engine.output_json()
