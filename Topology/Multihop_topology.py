#!/usr/bin/env python3
"""
Multihop Topology Generator

Creates a network topology designed for testing multihop protocols:
- Multiple clusters of nodes
- Nodes within each cluster are close together (can communicate directly, SF7, -123 dBm threshold)
- Clusters are spaced such that nodes must relay through intermediate nodes
- All nodes are SF7 for multihop protocol testing

Topology structure:
- Primary cluster: 2-3 nodes within 100-150m of each other (direct communication range)
- Secondary clusters: Additional groups of 2-3 nodes
- Inter-cluster distance: 300-500m (requires relay through intermediate nodes)
"""

import json
import math
import random
from pathlib import Path


class MultihopTopologyGenerator:

    def __init__(self, num_clusters=3, nodes_per_cluster=3, intra_cluster_dist=1000,
                 inter_cluster_dist=1500, gateway_range=5600, out_of_range_dist=5700,
                 default_sf=7, default_channel=1):
        """
        Initialize the multihop topology generator.

        Args:
            num_clusters: Number of node clusters to create
            nodes_per_cluster: Nodes per cluster (2-3 recommended)
            intra_cluster_dist: Max distance within a cluster (meters)
            inter_cluster_dist: Nominal distance between cluster centers (meters)
            gateway_range: Max distance for nodes to be in gateway range (meters)
            out_of_range_dist: Distance for nodes outside gateway range (meters)
            default_sf: Spreading factor (must be 7 for multihop)
            default_channel: Default channel (1-9 for EU868)
        """
        self.num_clusters = num_clusters
        self.nodes_per_cluster = nodes_per_cluster
        self.intra_cluster_dist = intra_cluster_dist
        self.inter_cluster_dist = inter_cluster_dist
        self.gateway_range = gateway_range
        self.out_of_range_dist = out_of_range_dist
        self.default_sf = default_sf
        self.default_channel = default_channel
        self.JSON_OUT = Path("Topology/topology.json")
        random.seed(40)  # Reproducible topology

    @staticmethod
    def random_point_in_circle(max_r: float) -> tuple:
        """Generate a random point uniformly distributed in a circle."""
        r = max_r * math.sqrt(random.random())  # √ for uniform disc density
        theta = random.uniform(0, 2 * math.pi)
        return r * math.cos(theta), r * math.sin(theta)

    def generate(self):
        """Generate multihop topology with multiple clusters."""
        nodes = []
        node_id = 1

        # Place clusters in a grid pattern
        cluster_positions = self._generate_cluster_positions()

        for cluster_idx, cluster_center in enumerate(cluster_positions):
            # Add nodes_per_cluster nodes to this cluster
            nodes_in_cluster = 0
            attempts = 0
            max_attempts = 1000

            while nodes_in_cluster < self.nodes_per_cluster and attempts < max_attempts:
                # Generate random point within cluster radius
                offset_x, offset_y = self.random_point_in_circle(self.intra_cluster_dist)
                x = cluster_center[0] + offset_x
                y = cluster_center[1] + offset_y

                # Check minimum distance to other nodes (avoid exact overlap)
                min_distance_ok = all(
                    math.hypot(x - n["Location"]["x"], y - n["Location"]["y"]) >= 10
                    for n in nodes
                )

                if min_distance_ok:
                    nodes.append({
                        "ID": f"{node_id}-end",
                        "Location": {"x": round(x, 2), "y": round(y, 2)},
                        "default_sf": self.default_sf,
                        "default_channel": self.default_channel,
                        "cluster": cluster_idx
                    })
                    node_id += 1
                    nodes_in_cluster += 1

                attempts += 1

        # Gateway at origin
        gateways = [{
            "ID": "1-gw",
            "Location": {"x": 0, "y": 0}
        }]

        # Dump to JSON
        topology = {"Nodes": nodes, "Gateways": gateways}
        with self.JSON_OUT.open("w", encoding="utf-8") as f:
            json.dump(topology, f, indent=2)

        # Print statistics
        print(f"Multihop topology generated:")
        print(f"  Clusters: {self.num_clusters}")
        print(f"  Nodes per cluster: {self.nodes_per_cluster}")
        print(f"  Total nodes: {len(nodes)}")
        print(f"  Intra-cluster distance: {self.intra_cluster_dist}m")
        print(f"  Inter-cluster distance: {self.inter_cluster_dist}m")
        print(f"  Gateway range: {self.gateway_range}m")
        print(f"  Out-of-range distance: {self.out_of_range_dist}m")
        print(f"  Spreading Factor: {self.default_sf}")
        print(f"\nCluster positions (from gateway at origin):")
        for idx, pos in enumerate(cluster_positions):
            dist = math.hypot(pos[0], pos[1])
            angle = math.degrees(math.atan2(pos[1], pos[0]))
            in_range = "IN RANGE" if dist <= self.gateway_range else "OUT OF RANGE"
            print(f"    Cluster {idx}: ({pos[0]:.1f}, {pos[1]:.1f}) - {dist:.1f}m at {angle:.1f}° [{in_range}]")
        print(f"\n  Topology written to {self.JSON_OUT.resolve()}")

        return topology

    def _generate_cluster_positions(self) -> list:
        """
        Generate cluster center positions with maximum spatial distribution:
        - First cluster: at gateway_range (in gateway coverage, master cluster)
        - Remaining clusters: spread radially OUTWARD from master cluster

        Strategy:
        - All relay clusters are positioned relative to the master cluster direction (0°)
        - Distribute evenly in angular space to maximize coverage
        - Calculate positions to ensure they spread AWAY from gateway, not toward it

        Returns:
            List of (x, y) tuples for cluster centers
        """
        positions = []

        if self.num_clusters == 0:
            return positions

        # Cluster 0: Master cluster in gateway range (at gateway_range distance, 0° angle)
        master_x, master_y = self.gateway_range, 0
        positions.append((master_x, master_y))

        if self.num_clusters == 1:
            return positions

        # Determine angular distribution to maximize spread
        remaining_clusters = self.num_clusters - 1

        if remaining_clusters == 1:
            # Single relay cluster: extend further along the same direction (0°)
            # Position it at gateway_range + inter_cluster_dist
            positions.append((self.gateway_range + self.inter_cluster_dist, 0))

        elif remaining_clusters == 2:
            # Two relay clusters: spread at equal angles from master direction
            # Use 60° and -60° offsets (120° total separation)
            for angle_offset_deg in [60, -60]:
                angle = math.radians(angle_offset_deg)
                # Position relative to master cluster
                x = master_x + self.inter_cluster_dist * math.cos(angle)
                y = master_y + self.inter_cluster_dist * math.sin(angle)
                positions.append((x, y))

        else:
            # Three or more relay clusters: distribute evenly around master cluster
            # Angular distribution centered on the master's direction
            angle_step = 360 / remaining_clusters
            start_angle = -180 + (angle_step / 2)  # Center distribution around 0°

            for i in range(remaining_clusters):
                angle_deg = start_angle + i * angle_step
                angle = math.radians(angle_deg)

                # Use varying distances for depth: alternate between inter_cluster_dist and out_of_range_dist
                if i % 2 == 0:
                    distance = self.inter_cluster_dist
                else:
                    distance = self.out_of_range_dist

                # Position relative to master cluster to ensure outward spread
                x = master_x + distance * math.cos(angle)
                y = master_y + distance * math.sin(angle)
                positions.append((x, y))

        return positions

    def get_statistics(self):
        """Print network connectivity statistics."""
        with open(self.JSON_OUT, 'r') as f:
            topology = json.load(f)

        nodes = topology["Nodes"]

        # Calculate distances between all nodes
        print("\nNetwork connectivity statistics:")
        print(f"Total nodes: {len(nodes)}")

        # Nodes by cluster
        clusters = {}
        for node in nodes:
            cluster = node.get("cluster", 0)
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(node)

        print(f"Clusters: {len(clusters)}")
        for cluster_id, cluster_nodes in sorted(clusters.items()):
            print(f"  Cluster {cluster_id}: {len(cluster_nodes)} nodes")

        # Check inter-node distances
        print("\nInter-node distances (sample):")
        for i, node1 in enumerate(nodes[:5]):
            for j, node2 in enumerate(nodes[i+1:6]):
                dist = math.hypot(
                    node1["Location"]["x"] - node2["Location"]["x"],
                    node1["Location"]["y"] - node2["Location"]["y"]
                )
                print(f"  {node1['ID']} ↔ {node2['ID']}: {dist:.1f}m")
