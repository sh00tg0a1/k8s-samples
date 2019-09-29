# 使用官方的示例来创建一个 Redis 服务

*参考资料：*

1. [官方示例](https://kubernetes.io/docs/tutorials/configuration/configure-redis-using-configmap/)
2. [官方文档](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)

## 第一步：创建配置文件

### 下载 k8s redis 的配置文件

使用下面的命令:

``` sh
curl -OL https://k8s.io/examples/pods/config/redis-config
```

### 使用 ConfigMap Generator 创建配置文件

首先创建一个 yaml 文件:

```sh
cat <<EOF >./kustomization.yaml
configMapGenerator:
- name: example-redis-config
  files:
  - redis-config
EOF
```

准备将如下的文件插入进去, 链接如下 [pods/config/redis-pod.yaml](https://raw.githubusercontent.com/kubernetes/website/master/content/en/examples/pods/config/redis-pod.yaml):

``` yaml
apiVersion: v1
kind: Pod
metadata:
  name: redis
spec:
  containers:
  - name: redis
    image: redis:5.0.4
    command:
      - redis-server
      - "/redis-master/redis.conf"
    env:
    - name: MASTER
      value: "true"
    ports:
    - containerPort: 6379
    resources:
      limits:
        cpu: "0.1"
    volumeMounts:
    - mountPath: /redis-master-data
      name: data
    - mountPath: /redis-master
      name: config
  volumes:
    - name: data
      emptyDir: {}
    - name: config
      configMap:
        name: example-redis-config
        items:
        - key: redis-config
          path: redis.conf
```

用如下的命令编辑配置文件:

```sh
curl -OL https://raw.githubusercontent.com/kubernetes/website/master/content/en/examples/pods/config/redis-pod.yaml

cat <<EOF >>./kustomization.yaml
resources:
- redis-pod.yaml
EOF
```

## 第二步：创建 ConfigMap 和 Pod

使用下面的命令来同步配置，同时创建 pod

``` sh
# kubectl apply -k .
```

输出是类似这样:

``` sh
configmap/example-redis-config-dgh9dg555m created
pod/redis created
```

获取 ConfigMap

```sh
# kubectl get -k .
NAME                                        DATA   AGE
configmap/example-redis-config-dgh9dg555m   1      20m

NAME        READY   STATUS    RESTARTS   AGE
pod/redis   1/1     Running   0          20m
```

获取配置:

``` sh
# kubectl get configmap
NAME                              DATA   AGE
example-redis-config-dgh9dg555m   1      68m
```

查看配置:

``` sh
# kubectl describe configmap/example-redis-config-dgh9dg555m
Name:         example-redis-config-dgh9dg555m
Namespace:    default
Labels:       <none>
Annotations:  kubectl.kubernetes.io/last-applied-configuration:
                {"apiVersion":"v1","data":{"redis-config":"maxmemory 2mb\nmaxmemory-policy allkeys-lru\n"},"kind":"ConfigMap","metadata":{"annotations":{}...

Data
====
redis-config:
----
maxmemory 2mb
maxmemory-policy allkeys-lru

Events:  <none>
```

查看 Pod

``` sh
# kubectl describe pods/redis
Name:               redis
Namespace:          default
...
```

### 配置文件解析

这里采用 ConfigMapping 的方式来配置卷

> 注意配置文件中如下的部分，说明 data 目录使用容器本地存储空间，而 config 使用的则是 redis.conf:

``` yaml
# container 部分，指定挂在点
  containers:
    ...
    volumeMounts:
    - mountPath: /redis-master-data
      name: data
    - mountPath: /redis-master
      name: config
    ...
```

描述卷的部分:

``` yaml
  volumes:
    # 对应 volumeMounts 中的 data
    - name: data
      emptyDir: {}
    # 对应 volumeMounts 中的 config
    - name: config
      # 这里使用的是 第一步中使用 configMapGenerator 添加的配置文件
      configMap:
        name: example-redis-config
        items:
        - key: redis-config
          # 配置项
          path: redis.conf
```

### 测试 Redis

使用 Redis-cli 测试服务

``` sh
# kubectl exec -it redis bash
root@redis:/data# redis-cli
127.0.0.1:6379> CONFIG GET maxmemory
1) "maxmemory"
2) "2097152"
127.0.0.1:6379> CONFIG GET maxmemory-policy
1) "maxmemory-policy"
2) "allkeys-lru"
127.0.0.1:6379>
```

尝试对外暴露端口

