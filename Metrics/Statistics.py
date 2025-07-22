# stats.py
from dataclasses import dataclass, field
from typing import List
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class RunStat:
    gen_prob:     float   # offered-load probability p (per slot or per node)
    tx_packets:   int     # total frames transmitted
    rx_packets:   int     # successfully received (collision-free) frames

    @property
    def offered_load_G(self) -> float:
        """Dimensionless offered load G = N·p for slotted ALOHA (or
        tx/slots in a full-time sim).  You may override this formula."""
        return self.gen_prob

    @property
    def throughput_S(self) -> float:
        """Throughput S = successful frames per frame-time."""
        return self.rx_packets / self.tx_packets if self.tx_packets else 0.0


@dataclass
class AlohaValidation:
    runs: List[RunStat] = field(default_factory=list)

    # --------------------------------------------------------------
    # record one finished simulation
    # --------------------------------------------------------------
    def add_run(self, gen_prob: float, tx_packets: int, rx_packets: int):
        self.runs.append(RunStat(gen_prob, tx_packets, rx_packets))

    # --------------------------------------------------------------
    # make the two classic plots
    # --------------------------------------------------------------
    def plot(self, title_suffix=""):
        if not self.runs:
            raise RuntimeError("No runs recorded")

        # sort by offered load for nice monotone curves
        runs_sorted = sorted(self.runs, key=lambda r: r.offered_load_G)

        G = np.array([r.offered_load_G for r in runs_sorted])
        S = np.array([r.throughput_S   for r in runs_sorted])
        loss = 1 - S / G

        # --- throughput plot --------------------------------------
        plt.figure(figsize=(6, 4))
        plt.plot(G, S, "o-", label="Simulated")
        # analytical slotted ALOHA curve S = G·e^-2G (dashed)
        plt.plot(G, G * np.exp(-2 * G), "k--", label="Theory  $S=G e^{-2G}$")
        plt.title(f"Throughput vs Offered Load{title_suffix}")
        plt.xlabel("Offered load  $G$")
        plt.ylabel("Throughput  $S$")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        # --- loss plot -------------------------------------------
        plt.figure(figsize=(6, 4))
        plt.plot(G, loss * 100, "o-")
        plt.title(f"Packet-loss probability{title_suffix}")
        plt.xlabel("Offered load  $G$")
        plt.ylabel("Loss  (%)")
        plt.grid(True)
        plt.tight_layout()

        plt.show()
