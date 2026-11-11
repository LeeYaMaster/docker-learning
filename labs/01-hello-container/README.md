# 实验 01：初识容器

预估时间：约 25 分钟

## 本实验目标

第一次把容器跑起来，走完它最常见的一生：启动、查看、看日志、走进去执行命令、停掉、删除。顺带看一眼本机有哪些镜像。

为什么先做这个？因为后面所有 Dockerfile、数据卷、网络、Compose，都建立在「容器是一个正在运行（或已经退出）的进程」这件事上。先把这组命令摸熟，后面不会在基本操作上卡住。

本实验使用现成的官方镜像，还不用自己写 Dockerfile：

- `hello-world:latest`：跑一下就退出，用来确认 Docker 工作正常
- `alpine:3.20`：很小的 Linux 环境，适合练 `exec` 和一次性命令
- `nginx:1.27-alpine`：启动一个网页服务，用浏览器打开 `http://localhost:8080`

## 准备工作

任意目录都可以执行本实验的命令（我们只用官方镜像，不依赖本目录里的文件）。建议先进入本实验目录，方便你对照 README：

```bash
cd labs/01-hello-container
```

若上面的路径报「没有那个文件或目录」，先 `cd` 到本项目根目录（有顶层 `README.md` 的那个目录）再执行。

请确认 Docker Desktop 已在运行：

```bash
docker version
```

预期结果：能看到 Client 和 Server 两段版本信息。如果只有 Client、报无法连接引擎，先启动 Docker Desktop，等它完全起来后再试。

## 动手步骤

### 步骤 1：跑通 hello-world

```bash
docker run --rm hello-world:latest
```

第一次执行会先下载镜像，需要一点时间。`--rm` 表示容器退出后自动删除，避免留下一次性的退出容器。

预期结果：终端打印一段英文说明，大意是「你的安装看起来正常」。这段文字来自容器里的程序，不是 Docker 自己编的。这个容器做完一件事就退出了，所以它不会一直留在后台。

### 步骤 2：看本机镜像和容器

```bash
docker images
docker ps
docker ps -a
```

预期结果：

- `docker images`（也可以写成 `docker image ls`）里会出现 `hello-world`，TAG 为 `latest`。
- `docker ps` 只列出**正在运行**的容器。刚才那个已经退出而且加了 `--rm`，这里通常是空的（或只有你本来就在跑的容器）。
- `docker ps -a` 会连同已退出的容器一起列出。因为用了 `--rm`，hello-world 一般不会出现在这里。

记住这对组合：`ps` 看活着的，`ps -a` 看全部。

### 步骤 3：用 alpine 执行一条命令

```bash
docker run --rm alpine:3.20 echo "hello from alpine"
```

预期结果：先拉镜像（若本地还没有），然后打印 `hello from alpine`。容器里默认的工作环境是一个很小的 Linux，`echo` 在里面执行完，容器就退出了。

再试一条，看看容器里的主机名和发行信息：

```bash
docker run --rm alpine:3.20 sh -c "hostname; cat /etc/os-release"
```

预期结果：会打印一个看起来像随机 ID 的主机名，以及 Alpine Linux 的版本信息。这个主机名就是容器的主机名，和你的 Mac 主机名不是一回事。

### 步骤 4：在后台启动 nginx，用浏览器打开

```bash
docker run -d --name lab01-nginx -p 8080:80 nginx:1.27-alpine
```

参数说明（请对照着记，后面会反复用到）：

- `-d`：后台运行（detached）
- `--name lab01-nginx`：给容器起一个好记的名字，后面的 `logs` / `exec` / `stop` 都可以用这个名字
- `-p 8080:80`：把**宿主机**的 8080 端口映射到**容器内** nginx 监听的 80 端口

```bash
docker ps
```

预期结果：能看到名为 `lab01-nginx` 的容器，状态是 `Up`，PORTS 一栏类似 `0.0.0.0:8080->80/tcp`。

打开浏览器访问 [http://localhost:8080](http://localhost:8080)。

预期结果：看到 nginx 的欢迎页，大标题一般是 **Welcome to nginx!**。这说明：请求打到了你的 Mac 的 8080，Docker 把它转发进了容器的 80 端口。

### 步骤 5：看日志

```bash
docker logs lab01-nginx
docker logs --tail 20 lab01-nginx
```

预期结果：能看到 nginx 的访问日志。如果你刚才用浏览器打开过，这里通常会出现对 `/` 的 GET 记录。`--tail 20` 只看最后 20 行，日志多的时候很有用。

想持续跟踪日志，可以再开一个终端执行 `docker logs -f lab01-nginx`，用 `Ctrl+C` 只是停止跟踪，不会把容器停掉。

### 步骤 6：走进容器执行命令

```bash
docker exec lab01-nginx ls /usr/share/nginx/html
docker exec lab01-nginx cat /usr/share/nginx/html/index.html
```

预期结果：列出 nginx 默认网页目录里的文件（至少有 `index.html`），然后打印出欢迎页的 HTML。

`exec` 是在**已经在运行的容器**里再启动一个进程。它和 `docker run` 不同：`run` 是用镜像新建一个容器，`exec` 是进入现有容器。

也可以开一个交互式 shell 看看（用完输入 `exit` 退出即可，容器不会因此停止）：

```bash
docker exec -it lab01-nginx sh
```

`-it` 是「分配伪终端 + 保持标准输入」，交互式命令一般都要加。在这个 shell 里可以执行 `pwd`、`ls`、`hostname`，输入 `exit` 回到你的 Mac 终端。

### 步骤 7：停止并删除容器

```bash
docker stop lab01-nginx
docker ps
docker ps -a
```

预期结果：`docker stop` 之后，`docker ps` 里看不到它了；`docker ps -a` 里还能看到，状态是 `Exited`。停止不等于删除。

```bash
docker rm lab01-nginx
docker ps -a
```

预期结果：名为 `lab01-nginx` 的容器消失。镜像还在，只是这个容器实例被删掉了。

以后也可以写成一条：`docker rm -f lab01-nginx`（先停再删）。养成「用完清理」的习惯，避免下次再跑同名容器时报名字冲突，或 8080 被占用。

### 步骤 8：再看一眼本机镜像

```bash
docker images
```

预期结果：至少能看到本次用过的 `hello-world`、`alpine`、`nginx`。镜像删不删随你。本实验**先不要** `docker rmi` 它们，实验 03 还会谈到如何安全清理。即使你删了某个容器，镜像仍可用来再 `docker run` 出新容器。

## 小练习

请先自己做，做完再看同目录的 `answers.md`。

1. 用 `alpine:3.20` 启动一个**后台**容器，名字叫 `lab01-alpine`，让它持续运行（提示：`sleep` 可以帮你）。然后用 `docker exec` 在里面执行 `uname -a`，最后把它删掉。
2. 再次启动 nginx，但把宿主机端口改成 **8081**（容器内仍是 80）。用浏览器确认能打开，然后清理容器。
3. 不指定 `--name` 再 `docker run -d` 一个会退出的容器（例如 `alpine:3.20 echo bye`，不要加 `--rm`）。用 `docker ps -a` 找到它，思考：没有名字时你该用什么来 `docker logs` / `docker rm`？

## 常见坑

- **`port is already allocated`。** 8080 被占用。先 `docker ps` 看是不是还有上次的 nginx，有就 `docker stop` 再 `docker rm`。
- **`Conflict. The container name "/lab01-nginx" is already in use`。** 同名容器还在（包括已退出但未删除的）。用 `docker ps -a` 找它，`docker rm` 或 `docker rm -f` 删掉再跑。
- **浏览器打不开，但 `docker ps` 显示是 Up。** 先确认你访问的是 `http://localhost:8080`（不是 https，也不是容器内的 80）。再 `docker logs lab01-nginx` 看有没有报错。
- **`docker exec` 报 not running。** 只能对正在运行的容器 exec。先 `docker ps` 确认状态是 Up。
- **交互式忘了加 `-it`。** `docker exec lab01-nginx sh` 可能会立刻退出或看起来「卡住没提示符」。加上 `-it`。

## 收尾

如果还留着本实验的容器，清理掉，把 8080 腾出来给后面的实验：

```bash
docker rm -f lab01-nginx lab01-alpine 2>/dev/null || true
docker ps
```

镜像可以保留，后面还会用到 alpine 和 nginx。
