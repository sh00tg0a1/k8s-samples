# 创建一个 k8s 服务

## 第一步：准备

### 使用 flask

* 官方文档 <https://flask.palletsprojects.com/en/1.1.x/tutorial/>
* PS:click 是个很棒的库，用于创建 Python 的命令行程序 <https://click.palletsprojects.com/en/7.x/>

### 使用 Flask 编写下面的服务

* server.py

    ``` python
    from flask import Flask
    app = Flask(__name__)


    @app.route('/')
    def hello():
        return "Hello World!"


    @app.route('/<name>')
    def hello_name(name):
        return "Hello {}!".format(name)


    if __name__ == '__main__':
        app.run(host='0.0.0.0')

    ```

* Dockerfile

    ``` Dockerfile
    FROM python:3.7-alpine
    RUN pip install flask
    COPY server.py .
    CMD python server.py
    ```

### 构建 image

``` bash
# docker build . -t mocker-server:1
```

## 第二步：创建一个 deploy

首先查看 k8s 的运行信息：

``` sh
获取集群信息
# kubectl cluster-info
Kubernetes master is running at <https://kubernetes.docker.internal:6443>
KubeDNS is running at <https://kubernetes.docker.internal:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy>
```

获取节点信息:

``` sh
获取节点信息
# kubectl get nodes
NAME             STATUS   ROLES    AGE     VERSION
docker-desktop   Ready    master   3d14h   v1.14.6
```

从 image 创建 Deployment

``` sh
# kubectl create deployment mock-server1 --image=mock-server:1
deployment.apps/mock-server1 created
```

查看 Deployment:

``` sh
#kubectl get deployments
NAME           READY   UP-TO-DATE   AVAILABLE   AGE
mock-server1   0/1     1            0           2m21s
```

我们发现 Pod 也被创建起来

``` sh
# kubectl get pods
NAME                           READY   STATUS             RESTARTS   AGE
mock-server1-bbd7bfb5b-ptwt9   0/1     ImagePullBackOff   0          4m7s
```

## 第三步：对外暴露端口

我们使用刚才创建的 Pod 来启动对外提供服务，flask app 使用的默认端口是 5000，而且我们需要这个服务对外开放这个端口，所以使用 LoadBalancer 模式

### 创建 Deployment

这里直接从 image 创建，所以会有相应的服务和 pod 被创建

``` sh
# kubectl expose deployment mock-server1 --type=LoadBalancer --port=5000
service/mock-server1 exposed
```

### 查看 Pod & Service

测试一下效果:

``` sh
# kubectl get services
NAME           TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
kubernetes     ClusterIP      10.96.0.1        <none>        443/TCP          3d14h
mock-server1   LoadBalancer   10.101.152.100   localhost     5000:32670/TCP   13m
```

查看 Pod 信息:

``` sh
# kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
mock-server1-bbd7bfb5b-45vp4   1/1     Running   0          8s
```

查看 ```Status```，已经是 ```Running``` 状态

### 测试服务

``` sh
# curl 'http://127.0.0.1:5000/k8s'
Hello k8s!
```

服务成功创建！

## 其他总结

1. images 的构建和 docker 一致
2. 创建 deployment 的时候会创建 pod，并运行
3. 使用 expose 来创建服务
4. 服务和 pod 之间没有直接关系，直接替换 pod 不影响服务的配置
