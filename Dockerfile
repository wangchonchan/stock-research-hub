# 使用 Node.js 22 作为基础镜像
FROM node:22-slim

# 安装 Python 和 pip
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 首先安装前端依赖
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

# 复制所有源代码
COPY . .

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 构建前端
RUN pnpm build

# 暴露端口
EXPOSE 3000

# 启动服务器
CMD ["node", "dist/index.js"]
