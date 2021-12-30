"""Middleware to communicate with PubSub Message Broker."""
from collections.abc import Callable
from enum import Enum
from queue import LifoQueue, Empty
import socket
import json
import pickle
import xml.etree.ElementTree as ET
from typing import Any
import time

from .protocol import PubSub, Pub, Sub, Ped, Can, ListMessage, PubSubBadFormat, Register


class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2


class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        self.mwsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._host = "localhost"
        self._port = 50018
        self._type = _type
        self.topic = topic
        self.cereal = 0
        self.mwsock.connect((self._host, self._port))
        #self.mwsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #print(f"[MIDDLEWARE] connected to {self._host}:{self._port}...") 
        """Create Queue."""
        #self.queue = LifoQueue()



    def push(self, value):
        """Sends data to broker. """
        #print("+++pushing ", value)
        #self.queue.put(value)
        #print("********")
        if self._type.value==2:
            #print("Middleware Push sending message ", PubSub.pub(self.topic,value))
            PubSub.send_msg(self.mwsock, self.cereal, PubSub.pub(self.topic,value))
        #print("sent *** message: ", PubSub.pub(self.topic,value))


    def pull(self) -> (str, Any):
        """Receives (topic, data) from broker.
        Should BLOCK the consumer!"""
        #print("below is incoming belhice")
        incoming = PubSub.recv_msg(self.mwsock)
        #print("Middleware Pull receiving message ", incoming)
        if incoming is None: return None
        return (incoming.topic, incoming.value)
        

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        #print("Middleware sending message ", PubSub.ped())
        PubSub.send_msg(self.mwsock, self.cereal, PubSub.ped())
        incoming = callback(PubSub.recv_msg(self.mwsock))
        #print("Middleware receiving message ", incoming)


    def cancel(self):
        """Cancel subscription."""
        #print("Middleware sending message ", PubSub.can(self.topic))
        PubSub.send_msg(self.mwsock, self.cereal, PubSub.can(self.topic))
        
    #criar funçao subscribe que envia mensagem do tipo subscribe


class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)
        self.cereal = 0
        if _type.value==1:
            #print("Middleware sending message REGISTER")
            PubSub.send_msg(self.mwsock, 0, PubSub.register(self.cereal))
            #print("Middleware sending message SUBSCRIBE to ", self.topic, " for the first time")
            PubSub.send_msg(self.mwsock, 0, PubSub.sub(self.topic))
        #else:
            #print("Producer is born")


class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""
    def __init__ (self,topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic,_type)
        self.cereal = 1
        if _type.value==1:
            #print("Middleware sending message REGISTER1")
            PubSub.send_msg(self.mwsock, 0, PubSub.register(self.cereal))
            PubSub.send_msg(self.mwsock, 1, PubSub.sub(self.topic))
        #else:
            #print("Producer1 is born")


class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""
    def __init__ (self,topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic,_type)
        self.cereal = 2
        if _type.value==1:
            #print("Middleware sending message REGISTER2")
            PubSub.send_msg(self.mwsock, 0, PubSub.register(self.cereal))
            #print("Middleware sending message SUBSCRIBE2 to ", self.topic, " for the first time")
            PubSub.send_msg(self.mwsock, 2, PubSub.sub(self.topic))
        #else:
            #print("Producer2 is born")

