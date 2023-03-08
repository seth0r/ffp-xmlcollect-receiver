import multiprocessing
import threading
import logging

class Thread(threading.Thread):
    def __init__( self ):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._shouldstop = threading.Event()
        self.daemon = True

    def stop(self):
        self._shouldstop.set()

    def shouldstop(self):
        return self._shouldstop.is_set()

class Process(multiprocessing.Process):
    def __init__( self ):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._shouldstop = multiprocessing.Event()

    def stop(self):
        self._shouldstop.set()

    def shouldstop(self):
        return self._shouldstop.is_set()

