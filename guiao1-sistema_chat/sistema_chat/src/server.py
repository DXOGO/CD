
# Echo server program       
"""CD Chat server program."""

import logging
import selectors
import socket

from .protocol import CDProto, CDProtoBadFormat
from collections import defaultdict

HOST = 'localhost'                 # Symbolic name meaning all available interfaces
PORT = 5555           # Arbitrary non-privileged port

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    """Chat Server process."""
    
    def __init__(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel = selectors.DefaultSelector()
        self.serversocket.bind((HOST, PORT))
        self.serversocket.listen()
        self.sel.register(self.serversocket, selectors.EVENT_READ, self.accept)
        print('[SERVER] initiating...') 
        
        self.client_list = []                   # criar lista p guardar socket de clientes
        self.channels = defaultdict(list)           # canais de chat  {conn : [canal1, canal2, canal 3]}

    def accept(self, conn, mask):
        conn, addr = self.serversocket.accept()  # Should be ready
        print(f"[SERVER] accepted connection from {addr[0]}:{addr[1]}")      # aceita conexao 
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        data = CDProto.recv_msg(conn)
        
        if data:
            # client envia para server e server vai devolver a mensagem
            print(data)

            if data.command == "register":
                self.client_list.append(conn)
                self.channels[conn] = [None]

            if data.command == "message":
                channel = data.channel
                for client, channel_list in self.channels.items():
                    if (client != conn and channel in channel_list):
                        CDProto.send_msg(client, data)

            if data.command == "join":
                channel = data.channel
                if (self.channels[conn] == [None]):     # se cliente n pertence a nenhum canal
                    print(f"Joined channel {channel}")
                    self.channels[conn] = [channel]

                elif (self.channels[conn] != [None] and self.channels[conn] != [channel]):    # se cliente pertence a outro(s) canal
                    print(f"Joined channel {channel}")
                    self.channels[conn].append(channel)
                    
                else:
                    print(f"Request ignored. User already belongs to {channel}")        # está a tentar juntar-se ao grupo q ja se encontra
                    pass     
  
        else:
            print(f"[SERVER] ending connection with {conn}")                     # fechar conexao
            self.client_list.remove(conn)
            self.sel.unregister(conn)
            conn.close()

    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)


