import socket, select
import sys
from threading import Thread
import traceback

class Tunnel:
    def __init__(self, session, location):
        self.client_fd = None
        self.server_fd= None
        self.ref = location[location.find("/", 8):] 
        self.session = session
        self.ip = location[8:location.find("/", 8)] 
        self.halt = False
        self.translate = False
        self.key = None
    def listen(self, port=None):
        sock = socket.socket()
        sock.bind(("127.0.0.1", port))
        sock.listen(1)
        self.client_fd, addr = sock.accept()
        self.server_fd  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_fd.connect((self.ip, 80))
        # self.server_fd.send("CONNECT /console?ref=%s&session_id=%s HTTP/1.1\r\n\r\n" % (self.ref, self.session))
        self.server_fd.send("CONNECT %s&session_id=%s HTTP/1.1\r\n\r\n" % (self.ref, self.session))
        data = self.server_fd.recv(17)
        data = self.server_fd.recv(24)
        data = self.server_fd.recv(35)
        data = self.server_fd.recv(2)
        self.server_fd.setblocking(0)
        Thread(target=self.read_from_server, args=()).start()
        try:
            codes = ["\x39", "\x02", "\x28", "\x04", "\x05", "\x06", "\x08", "\x28", #/*  !"#$%&' */
                      "\x0a", "\x0b", "\x09", "\x0d", "\x33", "\x0c", "\x34", "\x35", #* ()*+,-./ */
                      "\x0b", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07", "\x08", #* 01234567 */
                      "\x09", "\x0a", "\x27", "\x27", "\x33", "\x0d", "\x34", "\x35", #* 89:;<=>? */
                      "\x03", "\x1e", "\x30", "\x2e", "\x20", "\x12", "\x21", "\x22", #* @ABCDEFG */
                      "\x23", "\x17", "\x24", "\x25", "\x26", "\x32", "\x31", "\x18", #* HIJKLMNO */
                      "\x19", "\x10", "\x13", "\x1f", "\x14", "\x16", "\x2f", "\x11", #* PQRSTUVW */
                      "\x2d", "\x15", "\x2c", "\x1a", "\x2b", "\x1b", "\x07", "\x0c", #* XYZ[\]^_ */
                      "\x29", "\x1e", "\x30", "\x2e", "\x20", "\x12", "\x21", "\x22", #* `abcdefg */
                      "\x23", "\x17", "\x24", "\x25", "\x26", "\x32", "\x31", "\x18", #* hijklmno */
                      "\x19", "\x10", "\x13", "\x1f", "\x14", "\x16", "\x2f", "\x11", #* pqrstuvw */
                      "\x2d", "\x15", "\x2c", "\x1a", "\x2b", "\x1b", "\x29"        #* xyz{|}~  */
                    ] 

            codes2 = ["\x0239", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07", "\x0c", "\x09", "\x0a", "\x1b", "\x1b", # 12
                   "\x33", "\x35", "\x34", "\x08", #//space", !"#$%&'()*+`-./ -> 3
                   "\x0b", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07", "\x08", "\x09", "\x0a", #//0123456789 -> 10
                   #"\x0127", "\x27", "\x0133", "\x000d", "\x0134", "\x0135", "\x0103", #//:;<=>?@ 
                   "\x34", "\x33", "\x56", "\x0b", "\x56", "\x0c", "\x1f", #//:;<=>?@ -> 7
                   "\x11e", "\x130", "\x12e", "\x120", "\x112", "\x121", "\x122", "\x123", "\x117", "\x124", "\x125", "\x126", "\x132", "\x131",  # 14
                   "\x118", "\x119", "\x110", "\x113", "\x11f", "\x114", "\x116", "\x12f", "\x111", "\x12d", "\x115", "\x12c", #//A-Z -> 12
                   "\x1a", "\x2b", "\x1b", "\x07", "\x35", "\x29", #//[\]^_`
                   "\x1e", "\x30", "\x2e", "\x20", "\x12", "\x21", "\x22", "\x23", "\x17", "\x24", "\x25", "\x26", "\x32", "\x31", "\x18", "\x19", "\x10", \
                   "\x13", "\x1f", "\x14", "\x16", "\x2f", "\x11", "\x2d", "\x15", "\x2c", #a-z
                   "\x1a", "\x2b", "\x1b", "\x29" #//{|}~
            ]
            from struct import pack
            data = self.client_fd.recv(1024)
            while data and self.halt == False:
                if ord(data[0]) == 4 and self.translate:
                    if ord(data[7]) > 32 and ord(data[7]) < 127 and ord(data[7]) not in range(80, 91):
                        if self.key:
                            data = "\xfe" + data[1:7] + chr(int(self.key,16))
                        else:
                            data = "\xfe" + data[1:7] + codes[ord(data[7])-32]
                self.server_fd.send(data)
                data = self.client_fd.recv(1024)
        except:
            if self.halt == False:
                 print "Unexpected error:", sys.exc_info()
                 print traceback.print_exc()
            else:
                 pass

        self.client_fd.close()
    def get_free_port(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        (host, port) = sock.getsockname()
        sock.close()
        return port

    def send_data(self, data):
        self.server_fd.send(data)

    def read_from_server(self):
        try:
            while self.halt == False:
                 ready_to_read, ready_to_write, in_error = select.select([self.server_fd], [], [])
                 if self.server_fd in ready_to_read:
                     data = self.server_fd.recv(1024)
                     if "XenServer Virtual Terminal" in data:
                         self.translate = False
                         data = data[:7] + "\x00" + data[8:]
                     elif "+HVMXEN-" in data:
                         self.translate = True 
                         data = data[:7] + "\x00" + data[8:]
                     self.client_fd.send(data)
        except:
            if self.halt == False:
                 print "Unexpected error:", sys.exc_info()
                 print traceback.print_exc()
            else:
                 pass
        self.server_fd.close()

    def close(self):
        try:
            self.halt = True
            self.client_fd.send("close\n")
            self.client_fd.send("close\n")
            self.server_fd.send("close\n")
            del self
        except:
            pass


