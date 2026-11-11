# 实验 02：第一个 Dockerfile

预估时间：约 35 分钟

## 本实验目标

自己写一份 Dockerfile，把一个很小的 Python HTTP 服务打成镜像，再运行起来，用浏览器打开。

为什么要自己构建？`docker run nginx` 用的是别人做好的镜像。真正做项目时，你得把自己的代码、依赖和启动命令打包进去。Dockerfile 就是这份「如何从基础镜像变成我的应用镜像」的说明书。

本实验会用到这些指令：

- `FROM`：选基础镜像
- `WORKDIR`：设置工作目录
- `COPY`：把文件放进镜像
- `RUN`：在构建时执行命令（结果成为新的一层）
- `EXPOSE`：声明容器内端口
- `CMD`：容器启动时默认执行什么

另外会写一份 `.dockerignore`，以及用 `docker build` 和 `docker run -p` 跑起来。

服务本身只用 Python 标准库，没有第三方依赖，这样你可以专心看 Dockerfile，而不是被 pip 分心。

## 准备工作

请在本实验目录执行后续的 `docker build`，否则 Docker 找不到 `Dockerfile` 和 `app.py`：

```bash
cd labs/02-dockerfile
ls
```

预期结果：能看到 `Dockerfile`、`app.py`、`.dockerignore`、`README.md`。

先随意看一眼 `app.py` 和 `Dockerfile`，建立个印象再构建。应用会在容器内监听 `8000` 端口；我们稍后用 `-p 8080:8000` 映射到宿主机的 8080。

## 动手步骤

### 步骤 1：认识 Dockerfile 里的每一行

打开 `Dockerfile`，对照下面这份说明：

| 指令 | 这份文件里做什么 |
|------|------------------|
| `FROM python:3.12-slim` | 从带有 Python 3.12 的官方瘦身镜像开始。标签写成 `3.12-slim`，构建可重复，不会在某天突然变成另一个大版本 |
| `WORKDIR /app` | 之后的 `COPY`、`RUN`、`CMD` 都以 `/app` 为当前目录。目录不存在时会自动创建 |
| `COPY app.py .` | 把构建上下文里的 `app.py` 复制到 `/app/app.py` |
| `RUN echo ...` | 在**构建阶段**执行，生成 `/app/build-info.txt`。这是为了让你亲眼看到「RUN 的结果被写进镜像」 |
| `EXPOSE 8000` | 声明应用监听 8000。它不会自动帮你做端口映射 |
| `CMD ["python", "app.py"]` | 容器启动时执行的默认命令。JSON 数组形式（exec 形式）更适合作为主进程 |

构建上下文（context）默认是你在 `docker build` 后面写的那个目录（本实验是 `.`）。Docker 会把这个目录发给引擎，`COPY` 只能取到上下文里的文件。不想把 README、缓存目录也送进去，就靠 `.dockerignore`。

打开 `.dockerignore` 看一眼：这里排除了说明文档、`.git`、Python 缓存等。即便当前 Dockerfile 只 `COPY app.py`，养成写 `.dockerignore` 的习惯仍然很重要——下一步若改成 `COPY . .`，忽略名单就会立刻派上用场。

### 步骤 2：构建镜像

仍在 `labs/02-dockerfile` 目录：

```bash
docker build -t lab02-hello:latest .
```

- `-t lab02-hello:latest`：给镜像起名并打标签，格式是 `名字:标签`
- 最后的 `.`：构建上下文是当前目录，Docker 会在这里找默认的 `Dockerfile`

预期结果：终端按步骤输出每一层的构建过程（`FROM`、`WORKDIR`、`COPY`、`RUN`……），最后出现类似 `Successfully tagged lab02-hello:latest` 的提示。再执行：

```bash
docker images lab02-hello
```

应能看到刚刚打好的镜像。体积通常大约一百多 MB（slim 基础镜像本身就占了大部分），这是正常的。

若构建失败，先看报错指向哪一步：找不到 `app.py` 多半是当前目录不对；语法错误则对照仓库里的 `Dockerfile`。

### 步骤 3：运行，并在浏览器里打开

```bash
docker run -d --name lab02-web -p 8080:8000 lab02-hello:latest
docker ps
```

预期结果：容器状态为 `Up`，PORTS 为 `0.0.0.0:8080->8000/tcp`。注意映射方向：宿主机 8080，容器内 8000（和 `EXPOSE`、`app.py` 里的端口一致）。

打开 [http://localhost:8080](http://localhost:8080)。

预期结果：页面上有「你好，我来自容器里的 Python。」这类中文说明。若打不开，先看日志：

```bash
docker logs lab02-web
```

预期结果：有一行 `listening on 0.0.0.0:8000`，访问过后还会出现 GET 访问记录。

### 步骤 4：验证构建时的 RUN 真的写进了镜像

```bash
docker exec lab02-web cat /app/build-info.txt
docker exec lab02-web ls -l /app
```

预期结果：读到 `lab02 image built`。这个文件不是容器运行时才创建的，而是构建镜像时 `RUN` 留下来的。新启动的每一个基于该镜像的容器里都会有它。

### 步骤 5：体会 EXPOSE 和 `-p` 的差别

`EXPOSE 8000` 只是声明。如果运行时忘记 `-p`，容器内服务照样启动，但你的浏览器访问不了。

可以（可选）再开一个对照容器验证，注意换一个名字，并且不要抢 8080：

```bash
docker run -d --name lab02-no-publish lab02-hello:latest
docker logs lab02-no-publish
```

预期结果：日志同样有 `listening on 0.0.0.0:8000`，但 `docker ps` 的 PORTS 里没有 `0.0.0.0:....->8000`。本机浏览器访问 8000 或 8080 都不会打到这个容器（8080 此时仍属于 `lab02-web`）。

看完即可删掉它：

```bash
docker rm -f lab02-no-publish
```

要用浏览器访问，必须在 `docker run` 时写 `-p`，或后面用更完整的发布方式。`EXPOSE` 不能代替 `-p`。

### 步骤 6：改代码后必须重新构建

用编辑器把 `app.py` 里的标题改一个字，例如改成「你好，这是我改过的页面。」保存后，**先不要急着重跑容器**，直接：

```bash
docker stop lab02-web && docker rm lab02-web
docker run -d --name lab02-web -p 8080:8000 lab02-hello:latest
```

打开浏览器（必要时强制刷新）。

预期结果：页面**没有变**。因为你运行的还是旧镜像。改了构建上下文里的文件之后，需要重新 `docker build`：

```bash
docker build -t lab02-hello:latest .
docker rm -f lab02-web
docker run -d --name lab02-web -p 8080:8000 lab02-hello:latest
```

再刷新浏览器，这次应看到新文案。这是初学者最常见的「我改了怎么没效果」——改的是源代码，跑的是旧镜像。

看完后可以把文案改回去，再 build 一次，也可以就留着你的版本。

## 小练习

请先自己做，做完再看 `answers.md`。

1. 给同一个镜像再打一个标签 `lab02-hello:v1`（提示：`docker tag`），用 `docker images` 观察：这是两个镜像还是同一个镜像的两个名字？
2. 在 Dockerfile 里加一行 `LABEL maintainer="你的名字"` 或 `ENV APP_ENV=dev`，重新构建后，用 `docker exec` 或 `docker inspect` 验证它生效了。
3. 临时把 `.dockerignore` 里对 `README.md` 的忽略去掉，并把 Dockerfile 的 `COPY app.py .` 改成 `COPY . .`，构建一次。用 `docker exec lab02-web ls /app` 看看 README 是否进了镜像。观察完请改回原来的写法并重新构建，避免后面的实验被这份改动干扰。

## 常见坑

- **在错误的目录执行 `docker build`。** 必须在包含 `Dockerfile` 和 `app.py` 的 `labs/02-dockerfile` 目录，最后的 `.` 才有意义。
- **`-p 8080:8000` 写反。** 左边是宿主机，右边是容器。写成 `-p 8000:8080` 时，浏览器访问 8080 会对不上。
- **应用听在 `127.0.0.1` 而不是 `0.0.0.0`。** 本实验的 `app.py` 已经写成 `0.0.0.0`。若你自己改服务时绑到 `127.0.0.1`，容器内只有自己能访问，端口映射进来也会失败。
- **改了代码却只重启容器。** 镜像不会自动更新，需要重新 `docker build`，再用新镜像创建容器。
- **容器名冲突或 8080 被占用。** 先 `docker rm -f lab02-web`，并确认实验 01 的 nginx 已经清掉。

## 收尾

后面的实验 03 会复用 `lab02-hello` 这个镜像，请**保留镜像**，只关掉容器、放出 8080 即可：

```bash
docker rm -f lab02-web lab02-no-publish 2>/dev/null || true
docker images lab02-hello
```

预期结果：容器已删除，镜像 `lab02-hello` 仍在。
