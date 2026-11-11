# 实验 07 练习参考答案

请先自己做，再对照这里。

## 练习 1

在 `labs/07-multistage` 构建完成后：

```bash
docker images lab07
```

`lab07:single` 会明显更大。差值主要来自两点（往往第一点占大头）：

- 单阶段的基础镜像是完整的 `python:3.12`，多阶段运行阶段是 `python:3.12-slim`
- 单阶段把 `gcc` 留在了最终镜像里，多阶段的 gcc 只存在于已经被丢弃的 builder 阶段

应用代码本身只有几 KB，对体积几乎没有影响。

## 练习 2

先确保两个容器能 exec（可以同时跑，注意端口不要冲突：只给要浏览器访问的那一个做 `-p`，另一个可以不发布端口）：

```bash
docker rm -f lab07-web lab07-single 2>/dev/null || true
docker run -d --name lab07-web lab07:multi sleep 300
docker run -d --name lab07-single lab07:single sleep 300

docker exec lab07-web sh -c 'which gcc; gcc --version'
docker exec lab07-single sh -c 'which gcc; gcc --version'
```

这里用 `sleep` 是为了让你在 exec 时进程还在。若你更愿意用应用进程，直接 `docker run -d ... lab07:multi python app.py` 也可以。

预期：

- `lab07:multi`：`which gcc` 没有结果，`gcc --version` 报 not found。最终镜像没有安装编译器。
- `lab07:single`：能打印 gcc 版本。它被留在了最终镜像里，但运行这个 Flask 页面并不需要它。

看完后：

```bash
docker rm -f lab07-web lab07-single
```

如果刚才覆盖了原来在 8080 上跑的容器，需要的话再用 `lab07:multi` 按 README 步骤 4 启动一次。

## 练习 3

如果只把运行阶段改成 `FROM python:3.12`，最终镜像会重新变胖，体积会接近（或在同一量级上接近）单阶段——因为最大的那一块（完整 Python 基础镜像）又回来了。多阶段仍然可能略小一点（例如没有 gcc），但收益会小很多。

多阶段真正划算的地方，通常是：**运行阶段选更瘦的基础镜像，并且不要把构建工具拷进去**。只拆阶段、不换瘦镜像，效果有限。

验证示例（做完请清理）：

把运行阶段的 `FROM python:3.12-slim` 临时改成 `FROM python:3.12`，然后：

```bash
docker build -f Dockerfile.multi -t lab07:multi-fat .
docker images lab07
docker rmi lab07:multi-fat
```

记得把 Dockerfile 改回去，以免下次构建出的 `lab07:multi` 不再是瘦的那份。
