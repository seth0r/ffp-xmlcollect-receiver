from base import Process
import os
import time
from pymongo import MongoClient

class OfflineUpdater(Process):
    INTERVAL = 540
    def run(self):
        self.mdbe = MongoClient( os.getenv( "MONGODB_URI","mongodb://localhost/" ) )
        self.mdb = self.mdbe[os.getenv("MONGODB_DB")]
        now = time.time()
        for n in self.mdb["nodes"].find():
            offline = max(0,(now - n["last_ts"]) // 3600)
            if offline != n.get("offline",None):
                self.mdb["nodes"].update_one( {"_id":n["_id"],"last_ts":n["last_ts"]}, {"$set":{"offline":offline}} )
                self.mdb["changes"].insert_one({ "nid": n["_id"], "time": now, "ctime": now, "param": "offline", "new": offline, "old": n.get("offline",None) })
