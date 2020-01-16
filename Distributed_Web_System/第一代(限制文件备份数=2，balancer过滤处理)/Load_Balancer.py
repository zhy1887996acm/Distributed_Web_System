# -*- coding: utf-8 -*-
'''
Recv 4 Web Servers' IP and Port, and their files owned.

多用户同时上传同一个文件？如何解决？
'''
import os
import sys
import random
import socket
import hashlib
import json
import threading

from ThreadPool import ThreadPoolManger


balancerAddr = '127.0.0.1'
balancerPort = 8888
WebServerAddr = '127.0.0.1'
WebServerPort = 9000
recvBytes = 1024


def Load_Balance():
    # 请求Web Server的状态
    return 0

def handle_request(conn_socket):
    print('thread %s is running ' % threading.current_thread().name)
    data = conn_socket.recv(1024)
    if not data:
        print('客户端断开')
        return
    json_string = data.decode()
    reqList = json.loads(json_string)
    cmd = reqList[-1]
    files = reqList[0:-1]
    print(cmd, files)
    if cmd == 'download':
        # 处理客户端的下载请求
        WebServerAddrList = []
        for file in files:
            WebServerAddrList.append('127.0.0.1')
        json_string = json.dumps(WebServerAddrList)
        conn_socket.send(json_string.encode())
    elif cmd == 'upload':
        # 处理客户端的上传请求
        # 计算负载，选择一个最好的WebServerAddr
        WebServerAddr = '127.0.0.1'
        uploadList = [WebServerAddr]
        for file in files:
            uploadList.append(file)
        
        # 将uploadList发送给客户端
        json_string = json.dumps(uploadList)
        conn_socket.send(json_string.encode())
    elif cmd == 'backup':
        # 处理WebServer的备份请求，计算负载，选择除它以外的一个最好的WebServerAddr
        WebServerAddr = '127.0.0.1'
        uploadList = [WebServerAddr]
        for file in files:
            uploadList.append(file)
        
        # 将uploadList发送给客户端
        json_string = json.dumps(uploadList)
        conn_socket.send(json_string.encode())
    conn_socket.close()


def Req_Download(conn_socket):
    return

def Req_Upload(conn_socket):
    return


'''
创建多线程Load balancer
'''
thread_pool = ThreadPoolManger(4)

if __name__ == '__main__':
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = (balancerAddr, balancerPort)
        s.bind(addr)
        s.listen(4)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    
    # 循环等待接收客户端请求
    while True:
        print('>>>>>>>>>>等待请求...')
        # 阻塞等待请求
        conn_socket, conn_addr = s.accept()
        print('Load Balancer收到请求，连接地址:%s' % str(conn_addr))
        # 一旦有请求了，把socket扔到指定处理函数，放进任务队列
        
        '''
        这里单纯通过连接无法决定分配哪个处理函数：
            客户端的请求？Balancer的请求？其他WebServer的请求？
        需要从请求消息中解析请求类型
        最后，确定处理函数之后连同conn_socket送入线程池
        '''
        
        
        # 等待线程池分配线程处理
        thread_pool.add_job(handle_request, *(conn_socket, ))
    
    s.close()