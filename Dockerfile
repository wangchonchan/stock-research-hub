FROM node:22-slim

# 1. 安装 Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 复制所有文件
COPY . .

# 3. 自动进入代码目录并构建
# 我们直接用通配符找到包含 package.json 的目录
RUN cd $(find . -name "package.json" -not -path "*/node_modules/*" -exec dirname {} \;) && \
    npm install -g pnpm && \
    pnpm install && \
    pip3 install --no-cache-dir -r requirements.txt --break-system-packages && \
    pnpm build

# 4. 启动脚本：确保后端能找到前端文件
# 我们在启动时动态进入目录并运行
EXPOSE 3000
ENV NODE_ENV=production
CMD ["sh", "-c", "APP_DIR=$(find . -name \"package.json\" -not -path \"*/node_modules/*\" -exec dirname {} \\;) && cd $APP_DIR && node dist/index.js"]
