# 实验 06：用 Compose 跑起来一个留言板

预估时间：约 50 分钟

## 本实验目标

把前面学过的镜像、端口、卷、网络放到一起，用 **Docker Compose** 启动一个完整的小应用：

- **web**：Python Flask，同一个服务既出页面，也处理发表留言
- **db**：MySQL 8.0，保存留言
- **redis**：Redis 7，记录页面访问次数（每次打开首页就加 1）

为什么要用 Compose？三个容器要在同一网络里用名字互访，还要按顺序等待数据库就绪，一个个写 `docker run` 既长又容易漏。`docker-compose.yml` 把这些约定写在一份文件里，`up` / `down` / `logs` 都围绕这一组服务进行。

本实验还会专门练习：

- 用 **healthcheck + `depends_on: condition: service_healthy`**，让 Web 等到数据库真正可连接再启动
- 如何避开你本机已经在跑的 MySQL（3306）和 Redis（6379）

应用逻辑刻意很小，重点仍是把 Docker 跑顺。

## 准备工作

后续命令都请在本实验目录执行：

```bash
cd labs/06-compose-guestbook
ls
```

预期结果：能看到 `docker-compose.yml`、`Dockerfile`、`app.py`、`requirements.txt`、`.env.example`、`init.sql` 以及 `templates/`、`static/`。

复制一份本地环境变量文件（`.env` 已被 git 忽略，不要把真实密码提交到仓库）：

```bash
cp .env.example .env
```

打开 `.env` 看一眼即可。默认账号密码如下，**仅供本机学习使用**：

| 项目 | 值 |
|------|----|
| MySQL root 密码 | `learn_root_pass` |
| 数据库名 | `guestbook` |
| 应用用户 | `guestbook` |
| 应用密码 | `learn_pass` |

再确认 8080、3307、6380 没有被占用：

```bash
docker ps
```

若前面实验的容器还占着 8080，先按对应 README 的收尾命令清掉。

你的 Mac 上如果已经有 MySQL、Redis，请让它们继续占用 3306 / 6379 即可——本实验**不会去映射这两个默认端口**。

## 动手步骤

### 步骤 1：先把 compose 文件看一遍

打开 `docker-compose.yml`，对照这几处关键设计：

- 三个服务：`web`、`db`、`redis`。没有写已过时的 `version` 字段。
- `web` 的端口是 `8080:5000`（Flask 在容器内听 5000）。
- `db` 的端口是 `3307:3306`，`redis` 的端口是 `6380:6379`。容器之间互连仍走 **3306** 和 **6379**，因为它们在 Compose 创建的网络内部访问，不经过宿主机端口。
- `web` 通过环境变量把 `MYSQL_HOST` 设为 `db`，`REDIS_HOST` 设为 `redis`。这就是实验 05 里的容器名 / 服务名 DNS。
- `db` 和 `redis` 都有 `healthcheck`。`web` 的 `depends_on` 使用 `condition: service_healthy`，因此不会在 MySQL 还在初始化时就冲进去连库。
- 数据放在具名卷 `guestbook-mysql-data`、`guestbook-redis-data` 里（对照实验 04）。`init.sql` 挂到 MySQL 官方镜像的 `/docker-entrypoint-initdb.d/`，仅在数据目录第一次初始化时执行。应用启动时也会 `CREATE TABLE IF NOT EXISTS`，两条路径都可以建表。

Redis 在本应用里的用途很单纯：**访问计数**，不是缓存整页，也不是会话存储。每次 GET 首页，就会对键 `guestbook:visits` 执行 `INCR`。留言本身只进 MySQL。

### 步骤 2：启动整组服务

```bash
docker compose up -d --build
```

`--build` 会根据当前 Dockerfile 和代码构建 web 镜像。第一次拉取 `mysql:8.0`、`redis:7-alpine`、`python:3.12-slim` 需要一些时间，视网络而定。

```bash
docker compose ps
```

预期结果：三个服务都在运行。`db`、`redis` 的状态应很快变为 `healthy`（或在 STATUS 里看到 `(healthy)`）。`web` 会等前两者健康后再启动。MySQL 第一次初始化可能要十几秒到半分钟，期间 `ps` 里可能暂时是 `health: starting`。

若 `web` 反复重启，先看日志（下一步），不要连续多次 `up`。

### 步骤 3：看日志，确认应用已经连上数据库

```bash
docker compose logs web
docker compose logs -f --tail 50
```

`logs web` 只看应用。第二条会持续跟踪全部服务，用 `Ctrl+C` 停止跟踪，不会把容器停掉。

预期结果：`web` 日志里出现 `数据库表已就绪`，以及 Flask 启动信息。如果曾短暂连不上，你也会看到 `等待数据库就绪（1/30）：...`，随后成功。这是应用自己的重试，和 Compose 的 healthcheck 是两道保险。

### 步骤 4：在浏览器里使用留言板

打开 [http://localhost:8080](http://localhost:8080)。

预期结果：

- 能看到「留言板」页面和访问次数（例如「本页已被访问 1 次」）
- 刷新几次，次数会增加（这就是 Redis 在工作）
- 发表一条留言后，页面列出它，带有昵称和时间
- 再发表几条，最新的出现在上面

如果页面打不开，先 `docker compose ps` 和 `docker compose logs web`。若访问次数旁出现 Redis 报错、或页面顶部出现「读取留言失败」，把完整报错对照下面的「常见坑」。

健康检查接口也可以验证一下：

```bash
curl -s http://localhost:8080/health
```

预期结果：类似 `{"status":"ok"}`。

### 步骤 5：从本机客户端连映射端口（可选）

这步用来确认「避开本机 3306 / 6379」是怎么做到的。容器对外暴露的是 3307 和 6380。

若本机有 `mysql` 客户端：

```bash
mysql -h 127.0.0.1 -P 3307 -u guestbook -plearn_pass guestbook -e "SELECT id, author, content FROM messages;"
```

注意是 `-P 3307`（大写 P 表示端口），主机是 `127.0.0.1` 而不是 `localhost`（后者在某些 MySQL 客户端上会走套接字，绕过 TCP 端口）。

若本机有 `redis-cli`：

```bash
redis-cli -h 127.0.0.1 -p 6380 GET guestbook:visits
```

预期结果：能看到你刚才在网页上发表的留言，以及当前访问次数。这不会碰到本机原来的 MySQL / Redis。

**不要**把 Web 容器里的 `MYSQL_HOST` 改成 `127.0.0.1`。在容器里，`127.0.0.1` 指的是容器自己，不是你的 Mac。容器要访问的是服务名 `db` 和 `redis`。

### 步骤 6：停掉、再启动，确认数据还在

```bash
docker compose down
docker compose up -d
```

再打开 [http://localhost:8080](http://localhost:8080)。

预期结果：之前的留言还在（MySQL 具名卷）。访问次数通常也还在（Redis 开启了 AOF，数据在 `guestbook-redis-data` 卷里）。`down` 默认删除容器和网络，但**不会删除具名卷**。

若你希望连练习数据一起清空，才使用：

```bash
docker compose down -v
```

这会删除本项目的具名卷，留言和计数都会消失。下一次 `up` 时 MySQL 会重新初始化，`init.sql` 会再执行一遍。请只在确定要清空时使用 `-v`。

## 小练习

请先自己做，做完再看 `answers.md`。

1. 发表两三条留言后执行 `docker compose down`（不要加 `-v`），再 `up`，确认留言还在。用一句话说明数据存在哪里。
2. 在整组服务运行时，只停掉 Redis：`docker compose stop redis`。刷新留言板首页，观察页面和访问次数变成什么样。然后 `docker compose start redis` 恢复。想想：为什么留言通常还在，计数却出了提示？
3. 查看 `docker compose logs db` 的开头，找找 healthcheck 或初始化相关的输出。再用 `docker compose ps` 确认 `healthy` 字样。如果把 `web` 的 `depends_on` 改成不带 `condition` 的旧写法，可能会出现什么问题？（说清楚即可，不一定真改。）

## 常见坑

- **忘记 `cp .env.example .env`。** Compose 需要用这些变量给 MySQL 设密码。缺文件时，`docker compose up` 常会警告变量没有设置，数据库可能用空密码启动失败。
- **8080 / 3307 / 6380 被占用。** `docker ps` 看是不是其它实验或本机进程。本实验刻意不用 3306、6379，以免和你已经安装的 MySQL、Redis 打架。若冲突发生在 8080，可把 compose 里 `8080:5000` 的左边改掉，浏览器改访新端口。
- **web 启动时报连不上数据库。** 先等 `db` 变为 healthy。第一次拉镜像并初始化 InnoDB 较慢。仍失败就看 `docker compose logs db`：密码、权限、端口是否和 `.env` 一致。
- **改了 `app.py` 但页面没变。** 需要重新构建：`docker compose up -d --build`。只 `restart` 不会把新代码打进镜像（除非你后来改用 bind mount 开发）。
- **`down` 之后以为数据丢了，其实看错了环境；或反过来，想清空却发现数据还在。** 记住：`down` 保留卷，`down -v` 删除卷。
- **`init.sql` 没有重新执行。** 官方镜像只在数据目录为空时跑 `/docker-entrypoint-initdb.d/`。卷还在就不会再跑。表结构已改时，要么靠应用里的 `CREATE TABLE IF NOT EXISTS` / 迁移，要么 `down -v` 后重新初始化（练习数据会没）。
- **从本机用 `localhost` 连 MySQL 却连不上。** 换 `127.0.0.1` 并指定端口 `3307`。
- **healthcheck 一直不健康。** 检查 `.env` 里的 `MYSQL_ROOT_PASSWORD` 是否有特殊字符（本学习营默认值没有）。需要的话用 `docker compose ps` 和 `docker inspect guestbook-db` 看 Health 日志。

## 收尾

日常结束练习，保留数据卷：

```bash
docker compose down
```

连同练习数据一起删除，并释放端口：

```bash
docker compose down -v
docker ps
```

后面的实验 07、08 不再默认启动这组服务。实验 08 会给出一份更接近生产习惯的 Guestbook Dockerfile，你可以再回到本目录对照着看。
