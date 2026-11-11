# 实验 08：更接近生产的习惯

预估时间：约 35 分钟

## 本实验目标

在「能跑」之上，养成几条不容易回头踩坑的习惯：

- 为容器声明 **HEALTHCHECK**，让编排系统知道进程是否真的可用
- 用 **非 root 用户** 跑应用
- 给容器加上 **内存 / CPU 限制**，避免一个进程把宿主机吃满
- 日志打到标准输出，用 `docker logs` / `docker compose logs` 看，而不是在容器里写一份 `.log`
- 认真写 **`.dockerignore`**，不要把密钥、文档、缓存送进构建上下文

本实验提供一份可独立运行的小服务（`Dockerfile` + `app.py` + `docker-compose.yml`），以及一份可替换实验 06 的 `Dockerfile.guestbook`。请先把独立示例跑通，再按需把习惯带回留言板。

这些做法能降低风险、让问题更容易被看见，但并不等于把应用「上了生产」。密钥管理、备份、监控、反向代理和 HTTPS 都不在本实验范围内。

## 准备工作

请在本实验目录执行命令：

```bash
cd labs/08-best-practices
ls
```

预期结果：能看到 `Dockerfile`、`Dockerfile.guestbook`、`app.py`、`docker-compose.yml`、`.dockerignore`。

若 8080 被占用，先清掉占用它的容器。

## 动手步骤

### 步骤 1：读一遍独立示例的 Dockerfile

打开 `Dockerfile`，注意这几处和实验 02 的差别：

- `RUN useradd ... appuser`：创建一个 uid 为 1000 的普通用户
- `COPY --chown=appuser:appuser app.py .`：文件属主是这个用户，否则非 root 可能读不了自己的代码（本示例其实只读一个文件，但养成习惯更好）
- `USER appuser`：从此之后的指令（包括 `CMD`）都以该用户执行。主进程不再是 root
- `HEALTHCHECK ... CMD python -c "... urlopen('http://127.0.0.1:8000/health')"`：引擎会定期探测。slim 镜像不一定自带 `curl`，所以用 Python 标准库访问本进程的 `/health`
- `PYTHONUNBUFFERED=1`：日志立刻出现在 `docker logs` 里，不被 Python 块缓冲挡住

再看 `.dockerignore`：README、答案、`.env`、`*.log`、虚拟环境都被排除。构建上下文越干净，构建越可预期，也越不容易把 `.env` 打进镜像。

### 步骤 2：启动，并确认不是 root

```bash
docker compose up -d --build
docker compose ps
```

预期结果：`lab08-web` 在运行。过几秒后再 `ps` 一次，STATUS 里应出现 `(healthy)`。镜像里的 HEALTHCHECK 需要一次成功的探测，所以刚启动时可能短暂显示 `health: starting`。

打开 [http://localhost:8080](http://localhost:8080)，应看到说明页。再看进程身份：

```bash
docker exec lab08-web id
docker exec lab08-web whoami
docker logs lab08-web
```

预期结果：

- `id` 里 uid 是 `1000`，用户名 `appuser`，**不是** `uid=0(root)`
- `whoami` 打印 `appuser`
- 日志开头有 `listening on 0.0.0.0:8000, uid=1000`，访问记录也在同一份日志里

如果你在容器里执行 `docker exec lab08-web cat /etc/shadow` 或类似需要特权的操作，应被拒绝。这就是非 root 的意义：即便应用被人利用，权限也小一圈。

### 步骤 3：看资源限制是否生效

`docker-compose.yml` 里写了：

```yaml
mem_limit: 256m
cpus: "0.50"
```

含义是：这个容器最多使用 256 MB 内存、相当于半颗 CPU 的时间配额。查看实际生效的值：

```bash
docker inspect -f 'Memory={{.HostConfig.Memory}} Cpus={{.HostConfig.NanoCpus}}' lab08-web
```

预期结果：`Memory=268435456`（即 256 × 1024 × 1024），`Cpus=500000000`（0.5 个 CPU，单位是 nano CPU）。

也可以在 `docker run` 时直接写（了解即可，本步不必再跑一个）：

```bash
# 示例：docker run --memory 256m --cpus 0.5 ...
```

限制要按应用实际需要来设：太小会被系统杀掉（OOM），太大就失去保护作用。256m 对这个迷你 HTTP 服务非常宽裕，只是演示写法。

关于 `deploy.resources`：那是 Swarm 风格的字段。在当前 Docker Compose 里，对普通的 `docker compose up` 而言，使用 `mem_limit` 和 `cpus` 最直接、也最不容易误解。

### 步骤 4：日志为什么不要在容器里写一份 `.log`

这个示例把访问记录 `print` 到标准输出。Docker 会收集 stdout / stderr，于是：

```bash
docker logs --tail 20 lab08-web
docker compose logs -f web
```

就能看到。这有几个好处：

- 容器删了再重建，你仍可用日志驱动或桌面界面去回顾（视配置而定），不必先 exec 进容器翻文件
- 不必在镜像里配 logrotate，也不必为日志文件单独挂卷（业务数据另说）
- 和实验 06 一样，多个服务时用 `docker compose logs -f` 就能把它们放在一起看

如果你在应用里打开 `app.log` 往磁盘写，却忘记挂卷，容器一删日志就没了；即便挂了卷，也还要自己管切割和权限。学习阶段请默认：**日志走标准输出**。

`Ctrl+C` 只停止 `logs -f` 的跟踪，不会停容器。

### 步骤 5（可选）：把同样的习惯用到留言板

`Dockerfile.guestbook` 是给实验 06 准备的改进版：非 root、HEALTHCHECK、只拷贝运行所需文件。试用步骤：

```bash
# 先停掉本实验的 8080
docker compose down

cd ../06-compose-guestbook
cp Dockerfile Dockerfile.bak
cp ../08-best-practices/Dockerfile.guestbook Dockerfile
# 如已有 .env 可直接启动；否则先 cp .env.example .env
docker compose up -d --build
docker compose ps
docker exec guestbook-web id
```

预期结果：`guestbook-web` 变为 `healthy`，`id` 显示 `appuser`。页面仍在 [http://localhost:8080](http://localhost:8080)。

还可以把下面两行加到实验 06 的 `web` 服务下，给留言板也加上资源限制：

```yaml
    mem_limit: 256m
    cpus: "0.50"
```

看完后若要恢复实验 06 原来的 Dockerfile：

```bash
cd labs/06-compose-guestbook
mv Dockerfile.bak Dockerfile
docker compose down
```

不想覆盖文件时，把改进版只当对照阅读即可。

## 小练习

请先自己做，做完再看 `answers.md`。

1. 在正在运行的 `lab08-web` 里执行 `whoami` 和 `id`。若把 Dockerfile 里的 `USER appuser` 删掉后重新构建，这两条命令会变成什么？验证完请改回去。
2. 运行 `docker inspect --format '{{json .State.Health}}' lab08-web`（必要时用 Python 或手动把 JSON 看整齐），找出最近几次探测是成功还是失败。然后访问一下 `/health`，对照 Dockerfile 里的探测命令。
3. 打开本目录的 `.dockerignore`，假设有人误把 `.env` 和一份很大的 `venv/` 放在了这个目录，没有 ignore 会发生什么？列出至少两条坏处。

## 常见坑

- **先 `USER` 再 `RUN pip install`。** 非 root 可能没权限往系统目录装包。本实验的独立示例没有 pip；留言板那份把 `useradd`、`pip install` 放在 `USER appuser` **之前**，再切用户。顺序很重要。
- **HEALTHCHECK 探测的地址写了 `localhost` 以外的、容器并没有在听的地址。** 必须探测容器**内部**进程，例如 `127.0.0.1:8000`。写宿主机的 8080 在这里没有意义。
- **HEALTHCHECK 依赖 `curl`，但 slim 镜像没装。** 本实验因此改用 `python -c "urllib.request..."`。
- **资源限制过小导致容器不断重启。** `docker ps` 会看到重启次数增加，`docker logs` 或 Docker Desktop 可能提到 OOM。把限制调回合理值，不要用这个迷你服务去「压测到死」。
- **`COPY --chown` 写在 `USER` 之后、且构建用户已不是 root。** 构建阶段改属主也可能失败。本实验把需要特权的步骤都放在 `USER` 之前。
- **以为加了 HEALTHCHECK 应用就不会挂。** 它只是「把健康状态暴露出来」。Compose、重启策略或你自己看到 `unhealthy` 之后，还需要处理原因。

## 收尾

```bash
cd labs/08-best-practices
docker compose down
docker ps
```

若你改过实验 06 的 Dockerfile，请按步骤 5 恢复。镜像 `lab08-web` 或 compose 构建出的项目镜像可以留着，也可以 `docker compose down` 之后再 `docker image prune` 清悬空层。

到这里，八个实验就走完了。你已经从第一个 `hello-world`，走到了用 Compose 运行「Web + MySQL + Redis」，并知道如何把镜像变瘦、把运行习惯收紧。之后做自己的项目时，把本目录和实验 06 当作对照即可。
