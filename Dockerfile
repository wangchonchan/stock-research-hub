# Multi-stage build for Stock Research Hub
# Stage 1: Build Node.js frontend
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build the project
RUN pnpm build

# Stage 2: Runtime environment with Python support
FROM node:22-alpine

# Install Python and required dependencies
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Copy built files from builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

# Copy Python scripts and requirements
COPY research_engine.py generate_html.py ./
COPY requirements.txt ./

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy package.json for reference
COPY package.json ./

# Expose port
EXPOSE 3000

# Set environment to production
ENV NODE_ENV=production

# Start the server
CMD ["node", "dist/index.js"]
