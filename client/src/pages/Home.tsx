import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Loader2, Search, TrendingUp, BarChart3, 
  Activity, Clock, X, CheckCircle2, AlertCircle, 
  Info, Newspaper, ExternalLink, TrendingDown, Minus,
  ArrowLeftRight
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line
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
  news: NewsItem[];
  checklists: ChecklistItem[];
  capital_flow?: {
    market_bucket: string;
    market_cap: number | string;
    volume: number | string;
    avg_volume_10d: number | string;
    volume_ratio: number | string;
    estimated_flow_intensity: string;
    net_flow_proxy_usd: number | string;
  };
}

interface HistoryItem {
  id: string;
  ticker: string;
  timestamp: string;
  price: number;
  data: StockData;
}

const HISTORY_STORAGE_KEY = "stock_research_history_v9";

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [isCompareOpen, setIsCompareOpen] = useState(false);

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
    if (typeof num !== 'number') return num;
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
      if (!response.ok) throw new Error("Failed to fetch data");
      const result = await response.json();
      setData(result);
      const newItem: HistoryItem = {
        id: Date.now().toString(),
        ticker: result.ticker,
        timestamp: new Date().toLocaleString("en-US", { timeZone: "Asia/Hong_Kong" }),
        price: result.price.current_price,
        data: result
      };
      setHistory([newItem, ...history].slice(0, 20));
      toast.success(`Updated research for ${searchTicker.toUpperCase()}`);
    } catch (error) {
      console.error(error);
      toast.error("Error updating stock data.");
    } finally {
      setLoading(false);
    }
  };

  const deleteHistoryItem = (id: string) => {
    setHistory(history.filter(item => item.id !== id));
    setSelectedForCompare(selectedForCompare.filter(sid => sid !== id));
  };

  const toggleSelectForCompare = (id: string) => {
    if (selectedForCompare.includes(id)) {
      setSelectedForCompare(selectedForCompare.filter(sid => sid !== id));
    } else {
      if (selectedForCompare.length >= 2) {
        toast.warning("You can only compare 2 items at a time.");
        return;
      }
      setSelectedForCompare([...selectedForCompare, id]);
    }
  };

  const getCompareItems = () => {
    return history.filter(item => selectedForCompare.includes(item.id));
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white w-10 h-10 flex items-center justify-center rounded-lg font-bold text-xl">S</div>
            <h1 className="text-2xl font-bold text-slate-900">股票研究中心 v3.1</h1>
          </div>
          <form onSubmit={(e) => { e.preventDefault(); handleSearch(ticker); }} className="flex w-full md:w-auto gap-2">
            <Input placeholder="股票代码（例如 TSLA）" value={ticker} onChange={(e) => setTicker(e.target.value)} className="bg-white" />
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
              更新
            </Button>
          </form>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-3">
            {!data && !loading && (
              <div className="text-center py-20 bg-white rounded-2xl border-2 border-dashed border-slate-200">
                <BarChart3 className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                <h2 className="text-xl font-medium text-slate-600">输入股票代码开始分析</h2>
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
                          <h2 className="text-4xl font-black tracking-tight">{data.ticker}</h2>
                          <Badge variant="outline" className="text-blue-400 border-blue-400/30 bg-blue-400/10">
                            {data.company_name}
                          </Badge>
                        </div>
                        <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
                          {data.description}
                        </p>
                        <p className="text-slate-500 text-xs mt-2">最后更新：{data.updated_at}（HKT）</p>
                      </div>
                      <div className="text-right">
                        <div className="text-4xl font-bold">${data.price.current_price.toFixed(2)}</div>
                        <div className={`flex items-center justify-end gap-1 font-medium ${data.price.change >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {data.price.change >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                          {data.price.change >= 0 ? "+" : ""}{data.price.change_percent}%
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                      <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider mb-1">分析师共识</p>
                        <p className="text-lg font-bold text-blue-400">{data.consensus.recommendation}</p>
                      </div>
                      <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider mb-1">目标价</p>
                        <p className="text-lg font-bold">${data.consensus.target_price}</p>
                      </div>
                      <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider mb-1">上行空间</p>
                        <p className={`text-lg font-bold ${Number(data.consensus.upside_potential) > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          {data.consensus.upside_potential}%
                        </p>
                      </div>
                      <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                        <p className="text-slate-500 text-xs uppercase font-bold tracking-wider mb-1">市净率(PB)</p>
                        <p className="text-lg font-bold">{data.price.pb_ratio}</p>
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
                        营收趋势（近4季）
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={data.fundamentals.historical_trends}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis dataKey="period" axisLine={false} tickLine={false} tick={{fontSize: 12, fill: '#64748b'}} />
                            <YAxis axisLine={false} tickLine={false} tick={{fontSize: 12, fill: '#64748b'}} 
                              tickFormatter={(value) => `$${(value / 1e9).toFixed(0)}B`} />
                            <Tooltip 
                              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                              formatter={(value: number) => [formatLargeNumber(value), "Revenue"]}
                            />
                            <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
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
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis dataKey="period" axisLine={false} tickLine={false} tick={{fontSize: 12, fill: '#64748b'}} />
                            <YAxis axisLine={false} tickLine={false} tick={{fontSize: 12, fill: '#64748b'}}
                              tickFormatter={(value) => `$${(value / 1e9).toFixed(0)}B`} />
                            <Tooltip 
                              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                              formatter={(value: number) => [formatLargeNumber(value), "Net Income"]}
                            />
                            <Line type="monotone" dataKey="net_income" stroke="#10b981" strokeWidth={3} dot={{ r: 4, fill: '#10b981' }} activeDot={{ r: 6 }} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Technical Indicators Grid (RESTORED) */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-blue-600" />
                      <CardTitle>核心基本面（{data.fundamentals.quarter}）</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">营收</span>
                        <span className="font-semibold">{formatLargeNumber(data.fundamentals.revenue)}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">同比增长</span>
                        <span className={`font-semibold ${typeof data.fundamentals.revenue_yoy === 'number' && data.fundamentals.revenue_yoy >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {typeof data.fundamentals.revenue_yoy === 'number' ? `${data.fundamentals.revenue_yoy > 0 ? '+' : ''}${data.fundamentals.revenue_yoy}%` : data.fundamentals.revenue_yoy}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">毛利率</span>
                        <span className="font-semibold">{data.fundamentals.gross_margin}{typeof data.fundamentals.gross_margin === 'number' ? '%' : ''}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">净利率</span>
                        <span className="font-semibold">{data.fundamentals.net_margin}{typeof data.fundamentals.net_margin === 'number' ? '%' : ''}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">现金储备</span>
                        <span className="font-semibold">{formatLargeNumber(data.fundamentals.cash_reserves)}</span>
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
                        <span className={`font-semibold ${typeof data.technicals.rsi === 'number' && (data.technicals.rsi > 70 || data.technicals.rsi < 30) ? 'text-orange-600' : 'text-slate-900'}`}>
                          {data.technicals.rsi}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">MA (5)</span>
                        <span className="font-semibold">${data.technicals.ma_5}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">MA (60)</span>
                        <span className="font-semibold">${data.technicals.ma_60}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">OSC (20)</span>
                        <span className="font-semibold">{data.technicals.osc_20}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">CCI (14)</span>
                        <span className="font-semibold">{data.technicals.cci_14}</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Analyst Consensus Only */}
                <Card className="shadow-sm border-slate-200">
                  <CardHeader>
                    <CardTitle className="text-lg font-bold flex items-center gap-2">
                      <CheckCircle2 className="text-blue-600" />
                      分析师共识观察（仅供信息展示）
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-slate-500 mb-4">本页面不提供投资建议，仅展示分析师共识与客观指标。</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {data.checklists.map((item, idx) => (
                        <div key={idx} className={`p-4 rounded-xl border-2 transition-all ${item.triggered ? "border-emerald-100 bg-emerald-50/30" : "border-slate-100 bg-slate-50/30"}`}>
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-bold text-slate-900 text-sm">{item.name}</h4>
                            <Badge className={item.triggered ? "bg-emerald-500" : "bg-slate-400"}>
                              {item.status}
                            </Badge>
                          </div>
                          <p className="text-2xl font-black text-slate-900 mb-2">{item.value}</p>
                          <p className="text-xs text-slate-500 leading-relaxed">{item.description}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-sm border-slate-200">
                  <CardHeader>
                    <CardTitle className="text-lg font-bold">资金流入分析（实时）</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div className="p-4 rounded-xl bg-slate-50 border">
                        <p className="text-slate-500 mb-1">大盘资金流向</p>
                        <p className="font-semibold">实时接口接入中（预留）</p>
                      </div>
                      <div className="p-4 rounded-xl bg-slate-50 border">
                        <p className="text-slate-500 mb-1">特大盘资金流向</p>
                        <p className="font-semibold">实时接口接入中（预留）</p>
                      </div>
                      <div className="p-4 rounded-xl bg-slate-50 border">
                        <p className="text-slate-500 mb-1">小盘资金流向</p>
                        <p className="font-semibold">实时接口接入中（预留）</p>
                      </div>
                      <div className="p-4 rounded-xl bg-slate-50 border">
                        <p className="text-slate-500 mb-1">分类型资金流入</p>
                        <p className="font-semibold">实时接口接入中（预留）</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* News & Sentiment */}
                <Card className="shadow-sm border-slate-200">
                  <CardHeader>
                    <CardTitle className="text-lg font-bold flex items-center gap-2">
                      <Newspaper className="text-blue-600" />
                      最新资讯与情绪分析
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {data.news.map((item, idx) => (
                        <div key={idx} className="flex items-start gap-4 p-4 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-200 group">
                          <div className={`mt-1 p-2 rounded-lg ${
                            item.sentiment === 'Positive' ? 'bg-emerald-100 text-emerald-600' : 
                            item.sentiment === 'Negative' ? 'bg-rose-100 text-rose-600' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {item.sentiment === 'Positive' ? <TrendingUp size={20} /> : 
                             item.sentiment === 'Negative' ? <TrendingDown size={20} /> : <Minus size={20} />}
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between items-start mb-1">
                              <a href={item.link} target="_blank" rel="noopener noreferrer" className="font-bold text-slate-900 hover:text-blue-600 transition-colors line-clamp-1">
                                {item.title}
                              </a>
                              <ExternalLink size={14} className="text-slate-300 group-hover:text-blue-400" />
                            </div>
                            <div className="flex items-center gap-3 text-xs text-slate-500">
                              <span className="font-bold text-slate-700">{item.publisher}</span>
                              <span>•</span>
                              <span className="flex items-center gap-1"><Clock size={12} /> {item.provider_publish_time}</span>
                              <span>•</span>
                              <Badge variant="outline" className={`text-[10px] py-0 h-4 ${
                                item.sentiment === 'Positive' ? 'text-emerald-600 border-emerald-200' : 
                                item.sentiment === 'Negative' ? 'text-rose-600 border-rose-200' : 'text-slate-400 border-slate-200'
                              }`}>
                                {item.sentiment}
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

          {/* Sidebar - History & Compare (RESTORED) */}
          <div className="space-y-6">
            <Card className="shadow-sm border-slate-200">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Clock size={16} />
                  历史记录
                </CardTitle>
                {selectedForCompare.length === 2 && (
                  <Dialog open={isCompareOpen} onOpenChange={setIsCompareOpen}>
                    <DialogTrigger asChild>
                      <Button size="sm" variant="outline" className="h-7 text-xs gap-1">
                        <ArrowLeftRight size={12} /> Compare
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>股票对比</DialogTitle>
                      </DialogHeader>
                      <div className="grid grid-cols-2 gap-4 mt-4">
                        {getCompareItems().map((item) => (
                          <div key={item.id} className="space-y-4">
                            <div className="p-4 bg-slate-900 text-white rounded-xl">
                              <h3 className="text-2xl font-bold">{item.ticker}</h3>
                              <p className="text-slate-400 text-sm">${item.price.toFixed(2)}</p>
                            </div>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between border-b py-1">
                                <span className="text-slate-500">分析师共识</span>
                                <span className="font-bold">{item.data.consensus.recommendation}</span>
                              </div>
                              <div className="flex justify-between border-b py-1">
                                <span className="text-slate-500">目标价</span>
                                <span className="font-bold">${item.data.consensus.target_price}</span>
                              </div>
                              <div className="flex justify-between border-b py-1">
                                <span className="text-slate-500">上行空间</span>
                                <span className="font-bold">{item.data.consensus.upside_potential}%</span>
                              </div>
                              <div className="flex justify-between border-b py-1">
                                <span className="text-slate-500">市净率(PB)</span>
                                <span className="font-bold">{item.data.price.pb_ratio}</span>
                              </div>
                              <div className="flex justify-between border-b py-1">
                                <span className="text-slate-500">RSI (14)</span>
                                <span className="font-bold">{item.data.technicals.rsi}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </DialogContent>
                  </Dialog>
                )}
              </CardHeader>
              <CardContent className="px-2">
                <div className="space-y-1">
                  {history.length === 0 && (
                    <p className="text-xs text-slate-400 text-center py-4">暂无历史记录</p>
                  )}
                  {history.map((item) => (
                    <div
                      key={item.id}
                      className={`group relative flex items-center gap-2 p-2 rounded-lg transition-all hover:bg-slate-50 ${data?.ticker === item.ticker ? 'bg-blue-50/50' : ''}`}
                    >
                      <Checkbox 
                        checked={selectedForCompare.includes(item.id)}
                        onCheckedChange={() => toggleSelectForCompare(item.id)}
                        className="h-4 w-4"
                      />
                      <button
                        onClick={() => setData(item.data)}
                        className="flex-1 text-left"
                      >
                        <div className="font-bold text-slate-900 text-sm">{item.ticker}</div>
                        <div className="text-[10px] text-slate-400">{item.timestamp}</div>
                      </button>
                      <div className="text-right mr-6">
                        <div className="font-bold text-slate-700 text-xs">${item.price.toFixed(2)}</div>
                      </div>
                      <button 
                        onClick={() => deleteHistoryItem(item.id)}
                        className="absolute right-2 opacity-0 group-hover:opacity-100 p-1 hover:text-rose-500 transition-all"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="mt-12 py-8 border-t border-slate-200 text-center text-slate-400 text-xs">
        <p>© 2026 股票研究中心 v3.1 • 数据来源：Yahoo Finance 与 Google News</p>
      </footer>
    </div>
  );
}
