FROM node:22-slim

# 安装 Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制所有文件
COPY . .

# 极其稳健的移动命令：如果文件夹存在，就移出来；如果不存在，就跳过
RUN if [ -d "stock-research-hub" ]; then cp -r stock-research-hub/. . && rm -rf stock-research-hub; fi

# 现在直接开始安装和构建
RUN npm install -g pnpm && \
    pnpm install && \
    pip3 install --no-cache-dir -r requirements.txt --break-system-packages && \
    pnpm build

# 暴露端口
EXPOSE 3000

# 启动服务器
CMD ["node", "dist/index.js"]
