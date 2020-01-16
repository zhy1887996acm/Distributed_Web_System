# -*- coding: utf-8 -*-

import os

filename = './files/A.zip'
if os.path.isfile(filename):
    print(os.stat(filename).st_size)
    print(os.path.getsize(filename))
    with open(filename, 'rb') as fn:
        cnt = 0
        for line in fn:
            cnt += len(line)
        print(cnt)
    fn.close()