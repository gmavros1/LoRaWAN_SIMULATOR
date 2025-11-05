#!/usr/bin/env python3
import argparse, json, math, sys
from typing import List, Dict, Tuple

def load_topology(path: str):
    with (sys.stdin if path == "-" else open(path, "r")) as f:
        topo = json.load(f)

    def extract_points(key: str):
        pts = []
        for item in topo.get(key, []):
            try:
                pid = item["ID"]
                x = float(item["Location"]["x"])
                y = float(item["Location"]["y"])
                pts.append((pid, x, y))
            except Exception as e:
                raise ValueError(f"Bad or missing fields in {key} entry: {item}") from e
        return pts

    nodes = extract_points("Nodes")
    gws = extract_points("Gateways")
    if not nodes:
        raise ValueError("No Nodes found in topology.")
    if not gws:
        # Not fatal—some uses may want only node↔node
        sys.stderr.write("Warning: no Gateways found in topology.\n")
    return nodes, gws

def d(p1: Tuple[float,float], p2: Tuple[float,float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def print_node_to_gateway(nodes, gws, csv, prec, units):
    if not gws:
        return
    if csv:
        print("node_id,gw_id,distance_"+units)
    else:
        print("== Distances: Node → Gateway ==")
    for nid, nx, ny in nodes:
        for gid, gx, gy in gws:
            dist = round(d((nx, ny), (gx, gy)), prec)
            if csv:
                print(f"{nid},{gid},{dist}")
            else:
                print(f"{nid:>8} → {gid:>8}: {dist} {units}")
    if not csv:
        print()

def print_node_pairs(nodes, csv, prec, units):
    if csv:
        print("id1,id2,distance_"+units)
    else:
        print("== Distances: Node ↔ Node (unique pairs) ==")
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            (id1, x1, y1) = nodes[i]
            (id2, x2, y2) = nodes[j]
            dist = round(d((x1, y1), (x2, y2)), prec)
            if csv:
                print(f"{id1},{id2},{dist}")
            else:
                print(f"{id1:>8} ↔ {id2:>8}: {dist} {units}")
    if not csv:
        print()

def print_matrix(points: List[Tuple[str, float, float]], prec, units):
    ids = [p[0] for p in points]
    coords = [(p[1], p[2]) for p in points]
    # header
    widths = [max(len("id"), max(len(i) for i in ids))]
    row = ["id".rjust(widths[0])]
    for i in ids:
        widths.append(max(len(i), len(str(prec))+6))
        row.append(i.rjust(widths[-1]))
    print(" ".join(row))
    # rows
    for i, (id_i, xi, yi) in enumerate(points):
        row = [id_i.rjust(widths[0])]
        for j, (xj, yj) in enumerate(coords):
            val = 0.0 if i == j else d((xi, yi), (xj, yj))
            row.append(f"{val:.{prec}f}".rjust(widths[j+1]))
        print(" ".join(row))
    print(f"\n(all distances in {units})\n")

def main():
    ap = argparse.ArgumentParser(
        description="Compute distances from a topology JSON (use '-' to read from stdin).")
    ap.add_argument("path", nargs="?", default="topology.json",
                    help="Path to topology JSON (default: topology.json). Use '-' for stdin.")
    ap.add_argument("--csv", action="store_true", help="CSV output instead of pretty text.")
    ap.add_argument("--precision", type=int, default=2, help="Decimal places (default: 2).")
    ap.add_argument("--units", default="m", help="Units label for printing (default: m).")
    ap.add_argument("--matrix", action="store_true",
                    help="Also print a full distance matrix.")
    ap.add_argument("--include-gw-in-matrix", action="store_true",
                    help="Include gateways in the distance matrix (by default only nodes).")
    args = ap.parse_args()

    nodes, gws = load_topology(args.path)

    # 1) Node → Gateway distances
    print_node_to_gateway(nodes, gws, args.csv, args.precision, args.units)

    # 2) Node ↔ Node distances (unique pairs)
    print_node_pairs(nodes, args.csv, args.precision, args.units)

    # 3) Optional distance matrix
    if args.matrix:
        if args.include_gw_in_matrix and gws:
            points = nodes + gws
        else:
            points = nodes
        if not args.csv:  # matrix shown only in pretty mode
            print("== Distance Matrix ==")
        print_matrix(points, args.precision, args.units)

if __name__ == "__main__":
    main()
