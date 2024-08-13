import os
import copy
import datetime
import tsdb

class TimescaleFeeder:
    def feed(self,res):
        self.feedts_nodes(res)
        if "neighbours" in res:
            self.feedts_neighbours(res)

    def feedts_nodes(self,res):
        t = datetime.datetime.utcfromtimestamp( res["time"] )
        nid = res["node_id"]
        host = res["host"]
        macaddrs = set()
        network = None
        software = None
        loc = None
        contact = False
        if "nodeinfo" in res and "routes" in res:
            ni = copy.deepcopy( res["nodeinfo"] )
            stat = res.get("statistics",{})

            contact = ni.get("owner",{}).get("contact",None)
            loc = ni.get("location",{})

            ni["software"]["ffpcollect"] = res.get("scriptver",None)
            software = ni["software"]

            for d,dc in ni["network"]["mesh"].items():
                for i,a in dc.get("interfaces",{}).items():
                    macaddrs |= set(a)
            ni["network"].pop("mesh",None)
            ni["network"]["gateway"] = stat.get("gateway",None)
            ni["network"]["nexthop"] = stat.get("gateway_nexthop",None)
            ni["network"]["mesh_vpn"]["peers"] = []
            for p,c in stat.get("mesh_vpn",{}).get("groups",{}).get("backbone",{}).get("peers",{}).items():
                if c is not None and c.get("established",0) > 0:
                    ni["network"]["mesh_vpn"]["peers"].append( p )
            network = ni["network"]
            network["routes"] = res["routes"]

        with tsdb.SQLSession(tsdb.engine) as sess:
            node = sess.get(tsdb.Node, nid)
            if not node:
                node = tsdb.Node( nodeid=nid, hostname=host )
                sess.add(node)
                self.logger.info("New node %s with hostname %s.", nid, host)
            if not node.last_data or t > node.last_data:
                node.last_data = t
                if host != node.hostname:
                    self.logger.info("Nodes hostname of %s changed from %s to %s.", nid, node.hostname, host)
                    node.hostname = host
                if contact is not False and contact != node.contact:
                    node.contact = contact
                    node.last_contact_update = t
                    node.owners = []
                if loc is not None:
                    node.loc_lon = loc.get("longitude",None)
                    node.loc_lat = loc.get("latitude",None)
                if len(macaddrs) > 0:
                    node.macaddrs = []
                    for mac in macaddrs:
                        node.macaddrs.append(tsdb.MacAddr(mac=mac))
                if network:
                    node.network = network
                if software:
                    node.software = software
            sess.commit()

    def feedts_neighbours(self,res):
        pass

    def postprocess(self, host):
        pass

