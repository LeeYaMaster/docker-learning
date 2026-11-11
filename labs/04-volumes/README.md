# 实验 04：数据卷

预估时间：约 35 分钟

## 本实验目标

弄清楚容器里的数据怎样才能在「删掉容器再跑一个新的」之后还在。你会亲手对比三种常见做法：

- **匿名卷**（anonymous volume）：Docker 自动生成名字，用起来省事，管理起来不直观
- **具名卷**（named volume）：你给卷起名字，最适合放数据库数据这类「属于 Docker 管、但要长期留着」的东西
- **bind mount**：把宿主机的某一个目录或文件直接挂进容器，适合放代码、配置、你要在编辑器里改的文件

为什么这很重要？镜像是只读层叠起来的，容器自己的可写层默认和容器绑定。容器删了，写在可写层里的文件就没了。想让数据活得比容器久，就要用卷。

本实验用 `alpine:3.20` 和 `nginx:1.27-alpine` 做演示，并附带一个小页面（`site/index.html`）和可选脚本 `write-note.sh`。

## 准备工作

请进入本实验目录，bind mount 会用到这里的相对路径：

```bash
cd labs/04-volumes
ls -l
ls -l site
```

预期结果：能看到 `site/index.html` 和 `write-note.sh`。

若 8080 仍被前面实验的容器占用，先清掉（`docker ps` 然后 `docker rm -f <名字>`）。

## 动手步骤

### 步骤 1：先看「不用卷会怎样」

```bash
docker run --name lab04-ephemeral alpine:3.20 sh -c 'echo "only-in-this-container" > /tmp/note.txt && cat /tmp/note.txt'
```

预期结果：打印 `only-in-this-container`。这个文件写在容器自己的可写层里。

```bash
docker rm lab04-ephemeral
docker run --rm alpine:3.20 cat /tmp/note.txt
```

预期结果：第二条命令会报「没有那个文件」。即使容器名字你想复用，这也是一个**新**容器，旧容器里的文件不会跟过来。这就是「数据跟着容器一起消失」。

### 步骤 2：具名卷 —— 删掉容器，数据还在

先创建一个卷，再把它挂到容器的 `/data`：

```bash
docker volume create lab04-data
docker volume ls
```

预期结果：列表里出现 `lab04-data`。

把本目录的 `write-note.sh` 挂进去执行一次（脚本负责在 `/data/note.txt` 里写一行）：

```bash
docker run --rm \
  -v lab04-data:/data \
  -v "$(pwd)/write-note.sh:/write-note.sh:ro" \
  alpine:3.20 sh /write-note.sh
```

预期结果：打印 `/data/note.txt` 的内容，其中有一行带时间戳的 `written-inside-container`。

注意：`-v lab04-data:/data` 这种「左边没有 `/` 或 `.` 的」是**具名卷**；左边是宿主机路径的，才是 bind mount。两种写法看起来都是 `-v`，含义不同。

现在这个容器已经因 `--rm` 被删掉了。再开一个**全新的**容器，只挂同一个卷：

```bash
docker run --rm -v lab04-data:/data alpine:3.20 cat /data/note.txt
```

预期结果：刚才写的那一行还在。容器没了，数据还在卷里。这就是具名卷最值得记住的现象。

可以再执行一次 `write-note.sh` 那条命令，文件会追加第二行。然后再次 `cat` 确认。

查看卷的实际信息：

```bash
docker volume inspect lab04-data
```

预期结果：JSON 里有 `Name`、`Mountpoint` 等。在 Docker Desktop（Mac）上，Mountpoint 路径位于 Linux 虚拟机内部，不要指望它等于你 Mac 上的某个普通文件夹。这和稍后的 bind mount 正好相反。

### 步骤 3：匿名卷 —— 能持久，但名字不好记

不预先 `volume create`，只写挂载目标路径，Docker 就会自动建一个匿名卷：

```bash
docker run -d --name lab04-anon -v /data alpine:3.20 sleep 3600
docker exec lab04-anon sh -c 'echo "from-anonymous-volume" > /data/note.txt'
docker inspect -f '{{json .Mounts}}' lab04-anon
```

预期结果：`Mounts` 里有一项 `Type` 为 `volume`，`Name` 是一长串哈希，`Destination` 为 `/data`。这就是匿名卷。

```bash
docker rm -f lab04-anon
docker volume ls
```

预期结果：那个哈希名字的卷**还在**。删容器默认不会删卷。但你已经很难一眼想起「这个卷是干什么的」。

把数据读回来（把下面的 `VOLUME_NAME` 换成你在 `volume ls` 或刚才 `inspect` 里看到的那个哈希名）：

```bash
docker run --rm -v VOLUME_NAME:/data alpine:3.20 cat /data/note.txt
```

预期结果：打印 `from-anonymous-volume`。

匿名卷适合「我需要持久化，但不想给它起名」的场合，例如某些镜像在 Dockerfile 里写了 `VOLUME /data`，运行时就会自动挂上匿名卷。日常自己管理数据，更推荐具名卷。

清理这个匿名卷（把名字换掉）：

```bash
docker volume rm VOLUME_NAME
```

若提示 volume is in use，说明还有容器引用它，先 `docker ps -a` 清理容器。

### 步骤 4：bind mount —— 直接用宿主机目录

把本实验的 `site/` 挂到 nginx 的网页目录，用浏览器看宿主机上的文件：

```bash
docker run -d --name lab04-nginx \
  -p 8080:80 \
  -v "$(pwd)/site:/usr/share/nginx/html:ro" \
  nginx:1.27-alpine
```

`$(pwd)/site` 会展开成当前目录下 `site` 的绝对路径。`:ro` 表示容器内只读，防止 nginx 改掉你的源文件。

打开 [http://localhost:8080](http://localhost:8080)。

预期结果：看到「这是宿主机上的页面」，而不是 nginx 默认的 Welcome 页。

现在用编辑器修改 `labs/04-volumes/site/index.html` 里的标题，保存后**刷新浏览器**（不必重建镜像，也不必重启容器）。

预期结果：新文案立刻出现。这就是 bind mount 最舒服的地方：你在熟悉的编辑器里改文件，容器马上看到同一份文件。开发阶段经常这样挂代码。

顺手对比一下 inspect：

```bash
docker inspect -f '{{json .Mounts}}' lab04-nginx
```

预期结果：`Type` 为 `bind`，`Source` 是你 Mac 上 `site` 目录的绝对路径。和具名卷不同，文件就在你眼前这个项目里。

看完后先不要急着删，做完下面的练习再收尾也可以。

### 步骤 5：三种方式怎么选（记这张表即可）

| 方式 | 数据在哪 | 删容器后 | 适合 |
|------|----------|----------|------|
| 不挂卷，写在容器层 | 跟着容器 | 没了 | 临时文件、真正无所谓的数据 |
| 具名卷 `-v 名字:/路径` | Docker 管理的卷 | 还在 | 数据库文件、上传文件、不想和某台宿主机路径绑死时 |
| 匿名卷 `-v /路径` | Docker 管理，名字是哈希 | 还在，但难认 | 镜像声明了 `VOLUME`、你暂时不想命名 |
| bind mount `-v 宿主机路径:/路径` | 你指定的目录 | 还在（本来就在宿主机） | 开发时的代码、配置、要亲手编辑的文件 |

实验 06 的 MySQL、Redis 会使用具名卷保存数据。到时候你可以对照这次的实验，理解为什么 `docker compose down` 之后留言还在。

## 小练习

请先自己做，做完再看 `answers.md`。

1. 再创建一个具名卷 `lab04-practice`，在里面写入 `hello-practice`，删掉容器后用一个新容器把内容读出来。
2. 把 `site/index.html` 再改几个字，确认浏览器无需重建镜像就能看到变化。然后思考：如果把 bind mount 的 `:ro` 去掉，在容器里修改该目录下的文件，宿主机上的文件会不会变？可以做一次小实验验证。
3. 运行 `docker volume ls` 和 `docker volume prune` 之前，先想一想：`prune` 会删掉哪些卷？`lab04-data` 现在有没有容器在用？**先不要盲目确认删除**，看清提示再决定。做完本实验后，再按「收尾」一节清理。

## 常见坑

- **`-v 名字:/data` 和 `-v ./data:/data` 搞混。** 左边是简单名字（没有路径分隔符）时，Docker 当具名卷；左边是 `./`、`/` 或在 Mac/Linux 上的绝对路径时，是 bind mount。写成 `-v data:/data` 时，它不会使用当前目录下的 `data` 文件夹，而是一个叫 `data` 的卷。
- **bind mount 路径写错，nginx 出现 403 或空白页。** 检查当前目录是不是 `labs/04-volumes`，以及 `$(pwd)/site` 是否真有 `index.html`。路径不存在时，Docker 有时会在宿主机创建一个空目录，于是 nginx 的网页目录变成空的。
- **在 Mac 上找不到具名卷的 Mountpoint。** 那是虚拟机内部路径，请用另一个容器去 `-v lab04-data:/data` 查看，不要在 Finder 里硬找。
- **`volume rm` 报 in use。** 还有容器（包括已退出的）引用它。先 `docker rm` 容器。
- **权限问题。** 本实验的 alpine / nginx 示例通常不会踩到。若以后用非 root 用户写 bind mount 的目录，可能会遇到权限不足，需要调整目录属主或容器用户。实验 08 会谈到非 root。

## 收尾

```bash
docker rm -f lab04-nginx lab04-anon lab04-ephemeral 2>/dev/null || true
docker volume rm lab04-data lab04-practice 2>/dev/null || true
docker volume ls
```

若还有刚才练习留下的匿名卷，用 `docker volume ls` 找到后 `docker volume rm <名字>`。不要习惯性使用 `docker volume prune`，以免误删其它项目的未使用卷。

8080 应已释放。本目录里的 `site/index.html` 若被你改过，可以留着，不影响后面实验。
