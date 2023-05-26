import os
import influxdb_client
from influxdb_client.domain.write_precision import WritePrecision
from pymongo import MongoClient

class InfluxFeeder:
    def __init__(self):
        self.mdbe = MongoClient( os.getenv( "MONGODB_URI","mongodb://localhost/" ), connect = False )
        self.mdb = self.mdbe[os.getenv("MONGODB_DB")]
        self.idb = influxdb_client.InfluxDBClient(
            url   = os.getenv("INFLUXDB_URL"),
            token = os.getenv("INFLUXDB_TOKEN"),
            org   = os.getenv("INFLUXDB_ORG")
        )
        self.iwapi = self.idb.write_api()

    def feed(self,res):
        for sect in ["nodeinfo","neighbours","conn","statistics"]:
            if sect in res and hasattr(self,"feedi_%s" % sect):
                for p in getattr(self,"feedi_%s" % sect)(res):
                    self.iwapi.write(
                        bucket = os.getenv("INFLUXDB_BUCKET"),
                        org    = os.getenv("INFLUXDB_ORG"),
                        record = influxdb_client.Point.from_dict( p, WritePrecision.S )
                    )

    def postprocess(self, host):
        self.iwapi.flush()

    def feedi_nodeinfo(self,res):
        p = {
            "time": res["time"],
            "measurement": "nodes",
            "tags": {
                "node_id"   : res["node_id"],
                "host"      : res["host"],
                "hw_model"  : res["nodeinfo"]["hardware"]["model"],
                "fw_base"   : res["nodeinfo"]["software"]["firmware"]["base"],
                "fw_release": res["nodeinfo"]["software"]["firmware"]["release"],
                "au_branch" : res["nodeinfo"]["software"]["autoupdater"]["branch"],
                "au_enabled": res["nodeinfo"]["software"]["autoupdater"]["enabled"],
                "domain"    : res["nodeinfo"]["system"]["domain_code"],
            },
            "fields": {
                "value":1,
                "nproc":res["nodeinfo"]["hardware"]["nproc"],
            },
        }
        yield p

    def feedi_neighbours(self,res):
        for lmac,neigh in res["neighbours"].items():
            lnode = self.mdb["nodes"].find_one({"ifaddr":lmac})
            for rmac,attrs in neigh.items():
                rnode = self.mdb["nodes"].find_one({"ifaddr":rmac})
                p = {
                    "time": res["time"],
                    "measurement": "neighbours",
                    "tags": {
                        "lmac" : lmac,
                        "lnid" : None if lnode is None else lnode["_id"],
                        "lhost": None if lnode is None else lnode.get("host",None),
                        "rmac" : rmac,
                        "rnid" : None if rnode is None else rnode["_id"],
                        "rhost": None if rnode is None else rnode.get("host",None),
                    },
                    "fields": attrs,
                }
                yield p

    def feedi_conn(self,res):
        for l3p,conns in res["conn"].items():
            for l4p,num in conns.items():
                p = {
                    "time": res["time"],
                    "measurement": "conn",
                    "tags": {
                        "node_id": res["node_id"],
                        "host"   : res["host"],
                        "l3proto": l3p,
                        "l4proto": l4p,
                    },
                    "fields": {"number":num},
                }
                yield p

    def feedi_statistics(self,res):
        for sect in ["clients","traffic","memory","stat"]:
            if sect in res["statistics"] and hasattr(self,"feedi_statistics_%s" % sect):
                yield from getattr(self,"feedi_statistics_%s" % sect)(res)
        p = {
            "time": res["time"],
            "measurement": "statistics",
            "tags": {
                "node_id": res["node_id"],
                "host"   : res["host"],
            },
            "fields": {
                "gateway_tq"  : res["statistics"].get("gateway_tq",None),
                "rootfs_usage": res["statistics"].get("rootfs_usage",None),
                "uptime"      : res["statistics"].get("uptime",None),
                "idletime"    : res["statistics"].get("idletime",None),
                "loadavg"     : res["statistics"].get("loadavg",None),
                "proc_running": res["statistics"].get("processes",{}).get("running",None),
                "proc_total"  : res["statistics"].get("processes",{}).get("total",None),
            },
        }
        yield p

    def feedi_statistics_clients(self,res):
        p = {
            "time": res["time"],
            "measurement": "clients",
            "tags": {
                "node_id": res["node_id"],
                "host"   : res["host"],
            },
            "fields": res["statistics"]["clients"],
        }
        yield p

    def feedi_statistics_traffic(self,res):
        p = {
            "time": res["time"],
            "measurement": "traffic",
            "tags": {
                "node_id": res["node_id"],
                "host"   : res["host"],
            },
            "fields": {},
        }
        for l1,traf in res["statistics"]["traffic"].items():
            for l2,v in traf.items():
                p["fields"]["%s_%s" % (l1,l2)] = v
        if len(p["fields"]) > 0:
            yield p

    def feedi_statistics_memory(self,res):
        p = {
            "time": res["time"],
            "measurement": "memory",
            "tags": {
                "node_id": res["node_id"],
                "host"   : res["host"],
            },
            "fields": res["statistics"]["memory"],
        }
        yield p

    def feedi_statistics_stat(self,res):
        if "cpu" in res["statistics"]["stat"]:
            p = {
                "time": res["time"],
                "measurement": "cpu",
                "tags": {
                    "node_id": res["node_id"],
                    "host"   : res["host"],
                },
                "fields": res["statistics"]["stat"]["cpu"],
            }
            yield p
        res["statistics"]["stat"].pop("cpu",None)
        p = {
            "time": res["time"],
            "measurement": "stat",
            "tags": {
                "node_id": res["node_id"],
                "host"   : res["host"],
            },
            "fields": res["statistics"]["stat"],
        }
        yield p



