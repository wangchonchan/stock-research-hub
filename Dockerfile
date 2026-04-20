FROM node:22-slim

# 安装 Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制所有文件
COPY . .

# 自动定位到包含 package.json 的目录并执行所有操作
RUN DIR=$(find . -name "package.json" -not -path "*/node_modules/*" -exec dirname {} \;) && \
    cd $DIR && \
    npm install -g pnpm && \
    pnpm install && \
    pip3 install --no-cache-dir -r requirements.txt --break-system-packages && \
    pnpm build

# 暴露端口
EXPOSE 3000

# 启动命令：动态寻找 dist/index.js 并运行
CMD ["sh", "-c", "START_DIR=$(find . -name \"dist\" -type d -not -path \"*/node_modules/*\" -exec dirname {} \\;) && cd $START_DIR && node dist/index.js"]
