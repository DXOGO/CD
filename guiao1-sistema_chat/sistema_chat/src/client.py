# Echo client program
"""CD Chat client program"""

import logging
import socket
import sys
import selectors
import fcntl
import os

from .protocol import CDProto, CDProtoBadFormat

HOST = 'localhost'    # The remote host
PORT = 5555       # The same port as used by the server  -> OBRIGATORIO PARA FUNCIONAR

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)

class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (HOST, PORT)
        self.sel = selectors.DefaultSelector()
        self.channel = None

    def send(self, msg: str = "Hello, world") -> str:    # ignorar

        encode_msg = msg.encode("utf-8")
        self.clientsock.send(enconde_msg)
        

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        
        self.clientsock.connect(self.addr)
        self.sel.register(self.clientsock, selectors.EVENT_READ, self.receive_msg)
        print(f"[{self.name}] connecting to server {self.addr[0]}:{self.addr[1]}")
        register_server = CDProto.register(self.name)
        CDProto.send_msg(self.clientsock, register_server) # client -> server

    
    def receive_msg(self, conn, mask):

        pass_msg = CDProto.recv_msg(self.clientsock)
        
        if pass_msg.command == "message":
            logging.debug('received "%s', pass_msg.message)
        
        print(pass_msg.message)


    def got_keyboard_data(self,stdin, mask):
        
        input_msg = stdin.read().replace("\n", "")
        w = input_msg.split(" ")

        if(w[0] == "exit"):
            self.sel.unregister(self.clientsock)
            self.clientsock.close()
            sys.exit(f"Until next time {self.name}!")

        elif(w[0] == "/join" and len(w) == 2):
            self.channel = w[1]
            print(f"{self.name} joined {self.channel}")
            CDProto.send_msg(self.clientsock, CDProto.join(self.channel))

        else:
            msg = CDProto.message(input_msg, self.channel)
            CDProto.send_msg(self.clientsock, msg) # client -> server

    def loop(self):
        """Loop indefinetely."""
        
        print(f"[{self.name}] connected successfully!")
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)
        
        while True:
            sys.stdout.write('> ')
            sys.stdout.flush()
            events = self.sel.select()
            for k, mask in events:
                callback = k.data
                callback(k.fileobj, mask)

