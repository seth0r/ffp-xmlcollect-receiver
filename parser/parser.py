from base import Process
import queue
import os
import gzip
from xml.etree import ElementTree as ET
import parser
from collections import defaultdict

class defdict(defaultdict):
    def __init__(self,*args):
        super().__init__(self.__class__)

class Parser(Process,parser.ffgParser):
    def __init__( self, stordir, scheduler = None ):
        super().__init__()
        self.scheduler = scheduler
        self.stordir = stordir
        self.start()

    def run(self):
        self.logger.info("Started...")
        while not self.shouldstop():
            try:
                host, files = self.scheduler.get(timeout=1)
                for f in sorted(files):
                    self.parse( host, f )
            except queue.Empty:
                pass
        self.logger.info("Stopped.")

    def parse(self,host,fname):
        fp = os.path.join( self.stordir, host, fname )
        if not os.path.isfile(fp):
            self.logger.warning("%s from %s not found.",fname,host)
            return
        self.logger.info("Parsing %s from %s...",fname,host)
        try:
            if fname.endswith(".gz"):
                with gzip.open(fp,"rt") as fo:
                    self.parse_xml( fo, host )
            elif fname.endswith(".xml"):
                with open(fp,"rt") as fo:
                    self.parse_xml( fo, host )
            else:
                self.logger.warning("Parsing of %s from %s not implemented.", fname, host)
        except Exception as ex:
            self.logger.exception("Error parsing %s from %s.", fname, host)
        mvdir = os.path.join( self.stordir, ".mv", host )
        os.makedirs( mvdir, exist_ok = True)
        os.rename( fp, os.path.join( mvdir, fname ) )

    def parse_xml(self, fo, host):
        res = defdict()
        for evt,elem in ET.iterparse(fo, ["start","end"]):
            fnk = "%s_%s" % (elem.tag,evt)
            if hasattr(self,fnk):
                getattr(self,fnk)( elem, res, host )
            else:
                self.logger.warning("No method %s.",fnk)
