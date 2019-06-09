# 说明

fuzz web参数时,遇到请求参数被前端加signature, 为此编写的一个 http 代理，sqlmap 或 burp 可通过使用该代理，继续对应用进行fuzz

## 使用方法

针对不同站点前端signature 的生成机制，修改 upadte_post_body 函数。

常规情况下 运行 `python  proxy_add_sign.py -p 8080` 即可在 8080 端口开启一个http代理

若目标开启了https ，需运行`python  proxy_add_sign.py -p 8080 -s True`，程序会将sqlmap 、burp发来的http包以https的方式请求至源站，对sqlmap、burp来说相当于目标还是一个正常的http服务。
