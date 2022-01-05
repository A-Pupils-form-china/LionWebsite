import socket
import threading


def recv():
    lock = threading.Lock()
    receive = socket.socket()
    receive.connect(("127.0.0.1", 8888))
    print("receive ready")
    while True:
        print(receive.recv(100).decode('utf8').replace("\n", '').replace('\r', ''))


def send():
    sen = socket.socket()
    sen.bind(("127.0.0.1", 8889))
    sen.listen()
    print("send ready")
    client, address = sen.accept()
    while True:
        client.send(input().encode("utf8"))
        print("send")


s = threading.Thread(target=send)
r = threading.Thread(target=recv)
s.start()
r.start()
