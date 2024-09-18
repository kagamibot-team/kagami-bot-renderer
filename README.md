# 依赖

请安装 `RabbitMQ`。

# 配置方式

环境变量清单（可以用 `dotenv`）：

```properties
ACCOUNT=test_account
PASSWORD=test_password
HOST=127.0.0.1
PORT=5672
VIRTUAL_HOST=/
```

字体需要挂载：

```
-v /usr/share/fonts:/usr/share/fonts:ro
```
