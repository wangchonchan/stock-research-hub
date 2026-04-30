# 使用 Node.js 22 作为基础镜像
FROM node:22-slim AS builder

# 安装 Python 和构建工具
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm

# 复制依赖文件
COPY package.json pnpm-lock.yaml ./
COPY patches ./patches

# 安装 Node.js 依赖
RUN pnpm install --frozen-lockfile

# 复制所有源代码
COPY . .

# 构建前端和后端
RUN pnpm build

# 运行阶段
FROM node:22-slim

# 安装 Python 运行时环境和必要的库
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 pnpm 用于安装生产依赖
RUN npm install -g pnpm

# 复制构建产物和依赖描述文件
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json /app/pnpm-lock.yaml ./
COPY --from=builder /app/requirements.txt ./
COPY --from=builder /app/research_engine.py ./
COPY --from=builder /app/patches ./patches

# 安装 Node.js 生产依赖
RUN pnpm install --prod --frozen-lockfile

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 暴露端口
# Hugging Face Spaces uses port 7860 by default
EXPOSE 7860

# 设置环境变量
ENV NODE_ENV=production
ENV PORT=7860

# Add a healthcheck to let Hugging Face know the service is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

# 启动应用
# Use a shell to ensure environment variables are correctly expanded
CMD ["sh", "-c", "node dist/index.js"]
