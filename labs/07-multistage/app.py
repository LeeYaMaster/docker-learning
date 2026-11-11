#!/usr/bin/env python3
"""体积对比用的小服务。逻辑保持最少，方便把注意力放在镜像构建上。"""

import os
from flask import Flask

app = Flask(__name__)


@app.get("/")
def index():
    return (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<title>实验 07</title></head><body>"
        "<h1>多阶段构建演示</h1>"
        "<p>如果你能看到本页，说明当前这个镜像里的应用已经跑起来了。</p>"
        "<p>接下来请用 docker images 对比 lab07:single 和 lab07:multi 的体积。</p>"
        "</body></html>"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
