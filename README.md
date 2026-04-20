# 📊 Stock Research Hub (React Web Edition)

Stock Research Hub 现在是一个全功能的 React Web 应用程序。它将复杂的 Python 调研逻辑集成到了现代化的 Web 界面中，让您只需在浏览器中输入股票代码并点击按钮，即可完成深度调研。

## ✨ 核心功能

- **一键式 Web 交互**：在网页输入框输入股票代码（如 AAPL, TSLA），点击按钮即可触发实时调研。
- **实时数据集成**：后端自动调用 Python 调研引擎，通过 Yahoo Finance API 获取最新数据。
- **现代化 UI**：基于 React + Tailwind CSS + Shadcn UI 构建，提供流畅的响应式体验。
- **深度分析展示**：自动展示关键财务指标、技术指标以及三阶段投资策略。

## 🚀 快速开始

### 1. 安装依赖
确保您的系统中已安装 Node.js 和 Python 3.11+，然后运行：
```bash
pnpm install
pip install -r requirements.txt
```

### 2. 启动开发服务器
运行以下命令同时启动前端和后端：
```bash
pnpm dev
```
启动后，在浏览器中访问控制台输出的地址（通常是 `http://localhost:5173` 或 `http://localhost:3000`）。

## 📂 项目结构

- `client/`: React 前端代码，包含所有 UI 组件和交互逻辑。
- `server/`: Express 后端代码，负责处理 API 请求并调用 Python 引擎。
- `research_engine.py`: 核心调研引擎，负责数据抓取与逻辑分析。
- `requirements.txt`: Python 依赖项。

## 🛠️ 技术栈

- **前端**: React, TypeScript, Vite, Tailwind CSS, Shadcn UI
- **后端**: Node.js, Express
- **调研引擎**: Python, yfinance
- **数据流**: 前端 (React) -> 后端 (Express) -> 引擎 (Python) -> 返回数据 (JSON)

---
