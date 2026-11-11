# 实验 07：多阶段构建

预估时间：约 30 分钟

## 本实验目标

用**同一份小应用**各构建一次单阶段镜像和多阶段镜像，然后对比体积。你会看到：最终跑应用并不需要把编译器和较胖的基础镜像一起带上。

为什么要学这个？镜像越大，拉取越慢，攻击面也往往越大。多阶段构建（multi-stage build）允许你在「构建阶段」用比较完整的环境安装依赖，再把真正需要的文件拷进一个瘦的「运行阶段」。

本实验提供两份 Dockerfile：

- `Dockerfile.single`：一切都在一个阶段里，基础镜像是完整的 `python:3.12`，并且安装了 `gcc`
- `Dockerfile.multi`：先在 `builder` 阶段安装依赖，再把虚拟环境拷进 `python:3.12-slim`

应用仍然很小：一个 Flask 页面，听在容器内 8000 端口。重点是构建方式，不是业务。

## 准备工作

请在本实验目录执行构建命令：

```bash
cd labs/07-multistage
ls
```

预期结果：能看到 `Dockerfile.single`、`Dockerfile.multi`、`app.py`、`requirements.txt`、`.dockerignore`。

若 8080 被占用，先清掉占用它的容器。本实验验证运行时会用到 8080。

## 动手步骤

### 步骤 1：先看两份 Dockerfile 的差别

打开它们对照着看。关键差异只有几处：

| | 单阶段 | 多阶段 |
|--|--------|--------|
| 基础镜像 | `python:3.12`（完整 Debian，体积更大） | 运行阶段用 `python:3.12-slim` |
| 编译器 gcc | 装在最终镜像里 | 只出现在 `builder` 阶段，最终镜像没有 |
| 依赖安装 | 直接 `pip install` 到系统路径 | 装进 `/opt/venv`，再用 `COPY --from=builder` 拷走 |
| 构建指令 | 一个 `FROM` | 两个 `FROM`，第一段命名为 `builder` |

`COPY --from=builder /opt/venv /opt/venv` 的意思是：不要从构建上下文里拷，而从名为 `builder` 的那一阶段已经产生的文件里拷。这是多阶段构建的核心语法。

运行阶段设置了 `PATH="/opt/venv/bin:$PATH"`，所以 `CMD ["python", "app.py"]` 用的是虚拟环境里的 Python（带有 Flask）。

### 步骤 2：分别构建两个镜像

仍在 `labs/07-multistage`：

```bash
docker build -f Dockerfile.single -t lab07:single .
docker build -f Dockerfile.multi -t lab07:multi .
```

`-f` 指定 Dockerfile 路径。最后的 `.` 仍是构建上下文（当前目录）。

预期结果：两次都成功结束，分别打上 `lab07:single` 和 `lab07:multi`。第一次构建会拉基础镜像，时间更长。`python:3.12` 明显大于 `python:3.12-slim`，单阶段这次通常更慢一些。

### 步骤 3：对比体积

```bash
docker images lab07
```

也可以排得更整齐：

```bash
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}" lab07
```

预期结果：`lab07:single` 明显大于 `lab07:multi`。在不少机器上，前者可能到 1GB 上下，后者则是一百多到两百多 MB 的量级（具体数字随基础镜像版本变化，不必和别人完全一样）。差值主要来自：

- 完整 `python:3.12` 比 `slim` 多带了大量预装工具和库
- 单阶段把 `gcc` 留在了最终镜像里

功能并没有因此变强。两个镜像跑起来应是同一个页面。

再看层，感受「最终镜像里到底留下了什么」：

```bash
docker history lab07:single
docker history lab07:multi
```

预期结果：多阶段的最终镜像历史里，**看不到** builder 里那次 `apt-get install gcc` 的层。那些层属于构建阶段，不会自动成为最终镜像的一部分。你只会看到运行阶段的 `FROM python:3.12-slim`、拷贝 venv、拷贝 `app.py` 等。

### 步骤 4：运行较瘦的那个，确认功能正常

```bash
docker run -d --name lab07-web -p 8080:8000 lab07:multi
```

打开 [http://localhost:8080](http://localhost:8080)。

预期结果：页面标题或正文说明这是多阶段构建演示。再试：

```bash
curl -s http://localhost:8080/health
docker exec lab07-web python -c "import flask, sys; print('flask', flask.__version__); print(sys.executable)"
```

预期结果：健康检查返回 `{"status":"ok"}`；`sys.executable` 指向 `/opt/venv/bin/python`。说明最终镜像虽然瘦，但依赖是完整的。

（可选）把容器换成 `lab07:single` 再访问一次，页面应相同。记得先 `docker rm -f lab07-web`，避免名字和端口冲突。

### 步骤 5：什么时候值得用多阶段

记三条就够：

1. 构建需要编译器、SDK、测试工具，运行只需要语言运行时和依赖。
2. 想换更瘦的基础镜像（slim、distroless 等），但安装依赖时还得有构建工具。
3. 前端项目也很常见：在 Node 阶段 `npm run build`，再把静态文件拷进 `nginx` 镜像。本实验用 Python 演示同一思路。

它不是必须的。像实验 02 那种只用标准库、没有构建工具的小镜像，单阶段已经很干净。等依赖和工具变多时，再上多阶段收益更大。

## 小练习

请先自己做，做完再看 `answers.md`。

1. 把 `docker images lab07` 的两个体积记下来，用一句话写出你认为差值主要来自哪里。
2. 在 `lab07:multi` 容器里执行 `which gcc` 或 `gcc --version`，再在 `lab07:single` 里做同样的事。预期分别是什么？
3. （思考题，可选动手）如果把 `Dockerfile.multi` 的运行阶段也改成 `FROM python:3.12`（完整版），体积还会比单阶段小吗？为什么？可以改完构建一个 `lab07:multi-fat` 验证，看完后删掉这个标签即可。

## 常见坑

- **忘了 `-f`，Docker 去找默认的 `Dockerfile`。** 本目录故意没有名为 `Dockerfile` 的文件，漏写 `-f` 会直接报错。这是有意为之，避免构建到错误的那一份。
- **两份镜像 tag 打反了。** 对比体积前先看 `docker images` 的 TAG 列。
- **COPY --from 的名字写错。** 必须和前面 `FROM ... AS builder` 的名字一致。
- **运行阶段忘了把 venv 加入 PATH。** 容器一启动就会 `python: can't open file` 或找不到 flask。本实验的 `Dockerfile.multi` 已经写好了 `ENV PATH=...`。
- **在错误目录构建。** 上下文必须是包含 `app.py` 和 `requirements.txt` 的 `labs/07-multistage`。

## 收尾

```bash
docker rm -f lab07-web 2>/dev/null || true
docker images lab07
```

镜像可以留着对比，占一些磁盘。若想删掉：

```bash
docker rmi lab07:single lab07:multi
```

8080 应已释放。
