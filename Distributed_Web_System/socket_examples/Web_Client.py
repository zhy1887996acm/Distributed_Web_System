# -*- coding: utf-8 -*-

import socket
import sys
import time
import threading
import hashlib

# 定义需要线程池执行的任务
# 每个线程创建一个套接字与服务器进行连接
def do_job():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 8888))
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    # 循环发送请求
    cnt = 0
    while cnt<3:# 一次发送8个消息
        cnt += 1
        data = 'Data %d' % cnt
        s.send(data.encode('utf-8'))
        time.sleep(1)
    s.close()

if __name__ == '__main__':
    # 创建包括3个线程的线程池
    threads = []
    for i in range(3):
        t = threading.Thread(target=do_job)
        t.daemon=True # 设置线程daemon  主线程退出，daemon线程也会推出，即使正在运行
        threads.append(t)
        t.start()
    #等待所有线程任务结束。
    for t in threads:
        t.join()
    print("所有线程任务完成")