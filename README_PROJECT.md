# 🚀 Stock Research Hub

**一个智能股票分析平台，可以自动进行深度调研并生成动态更新的分析报告。**

## 💡 核心理念

传统的股票分析报告是**静态的、过时的**。而这个项目实现了**动态的、实时更新的**自动化研究系统：

- ✅ **自动调研** - 一键启动深度调研流程
- ✅ **真实 API** - 集成 Yahoo Finance 免费 API，获取实时股票数据
- ✅ **动态生成** - 根据最新数据自动生成网页
- ✅ **本地存储** - 所有代码和数据在您的电脑/GitHub 上
- ✅ **可扩展** - 轻松添加新的数据源和分析逻辑

## 🎯 快速开始

### 1. 安装依赖

```bash
cd /home/ubuntu/stock_research_hub
pip3 install -r requirements.txt
```

### 2. 生成初始报告

```bash
python3 research_engine.py FIGR
python3 generate_html.py
```

### 3. 查看报告

在浏览器中打开 `index.html` 文件。

### 4. 更新报告（获取最新数据）

```bash
./update.sh FIGR
```

## 📊 工作流程

```
调研脚本 (research_engine.py)
    ↓
    通过 Yahoo Finance API 抓取实时数据
    ↓
    保存为 JSON (research_data_FIGR.json)
    ↓
生成脚本 (generate_html.py)
    ↓
    读取 JSON → 生成 HTML
    ↓
网页 (index.html)
    ↓
在浏览器中查看
```

## 📁 项目文件

| 文件 | 说明 |
|------|------|
| `research_engine.py` | 深度调研脚本，集成 Yahoo Finance API |
| `generate_html.py` | HTML 生成脚本，根据数据生成网页 |
| `update.sh` | 自动化脚本，一键执行调研和生成 |
| `research_data_FIGR.json` | 调研数据（自动生成） |
| `index.html` | 生成的网页（自动生成） |
| `requirements.txt` | Python 依赖 |
| `RESEARCH_SYSTEM.md` | 详细文档 |

## 🔌 API 说明

### Yahoo Finance API（免费）

本项目使用 **yfinance** 库连接 Yahoo Finance API，完全免费，无需 API Key。

**支持的数据：**
- ✅ 实时股票价格
- ✅ 历史价格数据
- ✅ 财务指标（收入、利润率、ROE 等）
- ✅ 技术指标（移动平均线、RSI、MACD 等）
- ✅ 分析师目标价
- ✅ 市值、PE 比率等

**优势：**
- 完全免费，无请求限制
- 无需注册或 API Key
- 数据准确、实时更新
- 支持所有美股和全球股票

## 🚀 使用示例

### 分析单个股票

```bash
./update.sh FIGR
./update.sh AAPL
./update.sh TSLA
```

### 分析多个股票

```bash
./update.sh FIGR
./update.sh AAPL
./update.sh MSFT
```

### 定时自动更新（Linux/macOS）

编辑 crontab：
```bash
crontab -e
```

添加定时任务（每天上午 9 点更新）：
```bash
0 9 * * * cd /home/ubuntu/stock_research_hub && ./update.sh FIGR
```

## 🔧 自定义

### 修改分析的股票

```bash
./update.sh AAPL
```

### 修改网页样式

编辑 `generate_html.py` 中的 HTML 和 CSS。

### 添加新的数据源

编辑 `research_engine.py`，添加新的方法（例如 `fetch_news_sentiment()`）。

## 📊 生成的数据结构

### research_data_FIGR.json

```json
{
  "ticker": "FIGR",
  "timestamp": "2026-04-16T03:14:49.123456",
  "price": {
    "current_price": 35.62,
    "change": 0.08,
    "change_percent": 0.22,
    "high_52w": 42.27,
    "low_52w": 15.20,
    "market_cap": "2.5B",
    "pe_ratio": 45.2,
    "volume": "5.2M"
  },
  "fundamentals": {
    "revenue": 507000000,
    "gross_margin": 93,
    "net_margin": 9.4,
    "roe": 18.5,
    "book_value": 12.5
  },
  "technicals": {
    "ma_5": 36.30,
    "ma_20": 32.79,
    "ma_60": 44.92,
    "rsi": 68,
    "macd": 0.85
  },
  "consensus": {
    "target_price": 53.38,
    "upside_potential": 49.8,
    "number_of_analysts": 22
  },
  "strategy": {
    "stage_1": {
      "triggered": true,
      "price_range": "34.42 - 35.6",
      "status": "已触发"
    }
  }
}
```

## 💻 系统要求

- Python 3.7+
- Bash（macOS/Linux）或 PowerShell（Windows）
- 网络连接（用于 API 调用）

## 🐛 故障排除

### 问题：yfinance 无法安装

```bash
# 解决：使用 sudo
sudo pip3 install yfinance
```

### 问题：无法获取股票数据

```bash
# 解决：检查股票代码是否正确
# 确保网络连接正常
# 尝试使用其他股票代码测试
./update.sh AAPL
```

### 问题：脚本无法执行

```bash
# 解决：给脚本添加执行权限
chmod +x update.sh
```

## 📞 支持

有问题？查看 `RESEARCH_SYSTEM.md` 中的详细文档。

## 🎓 学习资源

- [yfinance 文档](https://github.com/ranaroussi/yfinance)
- [Yahoo Finance](https://finance.yahoo.com)
- [Python 官方文档](https://docs.python.org/3/)

---

**版本：** 1.0.0  
**最后更新：** 2026-04-16  
**作者：** Manus AI

**GitHub：** https://github.com/wangchonchan/stock-research-hub
