# -*- coding: utf-8 -*-

import socket
import json
import sys

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = ('127.0.0.1', 9988)
    s.bind(addr)
    s.listen(3)
except socket.error as msg:
    print(msg)
    sys.exit(1)

conn_socket, conn_addr = s.accept()
print('连接地址:%s' % str(conn_addr))

recv_data = conn_socket.recv(1024)
json_string = recv_data.decode()
mylist = json.loads(json_string)
print(mylist)

recv_data = conn_socket.recv(1024)
dict_string = recv_data.decode()
mydict = json.loads(dict_string)

for key in mydict:
    print(key, mydict[key])
    for v in mydict[key]:
        print(v)

conn_socket.close()

s.close()