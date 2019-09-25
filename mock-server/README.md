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
# docker build . -t mock-server:1
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
# #curl 'http://127.0.0.1:5000/k8s'
Hello k8s!
```

服务成功创建！

### 查看服务信息

通过 kubectl describe 能够查看服务信息

``` sh
kubectl describe services/mock-server1
Name:                     mock-server1
Namespace:                default
Labels:                   app=mock-server1
Annotations:              <none>
Selector:                 app=mock-server1
Type:                     LoadBalancer
IP:                       10.101.152.100
LoadBalancer Ingress:     localhost
Port:                     <unset>  5000/TCP
TargetPort:               5000/TCP
NodePort:                 <unset>  32670/TCP
Endpoints:                10.1.0.12:5000
Session Affinity:         None
External Traffic Policy:  Cluster
Events:                   <none>
```

这里列出的 ID 为集群内部的 IP

## 第四步: 实现应用伸缩

### 查看服务

查看我们已有的服务：

``` sh
# subectl get deployments
NAME           READY   UP-TO-DATE   AVAILABLE   AGE
mock-server1   1/1     1            1           98m
mock-server2   1/1     1            1           89m
```

其中:

* READY 代表的是 ```当前``` 和 ```期望``` 的 replica 数量
  * ```当前``` 是正在运行 Replica
  * ```期望``` 是配置中指定的 Replica 数量

* UP-TO-DATE 是指已经更新完毕，满足配置的 Replica
* AVAILABLE 现在正在对外提供服务的 Replica 数量

### 调整副本

用如下命令进行调整:

``` sh
# kubectl scale deployment/mock-server1 --replicas=4
deployment.extensions/mock-server1 scaled
```

再次查看状态，已经有了 4 个 Replica:

``` sh
# kubectl get deployments
NAME           READY   UP-TO-DATE   AVAILABLE   AGE
mock-server1   4/4     4            4           106m
mock-server2   1/1     1            1           97m
```

我们再来查看 pod 的运行情况，每个容器都被分配了一个 IP:

``` sh
# kubectl get pods -o wide
NAME                            READY   STATUS    RESTARTS   AGE     IP          NODE             NOMINATED NODE   READINESS GATES
mock-server1-bbd7bfb5b-9hlf8    1/1     Running   0          108m    10.1.0.12   docker-desktop   <none>           <none>
mock-server1-bbd7bfb5b-g5xcg    1/1     Running   0          2m27s   10.1.0.15   docker-desktop   <none>           <none>
mock-server1-bbd7bfb5b-trr9s    1/1     Running   0          2m27s   10.1.0.14   docker-desktop   <none>           <none>
mock-server1-bbd7bfb5b-vmrf4    1/1     Running   0          2m27s   10.1.0.16   docker-desktop   <none>           <none>
mock-server2-6d7b94ddc5-hwx6n   1/1     Running   0          99m     10.1.0.13   docker-desktop   <none>           <none>
```

也可以查看 deployment 的详情

``` sh
# kubectl describe deployment/mock-server1
Name:                   mock-server1
Namespace:              default
CreationTimestamp:      Wed, 25 Sep 2019 15:57:18 +0200
Labels:                 app=mock-server1
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=mock-server1
Replicas:               4 desired | 4 updated | 4 total | 4 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=mock-server1
  Containers:
   mock-server:
    Image:        mock-server:1
    Port:         <none>
    Host Port:    <none>
    Environment:  <none>
    Mounts:       <none>
  Volumes:        <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Progressing    True    NewReplicaSetAvailable
  Available      True    MinimumReplicasAvailable
OldReplicaSets:  <none>
NewReplicaSet:   mock-server1-bbd7bfb5b (4/4 replicas created)
Events:
  Type    Reason             Age    From                   Message
  ----    ------             ----   ----                   -------
  Normal  ScalingReplicaSet  4m31s  deployment-controller  Scaled up replica set mock-server1-bbd7bfb5b to 4
```

为了测试负载均衡，我们需要在 server.py 中增加代码并重新构建:

``` python
from flask import Flask
app = Flask(__name__)

N_OF_CALLS = 0


@app.route('/')
def hello():
    global N_OF_CALLS
    N_OF_CALLS += 1
    return "Hello World!, num_of_calls: {}".format(N_OF_CALLS)


@app.route('/<name>')
def hello_name(name):
    global N_OF_CALLS
    N_OF_CALLS += 1
    return "Hello {}!, num_of_calls: {}".format(name, N_OF_CALLS)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
```

还需要重新部署一下 deployment

``` sh
删除原来的 deployment
# kubectl delete deployment mock-server1
# kubectl create deployment mock-server1 --image=mock-server:1
# kubectl scale deployment/mock-server1 --replicas=4
```

测试 API 调用，实际上在进行 API 调用的时候就已经进行了负载均衡处理

``` sh
#curl 'http://127.0.0.1:5000'
Hello World!, num_of_calls: 2
#curl 'http://127.0.0.1:5000'
Hello World!, num_of_calls: 6
#curl 'http://127.0.0.1:5000'
Hello World!, num_of_calls: 2
#curl 'http://127.0.0.1:5000'
Hello World!, num_of_calls: 3
#curl 'http://127.0.0.1:5000'
Hello World!, num_of_calls: 7
#curl 'http://127.0.0.1:5000'
```

### 缩小 scale

使用如下的命令:

``` sh
# kubectl scale deployment/mock-server1 --replicas=2
NAME           READY   UP-TO-DATE   AVAILABLE   AGE
mock-server1   2/2     2            2           2m49s
mock-server2   1/1     1            1           137m
```

查看 pods，只有两个了

``` sh
kubectl get pods -o wide
NAME                            READY   STATUS    RESTARTS   AGE     IP          NODE             NOMINATED NODE   READINESS GATES
mock-server1-bbd7bfb5b-5qqk5    1/1     Running   0          3m39s   10.1.0.25   docker-desktop   <none>           <none>
mock-server1-bbd7bfb5b-zfhjk    1/1     Running   0          55s     10.1.0.26   docker-desktop   <none>           <none>
mock-server2-6d7b94ddc5-hwx6n   1/1     Running   0          138m    10.1.0.13   docker-desktop   <none>           <none>
```

## 第五步: 升级

## 重新制作 image

直接使用原代码，构建不 tag 的 image

``` sh
# docker build . -t mock-server:1.1
```

替换 image

``` sh
# kubectl set image deployments/mock-server1 mock-server=mock-server:1.1
```

查看 iamge 的版本

``` sh
# kubectl describe deployment/mock-server1
```

### 回退变化

可以使用如下的命令进行回退

``` sh
# kubectl rollout undo deployments/mock-server1
```

可以查看变更历史

``` sh
# kubectl rollout history deployments/mock-server1
deployment.extensions/mock-server1
REVISION  CHANGE-CAUSE
1         <none>
2         <none>```


## 其他总结

1. images 的构建和 docker 一致
2. 创建 deployment 的时候会创建 pod，并运行
3. 使用 expose 来创建服务
4. 服务和 pod 之间没有直接关系，直接替换 pod 不影响服务的配置
5. 如果重新构建了 image，但是没有更换 tag，deployment 是不会自动更新的，set image 也不可以
