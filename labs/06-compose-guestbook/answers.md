# 实验 06 练习参考答案

请先自己做，再对照这里。

## 练习 1

```bash
# 在 labs/06-compose-guestbook 目录，且已经发表过留言
docker compose down
docker compose up -d
```

浏览器刷新后，留言还在。

数据在 Docker 具名卷里，具体是 compose 文件中的 `guestbook-mysql-data`（挂到容器内 `/var/lib/mysql`）。`docker compose down` 删的是容器和网络，默认不动卷。这和实验 04 里「删掉容器、再跑一个新的，具名卷里的文件还在」是同一件事。

查看卷：

```bash
docker volume ls | grep guestbook
```

## 练习 2

```bash
docker compose stop redis
```

再刷新首页：留言列表通常仍能正常显示（它们在 MySQL 里），但访问次数会消失，并出现类似「无法连接 Redis……访问计数暂时不可用」的提示。应用被故意写成：Redis 故障时页面还用，只是计数不可用；连 MySQL 失败才会严重影响留言的读取和发表。

```bash
docker compose start redis
```

再刷新：计数会恢复可用（从 Redis 里的值继续累加；停掉期间未写入的刷新不会补上）。

这说明两个存储的职责不同：MySQL 负责留言，Redis 只负责计数。也说明把依赖拆到不同容器后，可以让应用在「部分依赖短暂不可用」时仍然给出清楚的提示，而不是整站空白。

## 练习 3

```bash
docker compose logs db
docker compose ps
```

`ps` 里 `db` 和 `redis` 应显示健康。`logs db` 在首次初始化时会有创建数据库、创建用户、执行 `/docker-entrypoint-initdb.d/init.sql` 之类的输出；之后再启动则主要是 InnoDB / 就绪日志。

如果 `depends_on` 只写成：

```yaml
depends_on:
  - db
  - redis
```

含义只是「先创建并启动这些容器」，**并不等待它们真正能接受连接**。MySQL 从进程启动到可以登录，往往还有一段初始化时间。Web 若在这段时间里去连库，就会失败。本应用在代码里做了重试，所以即使去掉 `condition` 也常常最终能起来，但启动日志会更吵，偶发仍可能在重试耗尽后退出。

`condition: service_healthy` 把「进程已启动」提升为「健康检查已经通过」，是更稳妥的做法。代码里的重试作为第二道保险保留，仍然有价值。
