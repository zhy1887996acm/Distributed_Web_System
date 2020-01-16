# -*- coding: utf-8 -*-

import threading
import queue

class ThreadPoolManger():
    """线程池管理器，包括创建线程、添加任意任务、"""
    def __init__(self, thread_num):
        # 初始化参数
        self.work_queue = queue.Queue()
        self.thread_num = thread_num
        self.threadList = []
        self.__init_threading_pool(self.thread_num)

    def __init_threading_pool(self, thread_num):
        # 初始化线程池，创建指定数量的线程池
        for i in range(thread_num):
            thread = ThreadManger(self.work_queue)
            thread.start()
            self.threadList.append(thread)

    def add_job(self, func, *args):
        # 将任务放入队列，等待线程池阻塞读取，参数是被执行的函数和函数的参数
        self.work_queue.put((func, args))

    def wait_jobs(self, tim=15):
        print('[Warning]: %d秒后，主进程将自动退出' % tim)
        #for thread in self.threadList:
        #    thread.join(30)
        self.threadList[0].join(tim)
        print('[Warning]: 主进程退出，所有子线程被销毁...')

    def get_thread_num(self):
        return self.work_queue.qsize()

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

# 创建一个有4个线程的线程池
#thread_pool = ThreadPoolManger(4)
