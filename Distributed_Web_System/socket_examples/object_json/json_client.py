# -*- coding: utf-8 -*-

import socket
import json
import sys
from collections import defaultdict

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = ('127.0.0.1', 9988)
    s.connect(addr)
except socket.error as msg:
    print(msg)
    sys.exit(1)

mylist = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print(mylist)
json_string = json.dumps(mylist)
s.send(json_string.encode())

mydict = defaultdict(list)
mydict['127.0.0.1:8888'].append('file01')
mydict['127.0.0.1:8887'].append('file02')
mydict['127.0.0.1:8888'].append('file03')
mydict['127.0.0.1:8887'].append('file04')
mydict['127.0.0.1:8886'].append('file04')
mydict['127.0.0.1:8887'].append('file04')
mydict['127.0.0.1:8886'].append('file04')

for key in mydict:
    print(key, mydict[key])
    for v in mydict[key]:
        print(v)

dict_string = json.dumps(mydict)
s.send(dict_string.encode())

s.close()