import os
from pymongo import MongoClient
import copy
import time

def dictdiff(old, new):
    for k in set(old.keys()) - set(new.keys()):
        yield k,old.get(k), None
    for k,newv in new.items():
        oldv = old.get(k,None)
        if type(oldv) != type(newv):
            yield k,oldv,newv
        elif isinstance(oldv,dict):
            diff = list(dictdiff(oldv,newv))
            if len(diff) < len(oldv):
                for sk,o,n in diff:
                    yield "%s.%s" % (k,sk),o,n
            else:
                yield k,oldv,newv
        elif oldv != newv:
            yield k,oldv,newv

class MongoFeeder:
    def __init__(self):
        self.mdbe = MongoClient( os.getenv( "MONGODB_URI","mongodb://localhost/" ), connect = False )
        self.mdb = self.mdbe[os.getenv("MONGODB_DB")]

    def feed(self,res):
        if "nodeinfo" in res and "routes" in res:
            self.feedm_nodes(res)
        if "neighbours" in res:
            self.feedm_neighbours(res)

    def feedm_nodes(self,res):
        node = copy.deepcopy( res )
        stat = node.pop("statistics",{})
        node.update(node.pop("nodeinfo"))
        node.pop("neighbours",None)
        node.pop("conn",None)
        if node["host"] == node["hostname"]:
            del node["hostname"]
        if "location" in node:
            node["location"] = [ node["location"].get("longitude"), node["location"].get("latitude") ]
        node["software"]["ffpcollect"] = node.pop("scriptver")

        node["uptime"] = stat.get("uptime",None)
        node["ifaddr"] = set()
        for d,dc in node["network"]["mesh"].items():
            for i,a in dc.get("interfaces",{}).items():
                node["ifaddr"] |= set(a)
        node["network"].pop("mesh",None)
        node["ifaddr"] = list(sorted( node["ifaddr"] ))
        node["network"]["gateway"] = stat.get("gateway",None)
        node["network"]["nexthop"] = stat.get("gateway_nexthop",None)
        node["network"]["mesh_vpn"]["peers"] = []
        for p,c in stat.get("mesh_vpn",{}).get("groups",{}).get("backbone",{}).get("peers",{}).items():
            if c is not None and c.get("established",0) > 0:
                node["network"]["mesh_vpn"]["peers"].append( p )
        self.mdb["tmpnodes"].insert_one( node )

    def feedm_neighbours(self,res):
        self.mdb["neighbours"].create_index([("local",1),("remote",1),("time",1)])
        for local,neighbours in res["neighbours"].items():
            for remote,stat in neighbours.items():
                self.mdb["neighbours"].update_one(
                    { "local": local, "remote": remote },
                    { "$setOnInsert": { "time": res["time"] }},
                    upsert = True
                )
                self.mdb["neighbours"].update_one(
                    { "local": local, "remote": remote, "time": { "$lte": res["time"] } },
                    { "$set": { "stat": stat, "time": res["time"] }}
                )

    def postprocess(self, host):
        self.mdb["tmpnodes"].create_index("node_id")
        self.mdb["tmpnodes"].create_index("host")
        self.mdb["tmpnodes"].create_index("time")
        for nid in self.mdb["tmpnodes"].distinct("node_id",{"host":host}):
            old = self.mdb["nodes"].find_one({ "_id": nid })
            last_ts = 0 if old is None else old.get( "last_ts", 0 )
            new = list( self.mdb["tmpnodes"].find({ "node_id": nid, "time": { "$gt": last_ts } }, sort = [("time",1)] ) )
            if len(new) > 0:
                if old is None:
                    self.mdb["changes"].insert_one({ "nid": nid, "time": time.time(), "ctime": new[0]["time"], "param": "_id", "new": nid, "old": None })
                    self.logger.info("New node %s with hostname %s.", nid, host)
                    old = {}
                for n in new:
                    for k in ["_id","node_id","last_ts","offline"]:
                        n.pop(k,None)
                        old.pop(k,None)
                    t = n.pop("time")
                    q = {
                        "$max": { "last_ts": t },
                        "$set": {},
                        "$unset": {},
                    }
                    for a,oldv,newv in dictdiff(old,n):
                        if newv is None:
                            q["$unset"][a] = True
                        else:
                            q["$set"][a] = newv
                        if old == {} or a in ["uptime"]:
                            continue
                        self.logger.info("Changed %s[%s].%s from %s to %s.",old["host"],nid,a,oldv,newv)
                        self.mdb["changes"].insert_one({
                            "nid": nid,
                            "time":time.time(),
                            "ctime": t,
                            "param": a,
                            "new": newv,
                            "old": oldv
                        })
                    self.mdb["nodes"].update_one( {"_id": nid}, q, upsert = True )
                    for k in set(old.keys()) - set(n.keys()):
                        del old[k]
                    old.update(n)
        self.mdb["tmpnodes"].delete_many({"time":{ "$lt":time.time() - 7*24*60*60 }})

