# 实验 04 练习参考答案

请先自己做，再对照这里。

## 练习 1

在 `labs/04-volumes` 目录下：

```bash
docker volume create lab04-practice
docker run --rm -v lab04-practice:/data alpine:3.20 sh -c 'echo hello-practice > /data/note.txt'
docker run --rm -v lab04-practice:/data alpine:3.20 cat /data/note.txt
```

预期输出：`hello-practice`。第二个容器和第一个没有关系，只是挂了同一块具名卷。

做完后可以先留着，等收尾时一起 `docker volume rm lab04-practice`。

## 练习 2

改 `site/index.html` 后刷新 [http://localhost:8080](http://localhost:8080)（容器 `lab04-nginx` 仍在运行的前提下），应立刻看到新内容。

关于去掉 `:ro` 之后在容器里改文件：

先停掉原来的只读容器，再以可写方式启动：

```bash
docker rm -f lab04-nginx
docker run -d --name lab04-nginx \
  -p 8080:80 \
  -v "$(pwd)/site:/usr/share/nginx/html" \
  nginx:1.27-alpine

docker exec lab04-nginx sh -c 'echo "<!-- edited in container -->" >> /usr/share/nginx/html/index.html'
```

然后在**宿主机**上查看 `site/index.html`，文件末尾应出现那行注释。bind mount 两边看到的是同一份文件，容器内的修改就是对宿主机文件的修改。这就是开发时既方便、也需要小心的地方：容器里一个误删，可能直接删掉你的源文件。`:ro` 可以降低这个风险。

nginx 主进程用户不一定有写权限（网页目录常属 root）。若 `docker exec` 报 `Permission denied`，加上 `-u root`：

```bash
docker exec -u root lab04-nginx sh -c 'echo "<!-- edited in container -->" >> /usr/share/nginx/html/index.html'
```

验证完记得看一眼（并可还原）你的 `index.html`。

## 练习 3

`docker volume prune` 会删除**当前没有任何容器引用**的卷，包括具名卷。它不会只删匿名卷。

只要 `lab04-data` 没有被任何容器（含已退出）挂着，它就会出现在 prune 的候选名单里。所以在还有练习数据时，不要急着对 prune 说 yes。

更稳妥的做法是：`docker volume ls` 看名单，用 `docker volume rm 明确的名字` 按需删除。本实验收尾一节就是这样做的。
