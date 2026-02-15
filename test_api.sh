#!/bin/bash

# 测试课标匹配API
echo "======================================"
echo "测试 /api/match 接口"
echo "======================================"

# 读取API Key（需要从.env文件获取）
cd "$(dirname "$0")/web"
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 准备测试数据
cat > /tmp/test_match.json <<'EOF'
{
  "query": "学习用弹簧秤测量物体的重力",
  "standards": [
    {
      "id": "DCI-PS1.A-2-1",
      "source": "NGSS-DCI",
      "grade_band": "1-2",
      "topic": "物质的结构与性质",
      "text": "存在不同种类的物质，其中许多可以是固体或液体，具体取决于温度。物质可以通过其可观察的属性来描述和分类。"
    },
    {
      "id": "PE-K-PS2-1",
      "source": "NGSS-PE",
      "grade_band": "K",
      "topic": "Motion and Stability: Forces and interactions",
      "text": "Plan and conduct an investigation to compare the effects of different strengths or different directions of pushes and pulls on the motion of an object."
    },
    {
      "id": "PS-2.1-1-MP",
      "source": "中国义务教育科学课标",
      "grade_band": "3-4",
      "topic": "物质的运动",
      "text": "能使用简单的仪器测量一些物体的长度、质量、体积、温度等常见特征，并使用恰当的计量单位进行记录。"
    }
  ],
  "apiKey": "${DEEPSEEK_API_KEY}"
}
EOF

echo ""
echo "请求内容："
cat /tmp/test_match.json | jq .

echo ""
echo "发送请求到 http://localhost:8001/api/match ..."
echo ""

# 发送请求
response=$(curl -s -X POST http://localhost:8001/api/match \
  -H "Content-Type: application/json" \
  -d @/tmp/test_match.json)

echo "响应内容："
echo "$response" | jq .

# 清理
rm /tmp/test_match.json

echo ""
echo "======================================"
echo "测试完成"
echo "======================================"
