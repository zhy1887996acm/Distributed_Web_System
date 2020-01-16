# -*- coding: utf-8 -*-

import socket
import threading
import sys
import time
import os
import queue
import hashlib

class ThreadPoolManger():
    """线程池管理器，包括创建线程、添加任意任务、"""
    def __init__(self, thread_num):
        # 初始化参数
        self.work_queue = queue.Queue()
        self.thread_num = thread_num
        self.__init_threading_pool(self.thread_num)

    def __init_threading_pool(self, thread_num):
        # 初始化线程池，创建指定数量的线程池
        for i in range(thread_num):
            thread = ThreadManger(self.work_queue)
            thread.start()

    def add_job(self, func, *args):
        # 将任务放入队列，等待线程池阻塞读取，参数是被执行的函数和函数的参数
        self.work_queue.put((func, args))

class ThreadManger(threading.Thread):
    """定义线程类，继承threading.Thread"""
    def __init__(self, work_queue):
        threading.Thread.__init__(self)
        self.work_queue = work_queue
        self.daemon = True
    """重载run()"""
    def run(self):
        # 启动线程，线程没事就会等待下一个task(来自Queue)
        while True:
            target_func, args = self.work_queue.get()# 默认是阻塞出队
            target_func(*args)
            self.work_queue.task_done()


class WebServer():
    """服务器类"""
    def __init__(self):
        # file folder's path, and let it's total size = 100MB
        self.folderPath = "D:\Python\MyFiles\Web_server\pyzmq_Examples"
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


# 创建一个有4个线程的线程池
thread_pool = ThreadPoolManger(4)
Web_Server = WebServer()


# 处理一个客户端的http请求
# 处理该客户端的多个消息，直到断开连接
'''解析msg请求，确定处理函数'''
def handle_request(conn_socket):
    msg = ''
    while True:
        recv_data = conn_socket.recv(1024)
        if not recv_data:
            print('客户端断开')
            break
        msg += recv_data.decode('utf-8')
    #    reply = 'HTTP/1.1 200 OK \r\n\r\n'
    #    reply += 'hello world'
    print('thread %s is running ' % threading.current_thread().name)
    print('接收到的消息：%s' % msg)
    #    conn_socket.send(reply)
    conn_socket.close()

# 等待Balancer的心跳请求(每30s一次)
# 计算当前的负载
# 发送负载信息给Balancer
###该task永远都不会停，除非线程退出
def handle_BalancerReq(conn_socket):
    conn_socket.close()
    return 0

# 处理Clients的下载请求
# find files, 
def handle_Clients_Download(conn_socket):
    conn_socket.close()
    return 0

# 处理Clients的上传请求
def handle_Clients_Upload(conn_socket):
    conn_socket.close()
    return 0

# 
def handle_PeerWebReq(conn_socket):
    conn_socket.close()
    return 0


if __name__ == '__main__':
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = ('127.0.0.1', 8888)
        s.bind(addr)
        s.listen(3)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    
    # 循环等待接收客户端请求
    while True:
        # 阻塞等待请求
        conn_socket, conn_addr = s.accept()
        print('连接地址:%s' % str(conn_addr))
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