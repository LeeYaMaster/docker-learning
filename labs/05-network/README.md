# 实验 05：容器网络

预估时间：约 30 分钟

## 本实验目标

让两个容器互相访问，并弄清「默认网络」和「自定义网络」的关键差别：

- 默认的 `bridge` 网络上，容器之间通常**不能靠名字**找到对方，往往只能用 IP（不推荐当日常做法）
- 你自己创建的桥接网络带有内置 DNS：用**容器名**就能互访
- 不在同一网络里的容器，即使你知道名字，也访问不到

为什么要练这个？实验 06 的留言板里，Web 容器会用主机名 `db`、`redis` 去连 MySQL 和 Redis。那不是魔法，而是 Compose 为这组服务创建了自定义网络。本实验把这件事拆开，用手敲命令看一遍。

本实验用 `alpine:3.20` 和 `nginx:1.27-alpine`。alpine 自带 `ping` 和 `wget`，不必再装其它镜像。

## 准备工作

任意目录都可以执行本实验命令。建议先进入本目录对照 README：

```bash
cd labs/05-network
```

若 8080 仍被占用，先清掉相关容器。本实验主要在容器之间互访，只有可选步骤会用到 8080。

先看一眼 Docker 自带的网络：

```bash
docker network ls
```

预期结果：至少有 `bridge`、`host`、`none`。本实验只涉及 `bridge` 和我们自己建的桥接网络。`host` 与 `none` 先不用管。

## 动手步骤

### 步骤 1：默认 bridge 上，名字往往走不通

先在默认网络上启动一个 nginx，再另起一个 alpine 去 ping 它的名字：

```bash
docker run -d --name lab05-web-default nginx:1.27-alpine
docker run --rm --name lab05-client-default alpine:3.20 ping -c 3 lab05-web-default
```

预期结果：`ping` **失败**，提示类似于 `bad address 'lab05-web-default'` 或无法解析主机名。这就是默认 `bridge` 的典型现象：容器之间没有「用名字找人」的 DNS。

再看看它的 IP，用 IP 可以通（用来对比，日常不要靠记 IP）：

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' lab05-web-default
```

把下面的 `IP` 换成你看到的地址（常见类似 `172.17.0.2`）：

```bash
docker run --rm alpine:3.20 ping -c 3 IP
```

预期结果：这次 ping 能通。所以默认网络上并非完全隔离，只是**没有好用的名字解析**。IP 会变，不适合写进应用配置。

先把这个 nginx 留着，后面对比完再删。也可以先删：

```bash
docker rm -f lab05-web-default
```

### 步骤 2：创建自定义网络，用容器名互访

```bash
docker network create lab05-net
docker network ls
```

预期结果：列表里出现 `lab05-net`，驱动一般是 `bridge`。它和默认那个 `bridge` 不是同一张网。

把服务放进这张网（用 `--network`），并再启动一个短暂的客户端去访问：

```bash
docker run -d --name lab05-web --network lab05-net nginx:1.27-alpine

docker run --rm --network lab05-net alpine:3.20 ping -c 3 lab05-web
```

预期结果：`ping` **成功**，三轮都有回复。注意目的主机写的是容器名 `lab05-web`，没有写 IP。

再用 HTTP 访问一下 nginx 默认页面（alpine 里用 `wget`）：

```bash
docker run --rm --network lab05-net alpine:3.20 wget -qO- http://lab05-web/
```

预期结果：终端打印出 nginx 欢迎页的 HTML，里面有 `Welcome to nginx!`。这说明同一自定义网络里，不仅 ping 得通，应用端口也可以用 `http://容器名/` 访问（nginx 听在 80，所以 URL 里不必写端口）。

这就是容器名 DNS。实验 06 里 Flask 连接 `db:3306`、`redis:6379`，依据的就是同一机制。

### 步骤 3：看清网络里都有谁

```bash
docker network inspect lab05-net
```

预期结果：`Containers` 一段里能看到 `lab05-web` 以及它的 IPv4 地址。已经退出的 `--rm` 客户端不会留在这里。

也可以让客户端挂起一会儿再 inspect，观察两个容器同时在网上：

```bash
docker run -d --name lab05-client --network lab05-net alpine:3.20 sleep 3600
docker network inspect lab05-net
docker exec lab05-client ping -c 2 lab05-web
docker rm -f lab05-client
```

预期结果：inspect 里同时出现两个容器；`exec` 里的 ping 成功。

### 步骤 4：不在同一网络，名字再对也走不通

再创建一个网络，把另一个客户端只放进去：

```bash
docker network create lab05-other
docker run --rm --network lab05-other alpine:3.20 ping -c 3 lab05-web
```

预期结果：ping 失败（无法解析或不可达）。`lab05-web` 在 `lab05-net` 上，这个客户端在 `lab05-other` 上，两张网默认不互通。

这是一个有用的隔离特性：不想让某两个容器互相访问，就不要把它们放进同一网络。Compose 会给「同一份 compose 文件里的服务」默认连到同一项目网络，所以它们能互相解析；其它项目的容器不会自动进来。

### 步骤 5（可选）：从你的浏览器访问自定义网络里的 nginx

自定义网络解决的是**容器到容器**的访问。你的浏览器在宿主机上，仍需要端口映射：

```bash
docker rm -f lab05-web
docker run -d --name lab05-web --network lab05-net -p 8080:80 nginx:1.27-alpine
```

打开 [http://localhost:8080](http://localhost:8080)，应看到欢迎页。

记住两套路径：

- 宿主机 / 浏览器 → 需要 `-p`
- 同一自定义网络里的其它容器 → 用 `http://容器名:容器端口`，不用走宿主机端口

## 小练习

请先自己做，做完再看 `answers.md`。

1. 在 `lab05-net` 上再启动一个名为 `lab05-web2` 的 nginx。在同一个网络里的 alpine 容器中，分别 `wget` `http://lab05-web/` 和 `http://lab05-web2/`，确认两个名字都能解析。
2. 故意把 alpine 放到 `lab05-other`，再去 `wget http://lab05-web/`，把你看到的失败信息记下来。
3. 用 `docker network inspect lab05-net`，找出 `lab05-web` 的 IP。思考：把这个 IP 写进应用配置，有什么缺点？

## 常见坑

- **忘记 `--network`，容器又回到了默认 `bridge`。** 之后用名字 ping 就会失败。`docker inspect -f '{{json .NetworkSettings.Networks}}' 容器名` 可以确认它在哪张网上。
- **容器名写错。** DNS 解析的是容器名（或你额外加的 `--network-alias`），不是镜像名。
- **ping 通但 wget/curl 失败。** 先确认对方进程确实在听那个端口。例如 alpine 默认没有 HTTP 服务；本实验是 wget 去访问 nginx。
- **从宿主机用容器名访问。** 你的 Mac 终端一般解析不了 `lab05-web` 这个名字。容器名 DNS 只作用于加入了同一 Docker 网络的容器。宿主机请继续用 `localhost:映射端口`。
- **网络或容器名冲突。** 上次实验没清干净时，`docker network create lab05-net` 或 `--name lab05-web` 会报 already exists。用 `docker network ls`、`docker ps -a` 检查后删掉即可。
- **alpine 里没有 `ping`？** 本实验指定的 `alpine:3.20` 带有 busybox 的 ping。若你换成了极简到没有 ping 的镜像，改用 `wget` 即可。

## 收尾

```bash
docker rm -f lab05-web lab05-web2 lab05-web-default lab05-client lab05-client-default 2>/dev/null || true
docker network rm lab05-net lab05-other 2>/dev/null || true
docker network ls
docker ps
```

预期结果：本实验的容器和自定义网络都已去掉，默认的 `bridge` / `host` / `none` 还在。8080 已释放，可以进入实验 06。
