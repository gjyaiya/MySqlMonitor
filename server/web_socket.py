#!/usr/bin/env python
# coding:utf-8


import base64
import hashlib
import socket
import struct
import threading

HOST = 'localhost'
PORT = 3368
MAGIC_STRING = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
HANDSHAKE_STRING = "HTTP/1.1 101 Switching Protocols\r\n" \
                   "Upgrade:websocket\r\n" \
                   "Connection: Upgrade\r\n" \
                   "Sec-WebSocket-Accept: {1}\r\n" \
                   "WebSocket-Location: ws://{2}/\r\n" \
                   "WebSocket-Protocol:chat\r\n\r\n"

clients = []


def recv_data(content):
    print content
    for client in clients:
        client.send_data(content)


class Client(threading.Thread):
    def __init__(self, conn, recv_func):
        threading.Thread.__init__(self)
        self.conn = conn
        self.shake = False
        self.recv_func = recv_func

    def run(self):
        while True:
            if not self.shake:
                self.shake = self.handshake()
            self.recv_func(self.recv_data())

    def handshake(self):
        headers = {}
        content = self.conn.recv(1024)

        if not len(content):
            return False

        header, data = content.split('\r\n\r\n', 1)
        for line in header.split('\r\n')[1:]:
            key, val = line.split(': ', 1)
            headers[key] = val

        if 'Sec-WebSocket-Key' not in headers:
            print ('This socket is not websocket, client close.')
            self.conn.close()
            return False

        sec_key = headers['Sec-WebSocket-Key']
        res_key = base64.b64encode(hashlib.sha1(sec_key + MAGIC_STRING).digest())

        str_handshake = HANDSHAKE_STRING.replace('{1}', res_key).replace('{2}', HOST + ':' + str(PORT))
        self.conn.send(str_handshake)
        clients.append(self)
        return True

    def send_data(self, data):
        token = "\x81"
        length = len(data)
        if length < 126:
            token += struct.pack("B", length)
        elif length <= 0xFFFF:
            token += struct.pack("!BH", 126, length)
        else:
            token += struct.pack("!BQ", 127, length)
        data = '%s%s' % (token, data)
        result = False
        try:
            self.conn.send(data)
            result = True
        finally:
            return result

    def recv_data(self):
        all_data = self.conn.recv(1024)
        if not len(all_data):
            return ""
        code_len = ord(all_data[1]) & 127
        if code_len == 126:
            masks = all_data[4:8]
            data = all_data[8:]
        elif code_len == 127:
            masks = all_data[10:14]
            data = all_data[14:]
        else:
            masks = all_data[2:6]
            data = all_data[6:]
        raw_str = ""
        i = 0
        for d in data:
            raw_str += chr(ord(d) ^ ord(masks[i % 4]))
            i += 1
        return raw_str


def start_ws(parse_recv_func):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((HOST, PORT))
        sock.listen(5)
        while True:
            conn, address = sock.accept()
            client = Client(conn, parse_recv_func)
            client.start()
    finally:
        sock.close()


if __name__ == '__main__':
    start_ws(recv_data)
