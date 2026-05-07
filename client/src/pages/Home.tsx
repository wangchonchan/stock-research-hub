import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  Search,
  TrendingUp,
  BarChart3,
  Activity,
  Clock,
  CheckCircle2,
  AlertCircle,
  Info,
  Newspaper,
  ExternalLink,
  Download,
  TrendingDown,
  Minus,
  ArrowLeftRight,
  Wallet,
  Globe,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
} from "recharts";

interface NewsItem {
  title: string;
  publisher: string;
  link: string;
  provider_publish_time: string;
  sentiment: "Positive" | "Negative" | "Neutral" | "中性" | string;
}

interface HistoricalTrend {
  period: string;
  revenue: number;
  net_income: number;
}

interface ChecklistItem {
  name: string;
  value: string | number;
  status: string;
  triggered: boolean;
  description: string;
}

interface FlowDetail {
  symbol: string;
  label: string;
  category: string;
  direction: "流入" | "流出" | "中性" | string;
  intensity: string;
  change_percent: number | string;
  volume_ratio: number | string;
  dollar_volume_proxy_usd: number | string;
  signed_flow_proxy_usd: number | string;
}

interface FlowDestinationSummary {
  top_inflow: string;
  top_outflow: string;
  risk_appetite: string;
}

interface InstitutionalHolding {
  holder: string;
  report_date: string;
  shares: number | string;
  market_value_usd: number | string;
  change_shares: number | string | null;
}

interface InstitutionalFlow {
  available: boolean;
  source: string;
  latest_report_date: string;
  note: string;
  top_holders: InstitutionalHolding[];
  top_increases: InstitutionalHolding[];
  top_decreases: InstitutionalHolding[];
}

interface UnusualOptionContract {
  contract_symbol: string;
  type: "看涨" | "看跌" | string;
  expiration: string;
  strike: number | string;
  last_price: number | string;
  volume: number | string;
  open_interest: number | string;
  volume_oi_ratio: number | string;
  premium_usd: number | string;
  implied_volatility: number | string;
  last_trade_date: string;
}

interface OptionsFlow {
  available: boolean;
  source: string;
  as_of: string;
  expirations_analyzed: string[];
  bullish_premium_proxy_usd: number | string;
  bearish_premium_proxy_usd: number | string;
  put_call_premium_ratio: number | string;
  unusual_contracts: UnusualOptionContract[];
  note: string;
}

interface CapitalFlow {
  market_bucket: string;
  market_cap: number | string;
  volume: number | string;
  avg_volume_10d: number | string;
  volume_ratio: number | string;
  estimated_flow_intensity: string;
  net_flow_proxy_usd: number | string;
  market_wide_flow: {
    mega_cap: string;
    large_cap: string;
    small_cap: string;
  };
  market_flow_source?: string;
  market_flow_details?: FlowDetail[];
  sector_flow_details?: FlowDetail[];
  flow_destination_summary?: FlowDestinationSummary;
  institutional_flow?: InstitutionalFlow;
  options_flow?: OptionsFlow;
}

interface StockData {
  ticker: string;
  company_name: string;
  description: string;
  timestamp: string;
  updated_at: string;
  price: {
    current_price: number;
    change: number;
    change_percent: number;
    pb_ratio: number | string;
    pe_ratio: number | string;
  };
  consensus: {
    target_price: number | string;
    upside_potential: number | string;
    recommendation: string;
  };
  fundamentals: {
    quarter: string;
    revenue: number | string;
    revenue_yoy: number | string;
    gross_margin: number | string;
    net_margin: number | string;
    cash_reserves: number | string;
    historical_trends: HistoricalTrend[];
  };
  technicals: {
    rsi: number | string;
    ma_5: number | string;
    ma_60: number | string;
    osc_20: number | string;
    bias_24: number | string;
    cci_14: number | string;
  };
  capital_flow: CapitalFlow;
  news: NewsItem[];
  checklists: ChecklistItem[];
  diagnostics?: string[];
}

interface HistoryItem {
  id: string;
  ticker: string;
  timestamp: string;
  price: number;
  data: StockData;
}

interface StockResearchError {
  error?: string;
  details?: string;
  diagnostics?: string[];
}

const isStockDataPayload = (value: unknown): value is StockData => {
  if (!value || typeof value !== "object") return false;
  const payload = value as Partial<StockData>;
  return (
    typeof payload.ticker === "string" &&
    Boolean(payload.ticker) &&
    Boolean(payload.price) &&
    typeof payload.price?.current_price === "number" &&
    Boolean(payload.capital_flow) &&
    Array.isArray(payload.news) &&
    Array.isArray(payload.checklists)
  );
};

const HISTORY_STORAGE_KEY = "stock_research_history_v10";

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(
    null
  );
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const savedHistory = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error("Failed to parse history:", e);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
    setCompareIds(prev =>
      prev.filter(id => history.some(item => item.id === id))
    );
  }, [history]);

  const compareItems = history.filter(item => compareIds.includes(item.id));

  const formatLargeNumber = (num: number | string) => {
    if (typeof num !== "number" || isNaN(num)) return num;
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
  };

  const handleSearch = async (searchTicker: string) => {
    if (!searchTicker) return;
    setLoading(true);
    try {
      const response = await fetch("/api/stock-research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: searchTicker }),
      });
      if (!response.ok) {
        let message = "Failed to fetch data";
        try {
          const errorPayload = (await response.json()) as StockResearchError;
          message = errorPayload.details || errorPayload.error || message;
        } catch {
          // Keep the generic message when the server does not return JSON.
        }
        throw new Error(message);
      }
      const result: unknown = await response.json();
      if (!isStockDataPayload(result)) {
        throw new Error("API 返回的数据结构不完整，请稍后重试。");
      }

      setData(result);
      const newItem: HistoryItem = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        ticker: result.ticker,
        timestamp: new Date().toLocaleString("zh-CN", {
          timeZone: "Asia/Hong_Kong",
        }),
        price: result.price.current_price,
        data: result,
      };
      setSelectedHistoryId(newItem.id);
      setHistory(prev => [newItem, ...prev].slice(0, 20));
      toast.success(`已更新 ${searchTicker.toUpperCase()} 的研究数据`);
    } catch (error) {
      console.error(error);
      const message = error instanceof Error ? error.message : "未知错误";
      toast.error("更新股票数据时出错", { description: message });
    } finally {
      setLoading(false);
    }
  };

  const toggleCompareItem = (itemId: string) => {
    setCompareIds(prev => {
      if (prev.includes(itemId)) return prev.filter(id => id !== itemId);
      return [itemId, ...prev].slice(0, 3);
    });
  };

  const openHistoryItem = (item: HistoryItem) => {
    setSelectedHistoryId(item.id);
    setData(item.data);
  };

  const deleteHistoryItem = (itemId: string) => {
    setHistory(prev => prev.filter(item => item.id !== itemId));
    setCompareIds(prev => prev.filter(id => id !== itemId));
    if (selectedHistoryId === itemId) {
      setSelectedHistoryId(null);
      setData(null);
    }
    toast.success("已删除这条搜索记录");
  };

  const clearHistory = () => {
    setHistory([]);
    setCompareIds([]);
    setSelectedHistoryId(null);
    setData(null);
    toast.success("已清空搜索记录");
  };

  const exportReport = () => {
    window.print();
  };

  const getFlowColor = (intensity: string) => {
    if (intensity.includes("流入"))
      return "text-emerald-600 bg-emerald-50 border-emerald-100";
    if (intensity.includes("流出") || intensity.includes("下跌"))
      return "text-rose-600 bg-rose-50 border-rose-100";
    return "text-slate-600 bg-slate-50 border-slate-100";
  };

  const getDirectionColor = (direction: string) => {
    if (direction === "流入")
      return "text-emerald-600 bg-emerald-50 border-emerald-100";
    if (direction === "流出") return "text-rose-600 bg-rose-50 border-rose-100";
    return "text-slate-600 bg-slate-50 border-slate-100";
  };

  const formatPercent = (value: number | string) => {
    if (typeof value !== "number" || isNaN(value)) return value;
    return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  const formatShares = (value: number | string | null) => {
    if (typeof value !== "number" || isNaN(value)) return value ?? "N/A";
    return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  };

  const hasFlowMetric = (item: FlowDetail) =>
    typeof item.change_percent === "number" ||
    typeof item.volume_ratio === "number" ||
    typeof item.signed_flow_proxy_usd === "number";

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 print:p-0 print:bg-white">
      <div className="max-w-6xl mx-auto" ref={reportRef}>
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4 print:hidden">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white w-10 h-10 flex items-center justify-center rounded-lg font-bold text-xl">
              S
            </div>
            <h1 className="text-2xl font-bold text-slate-900">
              股票研究中心 v3.2
            </h1>
          </div>
          <div className="flex gap-2 w-full md:w-auto">
            <form
              onSubmit={e => {
                e.preventDefault();
                handleSearch(ticker);
              }}
              className="flex flex-1 gap-2"
            >
              <Input
                placeholder="股票代码 (如: TSLA)"
                value={ticker}
                onChange={e => setTicker(e.target.value)}
                className="bg-white"
              />
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Search className="mr-2 h-4 w-4" />
                )}
                更新
              </Button>
            </form>
            {data && (
              <Button variant="outline" onClick={exportReport}>
                <Download className="mr-2 h-4 w-4" />
                导出
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-3">
            {!data && !loading && (
              <div className="text-center py-20 bg-white rounded-2xl border-2 border-dashed border-slate-200">
                <BarChart3 className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                <h2 className="text-xl font-medium text-slate-600">
                  输入股票代码开始研究
                </h2>
              </div>
            )}

            {data && (
              <div className="space-y-6 animate-in fade-in duration-500">
                {/* Insight Box */}
                <div className="bg-slate-900 text-white rounded-2xl p-6 md:p-8 shadow-xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-8 opacity-10">
                    <Activity size={120} />
                  </div>
                  <div className="relative z-10">
                    <div className="flex justify-between items-start mb-6">
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          <h2 className="text-4xl font-black tracking-tight">
                            {data.ticker}
                          </h2>
                          <Badge
                            variant="outline"
                            className="text-blue-400 border-blue-400/30 bg-blue-400/10"
                          >
                            {data.company_name}
                          </Badge>
                        </div>
                        <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
                          {data.description}
                        </p>
                        <p className="text-slate-500 text-xs mt-2">
                          最后更新: {data.updated_at} (HKT)
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-4xl font-bold">
                          $
                          {data.price.current_price
                            ? data.price.current_price.toFixed(2)
                            : "0.00"}
                        </div>
                        <div
                          className={`flex items-center justify-end gap-1 font-medium ${data.price.change >= 0 ? "text-emerald-400" : "text-rose-400"}`}
                        >
                          {data.price.change >= 0 ? (
                            <TrendingUp size={16} />
                          ) : (
                            <TrendingDown size={16} />
                          )}
                          {data.price.change >= 0 ? "+" : ""}
                          {data.price.change_percent}%
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                      <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider mb-1">
                          共识建议
                        </p>
                        <p className="text-lg font-bold text-blue-400">
                          {data.consensus.recommendation}
                        </p>
                      </div>
                      <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider mb-1">
                          目标价
                        </p>
                        <p className="text-lg font-bold">
                          ${data.consensus.target_price}
                        </p>
                      </div>
                      <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider mb-1">
                          上涨空间
                        </p>
                        <p
                          className={`text-lg font-bold ${Number(data.consensus.upside_potential) > 0 ? "text-emerald-400" : "text-rose-400"}`}
                        >
                          {data.consensus.upside_potential}%
                        </p>
                      </div>
                      <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider mb-1">
                          市净率 (PB)
                        </p>
                        <p className="text-lg font-bold">
                          {data.price.pb_ratio}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="shadow-sm border-slate-200">
                    <CardHeader>
                      <CardTitle className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                        <BarChart3 size={16} className="text-blue-600" />
                        营收趋势 (最近4个季度)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={data.fundamentals.historical_trends}>
                            <CartesianGrid
                              strokeDasharray="3 3"
                              vertical={false}
                              stroke="#f1f5f9"
                            />
                            <XAxis
                              dataKey="period"
                              axisLine={false}
                              tickLine={false}
                              tick={{ fontSize: 12, fill: "#64748b" }}
                            />
                            <YAxis
                              axisLine={false}
                              tickLine={false}
                              tick={{ fontSize: 12, fill: "#64748b" }}
                              tickFormatter={value =>
                                `$${(value / 1e9).toFixed(0)}B`
                              }
                            />
                            <Tooltip
                              contentStyle={{
                                borderRadius: "12px",
                                border: "none",
                                boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                              }}
                              formatter={(value: number) => [
                                formatLargeNumber(value),
                                "营收",
                              ]}
                            />
                            <Bar
                              dataKey="revenue"
                              fill="#3b82f6"
                              radius={[4, 4, 0, 0]}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="shadow-sm border-slate-200">
                    <CardHeader>
                      <CardTitle className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                        <Activity size={16} className="text-emerald-600" />
                        净利润趋势
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={data.fundamentals.historical_trends}>
                            <CartesianGrid
                              strokeDasharray="3 3"
                              vertical={false}
                              stroke="#f1f5f9"
                            />
                            <XAxis
                              dataKey="period"
                              axisLine={false}
                              tickLine={false}
                              tick={{ fontSize: 12, fill: "#64748b" }}
                            />
                            <YAxis
                              axisLine={false}
                              tickLine={false}
                              tick={{ fontSize: 12, fill: "#64748b" }}
                              tickFormatter={value =>
                                `$${(value / 1e9).toFixed(0)}B`
                              }
                            />
                            <Tooltip
                              contentStyle={{
                                borderRadius: "12px",
                                border: "none",
                                boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                              }}
                              formatter={(value: number) => [
                                formatLargeNumber(value),
                                "净利润",
                              ]}
                            />
                            <Line
                              type="monotone"
                              dataKey="net_income"
                              stroke="#10b981"
                              strokeWidth={3}
                              dot={{ r: 4, fill: "#10b981" }}
                              activeDot={{ r: 6 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Technical Indicators Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-blue-600" />
                      <CardTitle>
                        核心基本面 ({data.fundamentals.quarter})
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">营收</span>
                        <span className="font-semibold">
                          {formatLargeNumber(data.fundamentals.revenue)}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">同比增长 (YoY)</span>
                        <span
                          className={`font-semibold ${typeof data.fundamentals.revenue_yoy === "number" && data.fundamentals.revenue_yoy >= 0 ? "text-green-600" : "text-red-600"}`}
                        >
                          {typeof data.fundamentals.revenue_yoy === "number"
                            ? `${data.fundamentals.revenue_yoy > 0 ? "+" : ""}${data.fundamentals.revenue_yoy}%`
                            : data.fundamentals.revenue_yoy}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">毛利率</span>
                        <span className="font-semibold">
                          {data.fundamentals.gross_margin}
                          {typeof data.fundamentals.gross_margin === "number"
                            ? "%"
                            : ""}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">净利率</span>
                        <span className="font-semibold">
                          {data.fundamentals.net_margin}
                          {typeof data.fundamentals.net_margin === "number"
                            ? "%"
                            : ""}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">现金储备</span>
                        <span className="font-semibold">
                          {formatLargeNumber(data.fundamentals.cash_reserves)}
                        </span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center gap-2">
                      <Activity className="h-5 w-5 text-blue-600" />
                      <CardTitle>技术指标</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">RSI (14)</span>
                        <span
                          className={`font-semibold ${typeof data.technicals.rsi === "number" && (data.technicals.rsi > 70 || data.technicals.rsi < 30) ? "text-orange-600" : "text-slate-900"}`}
                        >
                          {data.technicals.rsi}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">MA (5)</span>
                        <span className="font-semibold">
                          ${data.technicals.ma_5}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">MA (60)</span>
                        <span className="font-semibold">
                          ${data.technicals.ma_60}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">OSC (20)</span>
                        <span className="font-semibold">
                          {data.technicals.osc_20}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">CCI (14)</span>
                        <span className="font-semibold">
                          {data.technicals.cci_14}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {compareItems.length >= 2 && (
                  <Card className="shadow-sm border-slate-200 overflow-hidden print:hidden">
                    <CardHeader className="bg-white border-b">
                      <CardTitle className="text-lg font-bold flex items-center gap-2">
                        <ArrowLeftRight className="text-blue-600" />
                        搜索记录对比
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6 overflow-x-auto">
                      <div
                        className="grid gap-4"
                        style={{
                          gridTemplateColumns: `repeat(${compareItems.length}, minmax(220px, 1fr))`,
                        }}
                      >
                        {compareItems.map(item => (
                          <div
                            key={item.id}
                            className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                          >
                            <div className="flex items-start justify-between gap-2 mb-4">
                              <div>
                                <p className="text-2xl font-black text-slate-900">
                                  {item.ticker}
                                </p>
                                <p className="text-[10px] text-slate-400">
                                  {item.timestamp}
                                </p>
                              </div>
                              <Badge variant="outline">
                                ${item.price ? item.price.toFixed(2) : "0.00"}
                              </Badge>
                            </div>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between gap-3">
                                <span className="text-slate-500">涨跌幅</span>
                                <span
                                  className={
                                    item.data.price.change_percent >= 0
                                      ? "font-bold text-emerald-600"
                                      : "font-bold text-rose-600"
                                  }
                                >
                                  {formatPercent(
                                    item.data.price.change_percent
                                  )}
                                </span>
                              </div>
                              <div className="flex justify-between gap-3">
                                <span className="text-slate-500">PE</span>
                                <span className="font-bold text-slate-900">
                                  {item.data.price.pe_ratio}
                                </span>
                              </div>
                              <div className="flex justify-between gap-3">
                                <span className="text-slate-500">PB</span>
                                <span className="font-bold text-slate-900">
                                  {item.data.price.pb_ratio}
                                </span>
                              </div>
                              <div className="flex justify-between gap-3">
                                <span className="text-slate-500">营收 YoY</span>
                                <span className="font-bold text-slate-900">
                                  {typeof item.data.fundamentals.revenue_yoy ===
                                  "number"
                                    ? formatPercent(
                                        item.data.fundamentals.revenue_yoy
                                      )
                                    : item.data.fundamentals.revenue_yoy}
                                </span>
                              </div>
                              <div className="flex justify-between gap-3">
                                <span className="text-slate-500">
                                  成交量比率
                                </span>
                                <span className="font-bold text-slate-900">
                                  {item.data.capital_flow.volume_ratio}x
                                </span>
                              </div>
                              <div className="flex justify-between gap-3">
                                <span className="text-slate-500">RSI</span>
                                <span className="font-bold text-slate-900">
                                  {item.data.technicals.rsi}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Capital Flow Analysis Section */}
                <Card className="shadow-sm border-slate-200 overflow-hidden">
                  <CardHeader className="bg-white border-b border-slate-100">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                      <div>
                        <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                          <Wallet className="text-blue-600" />
                          市场资金活跃度拆解
                        </CardTitle>
                        <p className="mt-1 text-xs text-slate-500">
                          ETF 活跃度数据源：
                          {data.capital_flow.market_flow_source ?? "N/A"}
                        </p>
                      </div>
                      <Badge
                        variant="outline"
                        className="border-blue-200 bg-blue-50 text-blue-700 w-fit"
                      >
                        {data.capital_flow.estimated_flow_intensity}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="p-6 space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="rounded-xl border border-slate-200 bg-white p-4">
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                          市值分类
                        </p>
                        <p className="text-xl font-black text-slate-900">
                          {data.capital_flow.market_bucket}
                        </p>
                        <p className="text-xs text-slate-500 mt-2">
                          总市值{" "}
                          {formatLargeNumber(data.capital_flow.market_cap)}
                        </p>
                      </div>
                      <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
                        <p className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-1">
                          成交量比率
                        </p>
                        <p className="text-3xl font-black text-blue-900">
                          {data.capital_flow.volume_ratio}x
                        </p>
                        <p className="text-xs text-blue-500 mt-2">
                          当日成交量 / 10日均量
                        </p>
                      </div>
                      <div className="rounded-xl border border-slate-200 bg-white p-4">
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                          预估成交额
                        </p>
                        <p className="text-xl font-black text-slate-900">
                          {formatLargeNumber(
                            data.capital_flow.net_flow_proxy_usd
                          )}
                        </p>
                        <p className="text-xs text-slate-500 mt-2">
                          成交量 × 股价
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="rounded-xl border border-emerald-100 bg-emerald-50/70 p-4">
                        <p className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-1">
                          最强流入板块
                        </p>
                        <p className="text-sm font-black text-emerald-950">
                          {data.capital_flow.flow_destination_summary
                            ?.top_inflow ?? "N/A"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-rose-100 bg-rose-50/70 p-4">
                        <p className="text-xs font-bold text-rose-700 uppercase tracking-wider mb-1">
                          最强流出板块
                        </p>
                        <p className="text-sm font-black text-rose-950">
                          {data.capital_flow.flow_destination_summary
                            ?.top_outflow ?? "N/A"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                          风险偏好
                        </p>
                        <p className="text-sm font-black text-slate-900">
                          {data.capital_flow.flow_destination_summary
                            ?.risk_appetite ?? "N/A"}
                        </p>
                      </div>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-white p-5">
                      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 mb-4">
                        <div>
                          <h4 className="font-bold text-slate-900">
                            真实机构持仓（13F）
                          </h4>
                          <p className="text-xs text-slate-500 mt-1">
                            数据源：
                            {data.capital_flow.institutional_flow?.source ??
                              "N/A"}
                            ；最新报告期：
                            {data.capital_flow.institutional_flow
                              ?.latest_report_date ?? "N/A"}
                          </p>
                        </div>
                        <Badge
                          className={
                            data.capital_flow.institutional_flow?.available
                              ? "bg-emerald-500 text-white"
                              : "bg-slate-400 text-white"
                          }
                        >
                          {data.capital_flow.institutional_flow?.available
                            ? "已连接真实 API"
                            : "等待 Yahoo 数据"}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mb-4">
                        {data.capital_flow.institutional_flow?.note ??
                          "Yahoo Finance 暂未返回机构持仓数据。"}
                      </p>

                      {data.capital_flow.institutional_flow?.available ? (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                          <div>
                            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                              主要机构持仓
                            </p>
                            <div className="space-y-2">
                              {(
                                data.capital_flow.institutional_flow
                                  .top_holders ?? []
                              )
                                .slice(0, 5)
                                .map((item, idx) => (
                                  <div
                                    key={`${item.holder}-${idx}`}
                                    className="rounded-lg border border-slate-100 bg-slate-50 p-3"
                                  >
                                    <p className="font-bold text-slate-900 text-sm line-clamp-1">
                                      {item.holder}
                                    </p>
                                    <p className="text-xs text-slate-500 mt-1">
                                      {formatShares(item.shares)} 股 ·{" "}
                                      {formatLargeNumber(item.market_value_usd)}
                                    </p>
                                  </div>
                                ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-2">
                              增持最多
                            </p>
                            <div className="space-y-2">
                              {(
                                data.capital_flow.institutional_flow
                                  .top_increases ?? []
                              )
                                .slice(0, 5)
                                .map((item, idx) => (
                                  <div
                                    key={`${item.holder}-inc-${idx}`}
                                    className="rounded-lg border border-emerald-100 bg-emerald-50/60 p-3"
                                  >
                                    <p className="font-bold text-emerald-900 text-sm line-clamp-1">
                                      {item.holder}
                                    </p>
                                    <p className="text-xs text-emerald-700 mt-1">
                                      +{formatShares(item.change_shares)} 股
                                    </p>
                                  </div>
                                ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-xs font-bold text-rose-600 uppercase tracking-wider mb-2">
                              减持最多
                            </p>
                            <div className="space-y-2">
                              {(
                                data.capital_flow.institutional_flow
                                  .top_decreases ?? []
                              )
                                .slice(0, 5)
                                .map((item, idx) => (
                                  <div
                                    key={`${item.holder}-dec-${idx}`}
                                    className="rounded-lg border border-rose-100 bg-rose-50/60 p-3"
                                  >
                                    <p className="font-bold text-rose-900 text-sm line-clamp-1">
                                      {item.holder}
                                    </p>
                                    <p className="text-xs text-rose-700 mt-1">
                                      {formatShares(item.change_shares)} 股
                                    </p>
                                  </div>
                                ))}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
                          Yahoo Finance 暂未返回机构持仓数据；如果需要备用真实
                          13F 数据源，可以在部署环境变量里配置{" "}
                          <code className="font-mono text-xs bg-white px-1 py-0.5 rounded">
                            ALPHA_VANTAGE_API_KEY
                          </code>
                          。
                        </div>
                      )}
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-white p-5">
                      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 mb-4">
                        <div>
                          <h4 className="font-bold text-slate-900">
                            异常期权大单
                          </h4>
                          <p className="text-xs text-slate-500 mt-1">
                            数据源：
                            {data.capital_flow.options_flow?.source ?? "N/A"}
                            ；更新时间：
                            {data.capital_flow.options_flow?.as_of ?? "N/A"}
                          </p>
                        </div>
                        <Badge
                          className={
                            data.capital_flow.options_flow?.available
                              ? "bg-blue-600 text-white"
                              : "bg-slate-400 text-white"
                          }
                        >
                          {data.capital_flow.options_flow?.available
                            ? "已连接 Yahoo 期权链"
                            : "等待 Yahoo 期权链"}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mb-4">
                        {data.capital_flow.options_flow?.note ??
                          "Yahoo Finance 暂未返回期权链数据。"}
                      </p>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-4">
                          <p className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-1">
                            看涨权利金
                          </p>
                          <p className="text-xl font-black text-emerald-900">
                            {formatLargeNumber(
                              data.capital_flow.options_flow
                                ?.bullish_premium_proxy_usd ?? "N/A"
                            )}
                          </p>
                        </div>
                        <div className="rounded-xl border border-rose-100 bg-rose-50/60 p-4">
                          <p className="text-xs font-bold text-rose-600 uppercase tracking-wider mb-1">
                            看跌权利金
                          </p>
                          <p className="text-xl font-black text-rose-900">
                            {formatLargeNumber(
                              data.capital_flow.options_flow
                                ?.bearish_premium_proxy_usd ?? "N/A"
                            )}
                          </p>
                        </div>
                        <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4">
                          <p className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-1">
                            Put/Call 权利金比
                          </p>
                          <p className="text-xl font-black text-blue-900">
                            {data.capital_flow.options_flow
                              ?.put_call_premium_ratio ?? "N/A"}
                          </p>
                        </div>
                      </div>

                      {(data.capital_flow.options_flow?.unusual_contracts ?? [])
                        .length > 0 ? (
                        <div className="space-y-3">
                          {(
                            data.capital_flow.options_flow?.unusual_contracts ??
                            []
                          ).map(item => (
                            <div
                              key={item.contract_symbol}
                              className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                            >
                              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-3">
                                <div>
                                  <p className="font-black text-slate-900">
                                    {item.contract_symbol}
                                  </p>
                                  <p className="text-xs text-slate-500">
                                    {item.expiration} · {item.type} · 行权价 $
                                    {item.strike}
                                  </p>
                                </div>
                                <Badge
                                  className={
                                    item.type === "看涨"
                                      ? "bg-emerald-500 text-white"
                                      : "bg-rose-500 text-white"
                                  }
                                >
                                  {item.type}
                                </Badge>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs font-semibold text-slate-600">
                                <span>成交量 {formatShares(item.volume)}</span>
                                <span>
                                  未平仓 {formatShares(item.open_interest)}
                                </span>
                                <span>量/OI {item.volume_oi_ratio}</span>
                                <span>
                                  权利金 {formatLargeNumber(item.premium_usd)}
                                </span>
                                <span>IV {item.implied_volatility}%</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
                          当前没有筛选出异常期权合约，或 Yahoo Finance
                          暂未返回期权链数据。
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                          <Globe size={16} className="text-blue-600" />
                          大盘成交活跃度
                        </h4>
                        <div className="space-y-3">
                          {(data.capital_flow.market_flow_details ?? []).filter(
                            hasFlowMetric
                          ).length > 0 ? (
                            (data.capital_flow.market_flow_details ?? [])
                              .filter(hasFlowMetric)
                              .map(item => (
                                <div
                                  key={item.symbol}
                                  className="rounded-xl border border-slate-200 bg-white p-4"
                                >
                                  <div className="flex items-start justify-between gap-3 mb-3">
                                    <div>
                                      <p className="font-black text-slate-900">
                                        {item.symbol}
                                      </p>
                                      <p className="text-xs text-slate-500">
                                        {item.label}
                                      </p>
                                    </div>
                                    <Badge
                                      className={getDirectionColor(
                                        item.direction
                                      )}
                                    >
                                      {item.direction}
                                    </Badge>
                                  </div>
                                  <div className="grid grid-cols-3 gap-2 text-xs font-semibold text-slate-600">
                                    <span>
                                      {formatPercent(item.change_percent)}
                                    </span>
                                    <span>{item.volume_ratio}x 成交量</span>
                                    <span>
                                      {formatLargeNumber(
                                        item.signed_flow_proxy_usd
                                      )}
                                    </span>
                                  </div>
                                </div>
                              ))
                          ) : (
                            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
                              当前 ETF 活跃度 API 暂未返回可用数据，请稍后重试。
                            </div>
                          )}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                          <Activity size={16} className="text-emerald-600" />
                          板块成交活跃度
                        </h4>
                        <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
                          {(data.capital_flow.sector_flow_details ?? []).filter(
                            hasFlowMetric
                          ).length > 0 ? (
                            (data.capital_flow.sector_flow_details ?? [])
                              .filter(hasFlowMetric)
                              .map(item => (
                                <div
                                  key={item.symbol}
                                  className="rounded-xl border border-slate-200 bg-white p-4"
                                >
                                  <div className="flex items-start justify-between gap-3 mb-3">
                                    <div>
                                      <p className="font-black text-slate-900">
                                        {item.symbol}
                                      </p>
                                      <p className="text-xs text-slate-500">
                                        {item.label}
                                      </p>
                                    </div>
                                    <Badge
                                      className={getFlowColor(item.intensity)}
                                    >
                                      {item.intensity}
                                    </Badge>
                                  </div>
                                  <div className="grid grid-cols-3 gap-2 text-xs font-semibold text-slate-600">
                                    <span>
                                      {formatPercent(item.change_percent)}
                                    </span>
                                    <span>{item.volume_ratio}x 成交量</span>
                                    <span>
                                      {formatLargeNumber(
                                        item.signed_flow_proxy_usd
                                      )}
                                    </span>
                                  </div>
                                </div>
                              ))
                          ) : (
                            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
                              当前板块 ETF 活跃度 API
                              暂未返回可用数据，请稍后重试。
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Smart Checklist */}
                <Card className="shadow-sm border-slate-200">
                  <CardHeader>
                    <CardTitle className="text-lg font-bold flex items-center gap-2">
                      <CheckCircle2 className="text-blue-600" />
                      智能投资检查清单
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {data.checklists.map((item, idx) => (
                        <div
                          key={idx}
                          className={`p-4 rounded-xl border-2 transition-all ${item.triggered ? "border-emerald-100 bg-emerald-50/30" : "border-slate-100 bg-slate-50/30"}`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-bold text-slate-900 text-sm">
                              {item.name}
                            </h4>
                            <Badge
                              className={
                                item.triggered
                                  ? "bg-emerald-500"
                                  : "bg-slate-400"
                              }
                            >
                              {item.status}
                            </Badge>
                          </div>
                          <p className="text-2xl font-black text-slate-900 mb-2">
                            {item.value}
                          </p>
                          <p className="text-xs text-slate-500 leading-relaxed">
                            {item.description}
                          </p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* News & Sentiment */}
                <Card className="shadow-sm border-slate-200">
                  <CardHeader>
                    <CardTitle className="text-lg font-bold flex items-center gap-2">
                      <Newspaper className="text-blue-600" />
                      最新新闻与情绪分析
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {data.news.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-4 p-4 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-200 group"
                        >
                          <div
                            className={`mt-1 p-2 rounded-lg ${
                              item.sentiment === "Positive"
                                ? "bg-emerald-100 text-emerald-600"
                                : item.sentiment === "Negative"
                                  ? "bg-rose-100 text-rose-600"
                                  : "bg-slate-100 text-slate-600"
                            }`}
                          >
                            {item.sentiment === "Positive" ? (
                              <TrendingUp size={20} />
                            ) : item.sentiment === "Negative" ? (
                              <TrendingDown size={20} />
                            ) : (
                              <Minus size={20} />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between items-start mb-1">
                              <a
                                href={item.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="font-bold text-slate-900 hover:text-blue-600 transition-colors line-clamp-1"
                              >
                                {item.title}
                              </a>
                              <ExternalLink
                                size={14}
                                className="text-slate-300 group-hover:text-blue-400"
                              />
                            </div>
                            <div className="flex items-center gap-3 text-xs text-slate-500">
                              <span className="font-bold text-slate-700">
                                {item.publisher}
                              </span>
                              <span>•</span>
                              <span className="flex items-center gap-1">
                                <Clock size={12} /> {item.provider_publish_time}
                              </span>
                              <span>•</span>
                              <Badge
                                variant="outline"
                                className={`text-[10px] py-0 h-4 ${
                                  item.sentiment === "Positive"
                                    ? "text-emerald-600 border-emerald-200"
                                    : item.sentiment === "Negative"
                                      ? "text-rose-600 border-rose-200"
                                      : "text-slate-400 border-slate-200"
                                }`}
                              >
                                {item.sentiment === "Positive"
                                  ? "看多"
                                  : item.sentiment === "Negative"
                                    ? "看空"
                                    : "中性"}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* Sidebar - History */}
          <div className="print:hidden">
            <Card className="sticky top-8 shadow-sm border-slate-200">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                    <Clock size={16} className="text-blue-600" />
                    最近搜索
                  </CardTitle>
                  {history.length > 0 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={clearHistory}
                      className="h-7 px-2 text-xs text-slate-400 hover:text-rose-600"
                    >
                      清空
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="px-2">
                {history.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-8">
                    暂无搜索记录
                  </p>
                ) : (
                  <div className="space-y-1">
                    {history.map(item => {
                      const isSelected = selectedHistoryId === item.id;
                      const isComparing = compareIds.includes(item.id);
                      return (
                        <div
                          key={item.id}
                          className={`rounded-xl transition-all ${isSelected ? "bg-blue-50 border border-blue-100" : "border border-transparent hover:bg-slate-100"}`}
                        >
                          <div className="flex items-stretch gap-1 p-1">
                            <button
                              onClick={() => openHistoryItem(item)}
                              className="min-w-0 flex-1 flex items-center justify-between rounded-lg p-2 text-left group hover:bg-white/70"
                            >
                              <div className="min-w-0">
                                <p className="font-bold text-slate-900 truncate">
                                  {item.ticker}
                                </p>
                                <p className="text-[10px] text-slate-400 truncate">
                                  {item.timestamp}
                                </p>
                              </div>
                              <div className="text-right pl-2">
                                <p className="font-bold text-slate-900">
                                  ${item.price ? item.price.toFixed(2) : "0.00"}
                                </p>
                                <ArrowLeftRight
                                  size={14}
                                  className="ml-auto text-slate-300 group-hover:text-blue-500"
                                />
                              </div>
                            </button>
                            <button
                              type="button"
                              aria-label={`删除 ${item.ticker} 搜索记录`}
                              onClick={() => deleteHistoryItem(item.id)}
                              className="my-2 rounded-lg px-2 text-slate-300 hover:bg-rose-50 hover:text-rose-600"
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                          <button
                            onClick={() => toggleCompareItem(item.id)}
                            className={`mx-3 mb-3 w-[calc(100%-1.5rem)] rounded-lg border px-2 py-1 text-xs font-bold transition-colors ${isComparing ? "border-blue-200 bg-blue-600 text-white" : "border-slate-200 bg-white text-slate-500 hover:text-blue-600"}`}
                          >
                            {isComparing ? "已加入对比" : "加入对比"}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
