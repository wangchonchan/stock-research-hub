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
  sentiment: "Positive" | "Negative" | "Neutral";
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
  direction: "Inflow" | "Outflow" | "Neutral" | string;
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
  market_flow_details?: FlowDetail[];
  sector_flow_details?: FlowDetail[];
  flow_destination_summary?: FlowDestinationSummary;
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

const HISTORY_STORAGE_KEY = "stock_research_history_v10";

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
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
  }, [history]);

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
      const result = await response.json();
      setData(result);
      const newItem: HistoryItem = {
        id: Date.now().toString(),
        ticker: result.ticker,
        timestamp: new Date().toLocaleString("zh-CN", {
          timeZone: "Asia/Hong_Kong",
        }),
        price: result.price.current_price,
        data: result,
      };
      setHistory(prev =>
        [newItem, ...prev.filter(h => h.ticker !== result.ticker)].slice(0, 20)
      );
      toast.success(`已更新 ${searchTicker.toUpperCase()} 的研究数据`);
    } catch (error) {
      console.error(error);
      const message = error instanceof Error ? error.message : "未知错误";
      toast.error("更新股票数据时出错", { description: message });
    } finally {
      setLoading(false);
    }
  };

  const exportReport = () => {
    window.print();
  };

  const getFlowColor = (intensity: string) => {
    if (intensity.includes("Inflow") || intensity.includes("流入"))
      return "text-emerald-600 bg-emerald-50 border-emerald-100";
    if (
      intensity.includes("Outflow") ||
      intensity.includes("流出") ||
      intensity.includes("下跌")
    )
      return "text-rose-600 bg-rose-50 border-rose-100";
    return "text-slate-600 bg-slate-50 border-slate-100";
  };

  const getDirectionColor = (direction: string) => {
    if (direction === "Inflow")
      return "text-emerald-600 bg-emerald-50 border-emerald-100";
    if (direction === "Outflow")
      return "text-rose-600 bg-rose-50 border-rose-100";
    return "text-slate-600 bg-slate-50 border-slate-100";
  };

  const formatPercent = (value: number | string) => {
    if (typeof value !== "number" || isNaN(value)) return value;
    return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

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

                {/* Capital Flow Analysis Section */}
                <Card className="shadow-sm border-slate-200 overflow-hidden">
                  <CardHeader className="bg-slate-950 text-white border-b">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                      <div>
                        <CardTitle className="text-lg font-bold flex items-center gap-2">
                          <Wallet className="text-blue-300" />
                          资金流向拆解 (Capital Flow Map)
                        </CardTitle>
                        <p className="text-xs text-slate-400 mt-2 max-w-3xl leading-relaxed">
                          使用成交额 × 涨跌方向估算资金活跃与去向；这是
                          ETF/个股层面的 proxy，不是逐笔真实净流入。
                        </p>
                      </div>
                      <Badge
                        variant="outline"
                        className="border-blue-300/40 bg-blue-400/10 text-blue-100 w-fit"
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
                          预估成交额 Proxy
                        </p>
                        <p className="text-xl font-black text-slate-900">
                          {formatLargeNumber(
                            data.capital_flow.net_flow_proxy_usd
                          )}
                        </p>
                        <p className="text-xs text-slate-500 mt-2">
                          成交量 × 股价，不等于真实净流入
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-4">
                        <p className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-1">
                          资金最可能流入
                        </p>
                        <p className="font-bold text-emerald-900">
                          {data.capital_flow.flow_destination_summary
                            ?.top_inflow ?? "N/A"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-rose-100 bg-rose-50/60 p-4">
                        <p className="text-xs font-bold text-rose-600 uppercase tracking-wider mb-1">
                          资金最可能流出
                        </p>
                        <p className="font-bold text-rose-900">
                          {data.capital_flow.flow_destination_summary
                            ?.top_outflow ?? "N/A"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4">
                        <p className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-1">
                          风险偏好
                        </p>
                        <p className="font-bold text-blue-900">
                          {data.capital_flow.flow_destination_summary
                            ?.risk_appetite ?? "N/A"}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                          <Globe size={16} className="text-blue-600" />
                          大盘资金流向 Proxy
                        </h4>
                        <div className="space-y-3">
                          {(data.capital_flow.market_flow_details ?? []).map(
                            item => (
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
                                  <span>{item.volume_ratio}x vol</span>
                                  <span>
                                    {formatLargeNumber(
                                      item.signed_flow_proxy_usd
                                    )}
                                  </span>
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                          <Activity size={16} className="text-emerald-600" />
                          板块资金去向 Proxy
                        </h4>
                        <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
                          {(data.capital_flow.sector_flow_details ?? []).map(
                            item => (
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
                                  <span>{item.volume_ratio}x vol</span>
                                  <span>
                                    {formatLargeNumber(
                                      item.signed_flow_proxy_usd
                                    )}
                                  </span>
                                </div>
                              </div>
                            )
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
                <CardTitle className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Clock size={16} className="text-blue-600" />
                  最近搜索
                </CardTitle>
              </CardHeader>
              <CardContent className="px-2">
                {history.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-8">
                    暂无搜索记录
                  </p>
                ) : (
                  <div className="space-y-1">
                    {history.map(item => (
                      <button
                        key={item.id}
                        onClick={() => setData(item.data)}
                        className={`w-full flex items-center justify-between p-3 rounded-xl transition-all hover:bg-slate-100 group ${data?.ticker === item.ticker ? "bg-blue-50 border-blue-100" : ""}`}
                      >
                        <div className="text-left">
                          <p className="font-bold text-slate-900">
                            {item.ticker}
                          </p>
                          <p className="text-[10px] text-slate-400">
                            {item.timestamp}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-slate-900">
                            ${item.price ? item.price.toFixed(2) : "0.00"}
                          </p>
                          <ArrowLeftRight
                            size={14}
                            className="ml-auto text-slate-300 group-hover:text-blue-500"
                          />
                        </div>
                      </button>
                    ))}
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
