__all__ = []

import pkgutil
import inspect

DEBUG = False

lastn = None
maxtrys = len(list( pkgutil.walk_packages(__path__) ))
while True:
    for loader, mname, is_pkg in pkgutil.walk_packages(__path__):
        try:
            if DEBUG:
                print("Trying to load %s..." % mname, end=" ")
            module = loader.find_module(mname).load_module(mname)
            for name, value in inspect.getmembers(module):
                if name.startswith('__'):
                    continue
                globals()[name] = value
                __all__.append(name)
            if lastn == mname:
                lastn = None
            if DEBUG:
                print("loaded.")
        except NameError as ne:
            if DEBUG:
                print( ne )
            if mname == lastn:
                raise
            lastn = mname
    if lastn is None:
        break
    elif maxtrys <= 0:
        raise
    maxtrys -= 1

import time
from base import Process,Thread
class Cron(Process):
    def __init__( self ):
        super().__init__()
        self.classes = {}
        self.last = {}
        self.running = {}
        for cn in __all__:
            c = globals()[cn]
            if callable(c) and issubclass(c,(Process,Thread)) and hasattr(c,"INTERVAL"):
                self.classes[ cn ] = c
                self.last[ cn ] = 0
        self.start()

    def run(self):
        self.logger.info("Started with %d jobs.",len(self.classes))
        while not self.shouldstop():
            now = time.time()
            for cn,c in self.classes.items():
                if cn in self.running:
                    continue
                if self.last.get(cn,0) < now - c.INTERVAL:
                    self.logger.info("Job %s starting...", cn)
                    self.last[cn] = now
                    try:
                        i = c()
                        if not i.is_alive():
                            i.start()
                        self.running[cn] = i
                    except:
                        self.logger.exception("Job %s failed.", cn)
            for cn,i in list(self.running.items()):
                if not i.is_alive():
                    del self.running[cn]
                    self.logger.info("Job %s done.", cn)
            time.sleep(1)
