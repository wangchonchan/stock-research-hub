# 📊 Stock Research Hub

Stock Research Hub 是一个基于 AI 的自动化股票调研工具。它能够自动从 Yahoo Finance 获取实时数据，进行深度技术面和基本面分析，并生成精美的可视化研究报告。

## ✨ 核心功能

- **自动化调研**：集成 Yahoo Finance API，一键获取股价、财务指标、技术指标及分析师共识。
- **Web 交互界面**：无需记忆复杂的终端命令，通过浏览器即可输入股票代码并触发更新。
- **可视化报告**：自动生成基于 Tailwind CSS 的响应式 HTML 报告，提供直观的投资决策支持。
- **三阶段策略**：内置科学的仓位管理建议，帮助投资者执行卖出和风控计划。

## 🚀 快速开始

### 1. 安装依赖
确保您的系统中已安装 Python 3.11+，然后运行：
```bash
pip install -r requirements.txt
```

### 2. 启动 Web 控制面板
运行以下命令启动交互式界面：
```bash
python app.py
```
启动后，在浏览器中访问 `http://localhost:5000` 即可使用。

### 3. 命令行使用 (可选)
如果您更喜欢使用终端，也可以直接运行更新脚本：
```bash
./update.sh [TICKER]
```
例如：`./update.sh AAPL`

## 📂 项目结构

- `app.py`: Flask Web 应用程序，提供图形化操作界面。
- `research_engine.py`: 核心调研引擎，负责数据抓取与逻辑分析。
- `generate_html.py`: 报告生成器，将 JSON 数据转换为可视化 HTML。
- `update.sh`: 自动化流水线脚本。
- `index.html`: 最新生成的调研报告页面。

## 🛠️ 技术栈

- **后端**: Python, Flask
- **数据源**: Yahoo Finance (yfinance)
- **前端**: Tailwind CSS, HTML5
- **分析**: NumPy, Pandas

---
*免责声明：本工具生成的报告仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。*
