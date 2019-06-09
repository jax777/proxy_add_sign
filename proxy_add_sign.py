#!/usr/bin/env python
#coding:utf-8

import logging
import os
import re
import socket
import hashlib

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient


logger = logging.getLogger()
#logger.level = logging.DEBUG

# update signature
def upadte_post_body(body):
    '''
    token=o5z2z6f0U9X6T1x4T3Z1O685N5K0z6A2D8B37675p2k3h5c889e9q253b42243q985f9006526q1o929k3j605q80731&
    time=1559801535&
    version=2&
    signature=5af79f46836aa9d935615bee565ba9ab&
    md5str=time1559801535tokeno5z2z6f0U9X6T1x4T3Z1O685N5K0z6A2D8B37675p2k3h5c889e9q253b42243q985f9006526q1o929k3j605q80731version2
    '''
    key = '08e95876b4d844789c00b350c1dc3e5d'

    paramlist = body.split('&')

    paramlist.sort()  # Simulate js key field sorting
    
    paramdic = {}

    new_md5str = ''
    old_md5str = ''
    
    new_sign = ''
    old_sign = ''

    for i in paramlist:
        _ = i.split('=')
        if _[0] != 'md5str' and _[0] != 'signature':
            new_md5str = new_md5str + i
        elif _[0] == 'md5str':
            old_md5str = _[1]
        elif _[0] == 'signature':
            old_sign = _[1]
    
    md5 = hashlib.md5()
    hashstring = new_md5str + key
    md5.update(hashstring.encode('utf-8'))   
    new_sign = md5.hexdigest()

    body.replace(old_sign,new_sign)
    body.replace(old_md5str,new_md5str)

    return body

class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'CONNECT']

    @tornado.web.asynchronous
    def get(self):
        logger.debug('Handle %s request to %s', self.request.method, self.request.uri)
        logger.debug('Handle %s %s %s %s',self.request.uri, self.request.method, self.request.body,self.request.headers)

        # http://www.guimaizi.com:443/ GET  {'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2', 'Accept-Encoding': 'gzip, deflate', 'Connection': 'keep-alive', 'Accept':
#'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0', 'Host': 'www.guimaizi.com:443', 'Cookie': 'UM_distinctid=167b17756ad7b-0d61507f3852b48-4c312a7a-1fa400-167b17756ae1de; CNZZDATA1262779369=495412619-1544870736-%7C1560095020', 'Upgrade-Insecure-Requests': '1'}
        def handle_response(response):
            #self.request.headers.get("X-Real-Ip",'')
            if (response.error and not
                    isinstance(response.error, tornado.httpclient.HTTPError)):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
            else:
                self.set_status(response.code)
                for header in ('Date', 'Cache-Control', 'Server', 'Content-Type', 'Location'):
                    v = response.headers.get(header)
                    if v:
                        self.set_header(header, v)
                v = response.headers.get_list('Set-Cookie')
                if v:
                    for i in v:
                        self.add_header('Set-Cookie', i)
                #self.add_header('VIA', 'Toproxy')
                if response.body:
                    self.write(response.body)
            self.finish()

        if base_auth_user:
            auth_header = self.request.headers.get('Authorization', '')
            if not base_auth_valid(auth_header):
                self.set_status(403)
                self.write('Auth Faild')
                self.finish()
                return




        body = self.request.body
        
        # modify here  ----------------------
        upadte_post_body(body)

        if not body:
            body = None
        try:
            fetch_request(
                self.request.uri, handle_response,
                method=self.request.method, body=body,
                headers=self.request.headers, follow_redirects=False,
                allow_nonstandard_methods=True)
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                handle_response(e.response)
            else:
                self.set_status(500)
                self.write('Internal server error:\n' + str(e))
                self.finish()

    @tornado.web.asynchronous
    def post(self):
        return self.get()
    


def base_auth_valid(auth_header):
    auth_mode, auth_base64 = auth_header.split(' ', 1)
    assert auth_mode == 'Basic'
    auth_username, auth_password = auth_base64.decode('base64').split(':', 1)
    if auth_username == base_auth_user and auth_password == base_auth_passwd:
        return True
    else:
        return False


def fetch_request(url, callback, **kwargs):
    if ssf_flag:
        url = 'https' + url[4:]
        req = tornado.httpclient.HTTPRequest(url,validate_cert = False, **kwargs)
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(req, callback, follow_redirects=True, max_redirects=3)
    else:
        req = tornado.httpclient.HTTPRequest(url, **kwargs)
        client = tornado.httpclient.AsyncHTTPClient()
        client.fetch(req, callback, follow_redirects=True, max_redirects=3)


def run_proxy(port, pnum=1, start_ioloop=True):
    import tornado.process
    app = tornado.web.Application([
        (r'.*', ProxyHandler),
    ])

    if pnum > 200 or pnum < 0:
        raise("process num is too big or small")
    if pnum == 1:
        app.listen(port)
        ioloop = tornado.ioloop.IOLoop.instance()
        if start_ioloop:
            ioloop.start()
    else:
        sockets = tornado.netutil.bind_sockets(port)
        tornado.process.fork_processes(pnum)
        server = tornado.httpserver.httpserver(app)
        server.add_sockets(sockets)
        tornado.ioloop.ioloop.instance().start()


if __name__ == '__main__':
    import argparse
    white_iplist = []
    parser = argparse.ArgumentParser(description='''python  proxy_add_sign.py -p 8080 -s True''')

    parser.add_argument('-p', '--port', help='tonado proxy listen port', action='store', default=8080)
    parser.add_argument('-s', '--ssl', help='if the web site is https', action='store', default=False)
    parser.add_argument('-u', '--user', help='Base Auth , xiaoming:123123', action='store', default=None)
    parser.add_argument('-f', '--fork', help='fork process to support', action='store', default=1)
    args = parser.parse_args()

    if not args.port:
        parser.print_help()

    port = int(args.port)
    ssf_flag = args.ssl
    
    if args.user:
        base_auth_user, base_auth_passwd = args.user.split(':')
    else:
        base_auth_user, base_auth_passwd = None, None

    print ("Starting HTTP proxy on port %d" % port)

    pnum = int(args.fork)
    run_proxy(port, pnum)