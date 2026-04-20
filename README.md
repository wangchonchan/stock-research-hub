# 📊 Stock Research Hub (React Web Edition)

Stock Research Hub 现在是一个全功能的 React Web 应用程序。它将复杂的 Python 调研逻辑集成到了现代化的 Web 界面中，让您只需在浏览器中输入股票代码并点击按钮，即可完成深度调研。

## ✨ 核心功能

- **一键式 Web 交互**：在网页输入框输入股票代码（如 AAPL, TSLA），点击按钮即可触发实时调研。
- **实时数据集成**：后端自动调用 Python 调研引擎，通过 Yahoo Finance API 获取最新数据。
- **现代化 UI**：基于 React + Tailwind CSS + Shadcn UI 构建，提供流畅的响应式体验。
- **深度分析展示**：自动展示关键财务指标、技术指标以及三阶段投资策略。
- **📝 搜索历史记录**：自动保存您最近查询过的 10 个股票，点击即可快速切换查看。历史记录存储在浏览器本地，不会丢失。

## 🚀 快速开始（本地开发）

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

## 🌐 云端部署（推荐）

现在您可以将此项目部署到云端，实现 24 小时在线访问，无需本地运行任何命令。

### 部署到 Zeabur（最推荐）

1.  访问 [Zeabur](https://zeabur.com/)，使用 GitHub 账号登录。
2.  点击 **"New Project"** → **"Deploy from Git"**。
3.  选择您的 `stock-research-hub` 仓库。
4.  Zeabur 会自动识别 `Dockerfile` 并完成部署。
5.  部署完成后，您会获得一个永久的公网 URL（例如 `stock-hub.zeabur.app`）。
6.  每次您推送代码到 GitHub，网站会自动更新。

### 部署到 Railway

1.  访问 [Railway](https://railway.app/)，使用 GitHub 账号登录。
2.  点击 **"New Project"** → **"Deploy from GitHub repo"**。
3.  选择您的 `stock-research-hub` 仓库。
4.  Railway 会自动检测并部署。
5.  配置环境变量（如需要）并启动。

### 部署到 Render

1.  访问 [Render](https://render.com/)，使用 GitHub 账号登录。
2.  点击 **"New +"** → **"Web Service"**。
3.  连接您的 GitHub 仓库。
4.  选择 **"Docker"** 作为构建方式。
5.  点击 **"Deploy"**。

## 📂 项目结构

- `client/`: React 前端代码，包含所有 UI 组件和交互逻辑。
- `server/`: Express 后端代码，负责处理 API 请求并调用 Python 引擎。
- `research_engine.py`: 核心调研引擎，负责数据抓取与逻辑分析。
- `requirements.txt`: Python 依赖项。
- `Dockerfile`: 容器化部署配置。

## 🛠️ 技术栈

- **前端**: React, TypeScript, Vite, Tailwind CSS, Shadcn UI
- **后端**: Node.js, Express
- **调研引擎**: Python, yfinance
- **部署**: Docker, Zeabur / Railway / Render
- **数据流**: 前端 (React) → 后端 (Express) → 引擎 (Python) → 返回数据 (JSON)

## 📝 使用说明

1.  打开网站（本地或云端 URL）。
2.  在顶部输入框输入股票代码（例如 `TSLA`）。
3.  点击 **"Update"** 按钮。
4.  等待数据加载（通常需要 3-10 秒）。
5.  查看详细的分析报告，包括股价、财务指标、技术指标和交易策略。
6.  右侧边栏会自动保存您的搜索历史，点击即可快速切换。

---
*免责声明：本工具生成的报告仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。*
