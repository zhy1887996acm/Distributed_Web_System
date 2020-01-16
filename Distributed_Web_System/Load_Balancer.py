# -*- coding: utf-8 -*-
'''
Recv 4 Web Servers' IP and Port, and their files owned.

多用户同时上传同一个文件？如何解决？
'''
import os
import sys
import random
import socket
import threading
import hashlib
import json
from collections import defaultdict

from ThreadPool import ThreadPoolManger


balancerAddr = '127.0.0.1'
balancerPort = 8888
WebServerAddr = '127.0.0.1'
WebServerPort = 9000
recvBytes = 1024


class WebServer():
    """服务器类"""
    def __init__(self):
        # file folder's path, and let it's total size = 100MB
        self.folderPath = "D:\\Python\\MyFiles\\Web_server\\pyzmq_Examples"
        self.folderSize = 100*1024*1024
        # calculate it's left space size
        self.folderFree = self.getFolderFreeSize(self.folderPath)
        # PV(Page View)
        self.PV = 0
        # response time, depends on Nerwork
        self.Network = 0
        
    def getFolderFreeSize(self, folderPath):
        size=0
        for root, dirs, files in os.walk(folderPath):
            for f in files:
                # os.path.getsize获取单个文件大小
                size += os.path.getsize(os.path.join(root, f))
                #print(root,dirs,f)
        return self.folderSize - size

# 
FileTable = defaultdict(set)
# WebServerAddr --> alive, folderFreeSize, ThreadNum
WebServerTable = defaultdict(list)



def Load_Balance():
    # 请求Web Server的状态
    return 0

def handle_request(conn_socket, conn_addr):
    print('thread %s is running ' % threading.current_thread().name)
    data = conn_socket.recv(1024)
    if not data:
        print('客户端断开')
        return
    global WebServerTable, FileTable
    json_string = data.decode()
    reqList = json.loads(json_string)
    cmd = reqList[-1]
    files = reqList[0:-1]
    print(cmd, files)
    if cmd == 'download':
        # 处理客户端的下载请求
        WebServerAddrList = []
        for file in files:
            # 遍历FileTable的key=file的WebServerAddr
            l = list(FileTable[file])
            WebServerAddr = l[random.randint(1, len(l)) - 1]
            WebServerAddrList.append(WebServerAddr)
        json_string = json.dumps(WebServerAddrList)
        conn_socket.send(json_string.encode())
    elif cmd == 'upload':
        # 处理客户端的上传请求
        # 计算负载，选择一个最好的WebServerAddr，发送给客户端
        l = list(WebServerTable.keys())
        WebServerAddr = l[random.randint(1, len(l)) - 1]
        conn_socket.send(WebServerAddr.encode())
    elif cmd == 'backup':
        # 处理WebServer的备份请求
        # 更新文件列表
        
        
        # 计算负载，选择除它以外的一个最好的WebServerAddr，发送给WebServer
        WebServerAddrList = list(WebServerTable.keys())
        WebServerAddr = WebServerAddrList[0]
        for i in WebServerAddrList:
            if i != conn_addr:
                WebServerAddr = i
        conn_socket.send(WebServerAddr.encode())
    elif cmd == 'Init':
        print('一个WebServer正在进行连接...')
        WebServerAddr = str(conn_addr).split('\'')[1]
        ThreadNum = reqList[-2]
        folderFreeSize = reqList[-3]
        files = reqList[0:-3]
        WebServerTable[WebServerAddr] = list((1, folderFreeSize, ThreadNum))
        for file in files:
            FileTable[file].add(WebServerAddr)
        conn_socket.send('ok'.encode())
        print('文件表、WebServer表已更新:')
        print(WebServerTable)
        print(FileTable)
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
        thread_pool.add_job(handle_request, *(conn_socket, conn_addr, ))
    
    s.close()