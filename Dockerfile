# 基于Alpine Linux发行版的python镜像基础
FROM python:3.6-alpine

# 设置运行时的环境变量
ENV FLASK_APP flasky.py
ENV FLASK_CONFIG production

# RUN 命令在容器映像的上下文中执行指定的命令,这里创建个用户
# -D 禁止命令提示用户输入密码
RUN adduser -D flasky

# 使用flasky身份运行容器
USER flasky

# 设置代码文件夹工作目录 /home/flasky
WORKDIR /home/flaskr

# 剩下下面的命令都是在上面这个目录下执行

# 从本地文件系统中把文件复制到容器的文件系统中
COPY requirements requirements

# 创建虚拟环境，并在里面安装所需的包
RUN python -m venv venv
RUN venv/Scripts/pip install -r requirements/docker.txt

#  复制app，migrations文件到当前路径
COPY app app
COPY migrations migrations
COPY flasky.py config.py boot.sh ./

# 运行时配置，定义程序运行哪个端口上
EXPOSE 5000

#指定启动容器时如何运行应用
ENTRYPOINT ["./boot.sh"]
