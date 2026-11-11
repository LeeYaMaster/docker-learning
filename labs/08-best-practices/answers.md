# 实验 08 练习参考答案

请先自己做，再对照这里。

## 练习 1

当前改进版正在运行时：

```bash
docker exec lab08-web whoami
docker exec lab08-web id
```

预期：`appuser`，以及 `uid=1000(appuser) gid=1000(appuser)`。

如果删掉 Dockerfile 中的 `USER appuser` 并重新 `docker compose up -d --build`，默认用户回到 root：

```bash
docker exec lab08-web whoami   # root
docker exec lab08-web id       # uid=0(root) ...
```

启动日志里的 `uid=` 也会变成 `0`。应用看起来还能用，但这是「能跑」和「跑得更稳妥」的差别。

验证完请把 `USER appuser` 改回去，再次 `--build` 启动，确认又变回 `appuser`。

## 练习 2

```bash
docker inspect --format '{{json .State.Health}}' lab08-web
```

在 `Log` 数组里，每次探测都有 `ExitCode` 和 `Output`。成功时 `ExitCode` 为 `0`，`Status` 字段（在 Health 对象顶层）应为 `healthy`。

Dockerfile 里的探测命令访问的是容器内的 `http://127.0.0.1:8000/health`。你在宿主机上可以这样对照：

```bash
curl -s http://localhost:8080/health
```

预期是 `{"status":"ok"}`。两边走的是同一条应用路由：一个从容器内部由 HEALTHCHECK 调用，一个从你的 Mac 经端口映射调用。

若应用还没起来，会看到 `starting` 或失败的 `ExitCode`。等 `start-period` 和几次重试通过后应变为 `healthy`。

## 练习 3

如果没有忽略 `.env` 和庞大的 `venv/`：

1. **`.env` 可能被打包进构建上下文，甚至被 `COPY . .` 写进镜像。** 任何人拿到这个镜像，都有机会读到数据库密码。密钥应在运行时通过环境变量或编排文件注入，而不是打进镜像层。
2. **`venv/` 会让构建上下文变得非常大，构建变慢**，还可能把宿主机的虚拟环境（往往是 macOS 的二进制）拷进 Linux 镜像，既无用又容易造成混乱。依赖应在 Dockerfile 里用 `pip install` 安装。

另外，README、答案、`.git` 进镜像也不会让应用更好跑，只是增加层内容和泄露内部说明的机会。`.dockerignore` 的作用和 `.gitignore` 很像：明确「这些东西不要进入那条流水线」。
