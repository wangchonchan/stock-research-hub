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

# 安装 Python 运行时环境
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制构建产物
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./
COPY --from=builder /app/requirements.txt ./
COPY --from=builder /app/research_engine.py ./

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 暴露端口
EXPOSE 3000

# 设置环境变量
ENV NODE_ENV=production

# 启动应用
CMD ["node", "dist/index.js"]
