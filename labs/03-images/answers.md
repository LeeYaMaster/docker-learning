# 实验 03 练习参考答案

请先自己做，再对照这里。

## 练习 1

```bash
docker history --no-trunc lab02-hello:latest
```

通常**最大的一层（或最下面几层合计最大）来自基础镜像 `python:3.12-slim`**，也就是 Dockerfile 第一行 `FROM`。你自己的 `COPY app.py` 和 `RUN echo ...` 都非常小。

这就是为什么选择基础镜像很重要：`python:3.12`（非 slim）往往比 `python:3.12-slim` 大数百 MB，而应用代码可能只有几 KB。实验 07 会专门对比镜像体积。

## 练习 2

```bash
docker tag lab02-hello:latest lab02-hello:keep
docker rmi lab02-hello:keep
docker images lab02-hello
```

`keep` 标签消失后，只要 `latest`（或其它标签）还在，**IMAGE ID 对应的镜像还在**，磁盘上的层不会被删掉。

要真正删除这份镜像，需要去掉所有指向它的标签，并且没有容器再引用它。例如（**示范，请勿在还想保留练习镜像时执行最后一步**）：

```bash
# 假设只剩下 lab02-hello:latest（以及可能的 v1）
# docker rmi lab02-hello:v1 lab02-hello:latest
```

若仍被容器占用，先 `docker rm` 再 `docker rmi`。删掉之后，`docker images lab02-hello` 应为空。恢复方法是回到实验 02 重新构建。

请把 `lab02-hello:latest` 留着。

## 练习 3

```bash
docker inspect -f 'Cmd={{json .Config.Cmd}}' lab02-hello:latest
docker inspect -f 'ExposedPorts={{json .Config.ExposedPorts}}' lab02-hello:latest
```

预期大致为：

- `Cmd`：`["python","app.py"]`，对应 Dockerfile 的 `CMD ["python", "app.py"]`
- `ExposedPorts`：`{"8000/tcp":{}}`，对应 `EXPOSE 8000`

如果中间你改过 Dockerfile 却没重新构建，这里会仍是旧值。`inspect` 看的是镜像里已经记下的配置，不是你磁盘上那份 Dockerfile 的实时内容。
