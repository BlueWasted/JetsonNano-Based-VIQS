#!coding=utf-8

import threading
import socket
import struct
import sys
import os
from Match import database
from AccessImg import AccessServer


abs_path = os.path.abspath(__file__)  # 获取绝对路径
dir_name = os.path.dirname(abs_path)
path_t = os.path.join(dir_name, 'Nano/txt')
path_img = os.path.join(dir_name, 'Nano/img')
threadLock = threading.Lock()


class dataThread(threading.Thread):
    def __init__(self, conn, addr, name):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.name = name

    def run(self):
        print("开启线程： " + self.name)
        # 获取锁，用于线程同步
        threadLock.acquire()
        deal_data(self.conn, self.addr)
        # 释放锁，开启下一个线程
        threadLock.release()


class analyzeThread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        print("开启线程： " + self.name)
        # 获取锁，用于线程同步
        threadLock.acquire()
        database()
        # 释放锁，开启下一个线程
        threadLock.release()


class accessThread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        print("开启线程： " + self.name)
        # 获取锁，用于线程同步
        threadLock.acquire()
        AccessServer()
        # 释放锁，开启下一个线程
        threadLock.release()


def dir_build(Path):
    if not os.path.exists(Path):
        os.mkdir(Path)
        print("{0}目录已创建\n".format(Path))


def socket_service():
    threads = []
    a = threading.Thread(target=AccessServer)
    a.start()
    try:
        Soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定端口为5000
        Soc.bind(('0.0.0.0', 6000))
        # 设置监听数
        Soc.listen(5)

    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print('Waiting connection...')

    while True:
        thread2 = analyzeThread('Analyze')
        thread2.start()
        connt, addrt = Soc.accept()
        thread1 = dataThread(connt, addrt, 'Transmit')
        thread1.start()
        threads.append(thread1)
        threads.append(thread2)
        for t in threads:
            t.join()
        # a = threading.Thread(target=AccessServer)
        # m.start()
        # a.start()

        # 接收数据
        # t = threading.Thread(target=deal_data, args=(connt, addrt))
        # t.start()


def deal_data(conn, addr):
    print('Accept new connection from {0}'.format(addr))
    # conn.settimeout(500)
    # 收到请求后的回复
    conn.send('Confirmed!'.encode('utf-8'))

    while 1:
        # 申请相同大小的空间存放发送过来的文件名与文件大小信息
        fileinfo_size = struct.calcsize('128sl')
        # 接收文件名与文件大小信息
        buf = conn.recv(fileinfo_size)
        # 判断是否接收到文件头信息
        if buf:
            # 获取文件名和文件大小
            filename, filesize = struct.unpack('128sl', buf)
            # fn = filename.strip(b'\00')
            # fn = fn.decode()
            fn = filename.decode().strip('\x00')
            print('file new name is {0}, filesize is {1}'.format(str(fn), filesize))
            recvd_size = 0  # 定义已接收文件的大小
            name = fn.replace(":", "%", 2)
            if fn[-4:].upper() == '.JPG':
                new_filename = os.path.join(path_img,
                                            '%'.join((name.split(
                                                '_'))))  # 在服务器端新建图片名（可以不用新建的，直接用原来的也行，只要客户端和服务器不是同一个系统或接收到的图片和原图片不在一个文件夹下）
            elif fn[-4:].upper() == '.TXT':
                new_filename = os.path.join(path_t,
                                            '%'.join((name.split('_'))))
            else:
                continue
            fp = open(new_filename, 'wb')
            print('start receiving...')

            # 将分批次传输的二进制流依次写入到文件
            while not recvd_size == filesize:
                if filesize - recvd_size > 1024:
                    data = conn.recv(1024)
                    recvd_size += len(data)
                else:
                    data = conn.recv(filesize - recvd_size)
                    recvd_size = filesize
                fp.write(data)
            fp.close()
            print('end receive...')
        # 传输结束断开连接
        conn.close()
        break


if __name__ == "__main__":
    dir_build(os.path.join(dir_name, 'Nano'))
    dir_build(path_img)
    dir_build(path_t)
    socket_service()
