#!/usr/bin/env python3
"""
HTML Generator
根据 JSON 研究数据动态生成 HTML 网页
"""

import json
from datetime import datetime
from pathlib import Path


def load_research_data(filepath: str = "research_data_FIGR.json") -> dict:
    """加载研究数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found, using default data")
        return get_default_data()


def get_default_data() -> dict:
    """获取默认数据（当没有研究数据时）"""
    return {
        "ticker": "FIGR",
        "timestamp": datetime.now().isoformat(),
        "price": {
            "current_price": 34.542,
            "change": -0.458,
            "change_percent": -1.31
        },
        "consensus": {
            "total_analysts": 22,
            "buy_percent": 100,
            "target_price": 56.89,
            "upside_potential": 65
        },
        "fundamentals": {
            "q4_revenue": 160000000,
            "yoy_growth": 90.7,
            "gross_margin": 93,
            "net_margin": 9.4,
            "cash_reserve": 1200000000
        },
        "technicals": {
            "osc_20": {"value": 85, "status": "严重超买"},
            "bias_24": {"value": 72, "status": "超买"},
            "cci_14": {"value": 68, "status": "超买"},
            "ma_5": 36.30,
            "ma_60": 44.92
        },
        "strategy": {
            "stage_1": {"triggered": True, "status": "已触发", "price_range": "34.42 - 35.6"},
            "stage_2": {"triggered": False, "status": "监控中", "price_range": "37.6 - 38.0"},
            "stage_3": {"triggered": False, "status": "目标中", "price_range": "39.5 - 40.0"}
        }
    }


def format_currency(value: float) -> str:
    """格式化货币"""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    else:
        return f"${value:.2f}"


def get_stage_badge_color(status: str) -> tuple:
    """根据状态返回徽章颜色"""
    if "已触发" in status:
        return ("badge-red", "red")
    elif "监控中" in status:
        return ("badge-orange", "orange")
    else:
        return ("badge-green", "green")


def generate_html(data: dict) -> str:
    """生成完整的 HTML 页面"""
    
    price = data.get("price", {})
    consensus = data.get("consensus", {})
    fundamentals = data.get("fundamentals", {})
    technicals = data.get("technicals", {})
    strategy = data.get("strategy", {})
    ticker = data.get("ticker", "FIGR")
    
    current_price = price.get("current_price", 0)
    stage_1_badge, stage_1_color = get_stage_badge_color(strategy.get("stage_1", {}).get("status", ""))
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ticker} Stock Analysis - Auto Generated</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #f8fafc; }}
        .card {{ background: white; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); padding: 1.5rem; margin-bottom: 1.5rem; }}
        .badge {{ padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; }}
        .badge-red {{ background-color: #fee2e2; color: #991b1b; }}
        .badge-orange {{ background-color: #ffedd5; color: #9a3412; }}
        .badge-green {{ background-color: #dcfce7; color: #166534; }}
        .auto-generated {{ background: #f0f9ff; border-left: 4px solid #0284c7; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem; font-size: 0.875rem; color: #0c4a6e; }}
    </style>
</head>
<body class="p-4 md:p-8 max-w-5xl mx-auto">

    <!-- Auto-Generated Notice -->
    <div class="auto-generated">
        <strong>⚡ 自动生成报告</strong> - 最后更新: {datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M:%S')}
        <br/>此报告由 AI 自动调研和生成。运行 <code style="background: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">python3 research_engine.py</code> 来更新数据。
    </div>

    <!-- Header -->
    <div class="flex justify-between items-start mb-8">
        <div>
            <div class="flex items-center gap-2 mb-1">
                <div class="bg-blue-600 text-white w-8 h-8 flex items-center justify-center rounded font-bold">F</div>
                <h1 class="text-xl font-bold text-slate-900">{ticker} 洞察</h1>
            </div>
            <p class="text-slate-500 text-sm">Figure Technology Solutions</p>
        </div>
        <div class="text-right">
            <div class="text-2xl font-bold text-slate-900">${current_price:.3f}</div>
            <p class="text-slate-500 text-xs mb-2">当前股价（美股盘后）</p>
            <span class="badge {stage_1_badge}">{strategy.get('stage_1', {}).get('status', '未知')}</span>
        </div>
    </div>

    <!-- Summary Card -->
    <div class="bg-blue-600 text-white rounded-2xl p-8 mb-8 shadow-xl">
        <h2 class="text-2xl font-bold mb-4">投资决策摘要</h2>
        <p class="text-blue-100 mb-8 leading-relaxed">
            {ticker}.US 是一家处于扩张期但盈利有波动的金融科技公司。当前股价已触发您策略的首个卖出点，应果断执行。后续上涨之路面临技术性调整和主力抛压，实现更高卖出目标需要耐心和基本面的进一步验证。
        </p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                <p class="text-blue-200 text-sm mb-1">分析师共识</p>
                <p class="text-xl font-bold">{consensus.get('total_analysts', 0)}位 {consensus.get('buy_percent', 0)}%买入</p>
                <p class="text-blue-200 text-xs">平均目标价 ${consensus.get('target_price', 0):.2f}</p>
            </div>
            <div class="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                <p class="text-blue-200 text-sm mb-1">上升空间</p>
                <p class="text-xl font-bold">+{consensus.get('upside_potential', 0)}%</p>
                <p class="text-blue-200 text-xs">相对当前价格</p>
            </div>
            <div class="bg-white/10 p-4 rounded-xl backdrop-blur-sm">
                <p class="text-blue-200 text-sm mb-1">风控线</p>
                <p class="text-xl font-bold">${strategy.get('risk_control', {}).get('stop_loss', 0):.2f}</p>
                <p class="text-blue-200 text-xs">最终防线</p>
            </div>
        </div>
    </div>

    <h2 class="text-2xl font-bold text-slate-900 mb-6 border-l-4 border-blue-600 pl-4">一、概览</h2>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <!-- Key Metrics -->
        <div class="card">
            <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                <span class="text-blue-600">◎</span> 关键指标
            </h3>
            <div class="space-y-3">
                <div class="flex justify-between border-b pb-2">
                    <span class="text-slate-500">Q4收入</span>
                    <span class="font-semibold">{format_currency(fundamentals.get('q4_revenue', 0))}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                    <span class="text-slate-500">同比增长</span>
                    <span class="font-semibold text-green-600">+{fundamentals.get('yoy_growth', 0):.1f}%</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                    <span class="text-slate-500">毛利率</span>
                    <span class="font-semibold">{fundamentals.get('gross_margin', 0):.0f}%+</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                    <span class="text-slate-500">Q4净利率</span>
                    <span class="font-semibold text-red-500">{fundamentals.get('net_margin', 0):.1f}%</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">现金储备</span>
                    <span class="font-semibold">{format_currency(fundamentals.get('cash_reserve', 0))}</span>
                </div>
            </div>
        </div>

        <!-- Technical Indicators -->
        <div class="card">
            <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                <span class="text-blue-600">⚡</span> 技术指标
            </h3>
            <div class="space-y-3">
                <div class="flex justify-between border-b pb-2">
                    <span class="text-slate-500">OSC_20</span>
                    <span class="badge badge-red">{technicals.get('osc_20', {}).get('value', 0)} {technicals.get('osc_20', {}).get('status', '')}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                    <span class="text-slate-500">BIAS_24</span>
                    <span class="badge badge-orange">{technicals.get('bias_24', {}).get('value', 0)} {technicals.get('bias_24', {}).get('status', '')}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                    <span class="text-slate-500">CCI_14</span>
                    <span class="badge badge-orange">{technicals.get('cci_14', {}).get('value', 0)} {technicals.get('cci_14', {}).get('status', '')}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                    <span class="text-slate-500">5日均线</span>
                    <span class="font-semibold">${technicals.get('ma_5', 0):.2f}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-500">60日均线</span>
                    <span class="font-semibold">${technicals.get('ma_60', 0):.2f}</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Strategy -->
    <div class="card">
        <h3 class="text-lg font-bold mb-6 flex items-center gap-2">
            <span class="text-blue-600">✓</span> 三阶段卖出策略
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="p-4 rounded-xl border-2 border-red-100 bg-red-50">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-red-900">第一阶段</span>
                    <span class="badge badge-red">{strategy.get('stage_1', {}).get('status', '')}</span>
                </div>
                <p class="text-sm text-red-800 mb-1">价格范围: {strategy.get('stage_1', {}).get('price_range', '')}</p>
                <p class="text-sm text-red-800 mb-1">卖出数量: {strategy.get('stage_1', {}).get('quantity', '')}</p>
                <p class="text-sm font-semibold text-red-900">目标: {strategy.get('stage_1', {}).get('target', '')}</p>
            </div>
            <div class="p-4 rounded-xl border-2 border-orange-100 bg-orange-50">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-orange-900">第二阶段</span>
                    <span class="badge badge-orange">{strategy.get('stage_2', {}).get('status', '')}</span>
                </div>
                <p class="text-sm text-orange-800 mb-1">价格范围: {strategy.get('stage_2', {}).get('price_range', '')}</p>
                <p class="text-sm text-orange-800 mb-1">卖出数量: {strategy.get('stage_2', {}).get('quantity', '')}</p>
                <p class="text-sm font-semibold text-orange-900">目标: {strategy.get('stage_2', {}).get('target', '')}</p>
            </div>
            <div class="p-4 rounded-xl border-2 border-green-100 bg-green-50">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-green-900">第三阶段</span>
                    <span class="badge badge-green">{strategy.get('stage_3', {}).get('status', '')}</span>
                </div>
                <p class="text-sm text-green-800 mb-1">价格范围: {strategy.get('stage_3', {}).get('price_range', '')}</p>
                <p class="text-sm text-green-800 mb-1">卖出数量: {strategy.get('stage_3', {}).get('quantity', '')}</p>
                <p class="text-sm font-semibold text-green-900">目标: {strategy.get('stage_3', {}).get('target', '')}</p>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="text-center text-slate-400 text-xs mt-12 pb-8">
        Stock Research Hub • Auto-Generated Report • Powered by AI Research Engine
    </div>

</body>
</html>"""
    
    return html


def main():
    """主函数"""
    # 加载数据
    data = load_research_data()
    
    # 生成 HTML
    html_content = generate_html(data)
    
    # 保存到文件
    output_path = "index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML 已生成: {output_path}")
    print(f"📊 数据来源: research_data_{data.get('ticker', 'FIGR')}.json")
    print(f"🕐 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
