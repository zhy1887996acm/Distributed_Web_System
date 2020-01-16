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


# 创建一个有4个线程的线程池
thread_pool = ThreadPoolManger(4)
Web_Server = WebServer()


# 处理一个客户端的请求，一个客户端可能有多个请求，循环等待
# 处理该客户端的多个消息，直到断开连接
'''解析多个msg请求，为不同msg确定处理函数'''
def handle_socket(conn_socket):
    print('thread %s is running ' % threading.current_thread().name)
    
    upload_file_list = []
    while True:
        data = conn_socket.recv(1024)
        if not data:
            print('客户端断开')
            break
        
        # 第一次接收的是命令，包括get和文件名，用filename接受文件名
        cmd, filename = data.decode().split(' ',1)
        
        if cmd == 'download' or 'backup':
            # 处理客户端的下载请求/Web端的备份请求
            handle_Clients_Download(conn_socket, filename)
        elif cmd == 'upload':
            # 处理客户端的上传请求
            print('接收到upload请求...')
            flag = handle_Clients_Upload(conn_socket, filename)
            if (flag):
                upload_file_list.append(filename)
        elif cmd == 'Balancer':
            # 处理Balancer的心跳请求
            break
        else:
            print('bye')
    conn_socket.close()
    # 若是接收文件，则通知Balancer，让其更新文件列表
    if len(upload_file_list) > 0:
        print('接收到文件：', upload_file_list)
        #for filename in upload_file_list:
            # 对文件进行筛选、备份


# 等待Balancer的心跳请求(每30s一次)
# 计算当前的负载
# 发送负载信息给Balancer
###该task永远都不会停，除非线程退出
def handle_BalancerReq(conn_socket):
    print()
    return 0

# 处理Clients的下载请求
# find files, 
def handle_Clients_Download(conn_socket, filename):
    filename = './files/' + filename
    if not os.path.isfile(filename):
        error = '0'# 文件不存在，返回'0'给客户端
        conn_socket.send(error.encode())
        return
    # 发送文件大小
    conn_socket.send(str(os.stat(filename).st_size).encode())
    # 生成md5对象
    m = hashlib.md5()
    with open(filename, 'rb') as fn:
        # 开始发文件
        for line in fn:
            # 发一行更新一下md5的值，因为不能直接md5文件
            # 到最后读完就是一个文件的md5的值
            m.update(line)
            conn_socket.send(line)
        # 打印整个文件的md5
        print('file md5:', m.hexdigest())
    fn.close()
    # send md5
    conn_socket.send(m.hexdigest().encode())
    print('file [', filename, '] sended to [', addr, ']')
    print()

# 处理Clients的上传请求
def handle_Clients_Upload(conn_socket, filename):
    filename = './files/' + filename
    if os.path.isfile(filename):
        error = 'file already exist in Server!'# 文件已存在，不能上传
        conn_socket.send(error.encode())
        return False
    conn_socket.send('ok'.encode())
    print('ok')
    # 接收文件大小，输出文件大小 or 文件不存在！
    file_size = conn_socket.recv(1024)
    print('file size:', file_size.decode())
    # 转整形，方便下面大小判断
    file_size = int(file_size.decode())
    if file_size == 0:
        print('File Not Exist')
        return False
    # 赋值方便最后打印大小
    new_file_size = file_size
    # 生成md5对象
    m = hashlib.md5()
    
    cnt = 0# 记录接收字节数
    with open(filename, 'wb') as fn:
        while new_file_size > 0:
            data = conn_socket.recv(1024)
            # 收多少减多少
            new_file_size -= len(data)
            cnt += len(data)
            # 同步服务器端，收一次更新一次md5
            m.update(data)
            # 写入数据
            fn.write(data)
        fn.flush
    # 得到下载完的文件的md5
    new_file_md5 = m.hexdigest()
    print('file recv:', cnt)
    print('file saved in:', filename)
    fn.close()
    # 接收服务器端的文件的md5
    server_file_md5 = conn_socket.recv(1024)
    
    # 打印两端的md5值，看是否相同
    print('server file md5:', server_file_md5.decode())
    print('recved file md5:', new_file_md5)
    print()
    if server_file_md5 == new_file_md5:
        return True
    else:
        print(filename, '文件无效，删除文件')
        os.remove(filename)
        return False

# 
def handle_PeerWebReq(conn_socket):
    
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
        print('>>>>>>>>>>等待请求...')
        # 阻塞等待请求
        conn_socket, conn_addr = s.accept()
        print('收到请求，连接地址:%s' % str(conn_addr))
        # 一旦有请求了，把socket扔到指定处理函数，放进任务队列
        
        '''
        这里单纯通过连接无法决定分配哪个处理函数：
            客户端的请求？Balancer的请求？其他WebServer的请求？
        需要从请求消息中解析请求类型
        最后，确定处理函数之后连同conn_socket送入线程池
        '''
        
        
        # 等待线程池分配线程处理
        thread_pool.add_job(handle_socket, *(conn_socket, ))
    
    s.close()