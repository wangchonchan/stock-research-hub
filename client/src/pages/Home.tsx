import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, TrendingUp, ShieldAlert, BarChart3, Activity } from "lucide-react";
import { toast } from "sonner";

interface StockData {
  ticker: string;
  timestamp: string;
  price: {
    current_price: number;
    change: number;
    change_percent: number;
  };
  consensus: {
    target_price: number;
    upside_potential: number;
    number_of_analysts: number;
  };
  fundamentals: {
    revenue: number;
    gross_margin: number;
    net_margin: number;
    book_value: number;
    roe: number;
  };
  technicals: {
    rsi: number;
    macd: number;
    ma_5: number;
    ma_20: number;
    ma_60: number;
  };
  strategy: {
    stage_1: { status: string; price_range: string; quantity: string; target: string };
    stage_2: { status: string; price_range: string; quantity: string; target: string };
    stage_3: { status: string; price_range: string; quantity: string; target: string };
    risk_control: { stop_loss: number };
  };
}

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockData | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker) return;

    setLoading(true);
    try {
      const response = await fetch("/api/stock-research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker }),
      });

      if (!response.ok) throw new Error("Failed to fetch data");

      const result = await response.json();
      setData(result);
      toast.success(`Successfully updated research for ${ticker.toUpperCase()}`);
    } catch (error) {
      console.error(error);
      toast.error("Error updating stock data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header & Search */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white w-10 h-10 flex items-center justify-center rounded-lg font-bold text-xl">S</div>
            <h1 className="text-2xl font-bold text-slate-900">Stock Research Hub</h1>
          </div>
          
          <form onSubmit={handleSearch} className="flex w-full md:w-auto gap-2">
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

        {!data && !loading && (
          <div className="text-center py-20 bg-white rounded-2xl border-2 border-dashed border-slate-200">
            <BarChart3 className="mx-auto h-12 w-12 text-slate-300 mb-4" />
            <h2 className="text-xl font-medium text-slate-600">Enter a stock ticker to start research</h2>
            <p className="text-slate-400">Real-time data from Yahoo Finance API</p>
          </div>
        )}

        {data && (
          <div className="space-y-6 animate-in fade-in duration-500">
            {/* Summary Banner */}
            <div className="bg-blue-600 text-white rounded-2xl p-6 md:p-8 shadow-lg">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-3xl font-bold mb-1">{data.ticker} Insight</h2>
                  <p className="text-blue-100 opacity-80">Last Updated: {new Date(data.timestamp).toLocaleString()}</p>
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
                  <p className="text-xl font-bold">{data.consensus.number_of_analysts} Analysts Buy</p>
                  <p className="text-blue-200 text-xs">Target: ${data.consensus.target_price.toFixed(2)}</p>
                </div>
                <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                  <p className="text-blue-200 text-sm mb-1">Upside Potential</p>
                  <p className="text-xl font-bold">+{data.consensus.upside_potential}%</p>
                  <p className="text-blue-200 text-xs">Relative to current</p>
                </div>
                <div className="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                  <p className="text-blue-200 text-sm mb-1">Risk Control</p>
                  <p className="text-xl font-bold">${data.strategy.risk_control.stop_loss.toFixed(2)}</p>
                  <p className="text-blue-200 text-xs">Stop Loss Line</p>
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
                    <span className="font-semibold text-green-600">{data.fundamentals.gross_margin}%</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Net Margin</span>
                    <span className="font-semibold text-orange-600">{data.fundamentals.net_margin}%</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">ROE</span>
                    <span className="font-semibold">{data.fundamentals.roe}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Book Value</span>
                    <span className="font-semibold">${data.fundamentals.book_value}</span>
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
                    <Badge className={data.technicals.rsi > 70 ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"}>
                      {data.technicals.rsi} {data.technicals.rsi > 70 ? "Overbought" : "Neutral"}
                    </Badge>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">MA (5)</span>
                    <span className="font-semibold">${data.technicals.ma_5}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">MA (20)</span>
                    <span className="font-semibold">${data.technicals.ma_20}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">MA (60)</span>
                    <span className="font-semibold">${data.technicals.ma_60}</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Strategy Section */}
            <Card>
              <CardHeader className="flex flex-row items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-blue-600" />
                <CardTitle>3-Stage Exit Strategy</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[data.strategy.stage_1, data.strategy.stage_2, data.strategy.stage_3].map((stage, i) => (
                    <div key={i} className="p-4 rounded-xl border bg-slate-50">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-slate-900">Stage {i + 1}</span>
                        <Badge variant="outline">{stage.status}</Badge>
                      </div>
                      <p className="text-sm text-slate-600 mb-1">Range: {stage.price_range}</p>
                      <p className="text-sm text-slate-600 mb-1">Qty: {stage.quantity}</p>
                      <p className="text-sm font-semibold text-blue-700">Target: {stage.target}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
