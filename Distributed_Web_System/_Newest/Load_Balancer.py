# -*- coding: utf-8 -*-
'''
Recv 4 Web Servers' IP and Port, and their files owned.

多用户同时上传同一个文件？如何解决？
'''
import os
import sys
import random
import time
import socket
import threading
import hashlib
import json
from collections import defaultdict

from ThreadPool import ThreadPoolManger


#balancerAddr = '127.0.0.1'  # 默认地址，与本机局域网内IP地址不一样
balancerAddr = input('\n请输入本机局域网内的IP地址:').strip()
balancerPort = 8888  # 默认负载均衡服务器的端口号，各端须保持一致
#WebServerAddr = '127.0.0.1'  # 默认地址
WebServerPort = 9000  # 默认WebServer的端口号，各端须保持一致
recvBytes = 1024
Load_Balance_Time = 5  # 计算负载间隔
folderMaxSize = 100*1024*1024


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
# WebServerAddr --> [alive, folderFreeSize, threads_run, ThreadNum, time_delay]
#                   是否存活   剩余存储     正在运行线程数 总线程数
#               --> [alive, score]
# define: score = (folderFreeSize/folderMaxSize + (ThreadNum-threads_run)/ThreadNum)/time_delay
WebServerTable = defaultdict(list)


def Load_Balance():
    # 独立线程，更新Web Server的状态
    global WebServerTable
    while True:
        WebServerAddrList = list(WebServerTable.keys())
        print('WebServer表已更新:')
        for it in WebServerTable.items():
            print(it)
        for WebServerAddr in WebServerAddrList:
            try:
                conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn_socket.connect((WebServerAddr, WebServerPort))
                inputs = 'Balance ' + 'Alive?'
                starttime = time.time()
                conn_socket.send(inputs.encode())
                data = conn_socket.recv(recvBytes)
                time_delay = time.time() - starttime
                json_string = data.decode()
                folderFreeSize, threads_run, ThreadNum = json.loads(json_string)
                WebServerTable[WebServerAddr] = list((1, (folderFreeSize/folderMaxSize + (ThreadNum - threads_run)/ThreadNum)/time_delay))
                conn_socket.close()
            except socket.error as msg:
                print(WebServerAddr, 'is Dead!')
                WebServerTable[WebServerAddr][0] = 0
                continue
        time.sleep(Load_Balance_Time)

    return 0

def handle_request(conn_socket, conn_addr):
    conn_addr = str(conn_addr).split('\'')[1]
    print('thread %s is running ' % threading.current_thread().name)
    data = conn_socket.recv(recvBytes)
    if not data:
        print('客户端断开')
        return
    #global WebServerTable, FileTable
    json_string = data.decode()
    reqList = json.loads(json_string)
    cmd = reqList[-1]
    print(reqList)
    if cmd == 'download':
        # 处理客户端的下载请求
        files = reqList[0:-1]
        WebServerAddrList = []
        for file in files:
            # 遍历FileTable的key=file的WebServerAddr
            addrs = list(FileTable[file])
            if len(addrs) <= 0:  # file不存在
                continue
            WebServerAddr = addrs[0]
            for addr in addrs:
                if WebServerTable[addr][0] != 0:
                    if WebServerTable[addr][1] > WebServerTable[WebServerAddr][1]:
                        WebServerAddr = addr
            WebServerAddrList.append(WebServerAddr)
        json_string = json.dumps(WebServerAddrList)
        conn_socket.send(json_string.encode())
    elif cmd == 'upload':
        # 处理客户端的上传请求
        # 计算负载，选择一个最好的WebServerAddr，发送给客户端
        # 《这里也可以设计成逐个文件判断是否需要上传，返回列表，但加重负载》
        addrs = list(WebServerTable.keys())
        WebServerAddr = addrs[0]
        for addr in addrs:
            if WebServerTable[addr][0] != 0:
                if WebServerTable[addr][1] > WebServerTable[WebServerAddr][1]:
                    WebServerAddr = addr
        conn_socket.send(WebServerAddr.encode())
    elif cmd == 'backup':
        # 处理WebServer的备份请求
        # 更新文件列表
        files = reqList[0:-1]
        for file in files:
            FileTable[file].add(conn_addr)
        print('文件表已更新:')
        for it in FileTable.items():
            print(it)
        # 计算负载，选择除它以外的一个最好的WebServerAddr，发送给WebServer
        # 《这里也可以设计成逐个文件判断是否需要备份，对方的已有文件就无需备份，
        #   但是，完全可由WebServer之间自行判断，只需发送一个WebServerAddr，
        #   也保证了同一个文件一定有备份，并减少负载均衡的负载。》
        addrs = list(WebServerTable.keys())
        WebServerAddr = addrs[0]
        for addr in addrs:
            if addr != conn_addr and WebServerTable[addr][0] != 0:
                if WebServerTable[addr][1] > WebServerTable[WebServerAddr][1]:
                    WebServerAddr = addr
        if WebServerAddr == conn_addr:
            WebServerAddr = 'Error! Can not backup! Only one WebServer?'
        conn_socket.send(WebServerAddr.encode())
    elif cmd == 'Init':
        print('一个WebServer正在进行连接...')
        WebServerAddr = conn_addr
        ThreadNum = reqList[-2]
        threads_run = reqList[-3]
        folderFreeSize = reqList[-4]
        files = reqList[0:-4]
        WebServerTable[WebServerAddr] = list((1, folderFreeSize/folderMaxSize + (ThreadNum - threads_run)/ThreadNum))
        for file in files:
            FileTable[file].add(WebServerAddr)
        conn_socket.send('ok'.encode())
        print('WebServer表已更新:')
        for it in WebServerTable.items():
            print(it)
        print('文件表已更新:')
        for it in FileTable.items():
            print(it)
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

    thread_pool.add_job(Load_Balance)
    # 循环等待接收客户端请求
    while True:
        ####################print('>>>>>>>>>>等待请求...')
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