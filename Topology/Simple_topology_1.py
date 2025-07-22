#!/usr/bin/env python3
import json
import math
import random
from pathlib import Path

# ----------------------------------------------------------------------
# Parameters you can tweak
# ----------------------------------------------------------------------
N_NODES          = 100
MIN_DIST_M       = 200         # minimum node-to-node spacing
MAX_RADIUS_M     = 1200      # furthest node from gateway
DEFAULT_SF       = 7           # initial spreading factor
JSON_OUT         = Path("topology.json")

def default_sf():
    return random.randint(7,12)

def default_channel():
    return random.randint(1,9)

random.seed(42)                # reproducible demo; drop for full random

# ----------------------------------------------------------------------
# Helper: generate a random point inside a circle, polar-uniform
# ----------------------------------------------------------------------
def random_point(max_r: float):
    r = max_r * math.sqrt(random.random())   # √ for uniform disc density
    theta = random.uniform(0, 2*math.pi)
    return r * math.cos(theta), r * math.sin(theta)

# ----------------------------------------------------------------------
# Build node list with rejection sampling
# ----------------------------------------------------------------------
nodes = []
while len(nodes) < N_NODES:
    x, y = random_point(MAX_RADIUS_M)
    if all(math.hypot(x-n["Location"]["x"], y-n["Location"]["y"]) >= MIN_DIST_M
           for n in nodes):
        nodes.append({
            "ID": str(len(nodes)+1),
            "Location": {"x": round(x, 2), "y": round(y, 2)},
            "default_sf": default_sf(),
            "default_channel": default_channel()
        })

# ----------------------------------------------------------------------
# Gateway at origin
# ----------------------------------------------------------------------
gateways = [{
    "ID": "1",
    "Location": {"x": 0, "y": 0}
}]

# ----------------------------------------------------------------------
# Dump to JSON
# ----------------------------------------------------------------------
topology = {"Nodes": nodes, "Gateways": gateways}
with JSON_OUT.open("w", encoding="utf-8") as f:
    json.dump(topology, f, indent=2)

print(f"Topology written to {JSON_OUT.resolve()}")


# for _ in range(20):
#     print(default_sf())