# Parser for Freifunk Potsdam Gluon Status Format
import json

class ffgParser:
    def ffgstat_start(self, elem, res, host):
        if elem.attrib["host"] != host:
            raise Exception("Hostname in filename and XML do ot match.")
        res["host"] = host
        res["time"] = int(elem.attrib["time"])
        res["scriptver"] = elem.attrib["ver"]
    def ffgstat_end(self, elem, res, host):
        pass

    def neighbours_start(self, elem, res, host):
        pass
    def neighbours_end(self, elem, res, host):
        if elem.text is not None and elem.text.strip() != "":
            neighbours = json.loads(elem.text)
            res["node_id"] = neighbours["node_id"]
            for mac,neigh in neighbours.get("batadv",{}).items():
                for nmac,nattr in neigh["neighbours"].items():
                    for k,v in nattr.items():
                        res["neighbours"][mac.lower()][nmac.lower()][k.lower()] = v
                    for k,v in neighbours["wifi"].get(mac,{}).get("neighbours",{}).get(nmac,{}).items():
                        res["neighbours"][mac.lower()][nmac.lower()][k.lower()] = v

    def statistics_start(self, elem, res, host):
        pass
    def statistics_end(self, elem, res, host):
        if elem.text is not None and elem.text.strip() != "":
            res["statistics"] = json.loads(elem.text)

    def conn_start(self, elem, res, host):
        pass
    def conn_end(self, elem, res, host):
        if elem.text is not None and elem.text.strip() != "":
            for l in elem.text.split("\n"):
                l = l.strip().split()
                if len(l) >= 4:
                    res["conn"][l[1]][l[3]] = int(l[0])


    def nodeinfo_start(self, elem, res, host):
        pass
    def nodeinfo_end(self, elem, res, host):
        if elem.text is not None and elem.text.strip() != "":
            res["nodeinfo"] = json.loads(elem.text)

    def routes_start(self, elem, res, host):
        pass
    def routes_end(self, elem, res, host):
        if elem.text is not None and elem.text.strip() != "":
            for l in elem.text.split("\n"):
                l = l.strip().split()
                if len(l) < 4:
                    continue
                if l[4] not in res["routes"]:
                    res["routes"][ l[4] ] = []
                res["routes"][ l[4] ].append({ "gateway":l[2] })
                for i in range(5,len(l),2):
                    res["routes"][ l[4] ][ -1 ][ l[i] ] = l[i+1]
