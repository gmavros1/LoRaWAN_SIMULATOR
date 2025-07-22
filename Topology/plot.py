#!/usr/bin/env python3
# plot_topology.py
import json
import matplotlib.pyplot as plt
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
JSON_IN   = Path("topology.json")     # path to the file you generated
IMG_OUT   = Path("topology.png")      # output image file
FIGSIZE   = (8, 8)                    # inches

# ----------------------------------------------------------------------
# Load topology
# ----------------------------------------------------------------------
with JSON_IN.open(encoding="utf-8") as f:
    topo = json.load(f)

nodes     = topo["Nodes"]
gateways  = topo["Gateways"]

# ----------------------------------------------------------------------
# Extract coordinates
# ----------------------------------------------------------------------
node_x  = [n["Location"]["x"] for n in nodes]
node_y  = [n["Location"]["y"] for n in nodes]
node_id = [n["ID"]             for n in nodes]

gw_x    = [g["Location"]["x"] for g in gateways]
gw_y    = [g["Location"]["y"] for g in gateways]
gw_id   = [g["ID"]             for g in gateways]

# ----------------------------------------------------------------------
# Plot
# ----------------------------------------------------------------------
plt.figure(figsize=FIGSIZE)
plt.scatter(node_x, node_y, marker="o", s=30, label="Nodes")
plt.scatter(gw_x,   gw_y,   marker="*", s=150, label="Gateway")

# annotate IDs
for x, y, txt in zip(node_x, node_y, node_id):
    plt.text(x, y, txt, fontsize=8, ha="left", va="bottom")
for x, y, txt in zip(gw_x, gw_y, gw_id):
    plt.text(x, y, f"GW{txt}", fontsize=9, ha="right", va="top",
             fontweight="bold")

plt.title("LoRa Topology")
plt.xlabel("x [m]")
plt.ylabel("y [m]")
plt.gca().set_aspect("equal", adjustable="box")
plt.grid(True)
plt.legend()

# save and show
plt.savefig(IMG_OUT, dpi=300, bbox_inches="tight")
print(f"Saved figure to {IMG_OUT.resolve()}")
plt.show()
