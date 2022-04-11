import os.path
import numpy as np
import cv2
import struct
import socket
import time

abs_path = os.path.abspath(__file__) #获取绝对路径
dir_name = os.path.dirname(abs_path)
save_path = os.path.join(dir_name, 'recd.log')


def SaveAccessLog(addr):
    stamp = time.time()
    timeArray = time.localtime(stamp)
    styletime = time.strftime("%Y-%m-%d_%H:%M:%S", timeArray)
    recd = 'UTC+8/{0}/客户端接入/{1}\n'.format(styletime, addr)
    with open(save_path, 'a+') as fs:
        fs.seek(0, 0)
        fs.write(recd)
    fs.close()
    return recd


def AccessServer():
    SocA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SocA.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    SocA.bind(('0.0.0.0', 8000))
    # 设置监听数
    SocA.listen(5)

    while True:
        conn, addr = SocA.accept()
        print(SaveAccessLog(addr))
        # 接收客户端消息
        recv_data = conn.recv(1024)
        # client_socket.send("收到！！".encode("utf-8"))

        if recv_data:
            try:
                img = cv2.imread(recv_data.decode("utf-8"))  # cv2.flip(img, 1)
                # 压缩图片
                img_encode = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 40])[1]
                data_encode = np.array(img_encode)
                data = data_encode.tobytes()
                fhead = struct.pack('Q', len(data))
                #print(fhead)
                conn.send(fhead)
                for i in range(len(data) // 1024 + 1):
                    if 1024 * (i + 1) > len(data):
                        conn.send(data[1024 * i:])
                    else:
                        conn.send(data[1024 * i:1024 * (i + 1)])
                conn.close()

            except UnicodeDecodeError:
                print("Illeagal Codec")
        conn.close()




"""
    fhead = struct.pack('l', len(data))
    # 发送文件头:
    conn.send(fhead)
    # 循环发送图片码流
    for i in range(len(data) // 1024 + 1):
        if 1024 * (i + 1) > len(data):
            conn.send(data[1024 * i:])
        else:
            conn.send(data[1024 * i:1024 * (i + 1)])
"""