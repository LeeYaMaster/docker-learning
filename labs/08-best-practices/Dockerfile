# 实验 08 独立示例：非 root 用户 + HEALTHCHECK
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 先创建用户，再拷贝文件并调整属主，避免应用以 root 运行
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser

COPY --chown=appuser:appuser app.py .

USER appuser

EXPOSE 8000

# slim 镜像不一定带 curl，用标准库探测本进程即可
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

CMD ["python", "app.py"]
