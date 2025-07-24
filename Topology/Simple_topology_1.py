#!/usr/bin/env python3
import json
import math
import random
from pathlib import Path



class TopologyGenerator:

    def __init__(self, N_NODES, MIN_DIST_M, MAX_RADIOUS_M, DEFAULT_SF, DEFAULT_CHANNEL):
        # ----------------------------------------------------------------------
        # Parameters you can tweak
        # ----------------------------------------------------------------------
        self.N_NODES = N_NODES
        self.MIN_DIST_M = MIN_DIST_M  # minimum node-to-node spacing
        self.MAX_RADIUS_M = MAX_RADIOUS_M  # furthest node from gateway
        self.DEFAULT_SF = DEFAULT_SF  # initial spreading factor
        self.DEFAULT_CHANNEL = DEFAULT_CHANNEL
        self.JSON_OUT = Path("topology.json")

    @staticmethod
    def default_sf():
        return random.randint(7,12)

    @staticmethod
    def default_channel():
        return random.randint(1,9)

    random.seed(42)                # reproducible demo; drop for full random

    # ----------------------------------------------------------------------
    # Helper: generate a random point inside a circle, polar-uniform
    # ----------------------------------------------------------------------
    def random_point(self, max_r: float):
        r = max_r * math.sqrt(random.random())   # √ for uniform disc density
        theta = random.uniform(0, 2*math.pi)
        return r * math.cos(theta), r * math.sin(theta)

    def generate(self):
        # ----------------------------------------------------------------------
        # Build node list with rejection sampling
        # ----------------------------------------------------------------------
        nodes = []
        while len(nodes) < self.N_NODES:
            x, y = self.random_point(self.MAX_RADIUS_M)
            if all(math.hypot(x-n["Location"]["x"], y-n["Location"]["y"]) >= self.MIN_DIST_M
                   for n in nodes):
                nodes.append({
                    "ID": str(len(nodes)+1),
                    "Location": {"x": round(x, 2), "y": round(y, 2)},
                    "default_sf": self.DEFAULT_SF,
                    "default_channel": self.DEFAULT_CHANNEL
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
        with self.JSON_OUT.open("w", encoding="utf-8") as f:
            json.dump(topology, f, indent=2)

        print(f"Topology written to {self.JSON_OUT.resolve()}")
