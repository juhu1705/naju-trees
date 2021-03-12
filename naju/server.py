from socket import *

from past.builtins import raw_input

HOST = "127.0.0.1"  # local host
PORT = 6665  # open port 7000 for connection


def run():
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.bind((HOST, PORT))
    except OSError:
        return
    s.listen(1)  # how many connections can it receive at one time
    print("Server is started on port " + HOST + ":" + str(PORT))
    while True:
        conn, addr = s.accept()  # accept the connection
        print("Connected by: ", addr)  # print the address of the person connected
        disconnect = False
        while not disconnect:
            data = conn.recv(1024)  # how many bytes of data will the server receive
            print("Received: ", repr(data))
            reply = raw_input("Reply: ")  # server's reply to the client
            conn.sendall(reply)
