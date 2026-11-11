# 实验 01 练习参考答案

请先自己做，再对照这里。下面只是一种靠谱写法，你的命令在细节上可以不同，只要现象对得上就好。

## 练习 1

让 alpine 在后台一直运行，常见写法是让它 `sleep` 足够久：

```bash
docker run -d --name lab01-alpine alpine:3.20 sleep 3600
docker exec lab01-alpine uname -a
docker rm -f lab01-alpine
```

预期：`uname -a` 会打印一行 Linux 内核信息（注意是容器里的 Linux，不是 macOS）。`docker rm -f` 会先停再删。

如果不加类似 `sleep` 的前台命令，alpine 默认的 `sh` 在没有终端时会立刻退出，你会发现容器创建完就已经是 `Exited`，这时 `docker exec` 会失败。

## 练习 2

```bash
docker run -d --name lab01-nginx-8081 -p 8081:80 nginx:1.27-alpine
```

浏览器打开 [http://localhost:8081](http://localhost:8081)，应看到同样的 nginx 欢迎页。

`-p` 的左边是宿主机端口，右边是容器端口。容器里的 nginx 仍然听 80，只是你从 Mac 访问时改走 8081。

```bash
docker rm -f lab01-nginx-8081
```

## 练习 3

```bash
docker run -d alpine:3.20 echo bye
docker ps -a
```

没有 `--name` 时，Docker 会分配一个随机名字（例如 `funny_einstein`），同时每个容器都有一个 ID（例如 `a1b2c3d4e5f6`，`docker ps` 默认显示短 ID）。

`docker logs`、`docker rm` 既可以跟名字，也可以跟 ID（短 ID 即可）：

```bash
docker logs <容器ID或随机名字>
docker rm <容器ID或随机名字>
```

给常用的、要反复操作的容器起名字，会轻松很多；一次性容器用 ID 或 `--rm` 都很常见。
