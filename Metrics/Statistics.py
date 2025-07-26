"""
Refined statistics helper for ALOHA‑style simulations
====================================================
Public usage remains the same::

    stats = Statistics.AlohaValidation()
    stats.add_run(probability_generation,
                  generated_packets,
                  successfully_received,
                  sim_duration_ms=500_000,  # optional
                  slot_ms=1_000,            # optional
                  n_nodes=10)               # optional
    stats.plot("SIMULATION 1")

If *sim_duration_ms* and *slot_ms* are provided the class derives the
**offered load G** and throughput **S** from real airtime; otherwise it
falls back to using the first positional argument (*gen_prob*) exactly as
before.  The extra keyword arguments therefore do **not** break existing
code.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

__all__ = ["AlohaValidation"]

# ---------------------------------------------------------------------
# Per‑run record
# ---------------------------------------------------------------------
@dataclass
class RunStat:
    offered_load_G: float        # dimensionless offered load
    throughput_S:   float        # dimensionless throughput (0–1)
    tx_packets:     int          # raw counters kept for reference
    rx_packets:     int

# ---------------------------------------------------------------------
# Main container
# ---------------------------------------------------------------------
@dataclass
class AlohaValidation:
    runs: List[RunStat] = field(default_factory=list)

    # --------------------------------------------------
    # Record one completed simulation
    # --------------------------------------------------
    def add_run(
        self,
        gen_prob: float,
        tx_packets: int,
        rx_packets: int,
        *,
        sim_duration_ms: Optional[int] = None,
        slot_ms:         int = 1_000,
        n_nodes:         Optional[int] = None,
    ) -> None:
        """Store a run.

        Args
        ----
        gen_prob : float
            Probability of transmission per slot *per node* (legacy input).
            Ignored if *sim_duration_ms* is given.
        tx_packets / rx_packets : int
            Counters returned by your simulation.
        sim_duration_ms : int, optional
            Wall‑clock duration simulated; activates automatic G & S
            derivation from counters.  Leave *None* to keep old behaviour.
        slot_ms : int
            Reference slot length – default 1 s as used in ALOHA papers.
        n_nodes : int, optional
            Needed only if you want a theoretical G = N·p on the plot when
            *sim_duration_ms* is not given.
        """
        # ----------------------------------------------------------------
        # Compute offered load G and throughput S
        # ----------------------------------------------------------------
        if sim_duration_ms is not None:
            equiv_slots = sim_duration_ms / slot_ms
            offered_load_G = tx_packets / equiv_slots if equiv_slots > 0 else 0.0
            throughput_S   = rx_packets / equiv_slots if equiv_slots > 0 else 0.0
        else:
            # Old style: user supplied probability already mapped to G.
            offered_load_G = gen_prob if n_nodes is None else gen_prob * n_nodes
            throughput_S   = (rx_packets / tx_packets) if tx_packets else 0.0

        self.runs.append(RunStat(offered_load_G, throughput_S,
                                 tx_packets, rx_packets))

    # --------------------------------------------------
    # Plot curves
    # --------------------------------------------------
    def plot(self, title_suffix: str = "") -> None:
        if not self.runs:
            raise RuntimeError("No runs recorded – did you call add_run()?")

        runs_sorted = sorted(self.runs, key=lambda r: r.offered_load_G)
        G = np.array([r.offered_load_G for r in runs_sorted])
        S = np.array([r.throughput_S   for r in runs_sorted])

        # ---------------- throughput curve ---------------------------
        plt.figure(figsize=(6, 4))
        plt.plot(G, S, "o-", label="Simulation")
        plt.plot(G, G * np.exp(-2 * G), "k--", label="$S = G e^{-2G}$ theory")
        plt.title(f"Throughput vs Offered Load {title_suffix}")
        plt.xlabel("Offered load  $G$")
        plt.ylabel("Throughput  $S$")
        plt.ylim(top=0.5)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        # ---------------- loss curve --------------------------------
        loss = 1 - np.divide(S, G, out=np.zeros_like(S), where=G > 0)
        plt.figure(figsize=(6, 4))
        plt.plot(G, loss * 100, "o-")
        plt.title(f"Packet‑loss probability {title_suffix}")
        plt.xlabel("Offered load  $G$")
        plt.ylabel("Loss (%)")
        plt.grid(True)
        plt.tight_layout()

        plt.show()
