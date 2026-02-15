#!/bin/bash
# 启动Web服务器（支持AI代理）

echo "正在启动NGSS DCI检索系统..."
echo "服务器地址: http://localhost:8001"
echo "按 Ctrl+C 停止服务器"
echo ""

cd "$(dirname "$0")"

# 优先启动 Node 服务器（包含 /api/chat 代理）
if command -v node >/dev/null 2>&1; then
  if [ ! -d "node_modules" ]; then
    echo "首次运行：安装依赖中..."
    npm install
  fi
  node server.js
else
  echo "未检测到 node，退回到静态服务器（AI 功能不可用）"
  python3 -m http.server 8001
fi
