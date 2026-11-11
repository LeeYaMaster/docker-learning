# 实验 03：镜像管理

预估时间：约 25 分钟

## 本实验目标

弄清楚「镜像」在本机是怎么被命名、查看和清理的。你会用到：

- `docker tag`：给镜像起别名
- `docker history`：看一层层是怎么堆起来的
- `docker inspect`：查看镜像的详细配置
- 分层原理（简要）：为什么调整 Dockerfile 指令顺序能影响构建速度
- 如何清理不再需要的镜像，同时避免误删

为什么单独做这一实验？容器是用镜像创建出来的「一次运行」；镜像才是被保存、打标签、分发的那一份产物。管理不好，本机很快会堆满 `<none>` 镜像，或者你改了标签却不知道到底有没有删掉数据。

本实验**复用实验 02 构建的 `lab02-hello` 镜像**，不再写一套新应用。如果镜像不在了，下面「准备工作」里有一条重新构建的命令。

## 准备工作

任意目录都可以执行本实验的查看类命令。若需要重新构建 02 的镜像，则必须进入 `labs/02-dockerfile`。

先确认镜像还在：

```bash
docker images lab02-hello
```

预期结果：至少有一条 `lab02-hello`，标签通常是 `latest`。

若什么都没有，先构建一次：

```bash
cd labs/02-dockerfile
docker build -t lab02-hello:latest .
```

## 动手步骤

### 步骤 1：给镜像打上更多标签

```bash
docker tag lab02-hello:latest lab02-hello:v1
docker tag lab02-hello:latest lab02-hello:experiment
docker images lab02-hello
```

预期结果：同一镜像出现多行，**IMAGE ID 完全相同**，只是仓库名/标签不同。`docker tag` 不会复制一份新的文件系统，只是新增一个名字指向同一份镜像。

这也是为什么「给镜像起一个清楚的名字和版本标签」很有用：你可以用 `lab02-hello:v1` 跑昨天的版本，用 `lab02-hello:latest` 跑今天刚构建的版本。当它们还指向同一个 ID 时，两者其实是同一个东西；只有重新 `docker build -t lab02-hello:latest` 之后，`latest` 才会指向新构建的 ID，而 `v1` 仍指向旧的那一份。

### 步骤 2：用 history 看分层

```bash
docker history lab02-hello:latest
```

预期结果：会列出一串层，从下往上（最下面通常是基础镜像 `python:3.12-slim` 相关的层，上面是你 Dockerfile 里的 `WORKDIR`、`COPY`、`RUN`、`CMD` 等）。每一层都有大小。有些层显示 `0B`，并不代表指令没执行，而是没有新增文件（例如某些 `WORKDIR`、`EXPOSE`、`CMD` 只是改了配置）。

想看完整命令（不被截断）：

```bash
docker history --no-trunc lab02-hello:latest
```

对照你在实验 02 写的 Dockerfile，试着把每一层和指令对上。这能帮你建立直觉：镜像不是一个神秘的大文件，而是一层层叠起来的文件系统快照，再加上一点启动配置（CMD、环境变量、暴露端口等）。

### 步骤 3：用 inspect 看配置

```bash
docker inspect lab02-hello:latest
```

输出是一段比较长的 JSON。可以先别逐行读，用格式化取值看看几个关键字段：

```bash
docker inspect -f 'Id={{.Id}}' lab02-hello:latest
docker inspect -f 'Cmd={{json .Config.Cmd}}  WorkDir={{.Config.WorkingDir}}  ExposedPorts={{json .Config.ExposedPorts}}' lab02-hello:latest
```

预期结果：

- `Cmd` 类似 `["python","app.py"]`，和 Dockerfile 里的 `CMD` 一致
- `WorkDir` 为 `/app`
- `ExposedPorts` 里有 `8000/tcp`

`inspect` 对镜像和容器都能用。对容器再 `inspect` 一次，还能看到网络、挂载点、实际运行状态。需要查「它到底听哪个端口、工作目录在哪、环境变量是什么」时，这是最直接的方法。

### 步骤 4：分层原理（简要）

理解下面三句话就够用了：

1. **一条指令通常对应一层**（`FROM`、`COPY`、`RUN` 等）。下层改了，它上面的层都要重新构建。
2. **构建缓存**会复用没变化的层。所以要把「不常变的步骤」放在前面，把「经常改的代码」放在后面。例如先复制 `requirements.txt` 并 `pip install`，再复制源代码——只改了业务代码时，不必重装依赖。
3. **容器可写层**加在镜像只读层之上。容器里改的文件默认只属于这个容器，删掉容器这些改动就没了（除非用了卷，那是实验 04 的主题）。

可以用一次「改文档 vs 改 app.py」来感受缓存（可选，在 `labs/02-dockerfile` 目录）：

```bash
cd labs/02-dockerfile
docker build -t lab02-hello:latest .
```

什么都不改再构建一次，预期结果：大部分步骤显示 `CACHED`，很快结束。

然后只改 `app.py` 里一个字，再 build。预期结果：`COPY app.py` 及之后的层会重新执行，它之前的层（`FROM`、`WORKDIR` 等）仍然命中缓存。

### 步骤 5：观察悬空镜像，并做安全的清理

先制造一个常见场景：重新构建并打同一个标签后，旧镜像可能变成「没有名字、只有 ID」，也就是悬空（dangling）镜像，列表里仓库名和标签常显示为 `<none>`。

```bash
docker images -f dangling=true
```

如果你刚刚重新构建过 `lab02-hello:latest`，而旧的那份已经没有其它标签（例如练习里的 `v1` 也不再指向它），这里就可能出现 `<none>`。没有也没关系，不必强行制造。

清理**悬空**镜像（没有标签、也不被容器使用的）：

```bash
docker image prune
```

它会先询问确认。预期结果：删除的是 `<none>` 那些，**不会**删掉你仍然引用着的 `lab02-hello:latest`。

下面这条更猛，本实验**先不要执行**，只需要认识它：

```bash
# 不要现在跑：会试图删掉所有「没有被容器使用」的镜像，包括 alpine、nginx、lab02-hello
# docker image prune -a
```

删除某一个标签：

```bash
docker rmi lab02-hello:experiment
docker images lab02-hello
```

预期结果：`experiment` 这个名字没了。如果 `latest` / `v1` 还指向同一个 IMAGE ID，镜像本身还在。

若提示镜像正在被容器使用而无法删除，先停并删掉那个容器，再 `docker rmi`。

请保留 `lab02-hello:latest`，后面偶尔还会提到它；`experiment` 标签删掉即可。`v1` 你可以从练习里自己决定去留。

## 小练习

请先自己做，做完再看 `answers.md`。

1. 用 `docker history --no-trunc lab02-hello:latest` 找出体积明显比较大的层。它通常对应什么？（提示：想想基础镜像。）
2. 给 `lab02-hello:latest` 再打一个 `lab02-hello:keep`，然后执行 `docker rmi lab02-hello:keep`。用 `docker images` 确认：镜像的文件系统还在吗？怎样才能真正删掉这份镜像？**请不要真的把 `lab02-hello:latest` 删掉**，说清楚步骤即可。
3. 用 `docker inspect` 取出 `lab02-hello` 的 `Cmd` 和 `ExposedPorts`，写下来，和 Dockerfile 对照。

## 常见坑

- **把 tag 当成「复制」。** 两个标签、同一个 ID，占的是同一份磁盘。只有构建出不同 ID，才是两份内容。
- **`docker rmi 仓库:标签` 只是去掉一个名字。** 还有其它标签时，镜像不会消失。
- **`docker image prune -a` 太猛。** 日常清理优先用 `docker image prune`（只清悬空的），或精确 `docker rmi`。
- **误删了 `lab02-hello`。** 回到 `labs/02-dockerfile` 重新 `docker build -t lab02-hello:latest .` 即可，几分钟就能恢复。
- **`<none>` 不一定都是垃圾。** 有时它们仍被某个容器引用。`prune` 不会删除正在使用的镜像；若 `rmi` 失败，先检查 `docker ps -a`。

## 收尾

本实验不必长期占用端口。若你为了验证又启动了容器，清掉即可：

```bash
docker ps -a --filter ancestor=lab02-hello
# 如有残留容器：docker rm -f <名字或ID>
```

保留 `lab02-hello:latest` 镜像没有坏处。
