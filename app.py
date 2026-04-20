import os
import subprocess
from flask import Flask, render_template_string, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "stock_research_hub_secret"

# HTML 模板
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Research Hub - 控制面板</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f1f5f9; }
        .container { max-width: 800px; margin: 50px auto; }
        .card { background: white; border-radius: 1rem; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1); padding: 2rem; }
        .btn-primary { background-color: #2563eb; color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 600; transition: all 0.2s; }
        .btn-primary:hover { background-color: #1d4ed8; transform: translateY(-1px); }
        .btn-secondary { background-color: #64748b; color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 600; transition: all 0.2s; }
        .btn-secondary:hover { background-color: #475569; }
        .input-field { border: 1px solid #cbd5e1; padding: 0.75rem; border-radius: 0.5rem; width: 100%; margin-bottom: 1rem; }
        .status-msg { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem; }
        .status-success { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .status-error { background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    </style>
</head>
<body>
    <div class="container px-4">
        <div class="flex items-center gap-3 mb-8">
            <div class="bg-blue-600 text-white w-10 h-10 flex items-center justify-center rounded-lg font-bold text-xl">S</div>
            <h1 class="text-3xl font-bold text-slate-900">Stock Research Hub</h1>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="status-msg {% if category == 'success' %}status-success{% else %}status-error{% endif %}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="card mb-8">
            <h2 class="text-xl font-bold mb-4 text-slate-800">更新股票调研数据</h2>
            <p class="text-slate-600 mb-6">输入股票代码（如 AAPL, TSLA, FIGR），系统将自动抓取 Yahoo Finance 数据并重新生成分析页面。</p>
            
            <form action="/update" method="POST" class="space-y-4">
                <div>
                    <label for="ticker" class="block text-sm font-medium text-slate-700 mb-1">股票代码</label>
                    <input type="text" id="ticker" name="ticker" placeholder="例如: FIGR" class="input-field" required>
                </div>
                <div class="flex gap-4">
                    <button type="submit" class="btn-primary flex-1">立即更新数据</button>
                    <a href="/view" target="_blank" class="btn-secondary">查看分析页面</a>
                </div>
            </form>
        </div>

        <div class="text-center text-slate-500 text-sm">
            <p>© 2024 Stock Research Hub • Powered by AI Research Engine</p>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE)

@app.route("/update", methods=["POST"])
def update():
    ticker = request.form.get("ticker", "").strip().upper()
    if not ticker:
        flash("请输入有效的股票代码", "error")
        return redirect(url_for("index"))
    
    try:
        # 执行更新脚本
        # 注意：在生产环境中，这应该是一个异步任务，但为了简单起见，我们在这里同步执行
        result = subprocess.run(["bash", "update.sh", ticker], capture_output=True, text=True)
        
        if result.returncode == 0:
            flash(f"成功更新 {ticker} 的调研数据！", "success")
        else:
            flash(f"更新失败: {result.stderr}", "error")
            
    except Exception as e:
        flash(f"发生错误: {str(e)}", "error")
        
    return redirect(url_for("index"))

@app.route("/view")
def view():
    # 如果 index.html 存在，则返回它
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "分析页面尚未生成，请先进行更新。"

if __name__ == "__main__":
    # 默认在 5000 端口运行
    app.run(host="0.0.0.0", port=5000, debug=True)
