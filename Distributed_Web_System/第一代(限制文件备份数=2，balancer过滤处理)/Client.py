# -*- coding: utf-8 -*-

import os
import time
import random
import socket
import hashlib
import json
import threading

from ThreadPool import ThreadPoolManger


files_Client_Path = './files_Client/'
files_WebServer_Path = './files_WebServer/'
balancerAddr = '127.0.0.1'
balancerPort = 8888
WebServerPort = 9000
recvBytes = 1024


'''
向WebServerAddr上传filelist中的文件
'''
def uploading(WebServerAddr, filelist):
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_socket.connect((WebServerAddr, WebServerPort))
    for file in filelist:
        filename = files_Client_Path + file
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
从WebServerAddr下载filelist中的文件
'''
def downloading(WebServerAddr, filelist):
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_socket.connect((WebServerAddr, WebServerPort))
    for file in filelist:
        inputs = 'download ' + file
        conn_socket.send(inputs.encode())
        file_size = conn_socket.recv(1024)
        file_size = int(file_size.decode())
        if file_size == 0:
            print('File not exist in Server!')
            continue
        # 去除重复的文件名
        filename = files_Client_Path + file
        if os.path.isfile(filename):
            namewhat = 1
            nametmp = filename
            while os.path.isfile(filename):
                name, ext = os.path.splitext(nametmp)# 分离文件名和文件格式后缀
                filename = name + '(%d)'%namewhat + ext
                namewhat += 1
        # 开始下载
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
        # 打印两端的md5值，看是否相同
        print('server file md5:',origin_file_md5,'\nrecved file md5:',new_file_md5)
        if origin_file_md5 == new_file_md5:
            print(filename, '%d(bytes)'%file_size, '文件下载成功')
        else:
            print(filename, '文件无效，删除文件!')
            os.remove(filename)
    conn_socket.close()


'''
发送端上传文件：先向balancer请求，再上传到一个WebServer
'''
def Upload(files):
    print('thread %s is running, ' % threading.current_thread().name, files)
    '''连接balancer，获得可上传文件列表和目标地址'''
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_socket.connect((balancerAddr, balancerPort))
    # 向balancer发文件列表
    files.append('upload')
    json_string = json.dumps(files)
    conn_socket.send(json_string.encode())# cmd + files
    # 接收uploadList
    recv_data = conn_socket.recv(recvBytes)# uploadList
    json_string = recv_data.decode()
    uploadList= json.loads(json_string)
    # 解析得到WebServerAddr、filelist
    WebServerAddr = uploadList[0]
    filelist = uploadList[1:]
    #print(filelist, WebServerAddr)
    conn_socket.close()
    
    #连接目标地址的WebServer，上传文件
    uploading(WebServerAddr, filelist)


'''
接收端下载文件：先向balancer请求，再从多个WebServer上下载
'''
def Download(files):
    print('thread %s is running, ' % threading.current_thread().name, files)
    '''连接balancer，获得可上传文件列表和目标地址'''
    conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_socket.connect((balancerAddr, balancerPort))
    # 向balancer发文件列表
    files.append('download')
    json_string = json.dumps(files)
    conn_socket.send(json_string.encode())# cmd + files
    # 接收WebServerAddrList，与files[1:]一一对应
    recv_data = conn_socket.recv(recvBytes)# WebServerAddrList
    json_string = recv_data.decode()
    WebServerAddrList = json.loads(json_string)
    #print(WebServerAddrList)
    conn_socket.close()
    
    # 依次访问不重复的WebServerAddr
    length = len(WebServerAddrList)
    ConnAddrList = list(set(WebServerAddrList))
    for ConnAddr in ConnAddrList:
        filelist = [files[i] for i in range(length) if WebServerAddrList[i]==ConnAddr]
        downloading(ConnAddr, filelist)


'''
多线程模拟客户端请求
'''
thread_pool = ThreadPoolManger(4)

def handle_Input(Req=0, Cnt=5, Threads=4, fileNum=2):
    '''
    Req=0: 上传
    Req=1: 下载
    '''
    if Req==0:
        for root, dirs, files in os.walk(files_Client_Path):
            for C in range(Cnt):
                rs = random.sample(files, fileNum)
                thread_pool.add_job(Upload, *(rs, ))
    elif Req==1:
        for root, dirs, files in os.walk(files_WebServer_Path):
            for C in range(Cnt):
                rs = random.sample(files, fileNum)
                thread_pool.add_job(Download, *(rs, ))


if __name__ == '__main__':
    #Addr = input('\nInput balancerAddr(such as 127.0.0.1):').strip()
    #balancerAddr = Addr
    handle_Input()
    #thread_pool.wait_jobs(60)
    time.sleep(30)
    cmd = input('\n确实要退出吗？Y(y)/N(n):').strip()