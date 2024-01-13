#!/usr/bin/env python3
import multiprocessing
import queue
import collections
import time
import os
import string
from base import Process

class Scheduler(Process):
    def __init__( self, waittime ):
        super().__init__()
        self.waittime = waittime
        self.inq = multiprocessing.Queue()
        self.outq = multiprocessing.Queue()
        self.files = collections.defaultdict(set)
        self.lastfile = collections.defaultdict(float)
        self.start()

    def run(self):
        lastmsg = 0
        while not self.shouldstop():
            now = time.time()
            if now - lastmsg > 60:
                self.logger.info("%s alive, inQueue: %d, outQueue: %d" % (self.__class__.__name__, self.inq.qsize(), self.outq.qsize()))
                lastmsg = now
            try:
                ts,hostname,filename = self.inq.get(timeout=1)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                break
            else:
                self.files[hostname].add(filename)
                self.lastfile[hostname] = max( self.lastfile[hostname], ts )
            now = time.time()
            for h in list(self.files.keys()):
                ts = self.lastfile[h]
                if now - ts > self.waittime:
                    self.outq.put(( h, list(sorted(self.files[h])) ))
                    del self.lastfile[h]
                    del self.files[h]

    def put(self, ts, hostname, filename):
        self.inq.put((ts,hostname,filename))

    def get(self,*args,**kwargs):
        return self.outq.get(*args,**kwargs)
