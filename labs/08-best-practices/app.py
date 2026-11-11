#!/usr/bin/env python3
"""演示用的小服务：非 root、HEALTHCHECK、日志打到标准输出。"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import os

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))

INDEX = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>实验 08：更稳妥的运行习惯</title>
  <style>
    body { font-family: sans-serif; max-width: 42em; margin: 12vh auto; padding: 0 1.5em; color: #222; line-height: 1.6; }
    code { background: #f3f3f3; padding: 0.1em 0.35em; border-radius: 3px; }
  </style>
</head>
<body>
  <h1>这个容器不使用 root 跑应用。</h1>
  <p>访问 <code>/health</code> 会返回健康状态，Dockerfile 里的 HEALTHCHECK 也是探测这个地址。</p>
  <p>日志会打印到标准输出，请用 <code>docker logs</code> 查看，而不是在容器里翻文件。</p>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = b'{"status":"ok"}'
            content_type = "application/json"
        else:
            body = INDEX.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # 写到 stdout，由 Docker 收集。不要在容器里另写一份 .log 文件。
        print(self.address_string(), "-", fmt % args, flush=True)


if __name__ == "__main__":
    user = os.environ.get("USER") or os.getuid()
    print(f"listening on {HOST}:{PORT}, uid={os.getuid()}, user={user}", flush=True)
    HTTPServer((HOST, PORT), Handler).serve_forever()
