#!/bin/bash
# Stock Research Hub - 自动更新脚本
# 一键执行深度调研和网页生成

echo "🚀 Stock Research Hub - 自动更新"
echo "=================================="
echo ""

# 获取股票代码，默认为 FIGR
TICKER=${1:-FIGR}
echo "📊 开始调研 $TICKER..."
echo ""

# 运行 Python 调研脚本
python3 research_engine.py "$TICKER"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 调研完成！"
    echo ""
    echo "🔨 正在生成网页..."
    
    # 运行 HTML 生成脚本
    python3 generate_html.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✨ 完成！"
        echo "=================================="
        echo "📄 网页已生成: index.html"
        echo "📊 数据已保存: research_data_${TICKER}.json"
        echo ""
        echo "💡 下次更新，只需运行:"
        echo "   ./update.sh $TICKER"
        echo ""
    else
        echo "❌ HTML 生成失败"
        exit 1
    fi
else
    echo "❌ 调研失败"
    exit 1
fi
