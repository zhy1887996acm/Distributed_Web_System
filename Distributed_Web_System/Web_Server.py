# -*- coding: utf-8 -*-

import os
import sys
import random
import socket
import hashlib
import json
import threading
import signal

from ThreadPool import ThreadPoolManger


'''#################### 初始化 管理文件目录 文件夹大小 ####################'''
#foldername_Client = 'files_Client'
foldername_WebServer = 'files_WebServer'
files_WebServer_Path = os.getcwd() + '\\' + foldername_WebServer + '\\'
if not os.path.exists(files_WebServer_Path):
    os.mkdir(files_WebServer_Path)

folderMaxSize = 100*1024*1024
folderFreeSize = 0
# 根据指定的folderSize计算folderPath的剩余存储空间
def UpdateFolderFreeSize():
    global folderFreeSize
    size=0
    for root, dirs, files in os.walk(files_WebServer_Path):
        #print(root, dirs, files)
        for f in files:
            size += os.path.getsize(os.path.join(root, f))
    folderFreeSize = folderMaxSize - size
UpdateFolderFreeSize()

balancerAddr = '127.0.0.1'
balancerPort = 8888
WebServerAddr = '127.0.0.1'
WebServerPort = 9000
#WebServer_backup_Port = 9888# 本地测试，联机WebServer Port统一为9000
recvBytes = 1024
ThreadNum = 4


'''#################### 定义线程处理函数 ####################'''

'''
先收到download filename，开始处理Client的下载请求
一定是send()在最后
'''
def handle_Clients_Download(conn_socket, filename):
    filename = files_WebServer_Path + filename
    if not os.path.isfile(filename):
        error = '0'# 文件不存在，返回'0'给客户端
        conn_socket.send(error.encode())
        return False
    # 发送文件大小
    conn_socket.send(str(os.stat(filename).st_size).encode())
    confirm = conn_socket.recv(recvBytes)
    IsRecv = confirm.decode()
    print(IsRecv)
    if IsRecv != 'Prepared':
        return False
    # 生成md5对象
    m = hashlib.md5()
    with open(filename, 'rb') as fn:
        # 开始发文件，发一行更新一下md5的值，因为不能直接md5文件
        # 到最后读完就是整个文件的md5的值
        for line in fn:
            m.update(line)
            conn_socket.send(line)
    fn.close()
    origin_file_md5 = m.hexdigest()
    # 接收客户端接收成功
    confirm = conn_socket.recv(recvBytes)
    # send md5 to Client
    conn_socket.send(origin_file_md5.encode())
    print(filename, '===> sended ===> Client')
    return True

'''
先收到upload filename，开始处理Client的上传请求
一定是send()在最后
'''
def handle_Clients_Upload(conn_socket, filename):
    filename = files_WebServer_Path + filename
    if os.path.isfile(filename):
        error = 'File already exist in Server!'# 文件已存在，不能上传
        conn_socket.send(error.encode())
        return False
    conn_socket.send('ok'.encode())
    print('ok')
    # 接收文件大小，输出文件大小 or 文件不存在！
    file_size = conn_socket.recv(recvBytes)
    print('file size:', file_size.decode())
    # 转整形，方便下面大小判断
    file_size = int(file_size.decode())
    if file_size == 0:
        error = 'File is NULL'# 文件不存在！
        conn_socket.send(error.encode())
        return False
    conn_socket.send('Prepared'.encode())
    # 赋值方便最后打印大小
    new_file_size = file_size
    # 生成md5对象
    m = hashlib.md5()
    with open(filename, 'wb') as fn:
        while new_file_size > 0:
            data = conn_socket.recv(recvBytes)
            new_file_size -= len(data)# 收多少减多少
            m.update(data)# 同步发送端，收一次更新一次md5
            fn.write(data)
        fn.flush
    fn.close()
    # 得到下载完的文件的md5
    new_file_md5 = m.hexdigest()
    #print('file recv:', file_size)
    #print('file saved in:', filename)
    conn_socket.send('ok'.encode())
    # 接收服务器端的文件的md5
    server_file_md5 = conn_socket.recv(recvBytes)
    origin_file_md5 = server_file_md5.decode()
    conn_socket.send(new_file_md5.encode())
    # 打印两端的md5值，看是否相同
    print('server file md5:',origin_file_md5,'\nrecved file md5:',new_file_md5)
    if origin_file_md5 == new_file_md5:
        print(filename, '%d(bytes)'%file_size, '文件下载成功')
        return True
    else:
        print(filename, '文件无效，删除文件!')
        os.remove(filename)
        return False

'''
向WebServerAddr上传filelist中的文件
'''
def uploading(WebServerAddr, filelist):
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_socket.connect((WebServerAddr, WebServerPort))
    for file in filelist:
        filename = files_WebServer_Path + file
        # 文件不存在则跳过
        if os.path.isfile(filename):
            inputs = 'upload ' + file
            conn_socket.send(inputs.encode())# cmd + file
            confirm = conn_socket.recv(recvBytes)
            IsRecv = confirm.decode()
            print(IsRecv)
            if IsRecv != 'ok':
                continue
            # 发送文件大小
            conn_socket.send(str(os.stat(filename).st_size).encode())
            confirm = conn_socket.recv(recvBytes)
            IsRecv = confirm.decode()
            print(IsRecv)
            if IsRecv != 'Prepared':
                continue
            # 生成md5对象
            m = hashlib.md5()
            with open(filename, 'rb') as fn:
                # 开始发文件，发一行更新一下md5的值，因为不能直接md5文件
                # 到最后读完就是整个文件的md5的值
                for line in fn:
                    m.update(line)
                    conn_socket.send(line)
            fn.close()
            origin_file_md5 = m.hexdigest()
            # 接收服务器接收成功
            confirm = conn_socket.recv(recvBytes)
            # send md5
            conn_socket.send(origin_file_md5.encode())
            server_file_md5 = conn_socket.recv(recvBytes)
            new_file_md5 = server_file_md5.decode()
            print('file md5:',origin_file_md5,'\nrecved file md5:',new_file_md5)
            if origin_file_md5 == new_file_md5:
                print(filename, '===> sended ===>', WebServerAddr)
            else:
                print(filename, 'send Error! Check for the Network.')
    conn_socket.close()

'''
WebServer备份文件：先向balancer请求，让其更新文件列表，再上传到另一个WebServer
'''
def handle_Server_Backup(files):
    print('thread %s is running, ' % threading.current_thread().name, files)
    '''连接balancer，获得目标地址'''
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_socket.connect((balancerAddr, balancerPort))
    # 向balancer发文件列表
    files.append('backup')
    json_string = json.dumps(files)
    conn_socket.send(json_string.encode())# cmd + files
    # 接收一个WebServerAddr
    recv_data = conn_socket.recv(recvBytes)
    WebServerAddr = recv_data.decode()
    conn_socket.close()
    
    #连接目标地址的WebServer，上传文件
    uploading(WebServerAddr, files)

'''
# 处理一个客户端的请求，一个客户端可能有多个请求，循环等待
# 处理该客户端的多个消息，直到断开连接
解析多个msg请求，为不同msg确定处理函数
'''
def handle_socket(conn_socket):
    print('thread %s is running ' % threading.current_thread().name)
    # 记录接收上传的文件列表
    recvFilesList = []
    while True:
        data = conn_socket.recv(recvBytes)
        if not data:
            print('客户端断开连接')
            break
        print(data.decode())
        # 第一次接收的是命令，包括get和文件名，用filename接受文件名
        cmd, filename = data.decode().split(' ',1)
        if cmd == 'download':
            # 处理客户端的下载请求请求
            handle_Clients_Download(conn_socket, filename)
        elif cmd == 'upload':
            # 处理客户端上传/WebServer备份de请求
            flag = handle_Clients_Upload(conn_socket, filename)
            if (flag):
                recvFilesList.append(filename)
        elif cmd == 'Balancer':
            # 处理Balancer的心跳请求
            break
        else:
            print('bye')
    conn_socket.close()
    # 若是接收文件，则通知Balancer，让其更新文件列表，并获取一个备份WebServer地址
    if len(recvFilesList) > 0:
        print('接收到文件：', recvFilesList)
        #handle_Server_Backup(recvFilesList)

'''
# 等待Balancer的心跳请求(每30s一次)
# 计算当前的负载
# 发送负载信息给Balancer
###该task永远都不会停，除非线程退出
'''
def handle_BalancerReq():
    
    print()
    return 0


'''#################### 连接、处理请求 ####################'''

''' 尝试连接Balancer Server，初始化交互消息 '''
try:
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        balancerAddr = input('\n请输入Balancer的IP地址:').strip()
        if balancerAddr == '127':
            balancerAddr = '127.0.0.1'
        print('成功连接上Balancer Server:', balancerAddr)
        conn_socket.connect((balancerAddr, balancerPort))
        #if conn_socket.type == '':
        if True:
            break
    # 发送初始消息
    for root, dirs, files in os.walk(files_WebServer_Path):
        #print(root, dirs, files)
        files.append(folderFreeSize)
        files.append(ThreadNum)
        files.append('Init')
        json_string = json.dumps(files)
        conn_socket.send(json_string.encode())# files + folderFreeSize + ThreadNum
        # 接收Balancer确认消息
        recv_data = conn_socket.recv(recvBytes)
    conn_socket.close()
except socket.error as msg:
    conn_socket.close()
    print(msg)
    sys.exit(1)


# 创建多线程Web Server
thread_pool = ThreadPoolManger(ThreadNum)

''' 尝试创建socket作为服务器 '''
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = (WebServerAddr, WebServerPort)
    s.bind(addr)
    s.listen(3)
except socket.error as msg:
    s.close()
    print(msg)
    sys.exit(1)

''' 循环等待接收客户端请求 '''
while True:
    print('>>>>>>>>>>等待请求...')
    # 阻塞等待请求
    conn_socket, conn_addr = s.accept()
    print('WebServer接收到请求，连接地址:%s' % str(conn_addr))
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