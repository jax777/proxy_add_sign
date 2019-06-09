# 说明

fuzz web参数时,遇到请求参数被前端加signature, 为此编写的一个 http 代理，sqlmap 或 burp 可通过使用该代理，继续对应用进行fuzz

## 使用方法

针对不同站点前端signature 的生成机制，修改 upadte_post_body 函数。

常规情况下 运行 `python  proxy_add_sign.py -p 8080` 即可在 8080 端口开启一个http代理

### https 的问题

由于仅仅为了测试，sqlmap、burp 不必了解目标站点是否为https，就没有实现自签名证书的 https 代理。仅将sqlmap、burp发来的http包，以https的方式请求至源站，对工具来说目标只是一个正常的http服务。 
以如下命令 运行`python  proxy_add_sign.py -p 8080 -s True`