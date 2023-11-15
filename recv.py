#!/usr/bin/env python3
import socket
import multiprocessing.pool
import time
import os
import string
from base import Thread

VALIDCHARS = string.digits + string.ascii_letters + ' .-_'

class Receiver(Thread):
    def __init__( self, stordir, port, threads, scheduler = None ):
        super().__init__()
        self.scheduler = scheduler
        self.stordir = stordir
        self.port = port
        self.threads = threads
        os.makedirs(self.stordir, exist_ok = True)
        self.recv_workers = multiprocessing.pool.ThreadPool(self.threads)
        #self.srv = socket.create_server(("0.0.0.0",port),backlog=self.threads)
        self.srv = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.srv.settimeout(1)
        self.start()

    def run(self):
        self.logger.info("Listening on Port %d..." % self.port)
        self.srv.bind(('', self.port))
        self.srv.listen(self.threads)
        res = []
        while not self.shouldstop():
            try:
                (conn,address) = self.srv.accept()
                ip = address[0]
                port = address[1]
            except TimeoutError:
                pass
            except socket.timeout:
                pass
            except KeyboardInterrupt:
                break
            except:
                raise
            else:
                res.append( self.recv_workers.apply_async( self.receive, (conn,ip,port) ) )
            i = 0
            while i < len(res):
                if res[i].ready():
                    try:
                        res[i].get()
                    except Exception as ex:
                        self.logger.exception("Exception %s..." % ex)
                    del res[i]
                else:
                    i += 1
        self.logger.info("Stopped.")

    def stor_received(self,filename, hostname, buf):
        os.makedirs(os.path.join(self.stordir,hostname), exist_ok = True)
        fp = os.path.join(self.stordir,hostname,filename)
        f = open(fp,"wb")
        f.write(buf)
        f.close()

    def receive(self,conn,ip,port):
        start = time.time()
        try:
            buf = conn.recv(1024)
            # header is the first line, it should arrive in the first second,
            # should be terminated by a newline,
            # should have a maximum length of 1024 characters
            # and only contain a limited set of ascii characters in the form of
            # <length> <filename> <hostname>
            while b'\n' not in buf and len(buf) < 1024 and time.time() - start < 1:
                buf += conn.recv(1024)
            if b'\n' in buf:
                line,_,buf = buf.partition(b'\n')
                for c in line:
                    if c not in bytes(VALIDCHARS,'ascii'):
                        self.logger.warning("Invalid character %d in first line from %s" % (c,ip))
                        break
                else:
                    line = line.decode("ascii").split(None, 2)
                    if len(line) != 3:
                        self.logger.warning("Not enougth fields in first line %s from %s" % (str(line),ip))
                    else:
                        length, filename, hostname = line
                        try:
                            length = int(length)
                        except ValueError:
                            self.logger.warning("Invalid length '%s' from %s" % (length,ip))
                        else:
                            if length > 100 * 1024:
                                self.logger.warning("Length %d to big from %s" % (length,ip))
                            else:
                                start = time.time()
                                while len(buf) < length and time.time() - start < 5:
                                    buf += conn.recv(length)
                                if len(buf) == length:
                                    self.stor_received( filename, hostname, buf )
                                    self.logger.info("Received %s with %d bytes for %s from %s" % (filename,length,hostname,ip))
                                    if self.scheduler:
                                        self.scheduler.put( time.time(), hostname, filename )
                                    conn.sendall(b'success')
                                elif len(buf) > length:
                                    self.logger.warning("Did receive %d bytes, instead of %d bytes from %s" % (len(buf),length,ip))
                                else:
                                    self.logger.warning("Did not receive %d bytes in time from %s" % (length,ip))
        finally:
            conn.close()

if __name__ == "__main__":
    import logging
    logging.basicConfig( level = logging.INFO )
    r = Receiver( os.getenv("TMPSTOR", "./tmpstor"), int(os.getenv("PORT", 17485)), int(os.getenv("RECVTHREADS", 128)) )
    try:
        r.join()
    except KeyboardInterrupt:
        r.stop()
        r.join()
