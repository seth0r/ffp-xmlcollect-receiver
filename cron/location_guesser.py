from base import Process
import os
import time
import math
import random
from collections import defaultdict
from pymongo import MongoClient
from sympy import symbols, solve, solve_poly_system, Eq

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km * 1000

class LocationGuesser(Process):
    INTERVAL = 3600
    def run(self):
        self.mdbe = MongoClient( os.getenv( "MONGODB_URI","mongodb://localhost/" ) )
        self.mdb = self.mdbe[os.getenv("MONGODB_DB")]
        now = time.time()
        for node in self.mdb["nodes"].find({"location":{"$exists":False},"last_ts":{"$gte":now - 24*60*60}}):
            random.seed(node["_id"])
            neigh = {}
            ntqs = defaultdict(list)
            for l in self.mdb["neighbours"].find({ "local":{"$in":node["ifaddr"]}, "time":{"$gte":now - 24*60*60}, "stat.tq":{"$gt":0} }):
                n = self.mdb["nodes"].find_one({ "ifaddr":l["remote"], "location":{"$exists":True}, "last_ts":{"$gte":now - 24*60*60} })
                if n:
                    neigh[ n["_id"] ] = n
                    ntqs[ n["_id"] ].append( l["stat"]["tq"] / 255 )
            for l in self.mdb["neighbours"].find({ "remote":{"$in":node["ifaddr"]}, "time":{"$gte":now - 24*60*60}, "stat.tq":{"$gt":0} }):
                n = self.mdb["nodes"].find_one({ "ifaddr":l["local"], "location":{"$exists":True}, "last_ts":{"$gte":now - 24*60*60} })
                if n:
                    neigh[ n["_id"] ] = n
                    ntqs[ n["_id"] ].append( l["stat"]["tq"] / 255 )
            if len(neigh) == 0:
                continue
            for nid,tqs in list(ntqs.items()):
                ntqs[nid] = sum(tqs) / len(tqs)
            ntqs = sorted( ntqs.items(), key=lambda ntq: ntq[1], reverse=True )
            self.logger.info("%s has %d neighbours.", node["host"], len(neigh) )
            for nid,tq in ntqs:
                self.logger.info("  %s: %f using %f as pseudo distance", neigh[nid]['host'], tq, 1 / (tq**2) )
            x,y = self.guess_location( neigh, ntqs )
            if x and y:
                self.mdb["node_settings"].update({"_id":node["_id"]},{"$set":{"location_guess":[x,y]}},upsert=True)
            self.logger.info("  Guessed location of %s: %f : %f", node["host"], x, y)

    def guess_location(self, neigh, ntqs ):
        try:
            if len(neigh) >= 3:
                self.logger.info("  Guessing location based on three neighbour nodes...")
                res = self.trilaterate( neigh, ntqs )
                if res: return res
            if len(neigh) >= 2:
                self.logger.info("  Guessing location based on two neighbour nodes and some random value...")
                res = self.bilaterate_rnd( neigh, ntqs )
                if res: return res
            if len(neigh) >= 1:
                self.logger.info("  Guessing random location around neighbour node...")
                return self.near_rnd( neigh, ntqs )
        except:
            self.logger.exception("Guessing failed.")
        return None,None

    def trilaterate(self, neighbours, tqs):
        x,y,f = symbols('x y f', real=True)
        eqs = []
        for nid,tq in tqs[:3]:
            xn = int(neighbours[nid]["location"][0]*1000000)
            yn = int(neighbours[nid]["location"][1]*1000000)
            d = int(1/(tq**2)*1000000)
            eqs.append( Eq( (x-xn)**2 + (y-yn)**2, (f*d)**2 ) )
        res = solve(eqs, (x, y, f))
        if res:
            x,y,f = sorted(filter(lambda r: r[2]>0, res), key = lambda r: r[2])[0]
            return float(x)/1000000,float(y)/1000000

    def bilaterate_rnd(self, neighbours, tqs):
        x,y,f = symbols('x y f', real=True)
        x1 = int(neighbours[tqs[0][0]]["location"][0]*1000000)
        y1 = int(neighbours[tqs[0][0]]["location"][1]*1000000)
        d1 = int(1/(tqs[0][1]**2)*1000000)
        x2 = int(neighbours[tqs[1][0]]["location"][0]*1000000)
        y2 = int(neighbours[tqs[1][0]]["location"][1]*1000000)
        d2 = int(1/(tqs[1][1]**2)*1000000)
        minf = (((x1 - x2)**2 + (y1-y2)**2)**0.5) / (d1 + d2)
        maxf = (((x1 - x2)**2 + (y1-y2)**2)**0.5) / abs(d1 - d2)
        eq1 = Eq( (x-x1)**2 + (y-y1)**2, (f*d1)**2 )
        eq2 = Eq( (x-x2)**2 + (y-y2)**2, (f*d2)**2 )
        xv,yv = random.choice( solve((eq1,eq2), (x, y)) )
        fv = minf + (maxf-minf) * random.random()
        self.logger.info(str([minf,maxf,fv]))
        xv = xv.subs(f,fv)
        yv = yv.subs(f,fv)
        return float(xv)/1000000,float(yv)/1000000

    def near_rnd(self, neighbours, tqs):
        x = neighbours[tqs[0][0]]["location"][0] - 0.001 + random.random() * 0.002,
        y = neighbours[tqs[0][0]]["location"][1] - 0.001 + random.random() * 0.002,
        return x,y
