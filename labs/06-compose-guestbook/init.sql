-- MySQL 官方镜像会在数据目录第一次初始化时执行本目录挂载的 SQL。
-- 之后若数据卷已存在，不会再跑一遍。应用启动时也会 CREATE TABLE IF NOT EXISTS，两种路径都能用。

CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author VARCHAR(64) NOT NULL,
    content VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
