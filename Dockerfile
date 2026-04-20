FROM node:22-slim

# 安装 Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制所有文件
COPY . .

# 自动寻找 package.json 所在的目录并进入
RUN DIR=$(find . -name "package.json" -not -path "*/node_modules/*" -exec dirname {} \;) && \
    echo "Found package.json in $DIR" && \
    cd $DIR && \
    npm install -g pnpm && \
    pnpm install && \
    pip3 install --no-cache-dir -r requirements.txt --break-system-packages && \
    pnpm build

# 暴露端口
EXPOSE 3000

# 启动脚本：同样自动寻找并运行
CMD ["sh", "-c", "DIR=$(find . -name \"dist\" -type d -not -path \"*/node_modules/*\" -exec dirname {} \\;) && cd $DIR && node dist/index.js"]
