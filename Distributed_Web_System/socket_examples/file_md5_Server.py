# -*- coding: utf-8 -*-

# 1.读取客户端发来的文件名
# 2.查找文件是否存在
# 3.打开该文件
# 4.检测文件大小
# 5.发送大小给客户端
# 6.等待客户端确认
# 7.开始边读边发
# 8.发送md5校验

import socket
import os
import hashlib

server = socket.socket()
server.bind(('localhost', 9000))
server.listen()
print('等待命令...')
conn_socket, addr = server.accept()

# 
def SendFileToClient(filename):
    filename = './files/' + filename
    if not os.path.isfile(filename):
        error = '0'# 文件不存在，返回'0'给客户端
        conn_socket.send(error.encode())
        return False
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
    return True

def SaveFileFromClient(filename):
    filename = './files/' + filename
    if os.path.isfile(filename):
        error = 'file already exist in Server!'# 文件已存在，不能上传
        conn_socket.send(error.encode())
        return False
    conn_socket.send('ok'.encode())
    # 接收文件大小，输出文件大小 or 文件不存在！
    file_size = conn_socket.recv(1024)
    print('file size:', file_size.decode())
    # 转整形，方便下面大小判断
    file_size = int(file_size.decode())
    if file_size == 0:
        error = 'File Not Exist'# 文件不存在！
        print(error)
        conn_socket.send(error.encode())
        return False
    conn_socket.send('ok'.encode())
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
    return True

while True:
    '''处理同一个客户端的多个文件上传/下载请求'''
    data = conn_socket.recv(1024)
    if not data:
        print('客户端断开')
        break
    # 第一次接收的是命令，包括get和文件名，用filename接受文件名
    cmd, filename = data.decode().split(' ',1)
    
    if cmd == 'download':
        SendFileToClient(filename)
    elif cmd == 'upload':
        SaveFileFromClient(filename)
server.close()