FROM node:22-slim

# 安装 Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制所有文件
COPY . .

# 如果代码在子文件夹里，把它移出来到根目录
RUN if [ -d "stock-research-hub" ]; then mv stock-research-hub/* . && mv stock-research-hub/.* . || true; fi

# 现在所有文件都在 /app 根目录了，直接开始安装和构建
RUN npm install -g pnpm && \
    pnpm install && \
    pip3 install --no-cache-dir -r requirements.txt --break-system-packages && \
    pnpm build

# 暴露端口
EXPOSE 3000

# 启动服务器
CMD ["node", "dist/index.js"]
