# 📊 Stock Research Hub - 自动化研究系统

一个智能股票分析平台，可以自动进行深度调研并生成动态更新的分析报告。

## 🎯 核心特性

✅ **自动深度调研** - 实时抓取股票数据、财务数据、技术指标
✅ **AI 驱动分析** - 自动生成投资决策和交易策略
✅ **动态网页生成** - 根据最新数据自动更新网页内容
✅ **本地存储** - 所有代码和数据存储在您的项目中
✅ **一键更新** - 运行一个命令就能重新生成最新的分析报告

## 📁 项目结构

```
stock_research_hub/
├── research_engine.py          # 深度调研脚本（抓取数据）
├── generate_html.py            # HTML 生成脚本（渲染网页）
├── update.sh                   # 自动化脚本（一键更新）
├── research_data_FIGR.json     # 研究数据（自动生成）
├── index.html                  # 生成的网页（自动生成）
└── RESEARCH_SYSTEM.md          # 本文档
```

## 🚀 快速开始

### 1️⃣ 初次运行（生成初始报告）

```bash
# 进入项目目录
cd /home/ubuntu/stock_research_hub

# 给脚本执行权限
chmod +x update.sh

# 运行自动更新（默认分析 FIGR）
./update.sh
```

**输出示例：**
```
🚀 Stock Research Hub - 自动更新
==================================

📊 开始调研 FIGR...
🔍 开始调研 FIGR...
✅ 调研完成！当前股价: $34.542
💾 数据已保存到 research_data_FIGR.json

🔨 正在生成网页...
✅ HTML 已生成: index.html
📊 数据来源: research_data_FIGR.json
🕐 生成时间: 2026-04-16 15:30:45

✨ 完成！
==================================
📄 网页已生成: index.html
📊 数据已保存: research_data_FIGR.json
```

### 2️⃣ 查看生成的报告

```bash
# 在浏览器中打开生成的 HTML 文件
open index.html  # macOS
# 或
xdg-open index.html  # Linux
# 或
start index.html  # Windows
```

### 3️⃣ 更新报告（获取最新数据）

```bash
# 重新运行脚本，获取最新数据并重新生成网页
./update.sh FIGR

# 或分析其他股票
./update.sh AAPL
./update.sh TSLA
```

## 📊 工作流程

```
┌─────────────────────────────────────┐
│   1. 运行 update.sh FIGR             │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   2. research_engine.py 运行         │
│      - 抓取股票价格                  │
│      - 获取财务数据                  │
│      - 计算技术指标                  │
│      - 生成交易策略                  │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   3. 保存数据到 JSON 文件             │
│      research_data_FIGR.json         │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   4. generate_html.py 运行          │
│      - 读取 JSON 数据                │
│      - 生成 HTML 网页                │
│      - 应用 Tailwind 样式            │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   5. 输出 index.html                 │
│      - 在浏览器中打开                │
│      - 分享给他人                    │
└─────────────────────────────────────┘
```

## 🔧 自定义配置

### 修改分析的股票

编辑 `research_engine.py`，修改 `__init__` 方法中的默认 ticker：

```python
def __init__(self, ticker: str = "AAPL"):  # 改为 AAPL
    self.ticker = ticker
    ...
```

### 添加新的数据源

在 `research_engine.py` 中添加新的方法：

```python
def fetch_news_sentiment(self) -> Dict[str, Any]:
    """获取新闻情绪分析"""
    # 您的代码
    return sentiment_data
```

然后在 `run_research()` 中调用：

```python
def run_research(self) -> Dict[str, Any]:
    # ... 现有代码 ...
    sentiment = self.fetch_news_sentiment()  # 添加这行
    self.data["sentiment"] = sentiment
    # ... 现有代码 ...
```

### 修改网页样式

编辑 `generate_html.py` 中的 `generate_html()` 函数，修改 HTML 和 CSS：

```python
def generate_html(data: dict) -> str:
    """生成完整的 HTML 页面"""
    html = f"""<!DOCTYPE html>
    <!-- 修改这里的 HTML 结构和样式 -->
    """
```

## 📈 数据结构

### research_data_FIGR.json

```json
{
  "ticker": "FIGR",
  "timestamp": "2026-04-16T15:30:45.123456",
  "price": {
    "current_price": 34.542,
    "change": -0.458,
    "change_percent": -1.31
  },
  "fundamentals": {
    "q4_revenue": 160000000,
    "yoy_growth": 90.7,
    "gross_margin": 93,
    "net_margin": 9.4,
    "cash_reserve": 1200000000
  },
  "technicals": {
    "osc_20": { "value": 85, "status": "严重超买" },
    "bias_24": { "value": 72, "status": "超买" },
    "cci_14": { "value": 68, "status": "超买" },
    "ma_5": 36.30,
    "ma_60": 44.92
  },
  "consensus": {
    "total_analysts": 22,
    "buy_percent": 100,
    "target_price": 56.89,
    "upside_potential": 65
  },
  "strategy": {
    "stage_1": {
      "triggered": true,
      "price_range": "34.42 - 35.6",
      "status": "已触发"
    },
    "stage_2": {
      "triggered": false,
      "price_range": "37.6 - 38.0",
      "status": "监控中"
    },
    "stage_3": {
      "triggered": false,
      "price_range": "39.5 - 40.0",
      "status": "目标中"
    }
  }
}
```

## 🔄 自动化定时更新（可选）

### macOS/Linux - 使用 Cron

编辑 crontab：
```bash
crontab -e
```

添加定时任务（每天上午 9 点更新）：
```bash
0 9 * * * cd /home/ubuntu/stock_research_hub && ./update.sh FIGR
```

### Windows - 使用任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器（每天 9:00 AM）
4. 设置操作：运行 `update.sh`

## 💡 使用场景

### 场景 1：每日晨报

```bash
# 每天早上 9 点自动运行
0 9 * * * cd /home/ubuntu/stock_research_hub && ./update.sh FIGR && open index.html
```

### 场景 2：多股票监控

```bash
# 同时监控多个股票
./update.sh FIGR
./update.sh AAPL
./update.sh TSLA
```

### 场景 3：与 GitHub 同步

```bash
# 更新后自动提交到 GitHub
./update.sh FIGR
git add research_data_FIGR.json index.html
git commit -m "Auto-update: $(date)"
git push
```

## 🐛 故障排除

### 问题：脚本无法执行

```bash
# 解决：给脚本添加执行权限
chmod +x update.sh
```

### 问题：Python 找不到

```bash
# 解决：使用完整路径
/usr/bin/python3 research_engine.py
```

### 问题：JSON 文件找不到

```bash
# 解决：确保在正确的目录
cd /home/ubuntu/stock_research_hub
python3 research_engine.py
```

## 📚 进阶用法

### 集成到 Web 应用

```python
# 在 Flask/Django 中使用
from research_engine import StockResearchEngine
from generate_html import generate_html, load_research_data

@app.route('/update/<ticker>')
def update_research(ticker):
    engine = StockResearchEngine(ticker)
    data = engine.run_research()
    engine.save_to_json(f"research_data_{ticker}.json")
    return {"status": "success", "data": data}
```

### 连接真实 API

修改 `research_engine.py` 中的 `fetch_*` 方法，连接真实的数据源：

```python
def fetch_stock_price(self) -> Dict[str, Any]:
    """获取实时股票价格"""
    import yfinance as yf
    data = yf.Ticker(self.ticker)
    return {
        "current_price": data.info['currentPrice'],
        "change": data.info['regularMarketChange'],
        # ...
    }
```

## 📞 支持

有问题？

1. 检查 `RESEARCH_SYSTEM.md` 中的故障排除部分
2. 查看脚本的错误信息
3. 检查 JSON 数据格式是否正确

## 📄 许可证

MIT License

---

**最后更新：** 2026-04-16
**版本：** 1.0.0
