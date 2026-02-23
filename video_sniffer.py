import sys
import time
import threading
import json
from flask import Flask, render_template_string, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# 全局变量存储结果
sniff_results = {
    "status": "idle",
    "url": "",
    "preview_links": [],
    "index_links": [],
    "logs": []
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>视频 URL 自动解析工具</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; font-size: 28px; }
        .input-group { display: flex; margin-bottom: 20px; gap: 10px; }
        input[type="text"] { flex: 1; padding: 14px; border: 2px solid #ddd; border-radius: 8px; outline: none; font-size: 14px; transition: border-color 0.3s; }
        input[type="text"]:focus { border-color: #667eea; }
        button { padding: 14px 30px; border: none; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; cursor: pointer; border-radius: 8px; transition: transform 0.2s, box-shadow 0.2s; font-weight: bold; }
        button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .status { margin-bottom: 20px; padding: 15px; border-radius: 8px; display: none; }
        .status.running { display: block; background-color: #e7f3ff; color: #004085; border: 2px solid #b8daff; }
        .results { margin-top: 30px; }
        .results h3 { color: #333; margin-bottom: 15px; font-size: 18px; }
        .result-section { margin-bottom: 25px; }
        .result-section h4 { color: #667eea; margin-bottom: 10px; font-size: 16px; }
        .result-item { background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin-bottom: 10px; border-radius: 4px; word-break: break-all; }
        .result-item strong { display: block; margin-bottom: 8px; color: #555; }
        .result-url { color: #666; font-size: 13px; font-family: 'Courier New', monospace; }
        .copy-btn { margin-top: 10px; padding: 8px 15px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; transition: background 0.3s; }
        .copy-btn:hover { background: #764ba2; }
        .logs { margin-top: 30px; font-size: 12px; color: #666; max-height: 300px; overflow-y: auto; background: #fafafa; padding: 15px; border: 2px solid #eee; border-radius: 8px; font-family: 'Courier New', monospace; }
        .log-entry { margin-bottom: 5px; }
        .log-time { color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 视频 URL 自动解析工具</h1>
        <div class="input-group">
            <input type="text" id="targetUrl" placeholder="请输入包含视频的网页 URL" value="https://xinc.229421.xyz:8283/video-details/130185?channel=Onerun5-032-2x#1770879842966">
            <button id="startBtn" onclick="startSniffing()">开始解析</button>
        </div>
        
        <div id="statusBox" class="status">正在解析中，请稍候...</div>

        <div class="results" id="resultsList">
            <!-- 解析结果将显示在这里 -->
        </div>

        <div class="logs" id="logBox">
            <div class="log-entry"><span class="log-time">[系统]</span> 系统就绪</div>
        </div>
    </div>

    <script>
        let intervalId = null;
        let lastLogCount = 1;

        function addLog(msg) {
            const logBox = document.getElementById('logBox');
            const div = document.createElement('div');
            div.className = 'log-entry';
            const time = new Date().toLocaleTimeString();
            div.innerHTML = `<span class="log-time">[${time}]</span> ${msg}`;
            logBox.appendChild(div);
            logBox.scrollTop = logBox.scrollHeight;
        }

        function startSniffing() {
            const url = document.getElementById('targetUrl').value;
            if (!url) return alert('请输入 URL');

            document.getElementById('startBtn').disabled = true;
            document.getElementById('statusBox').className = 'status running';
            document.getElementById('resultsList').innerHTML = '';
            lastLogCount = 1;
            
            fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            })
            .then(res => res.json())
            .then(data => {
                addLog('解析任务已启动');
                pollStatus();
            });
        }

        function pollStatus() {
            intervalId = setInterval(() => {
                fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    // 更新日志
                    if (data.logs.length > lastLogCount) {
                        for (let i = lastLogCount; i < data.logs.length; i++) {
                            addLog(data.logs[i]);
                        }
                        lastLogCount = data.logs.length;
                    }

                    // 更新结果显示
                    if (data.preview_links.length > 0 || data.index_links.length > 0) {
                        const list = document.getElementById('resultsList');
                        list.innerHTML = '<h3>✅ 解析到的视频地址：</h3>';
                        
                        if (data.preview_links.length > 0) {
                            const previewSection = document.createElement('div');
                            previewSection.className = 'result-section';
                            previewSection.innerHTML = `<h4>Preview 类型 (${data.preview_links.length})</h4>`;
                            data.preview_links.forEach((link, idx) => {
                                const item = document.createElement('div');
                                item.className = 'result-item';
                                const btnId = 'copy-preview-' + idx;
                                item.innerHTML = `<strong>Preview URL:</strong> <div class="result-url">${link}</div> <button class="copy-btn" id="${btnId}">复制链接</button>`;
                                previewSection.appendChild(item);
                                document.getElementById(btnId).onclick = () => copyToClipboard(link);
                            });
                            list.appendChild(previewSection);
                        }

                        if (data.index_links.length > 0) {
                            const indexSection = document.createElement('div');
                            indexSection.className = 'result-section';
                            indexSection.innerHTML = `<h4>Index 类型 (${data.index_links.length})</h4>`;
                            data.index_links.forEach((link, idx) => {
                                const item = document.createElement('div');
                                item.className = 'result-item';
                                const btnId = 'copy-index-' + idx;
                                item.innerHTML = `<strong>Index URL:</strong> <div class="result-url">${link}</div> <button class="copy-btn" id="${btnId}">复制链接</button>`;
                                indexSection.appendChild(item);
                                document.getElementById(btnId).onclick = () => copyToClipboard(link);
                            });
                            list.appendChild(indexSection);
                        }
                    }

                    if (data.status === 'completed' || data.status === 'error') {
                        clearInterval(intervalId);
                        document.getElementById('startBtn').disabled = false;
                        document.getElementById('statusBox').style.display = 'none';
                        addLog(data.status === 'completed' ? '✓ 解析完成' : '✗ 解析出错');
                    }
                });
            }, 1000);
        }

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('已复制到剪贴板！');
            }).catch(() => {
                alert('复制失败，请手动复制');
            });
        }
    </script>
</body>
</html>
"""

def sniff_task(target_url):
    global sniff_results
    sniff_results["status"] = "running"
    sniff_results["preview_links"] = []
    sniff_results["index_links"] = []
    sniff_results["logs"] = ["启动浏览器..."]
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    try:
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        driver = webdriver.Chrome(options=chrome_options)
        sniff_results["logs"].append(f"正在访问: {target_url}")
        driver.get(target_url)
        
        sniff_results["logs"].append("等待视频加载并捕获网络请求...")
        
        found_preview = set()
        found_index = set()
        start_time = time.time()
        timeout = 45  # 45秒超时
        last_check_time = start_time
        check_interval = 1.5  # 每1.5秒检查一次
        
        while time.time() - start_time < timeout:
            current_time = time.time()
            
            # 定期检查日志
            if current_time - last_check_time >= check_interval:
                try:
                    logs = driver.get_log("performance")
                    sniff_results["logs"].append(f"[检查] 获取到 {len(logs)} 条日志")
                    
                    for entry in logs:
                        try:
                            log_data = json.loads(entry["message"])
                            message = log_data.get("message", {})
                            
                            # 监听网络请求
                            if "Network.requestWillBeSent" in message.get("method", ""):
                                url = message.get("params", {}).get("request", {}).get("url", "")
                                
                                if url:
                                    # 检查 preview 类型
                                    if "preview" in url and ".m3u8" in url and url not in found_preview:
                                        found_preview.add(url)
                                        sniff_results["preview_links"].append(url)
                                        sniff_results["logs"].append(f"✓ 发现 Preview M3U8: {url}")
                                    
                                    # 检查 index 类型
                                    elif "index" in url and ".m3u8" in url and url not in found_index:
                                        found_index.add(url)
                                        sniff_results["index_links"].append(url)
                                        sniff_results["logs"].append(f"✓ 发现 Index M3U8: {url}")
                        except Exception as e:
                            pass
                    
                    last_check_time = current_time
                    
                    # 如果两种都找到了，可以提前退出
                    if found_preview and found_index:
                        sniff_results["logs"].append("已找到两种类型的视频链接，继续等待以确保捕获所有链接...")
                        time.sleep(3)
                        break
                except Exception as e:
                    sniff_results["logs"].append(f"[错误] 获取日志异常: {str(e)}")
            
            time.sleep(0.3)
        
        driver.quit()
        sniff_results["status"] = "completed"
        
        if not found_preview and not found_index:
            sniff_results["logs"].append("未发现 m3u8 链接，请检查 URL 是否正确或视频是否可播放。")
        else:
            sniff_results["logs"].append(f"解析完成！共找到 {len(found_preview)} 个 Preview 链接，{len(found_index)} 个 Index 链接。")
            
    except Exception as e:
        sniff_results["status"] = "error"
        sniff_results["logs"].append(f"错误: {str(e)}")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/start', methods=['POST'])
def start_sniff():
    data = request.json
    url = data.get('url')
    threading.Thread(target=sniff_task, args=(url,)).start()
    return jsonify({"message": "started"})

@app.route('/api/status')
def get_status():
    return jsonify(sniff_results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
