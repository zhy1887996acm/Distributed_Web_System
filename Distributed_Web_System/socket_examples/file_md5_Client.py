# -*- coding: utf-8 -*-
'''
下载文件：
    判断文件是否已存在本地，若是，则增加后缀(i)
    向服务端发送input的msg，包括cmd和filename
    接收服务端的返回消息，文件大小，若文件大小为“0”则表示“文件不存在”（一般不会出现）
    然后一行一行接收文件（限制每次1024字节）
    
'''

import socket
import os
import hashlib
client = socket.socket()
client.connect(('localhost', 9000))

def handle_Clients_Download(inputs):
    client.send(inputs.encode())# 发送input的msg
    # 接收文件大小，输出文件大小，为0表示文件不存在！
    file_size = client.recv(1024)
    # 转整形，方便下面大小判断
    file_size = int(file_size.decode())
    print('file size:', file_size)
    if file_size == 0:
        print('file not exist in Server')
        return False
    
    cmd, filename = inputs.split(' ',1)
    # 文件名已存在，仍然可下载，在文件名后面加上编号(副本)
    if os.path.isfile(filename):
        namewhat = 1
        nametmp = filename
        while os.path.isfile(filename):
            name, ext = os.path.splitext(nametmp)# 分离文件名和文件格式后缀
            filename = name + '(%d)'%namewhat + ext
            namewhat += 1

    left_file_size = file_size
    # 生成md5对象
    m = hashlib.md5()
    
    cnt = 0# 记录接收字节数
    with open(filename, 'wb') as fn:
        while left_file_size > 0:
            data = client.recv(1024)
            # 收多少减多少
            left_file_size -= len(data)
            cnt += len(data)
            # 同步服务器端，收一次更新一次md5
            m.update(data)
            # 写入数据
            fn.write(data)
        fn.flush
    # 得到下载完的文件的md5
    new_file_md5 = m.hexdigest()
    print('file recv:', cnt)
    print('file saved', filename)
    fn.close()
    # 接收服务器端的文件的md5
    server_file_md5 = client.recv(1024)
    
    # 打印两端的md5值，看是否相同
    print('server file md5:', server_file_md5.decode())
    print('recved file md5:', new_file_md5)
    return False

def handle_Clients_Upload(inputs):
    cmd, filename = inputs.split(' ',1)
    # 客户端接收上传确认消息
    if not os.path.isfile(filename):
        print('File Not Exist')# 文件不存在，取消上传
        return False
    client.send(inputs.encode())# 发送input的msg
    confirm = client.recv(1024)
    IsRecv = confirm.decode()
    print(IsRecv)
    if IsRecv != 'ok':
        return False
    
    # 发送文件大小
    client.send(str(os.stat(filename).st_size).encode())
    confirm = client.recv(1024)
    IsRecv = confirm.decode()
    print(IsRecv)
    if IsRecv != 'ok':
        return False
    # 生成md5对象
    m = hashlib.md5()
    with open(filename, 'rb') as fn:
        # 开始发文件
        for line in fn:
            # 发一行更新一下md5的值，因为不能直接md5文件
            # 到最后读完就是一个文件的md5的值
            m.update(line)
            client.send(line)
        # 打印整个文件的md5
        print('file md5:', m.hexdigest())
    fn.close()
    # send md5
    client.send(m.hexdigest().encode())
    print('file [', filename, '] sended to [Server]')
    return True

while True:
    # 格式：upload xxx
    inputs = input('\nwhat do u want?:').strip()
    if inputs.startswith('upload'):
        handle_Clients_Upload(inputs)
    elif inputs.startswith('download'):
        handle_Clients_Download(inputs)
    else:
        break
client.close()