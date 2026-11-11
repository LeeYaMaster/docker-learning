# 实验 05 练习参考答案

请先自己做，再对照这里。

## 练习 1

假设 `lab05-net` 和 `lab05-web` 还在：

```bash
docker run -d --name lab05-web2 --network lab05-net nginx:1.27-alpine

docker run --rm --network lab05-net alpine:3.20 wget -qO- http://lab05-web/ | head
docker run --rm --network lab05-net alpine:3.20 wget -qO- http://lab05-web2/ | head
```

两次都应拿到 nginx 欢迎页 HTML。也可以在同一个 alpine 里连续访问：

```bash
docker run --rm --network lab05-net alpine:3.20 sh -c 'wget -qO- http://lab05-web/ >/dev/null && wget -qO- http://lab05-web2/ >/dev/null && echo ok'
```

预期打印 `ok`。两个容器名都能解析，因为它们都接在 `lab05-net` 上。

## 练习 2

```bash
docker run --rm --network lab05-other alpine:3.20 wget -qO- http://lab05-web/
```

预期失败。常见输出类似：

- `wget: bad address 'lab05-web'`（名字根本解析不到）
- 或在某些情况下是无法连接

把客户端放到另一张网络后，自定义网络的 DNS 不会帮它解析 `lab05-web`。这就是「不在同一网络，名字再对也走不通」。

## 练习 3

```bash
docker network inspect lab05-net
```

在 `Containers` → `lab05-web` → `IPv4Address` 能看到类似 `172.18.0.2/16` 的地址（具体数字会变）。

把这个 IP 写进应用配置的缺点：

- 容器重建后 IP 常常会变
- 不同网络的网段也不同，换一台机器或重新 `network create` 就可能对不上
- 你要自己维护这份易变的地址，完全丢掉了 DNS 的好处

所以在自定义网络里，配置应写 **容器名**（在 Compose 里则写**服务名**，通常和服务名、容器名一致或可预期），例如 `db`、`redis`，而不是某个 `172.x.x.x`。
