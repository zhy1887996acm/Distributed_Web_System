# -*- coding: utf-8 -*-

import zerorpc
import os
import zmq

def getFilesSize(filePath, size=0):
    for root, dirs, files in os.walk(filePath):
        for f in files:
            size += os.path.getsize(os.path.join(root, f))
            #print(root,dirs,f)
    return size

class LoadBalancerRPC(object):
    def __init__(self):
        # file folder's path, and let it's total size = 100MB
        self.folderPath = "D:\Python\MyFiles\Web_server\pyzmq_Examples"
        self.folderSize = 100*1024*1024
        # calculate it's left space size
        self.folderFree = self.folderSize - getFilesSize(self.folderPath)
        # PV(Page View)
        self.PV = 0
        # response time, depends on Nerwork
        self.Network = 0
    def update(self):
        self.folderFree = self.folderSize - getFilesSize(self.folderPath)
        self.PV += 10
        self.Network += 1

'''
for receiving files from Client
Receiving file that size is enough.
'''
class ClientRPC(object):
    def __init__(self):
        self.folderPath = "./recv"
        self.IP_Port = 5557
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:%d" % self.IP_Port)
    def recvFile(self, filename):
        self.socket.send_string('WebServer prepared to recv: %s' % filename)
        with open(os.path.join(self.folderPath, filename), 'wb+') as fn:
            while 1:
                data = self.socket.recv_pyobj()
                if data == []:
                    break
                fn.writelines(data)
                self.socket.send_pyobj(filename)
            fn.flush
        fn.close()
        print('%s successfully received!' % filename)
    def __del__(self):
        self.socket.close()
        self.context.destroy()
        print('ClientRPC has destroyed!')

if __name__ == '__main__':
    s = zerorpc.Server(ClientRPC())
    s.bind("tcp://0.0.0.0:4242")
    s.run()