# 实验 02 练习参考答案

请先自己做，再对照这里。

## 练习 1

```bash
docker tag lab02-hello:latest lab02-hello:v1
docker images lab02-hello
```

你会看到 `lab02-hello` 有 `latest` 和 `v1` 两行，但 **IMAGE ID 相同**。`docker tag` 并没有复制一份新镜像，只是给同一个镜像加了一个新名字。

删掉其中一个标签（例如 `docker rmi lab02-hello:v1`）后，另一个标签仍在，镜像也还在。只有指向它的标签（以及未打标签的引用）都去掉了，镜像才可能被真正删除。实验 03 还会再练这个现象。

若你做完练习想保持干净，可以保留 `lab02-hello:latest`，删掉 `v1` 标签：

```bash
docker rmi lab02-hello:v1
```

## 练习 2

在 Dockerfile 里 `FROM` 之后任意合适位置加上，例如：

```dockerfile
LABEL maintainer="levi"
ENV APP_ENV=dev
```

然后在 `labs/02-dockerfile` 目录重新构建并运行（若 `lab02-web` 还在，先删掉）：

```bash
docker build -t lab02-hello:latest .
docker rm -f lab02-web
docker run -d --name lab02-web -p 8080:8000 lab02-hello:latest
docker exec lab02-web sh -c 'echo APP_ENV=$APP_ENV'
docker inspect -f '{{.Config.Labels}} {{.Config.Env}}' lab02-web
```

预期：`APP_ENV=dev` 会出现在环境变量里；`inspect` 的 Labels 里能看到 `maintainer`。

验证完可以把这两行留着，也可以删掉后重新 build，恢复成仓库里的版本。实验 03 只要镜像还叫 `lab02-hello` 即可。

## 练习 3

`.dockerignore` 不再忽略 `README.md`，并且：

```dockerfile
COPY . .
```

重新构建并运行后：

```bash
docker exec lab02-web ls -l /app
```

这时 `/app` 下除了 `app.py`、`build-info.txt`，还会出现 `README.md`、`answers.md`、`Dockerfile` 等。它们对运行服务没有帮助，却增加了镜像内容和构建上下文的传输量。

这就是 `.dockerignore` 的意义：构建上下文默认会带上目录里的很多文件，你应该只让需要的文件参与构建。

请改回：

```dockerfile
COPY app.py .
```

并在 `.dockerignore` 中重新忽略 `README.md` 与 `answers.md`，然后：

```bash
docker build -t lab02-hello:latest .
```

若容器还在跑旧层，记得删掉重建，避免后面检查时看到残留文件。
