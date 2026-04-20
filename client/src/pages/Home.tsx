import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, TrendingUp, ShieldAlert, BarChart3, Activity, Clock, X, CheckCircle2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

interface StockData {
  ticker: string;
  timestamp: string;
  updated_at: string;
  price: {
    current_price: number;
    change: number;
    change_percent: number;
    pb_ratio: number | string;
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
  };
  technicals: {
    rsi: number | string;
    ma_5: number | string;
    ma_60: number | string;
    osc_20: number | string;
    bias_24: number | string;
    cci_14: number | string;
  };
  checklists: {
    [key: string]: {
      name: string;
      value: number | string;
      triggered: boolean;
      status: string;
    };
  };
}

interface HistoryItem {
  id: string;
  ticker: string;
  timestamp: string;
  price: number;
  data: StockData;
}

const HISTORY_STORAGE_KEY = "stock_research_history_v3";

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

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

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white w-10 h-10 flex items-center justify-center rounded-lg font-bold text-xl">S</div>
            <h1 className="text-2xl font-bold text-slate-900">Stock Research Hub</h1>
          </div>
          <form onSubmit={(e) => { e.preventDefault(); handleSearch(ticker); }} className="flex w-full md:w-auto gap-2">
            <Input placeholder="Stock Code (e.g. TSLA)" value={ticker} onChange={(e) => setTicker(e.target.value)} className="bg-white" />
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
              Update
            </Button>
          </form>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            {!data && !loading && (
              <div className="text-center py-20 bg-white rounded-2xl border-2 border-dashed border-slate-200">
                <BarChart3 className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                <h2 className="text-xl font-medium text-slate-600">Enter a stock ticker to start research</h2>
              </div>
            )}

            {data && (
              <div className="space-y-6 animate-in fade-in duration-500">
                <div className="bg-blue-600 text-white rounded-2xl p-6 md:p-8 shadow-lg">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h2 className="text-3xl font-bold mb-1">{data.ticker} Insight</h2>
                      <p className="text-blue-100 opacity-80">Last Updated: {data.updated_at} (HKT)</p>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold">${data.price.current_price.toFixed(3)}</div>
                      <Badge variant="secondary" className={data.price.change >= 0 ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}>
                        {data.price.change >= 0 ? "+" : ""}{data.price.change_percent}%
                      </Badge>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                      <p className="text-blue-200 text-sm mb-1">Analyst Consensus</p>
                      <p className="text-xl font-bold">{data.consensus.recommendation}</p>
                      <p className="text-blue-200 text-xs">Target: ${data.consensus.target_price}</p>
                    </div>
                    <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                      <p className="text-blue-200 text-sm mb-1">Upside Potential</p>
                      <p className="text-xl font-bold">{typeof data.consensus.upside_potential === 'number' ? `${data.consensus.upside_potential > 0 ? '+' : ''}${data.consensus.upside_potential}%` : data.consensus.upside_potential}</p>
                    </div>
                    <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                      <p className="text-blue-200 text-sm mb-1">Risk Control</p>
                      <p className="text-xl font-bold">${(data.price.current_price * 0.9).toFixed(2)}</p>
                      <p className="text-blue-200 text-xs">Final Defense Line</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-blue-600" />
                      <CardTitle>Key Fundamentals ({data.fundamentals.quarter})</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">Revenue</span>
                        <span className="font-semibold">{formatLargeNumber(data.fundamentals.revenue)}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">YoY Growth</span>
                        <span className={`font-semibold ${typeof data.fundamentals.revenue_yoy === 'number' && data.fundamentals.revenue_yoy >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {typeof data.fundamentals.revenue_yoy === 'number' ? `${data.fundamentals.revenue_yoy > 0 ? '+' : ''}${data.fundamentals.revenue_yoy}%` : data.fundamentals.revenue_yoy}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">Gross Margin</span>
                        <span className="font-semibold">{data.fundamentals.gross_margin}{typeof data.fundamentals.gross_margin === 'number' ? '%' : ''}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">Net Margin</span>
                        <span className="font-semibold">{data.fundamentals.net_margin}{typeof data.fundamentals.net_margin === 'number' ? '%' : ''}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Cash Reserves</span>
                        <span className="font-semibold">{formatLargeNumber(data.fundamentals.cash_reserves)}</span>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center gap-2">
                      <Activity className="h-5 w-5 text-blue-600" />
                      <CardTitle>Technical Indicators</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">OSC_20</span>
                        <span className="font-semibold">{data.technicals.osc_20}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">BIAS_24</span>
                        <span className={`font-semibold ${typeof data.technicals.bias_24 === 'number' && data.technicals.bias_24 >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {data.technicals.bias_24}{typeof data.technicals.bias_24 === 'number' ? '%' : ''}
                        </span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">CCI_14</span>
                        <span className="font-semibold">{data.technicals.cci_14}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">MA (5)</span>
                        <span className="font-semibold">${data.technicals.ma_5}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">MA (60)</span>
                        <span className="font-semibold">${data.technicals.ma_60}</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader className="flex flex-row items-center gap-2">
                    <ShieldAlert className="h-5 w-5 text-blue-600" />
                    <CardTitle>Research Checklist Monitoring</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(data.checklists).map(([key, list]) => (
                        <div key={key} className={`p-4 rounded-xl border ${list.triggered ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'}`}>
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-bold text-slate-900">{list.name}</span>
                            {list.triggered ? <AlertCircle className="h-5 w-5 text-amber-600" /> : <CheckCircle2 className="h-5 w-5 text-green-600" />}
                          </div>
                          <div className="flex items-baseline gap-2">
                            <span className="text-2xl font-bold">{list.value}</span>
                            <Badge variant={list.triggered ? "destructive" : "outline"}>{list.status}</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          <div className="lg:col-span-1">
            <Card className="sticky top-8">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-slate-400" />
                  <CardTitle className="text-lg">History</CardTitle>
                </div>
                {history.length > 0 && <Button variant="ghost" size="sm" onClick={() => setHistory([])} className="text-xs text-slate-400 hover:text-red-500">Clear</Button>}
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                  {history.map((item) => (
                    <div key={item.id} onClick={() => setData(item.data)} className={`p-3 rounded-xl border bg-white hover:border-blue-400 transition-all cursor-pointer ${data?.timestamp === item.data.timestamp ? 'border-blue-500 ring-1 ring-blue-500' : ''}`}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-slate-900">{item.ticker}</span>
                        <span className="text-sm font-semibold">${item.price.toFixed(2)}</span>
                      </div>
                      <p className="text-[10px] text-slate-400">{item.timestamp}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
