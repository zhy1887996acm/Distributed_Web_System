# -*- coding: utf-8 -*-

import time
from ThreadPool import ThreadPoolManger

thread_pool = ThreadPoolManger(4)

def printA(i):
    print(i)
    time.sleep(0.5)

for i in range(10):
    thread_pool.add_job(printA, *(i,))

thread_pool.wait_jobs(10)