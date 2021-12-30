"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
import errno
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self, command):
        self.command = command

    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, command, channel):
        super().__init__(command)
        self.channel = channel
    
    def __str__(self):
        return f'{{"command": "join", "channel": "{self.channel}"}}'

class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, command, user):
        super().__init__(command)
        self.user = user
    
    def __str__(self):
        return f'{{"command": "register", "user": "{self.user}"}}'

class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, command, message, ts, channel):
        super().__init__(command)
        self.message = message
        self.channel = channel
        self.ts = ts
    
    def __str__(self):
        if self.channel: 
                return f'{{"command": "message", "message": "{self.message}", "channel": "{self.channel}", "ts": {self.ts}}}'
        else:
            return f'{{"command": "message", "message": "{self.message}", "ts": {self.ts}}}'

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage("register", username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage("join", channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage("message", message, int(datetime.now().timestamp()), channel)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        if type(msg) is RegisterMessage:
            json_msg = json.dumps({"command" : "register", "user" : msg.user}).encode("utf-8")

        elif type(msg) is JoinMessage:
            json_msg = json.dumps({"command" : "join", "channel" : msg.channel}).encode("utf-8")

        elif type(msg) is TextMessage:
            json_msg = json.dumps({"command" : "message", "message" : msg.message, "channel" : msg.channel, "ts" : msg.ts}).encode("utf-8")    
        
        header = len(json_msg).to_bytes(2,"big")
        
        try:
            connection.sendall(header + json_msg)
        except IOError as err:
            if err.errno == errno.EPIPE:
                print(err)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""

        header = int.from_bytes(connection.recv(2), "big")
        if header == 0: return
        msg = connection.recv(header).decode("utf-8")

        try:
            dic_json = json.loads(msg)
        except json.JSONDecodeError as err:
            raise CDProtoBadFormat(msg)

        if dic_json["command"] == "register":
            username = dic_json["user"]
            return CDProto.register(username)
            
        elif dic_json["command"] == "message":
            message = dic_json["message"]
            if dic_json.get("channel"):
                channel = dic_json["channel"]
                return CDProto.message(message, channel)
            else:
                return CDProto.message(message)

        elif dic_json["command"] == "join":
            channel = dic_json["channel"]
            return CDProto.join(channel) 


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
