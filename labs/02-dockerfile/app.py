#!/usr/bin/env python3
"""一个只用标准库的迷你 HTTP 服务，方便把注意力放在 Dockerfile 上。"""

from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "0.0.0.0"
PORT = 8000

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>实验 02：第一个镜像</title>
  <style>
    body { font-family: sans-serif; max-width: 40em; margin: 12vh auto; padding: 0 1.5em; color: #222; }
    h1 { font-size: 1.6rem; }
    p { line-height: 1.6; color: #444; }
    code { background: #f3f3f3; padding: 0.1em 0.35em; border-radius: 3px; }
  </style>
</head>
<body>
  <h1>你好，我来自容器里的 Python。</h1>
  <p>这是实验 02 的小服务。如果你能在浏览器里看到这段话，说明镜像已经构建成功，并且端口映射生效了。</p>
  <p>服务监听 <code>0.0.0.0:8000</code>。</p>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # 让访问日志更易读地出现在 docker logs 里
        print(self.address_string(), "-", fmt % args, flush=True)


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"listening on {HOST}:{PORT}", flush=True)
    server.serve_forever()
