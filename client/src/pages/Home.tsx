import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, TrendingUp, ShieldAlert, BarChart3, Activity, Clock, X, CheckCircle2, AlertCircle, ShieldCheck } from "lucide-react";
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
    number_of_analysts: number | string;
    recommendation: string;
  };
  fundamentals: {
    revenue: number | string;
    gross_margin: number | string;
    net_margin: number | string;
    book_value: number | string;
    roe: number | string;
  };
  technicals: {
    rsi: number | string;
    macd: number | string;
    ma_5: number | string;
    ma_20: number | string;
    ma_60: number | string;
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
  id: string; // Unique ID for each search to allow duplicates
  ticker: string;
  timestamp: string;
  price: number;
  data: StockData; // Store full data for instant comparison
}

const HISTORY_STORAGE_KEY = "stock_research_history_v2";

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Load history from localStorage on mount
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

  // Save history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
  }, [history]);

  const getHKTTime = () => {
    return new Date().toLocaleString("en-US", { 
      timeZone: "Asia/Hong_Kong",
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric',
      hour12: true
    });
  };

  const addToHistory = (stockData: StockData) => {
    const newItem: HistoryItem = {
      id: Date.now().toString(),
      ticker: stockData.ticker,
      timestamp: getHKTTime(),
      price: stockData.price.current_price,
      data: stockData
    };

    // Keep duplicates for comparison, but limit total history
    setHistory([newItem, ...history].slice(0, 20));
  };

  const clearHistory = () => {
    setHistory([]);
    toast.success("History cleared");
  };

  const deleteHistoryItem = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setHistory(history.filter(item => item.id !== id));
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
      addToHistory(result);
      toast.success(`Successfully updated research for ${searchTicker.toUpperCase()}`);
    } catch (error) {
      console.error(error);
      toast.error("Error updating stock data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const onFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(ticker);
  };

  // Calculate Risk Control Line (Stop Loss) - e.g., 10% below current price
  const calculateStopLoss = (price: number) => {
    return (price * 0.9).toFixed(2);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header & Search */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white w-10 h-10 flex items-center justify-center rounded-lg font-bold text-xl">S</div>
            <h1 className="text-2xl font-bold text-slate-900">Stock Research Hub</h1>
          </div>

          <form onSubmit={onFormSubmit} className="flex w-full md:w-auto gap-2">
            <Input
              placeholder="Enter Stock Code (e.g. AAPL)"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              className="bg-white"
            />
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
              Update
            </Button>
          </form>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-3">
            {!data && !loading && (
              <div className="text-center py-20 bg-white rounded-2xl border-2 border-dashed border-slate-200">
                <BarChart3 className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                <h2 className="text-xl font-medium text-slate-600">Enter a stock ticker to start research</h2>
                <p className="text-slate-400">Real-time data from Yahoo Finance API (HKT Time)</p>
              </div>
            )}

            {data && (
              <div className="space-y-6 animate-in fade-in duration-500">
                {/* Summary Banner */}
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
                      <p className="text-blue-200 text-xs">Target: ${typeof data.consensus.target_price === 'number' ? data.consensus.target_price.toFixed(2) : data.consensus.target_price}</p>
                    </div>
                    <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                      <p className="text-blue-200 text-sm mb-1">Upside Potential</p>
                      <p className="text-xl font-bold">{typeof data.consensus.upside_potential === 'number' ? `${data.consensus.upside_potential > 0 ? '+' : ''}${data.consensus.upside_potential}%` : data.consensus.upside_potential}</p>
                      <p className="text-blue-200 text-xs">Relative to current</p>
                    </div>
                    <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                      <p className="text-blue-200 text-sm mb-1">Risk Control</p>
                      <p className="text-xl font-bold">${calculateStopLoss(data.price.current_price)}</p>
                      <p className="text-blue-200 text-xs">Final Defense Line</p>
                    </div>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-blue-600" />
                      <CardTitle>Key Fundamentals</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">Gross Margin</span>
                        <span className="font-semibold text-green-600">{data.fundamentals.gross_margin}{typeof data.fundamentals.gross_margin === 'number' ? '%' : ''}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">Net Margin</span>
                        <span className="font-semibold text-orange-600">{data.fundamentals.net_margin}{typeof data.fundamentals.net_margin === 'number' ? '%' : ''}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">ROE</span>
                        <span className="font-semibold">{data.fundamentals.roe}{typeof data.fundamentals.roe === 'number' ? '%' : ''}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Book Value</span>
                        <span className="font-semibold">{typeof data.fundamentals.book_value === 'number' ? `$${data.fundamentals.book_value}` : data.fundamentals.book_value}</span>
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
                        <span className="text-slate-500">RSI (14)</span>
                        <Badge className={typeof data.technicals.rsi === 'number' ? (data.technicals.rsi > 65 ? "bg-red-100 text-red-700" : data.technicals.rsi < 35 ? "bg-green-100 text-green-700" : "bg-blue-100 text-blue-700") : "bg-slate-100 text-slate-700"}>
                          {data.technicals.rsi} {typeof data.technicals.rsi === 'number' ? (data.technicals.rsi > 65 ? "Overbought" : data.technicals.rsi < 35 ? "Oversold" : "Neutral") : ""}
                        </Badge>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">MA (5)</span>
                        <span className="font-semibold">{typeof data.technicals.ma_5 === 'number' ? `$${data.technicals.ma_5}` : data.technicals.ma_5}</span>
                      </div>
                      <div className="flex justify-between border-b pb-2">
                        <span className="text-slate-500">MA (20)</span>
                        <span className="font-semibold">{typeof data.technicals.ma_20 === 'number' ? `$${data.technicals.ma_20}` : data.technicals.ma_20}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">MA (60)</span>
                        <span className="font-semibold">{typeof data.technicals.ma_60 === 'number' ? `$${data.technicals.ma_60}` : data.technicals.ma_60}</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Checklist Section */}
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

          {/* Sidebar / History */}
          <div className="lg:col-span-1">
            <Card className="sticky top-8">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-slate-400" />
                  <CardTitle className="text-lg">History (Comparison)</CardTitle>
                </div>
                {history.length > 0 && (
                  <Button variant="ghost" size="sm" onClick={clearHistory} className="text-xs text-slate-400 hover:text-red-500">
                    Clear All
                  </Button>
                )}
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <p className="text-sm text-slate-400 text-center py-4">No recent searches</p>
                ) : (
                  <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                    {history.map((item) => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setTicker(item.ticker);
                          setData(item.data); // Instant comparison
                          toast.info(`Viewing historical data for ${item.ticker}`);
                        }}
                        className={`w-full text-left p-3 rounded-xl border bg-white hover:border-blue-400 hover:shadow-sm transition-all group cursor-pointer relative ${data?.timestamp === item.data.timestamp ? 'border-blue-500 ring-1 ring-blue-500' : ''}`}
                      >
                        <button 
                          onClick={(e) => deleteHistoryItem(e, item.id)}
                          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-100 rounded-full transition-opacity"
                        >
                          <X className="h-3 w-3 text-slate-400" />
                        </button>
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-bold text-slate-900 group-hover:text-blue-600">{item.ticker}</span>
                          <span className="text-sm font-semibold">${item.price.toFixed(2)}</span>
                        </div>
                        <p className="text-[10px] text-slate-400">{item.timestamp}</p>
                      </div>
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
