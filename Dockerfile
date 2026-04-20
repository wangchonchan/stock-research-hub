# 使用 Node.js 22
FROM node:22-slim

# 安装 Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制所有内容
COPY . .

# 进入代码所在的子文件夹
WORKDIR /app/stock-research-hub

# 安装前端依赖
RUN npm install -g pnpm && pnpm install

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 构建前端
RUN pnpm build

# 暴露端口
EXPOSE 3000

# 启动服务器
CMD ["node", "dist/index.js"]
