"""Message Broker"""
import enum
from typing import Collection, Dict, List, Any, Tuple
import socket
import selectors

from .protocol import PubSub

class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2


class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        self._host = "localhost"
        self._port = 50018
        self.brokersock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.brokersock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.brokersock.bind((self._host, self._port))
        self.brokersock.listen()
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.brokersock, selectors.EVENT_READ, self.accept)
        print('[BROKER] initiating...')

        self.languages = {}     # { conn : serealizer }
        self.topics = {}        # { (topic, mensagem recente) : [conn1, conn2, conn3, conn4] }
                                # keys -> tuplos(topic, msg mais recent)
                                # values -> listas de conexoes
        #TODO como fazer para verificar subtopics dentro de topics

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        #print('Accepted conection from', addr)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        # chamar funcao receive do protocolo
        rcv_msg = PubSub.recv_msg(conn)
        #print("ended receiving message")
        if rcv_msg:
            print("server receving message: ", rcv_msg)
            if rcv_msg.type == "Subscribe":
                print("this is fd subs: ", rcv_msg.topic, " ", conn)
                self.subscribe(rcv_msg.topic, conn, self.languages[conn])       #TODO format
            elif rcv_msg.type == "Publish":
                self.put_topic(rcv_msg.topic, rcv_msg.value)
                curr_subs = self.list_subscriptions(rcv_msg.topic)
                print("--- this is current subs of ", rcv_msg.topic ,": ", curr_subs)
                for sub in curr_subs:
                    print("sending to subscriber")
                    #print("server sending message: ", rcv_msg, " to ", sub[0])
                    PubSub.send_msg(sub[0], sub[1].value, rcv_msg)
            elif rcv_msg.type == "RequestList":
                #print("server sending message: ", PubSub.list_msg(self.list_topics()))
                PubSub.send_msg(conn, self.languages[conn].value, PubSub.list_msg(self.list_topics()))
            elif rcv_msg.type == "Unsubscribe":
                self.unsubscribe(rcv_msg.topic, conn)
            elif rcv_msg.type =="Register" or rcv_msg["type"]=="Register":
                #print("received reggy of type", rcv_msg.lang)
                self.reggy(conn, rcv_msg.lang)
                
        else:
            if not self.unsubscribe("", conn): print("Publisher disconnect")
            else: print("Consumer disconnect")
            #TODO remove from data struct
            self.sel.unregister(conn)
            conn.close()

    def list_topics(self) -> List[str]:
        """Returns a list of strings containing all topics."""   
        List = []
        for key in self.topics:
            if key[1]:
                List.append(key[0])
        return List

    def get_topic(self, topic):
        """Returns the currently stored value in topic."""
        print("BELHICE")
        for key in self.topics:
            print(key)
        for key in self.topics:
            if key[0]==topic:
                return key[1]

    def put_topic(self, topic, value):
        """Store in topic the value."""
        print("putting topic: ", topic , " !")

        print("WOOP WOOPW ", self.topics)
        for key in self.topics:
            if key[0] == topic:
                old_cons = self.topics[key]
                del self.topics[key]
                self.topics[(topic, value)]= old_cons
                #print(key[0], " ",value)
                print("successful value update")
                print(self.topics)
                return
        print("topic isnt in self.topics dictionary")
        self.topics[(topic, value)] = []
        #old /uau, new /uau/ff

        for key in self.topics:
            if key[0] in topic:
                someconn = self.topics[key]
                self.topics[(topic, value)] = someconn



    def list_subscriptions(self, topic: str) -> List[socket.socket]:
        """Provide list of subscribers to a given topic."""
        lst = []
        for key in self.topics:
            if key[0] in topic:
                for connection in self.topics[key]:
                    lst.append((connection, self.languages[connection]))
                return lst
        return []


    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""

        # if dont exist, register
        if address not in self.languages:
            self.reggy(address, _format)

        t1 = topic
        a1 = address
        f1 = _format
        print("CURRENT SELF.TOPICS ", self.topics)

        for key in self.topics:
           
            print("TOPIC: ", topic)
            print("KEY:     ", key)
            print("KEY[0]:     ", key[0])

            if key[0] == topic:
                self.topics[key].append(address)
                if key[1] == None: 
                    print("consumer waits not blocked for message")
                    return
               
                PubSub.send_msg(address, _format.value, PubSub.pub(topic, key[1]))
                return

                #self.topics[(topic, None)] = [address]

        print("topic wasnt found")
        self.put_topic(t1, None)
        print("rerun subscribe")
        self.subscribe(t1, a1, f1)

    def unsubscribe(self, topic, address):
        """Unsubscribe to topic by client in address."""
        if topic == "":
            for key in self.topics:
                if address in self.topics[key]:
                    #print("removed consumer from all topics")
                    self.topics[key].remove(address)
                    return True
        else:
            for key in self.topics:
                if key[0]==topic:
                    if address in self.topics[key]:
                        #print("removed consumer from ", topic ," ...")
                        self.topics[key].remove(address)
                        return True
        return False

    def reggy(self, conn, _format):
        print("registering new conn: ", conn)
        if _format == 0 or _format == Serializer.JSON:
            self.languages[conn] = Serializer.JSON
        
        elif _format == 1 or _format == Serializer.XML:
            self.languages[conn] = Serializer.XML
            #print("XML registered confirmation")
        
        elif _format == 2 or _format == Serializer.PICKLE:
            self.languages[conn] = Serializer.PICKLE
            #print("pickle registered confirmation")
        
        else:
            print("something new ", _format)


    def run(self):
        """Run until canceled."""
        while not self.canceled:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

