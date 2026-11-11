# 实验 02：第一个 Dockerfile
# 基础镜像请写明标签，不要只写 python（那会默默指向 latest）
FROM python:3.12-slim

# 容器里的工作目录，后面的 COPY / RUN / CMD 都相对这里
WORKDIR /app

# 把服务代码放进镜像。只复制需要的文件，镜像会更干净
COPY app.py .

# 演示 RUN：构建镜像时执行的命令，结果会写进这一层
# 这里只写一个构建标记，实际项目里更常见的是安装依赖
RUN echo "lab02 image built" > /app/build-info.txt

# 声明容器内进程监听的端口（这是文档性质，真正对外发布要靠 docker run -p）
EXPOSE 8000

# 容器启动时的默认命令。使用 exec 形式（JSON 数组），信号可以正确传给 Python
CMD ["python", "app.py"]
