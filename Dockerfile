FROM node:22-slim

# 1. 安装 Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 复制所有文件
COPY . .

# 3. 强制规范化路径：如果代码在子文件夹，就把它移到根目录
RUN if [ -d "stock-research-hub" ]; then \
    cp -r stock-research-hub/* . && \
    cp -r stock-research-hub/.* . || true && \
    rm -rf stock-research-hub; \
    fi

# 4. 安装依赖并构建
RUN npm install -g pnpm && \
    pnpm install && \
    pip3 install --no-cache-dir -r requirements.txt --break-system-packages && \
    pnpm build

# 5. 关键修复：确保后端能找到前端文件
# 我们的后端代码预期前端在 ../dist/public 或 ./public
# 我们直接创建一个软链接确保万无一失
RUN mkdir -p dist/public && cp -r dist/client/* dist/public/ || true

# 6. 启动
EXPOSE 3000
ENV NODE_ENV=production
CMD ["node", "dist/index.js"]
