#!/usr/bin/env python3
"""留言板：留言存 MySQL，页面访问次数记在 Redis。"""

from __future__ import annotations

import os
import sys
import time

import pymysql
import redis
from flask import Flask, flash, redirect, render_template, request, url_for
from pymysql.cursors import DictCursor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-not-for-production")

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "db"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "guestbook"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "guestbook"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
    "connect_timeout": 5,
}

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
VISIT_KEY = "guestbook:visits"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author VARCHAR(64) NOT NULL,
    content VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def mysql_error_text(exc: BaseException) -> str:
    return (
        f"无法连接 MySQL（{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}，"
        f"数据库 {MYSQL_CONFIG['database']}，用户 {MYSQL_CONFIG['user']}）：{exc}"
    )


def get_db():
    try:
        return pymysql.connect(**MYSQL_CONFIG)
    except pymysql.Error as exc:
        raise RuntimeError(mysql_error_text(exc)) from exc


def get_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )


def init_db(retries: int = 30, delay: float = 2.0) -> None:
    last_error: BaseException | None = None
    for attempt in range(1, retries + 1):
        try:
            conn = get_db()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(CREATE_TABLE_SQL)
            finally:
                conn.close()
            print("数据库表已就绪", flush=True)
            return
        except Exception as exc:  # noqa: BLE001 — 启动阶段要打印任何连库失败原因
            last_error = exc
            print(f"等待数据库就绪（{attempt}/{retries}）：{exc}", flush=True)
            time.sleep(delay)
    print(f"启动失败：数据库一直不可用。{last_error}", file=sys.stderr, flush=True)
    sys.exit(1)


@app.get("/health")
def health():
    errors = []
    try:
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"mysql: {exc}")
    try:
        if get_redis().ping() is not True:
            errors.append("redis: ping 未返回 True")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"redis: {exc}")
    if errors:
        return {"status": "unhealthy", "errors": errors}, 503
    return {"status": "ok"}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        author = (request.form.get("author") or "").strip()
        content = (request.form.get("content") or "").strip()
        if not author or not content:
            flash("昵称和留言都不能为空。")
            return redirect(url_for("index"))
        if len(author) > 64:
            flash("昵称请控制在 64 个字符以内。")
            return redirect(url_for("index"))
        if len(content) > 500:
            flash("留言请控制在 500 个字符以内。")
            return redirect(url_for("index"))
        try:
            conn = get_db()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO messages (author, content) VALUES (%s, %s)",
                        (author, content),
                    )
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            flash(f"保存留言失败：{exc}")
        return redirect(url_for("index"))

    visits = None
    redis_error = None
    try:
        visits = get_redis().incr(VISIT_KEY)
    except Exception as exc:  # noqa: BLE001
        redis_error = (
            f"无法连接 Redis（{REDIS_HOST}:{REDIS_PORT}），访问计数暂时不可用：{exc}"
        )

    messages = []
    db_error = None
    try:
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, author, content, created_at "
                    "FROM messages ORDER BY id DESC"
                )
                messages = cursor.fetchall()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        db_error = str(exc)

    return render_template(
        "index.html",
        messages=messages,
        visits=visits,
        redis_error=redis_error,
        db_error=db_error,
    )


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
