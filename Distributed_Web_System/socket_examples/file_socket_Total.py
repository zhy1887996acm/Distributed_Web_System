# -*- coding: utf-8 -*-

import os


'''Sender'''
FILENAME = 'A.zip'
if not os.path.isfile(FILENAME):
    print('is not a file')
with open(FILENAME, 'rb') as fn:
    while True:
        line = fn.readlines(256)# read 256 Bytes every time
        if line == []:
            break
    
fn.close()
print('%s successfully send!' % FILENAME)


'''Recver'''
FILENAME = 'New_'
with open(FILENAME, 'wb+') as fn:
    while True:
        #recv: data = socket.recv_pyobj()
        data = 'socket.recv_pyobj()'
        if data == []:
            break
        fn.writelines(data)
    fn.flush
fn.close()