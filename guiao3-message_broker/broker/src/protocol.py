import json
import pickle
import xml.etree.ElementTree as et
import time
from datetime import datetime
from socket import socket
from typing import SupportsBytes
import enum


class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2


class Message:
    def __init__(self, type):
        self.type = type

class Sub(Message):
    def __init__(self, topic):
        super().__init__("Subscribe")
        self.topic = topic
    
    def __repr__(self):
        return f'{{"type": "{self.type}", "topic": "{self.topic}"}}'

    def picky(self):
        return {"type": self.type, "topic": self.topic}

    def xemele(self):
        return "<?xml version=\"1.0\"?><data type=\"{}\" topic=\"{}\"></data>".format( self.type, self.topic )

class Pub(Message):
    def __init__(self, topic, value):
        super().__init__("Publish")
        self.topic = topic
        self.value = value
    
    def __repr__(self):
        return f'{{"type": "{self.type}", "topic": "{self.topic}", "value": {self.value}}}'

    def picky(self):
        return {"type": self.type, "topic": self.topic, "value": self.value}

    def xemele(self):
        return "<?xml version=\"1.0\"?><data type=\"{}\" topic=\"{}\" value=\"{}\"></data>".format( self.type, self.topic, self.value )


class Ped(Message):
    def __init__(self):
        super().__init__("RequestList")
    
    def __repr__(self):
        return f'{{"type": "{self.type}"}}'
    
    def picky(self):
        return {"type": self.type}
    def xemele(self):
        return "<?xml version=\"1.0\"?><data type=\"{}\"></data>".format( self.type )



class Can(Message):
    def __init__(self, topic):
        super().__init__("Unsubscribe")
        self.topic = topic

    def __repr__(self):
        return f'{{"type": "{self.type}", "topic": "{self.topic}"}}'
        
    def picky(self):
        return {"type": self.type, "topic": self.topic}

    def xemele(self):
        return "<?xml version=\"1.0\"?><data type=\"{}\" topic=\"{}\"></data>".format( self.type, self.topic )

        
class ListMessage(Message):
    def __init__(self, lst):
        super().__init__("ReplyList")
        self.lst = lst
    
    def __repr__(self):
        return f'{{"type": "{self.type}", "lst": {self.lst}}}'
    
    def picky(self):
        return {"type": self.type, "lst": self.lst}

    def xemele(self):
        return "<?xml version=\"1.0\"?><data type=\"{}\" lst=\"{}\"></data>".format( self.type, self.lst )


class Register(Message):
    def __init__(self, lang):
        super().__init__("Register")
        self.lang = lang
    
    def __repr__(self):
        return f'{{"type": "{self.type}", "lang": {self.lang}}}'
    
    def picky(self):
        return {"type": self.type, "lang": self.lang}
    
    def xemele(self):
        return "<?xml version=\"1.0\"?><data type=\"{}\" lang=\"{}\"></data>".format( self.type, self.lang )

        

class PubSub:
    
    @classmethod
    def sub(cls, topic) -> Sub:
        return Sub(topic)

    @classmethod
    def pub(cls, topic, value) -> Pub:
        return Pub(topic, value)
        
    @classmethod
    def ped(cls) -> Ped:
        return Ped()

    @classmethod
    def can(cls, topic) -> Can:
        return Can(topic)

    @classmethod
    def list_msg(cls, lst) -> ListMessage:
        return ListMessage(lst)

    @classmethod
    def register(cls, lang) -> Register:
        return Register(lang)

   
    @classmethod
    def send_msg(cls, connection: socket, coding, msg: Message): #encode
        #print("> ", msg)
        #print("Sending :" , msg.__repr__())
        if coding == None: coding=0
        
        if type(coding)==str: coding = int(coding)
        
        connection.send(coding.to_bytes(1, 'big'))
        if coding == 0 or coding ==Serializer.JSON :       #json
            dicky = json.loads(msg.__repr__())
            temp = json.dumps(dicky).encode('utf-8')
            connection.send(len(temp).to_bytes(2, 'big'))
            connection.send(temp)
        elif coding == 2 or coding ==Serializer.PICKLE:
            payload = pickle.dumps(msg.picky())
            connection.send(len(payload).to_bytes(2, 'big'))
            connection.send(payload)
            #print("message sent", connection)
        elif coding == 1 or coding ==Serializer.XML:                         #xml
            msg_serialized = msg.xemele()
            payload = msg_serialized.encode('utf-8')
            connection.send(len(payload).to_bytes(2, 'big'))
            connection.send(payload)
    


    @classmethod
    def recv_msg(cls, connection: socket) -> Message:   #decode
        """Receives through a connection a Message object."""
        coding = int.from_bytes(connection.recv(1), 'big')
        header = int.from_bytes(connection.recv(2), 'big') #length of message
        if header == 0 : 
            #print("header is none")
            return None
        #print("header is this ", header, " and this is coding ", coding)
        try:
            if coding == 0 or coding == None:
                str_msg = connection.recv(header).decode('utf-8')
                if str_msg=="":return None
                msg = json.loads(str_msg)
            elif coding == 2:
                str_msg = connection.recv(header)
                #print("tou aqui ", str_msg)
                if str_msg=="":return None
                msg = pickle.loads(str_msg)
            elif coding == 1:
                str_msg = connection.recv(header).decode('utf-8') #str xml
                msg = {}
                root = et.fromstring(str_msg)
                for element in root.keys():
                    msg[element] = root.get(element)

        except json.JSONDecodeError as err:
            raise PubSubBadFormat(str_msg)

        #print(type(msg))       
        if msg["type"] == "Subscribe":
            return cls.sub(msg["topic"])
        
        elif msg["type"] == "Publish":
            return cls.pub(msg["topic"], msg["value"])
        
        elif msg["type"] == "Request":
            print("reggy check")
            return cls.ped()
        
        elif msg["type"] == "Unsubscribe":
            return cls.can(msg["topic"])
        
        elif msg["type"] == "ReplyList":
            return cls.list_msg(msg["lst"])      
        
        elif msg["type"] == "Register":    
            return cls.register(msg["lang"]) 
        
        else:
            #print("Error analysing type field")
            return None

class PubSubBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
